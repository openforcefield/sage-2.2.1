import pathlib
import typing

import click
from click_option_group import optgroup
import tqdm

import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow.dataset as ds


import numpy as np
from yammbs import MoleculeStore

def benchmark_single(
    row,
    parameter_id: str,
    parameter_smirks: str,
):
    from openff.toolkit import Molecule
    from openff.units import unit
    import numpy as np
    import MDAnalysis as mda

    mol = Molecule.from_mapped_smiles(
        row["mapped_smiles"],
        allow_undefined_stereo=True,
    )
    qm_coordinates = np.array(row["qm_coordinates"]).reshape((-1, 3))
    mm_coordinates = np.array(row["mm_coordinates"]).reshape((-1, 3))
    mol._conformers = [qm_coordinates * unit.angstrom]
    u_qm = mda.Universe(mol.to_rdkit())
    u_mm = mda.Universe(mol.to_rdkit())
    u_mm.atoms.positions = mm_coordinates

    ID_TO_PARAMETER_TYPE = {
        "b": ("bond", "Bonds"),
        "a": ("angle", "Angles"),
        "t": ("dihedral", "ProperTorsions"),
        "i": ("improper", "ImproperTorsions"),
    }
    mda_parameter, parameter_type = ID_TO_PARAMETER_TYPE[parameter_id[0]]

    all_entries = []
    matches = mol.chemical_environment_matches(parameter_smirks)

    for indices in matches:
        ix = np.array(indices)
        # reorder improper torsions
        if parameter_type == "ImproperTorsions":
            ix = ix[[1, 0, 2, 3]]

        qm_value = getattr(u_qm.atoms[ix], mda_parameter).value()
        mm_value = getattr(u_mm.atoms[ix], mda_parameter).value()

        entry = {
            "name": row["name"],
            "qcarchive_id": row["qcarchive_id"],
            "mapped_smiles": row["mapped_smiles"],
            "parameter": parameter_id,
            "smirks": parameter_smirks,
            "indices": list(indices),
            "qm": qm_value,
            "mm": mm_value,
        }
        all_entries.append(entry)
    return all_entries



def batch_compute(
    rows: list[dict[str, typing.Any]],
    forcefield: str = None,
    parameter_id: str = None,
):
    from openff.toolkit import ForceField

    PATTERNS = {
        "sx4": "[*:1]-[#16X4:2](-*)(-*)-[*:3]",
        "sulfamide": '[#7:1]-[#16X4:2](=[#8])(=[#8])~[#7:3]',
        "sulfonamide": '[#7:1]-[#16X4:2](=[#8])(=[#8])~[*:3]',
        "r3": '[r3:1]',
        "r4": '[r4:1]',
        "r5": '[r5:1]',
        "r5S": '[r5:1]1@[#16;r5:2]@[r5:3]@[r5]@[r5]1',
        "r4O": '[#8;r4:1]',
        "r4N": '[#7;r4:1]',
        "r3C": '[#6;r3:1]1@[#6;r3:2]@[#6;r3:3]1',
        "r3het": '[#6;r3:1]1@[!#6;r3:2]@[#6;r3:3]1',
        "r4C": '[#6;r4:1]1@[#6;r4:2]@[#6;r4:3]@[#6;r4]1',
    }
    if parameter_id in PATTERNS:
        parameter_smirks = PATTERNS[parameter_id]
    else:
        # fragile but confident these are the right smirks
        ff = ForceField(forcefield)
        for handler in ff._parameter_handlers.values():
            for parameter in handler.parameters:
                if parameter.id == parameter_id:
                    parameter_smirks = parameter.smirks
                    break
            else:
                continue


    results = []
    errors = []

    for row in tqdm.tqdm(rows):
        try:
            entries = benchmark_single(row, parameter_id, parameter_smirks)
        except Exception as e:
            errors.append(str(e))
        else:
            results.extend(entries)
    return results, errors


@click.command()
@click.option(
    "--input",
    "input_dataset_path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    required=True,
)
@click.option(
    "--output",
    "output_dataset_path",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    required=True,
)
@click.option(
    "--forcefield",
    type=str,
    required=True,
    help="The path to the force field file.",
)
@click.option(
    "--parameter-id",
    type=str,
    required=True,
)
@optgroup.group("Parallelization configuration")
@optgroup.option(
    "--n-workers",
    help="The number of workers to distribute the labelling across. Use -1 to request "
    "one worker per batch.",
    type=int,
    default=1,
    show_default=True,
)
@optgroup.option(
    "--worker-type",
    help="The type of worker to distribute the labelling across.",
    type=click.Choice(["lsf", "local", "slurm"]),
    default="local",
    show_default=True,
)
@optgroup.option(
    "--batch-size",
    help="The number of molecules to processes at once on a particular worker.",
    type=int,
    default=500,
    show_default=True,
)
@optgroup.group("LSF configuration", help="Options to configure LSF workers.")
@optgroup.option(
    "--memory",
    help="The amount of memory (GB) to request per LSF queue worker.",
    type=int,
    default=3,
    show_default=True,
)
@optgroup.option(
    "--walltime",
    help="The maximum wall-clock hours to request per LSF queue worker.",
    type=int,
    default=2,
    show_default=True,
)
@optgroup.option(
    "--queue",
    help="The LSF queue to submit workers to.",
    type=str,
    default="cpuqueue",
    show_default=True,
)
@optgroup.option(
    "--conda-environment",
    help="The conda environment that LSF workers should run using.",
    type=str,
)
def main(
    input_dataset_path: str,
    output_dataset_path: str,
    forcefield: str,
    parameter_id: str,
    worker_type: typing.Literal["lsf", "local"] = "local",
    queue: str = "cpuqueue",
    conda_environment: str = "openff-nagl",
    memory: int = 4,  # GB
    walltime: int = 32,  # hours
    batch_size: int = 300,
    n_workers: int = -1,
):
    from openff.nagl.utils._parallelization import batch_distributed
    from dask import distributed
    
    dataset = ds.dataset(input_dataset_path)
    expression = pc.field(parameter_id)
    dataset = dataset.filter(expression)
    columns = [
        "name",
        "qcarchive_id",
        "mapped_smiles",
        "mm_coordinates",
        "qm_coordinates",
    ]
    all_rows = dataset.to_table(columns=columns).to_pylist()
    print(f"Loaded {len(all_rows)} rows from {input_dataset_path}")

    output_directory = pathlib.Path(output_dataset_path)
    output_directory.mkdir(exist_ok=True, parents=True)

    start_index = 0
    try:
        print(f"Querying {output_directory}")
        existing = ds.dataset(output_directory)
        if existing.count_rows():
            new_columns = ["name", "qcarchive_id"]
            name_and_qca_ids = {
                (row["name"], row["qcarchive_id"])
                for row in existing.to_table(columns=new_columns).to_pylist()
            }
            all_rows = [
                row
                for row in all_rows
                if (row["name"], row["qcarchive_id"]) not in name_and_qca_ids
            ]
            print(f"Filtered to {len(all_rows)} rows not in {output_directory}")

            start_index = len(existing.files)
    except BaseException as e:
        print(e)

    with batch_distributed(
        all_rows,
        batch_size=batch_size,
        worker_type=worker_type,
        queue=queue,
        conda_environment=conda_environment,
        memory=memory,
        walltime=walltime,
        n_workers=n_workers,
    ) as batcher:
        futures = list(batcher(
            batch_compute,
            forcefield=forcefield,
            parameter_id=parameter_id,
        ))
        for future in tqdm.tqdm(
            distributed.as_completed(futures, raise_errors=False),
            total=len(futures),
            desc="Updating entries",
        ):
            batch_entries, errors = future.result()
            if errors:
                print("\n".join(errors))

            batch_table = pa.Table.from_pylist(batch_entries)
            print(batch_table.schema)

            table_path = output_directory / f"batch-{start_index:04d}.parquet"
            if len(batch_entries):
                pq.write_table(batch_table, table_path)
                print(f"Wrote {len(batch_entries)} to {table_path}")
                start_index += 1
            


if __name__ == "__main__":
    main()
