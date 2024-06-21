import json
import pathlib
import typing

import click
from click_option_group import optgroup
import tqdm
from dask import distributed
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.compute as pc
import pyarrow.parquet as pq

from openff.toolkit import Molecule, ForceField
from yammbs.checkmol import analyze_functional_groups
from openff.nagl.utils._parallelization import batch_distributed


def label(qm_entry, forcefield):
    mol = Molecule.from_smiles(qm_entry["cmiles"], allow_undefined_stereo=True)
    inchi = mol.to_inchi(fixed_hydrogens=True)

    labels = forcefield.label_molecules(mol.to_topology())[0]

    base_entry = {
        "mapped_smiles": qm_entry["cmiles"],
        "inchi": inchi,
        "record_id": qm_entry["record_id"],
        "type": qm_entry["type"],
    }

    entries = []
    for parameter_name, assigned in labels.items():
        for value in assigned.values():
            entry = dict(base_entry)
            entry["parameter_id"] = value.id
            entry["parameter_type"] = parameter_name
            entries.append(entry)

    groups = analyze_functional_groups(qm_entry["cmiles"])
    for group in groups:
        entry = dict(base_entry)
        entry["parameter_id"] = group.value
        entry["parameter_type"] = "functional_group"
        entries.append(entry)

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
    for key, pattern in PATTERNS.items():
        if mol.chemical_environment_matches(pattern):
            entry = dict(base_entry)
            entry["parameter_id"] = key
            entry["parameter_type"] = "additional"
            entries.append(entry)
    
    return entries


def batch_label(qm_entries, forcefield = None):
    entries = []
    ff = ForceField(forcefield, allow_cosmetic_attributes=True)
    for qm_entry in tqdm.tqdm(qm_entries):
        entries.extend(label(qm_entry, ff))
    return entries




@click.command()
@click.option(
    "--data-set",
    "data_sets",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    multiple=True,
    required=True,
    help="The path to the input data sets (JSON).",
)
@click.option(
    "--forcefield",
    type=str,
    required=True,
    help="The path to the force field file.",
)
@click.option(
    "--output",
    "output_dataset",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    required=True,
    help="The path to the output data set (directory, parquet format).",
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
@optgroup.group("Cluster configuration", help="Options to configure cluster workers.")
@optgroup.option(
    "--memory",
    help="The amount of memory (GB) to request per queue worker.",
    type=int,
    default=3,
    show_default=True,
)
@optgroup.option(
    "--walltime",
    help="The maximum wall-clock hours to request per queue worker.",
    type=int,
    default=2,
    show_default=True,
)
@optgroup.option(
    "--queue",
    help="The SLURM queue to submit workers to.",
    type=str,
    default="cpuqueue",
    show_default=True,
)
@optgroup.option(
    "--conda-environment",
    help="The conda environment that SLURM workers should run using.",
    type=str,
)
def main(
    data_sets: list[str],
    forcefield: str,
    output_dataset: str,
    worker_type: typing.Literal["slurm", "local"] = "local",
    queue: str = "free",
    conda_environment: str = "yammbs",
    memory: int = 4,  # GB
    walltime: int = 32,  # hours
    batch_size: int = 300,
    n_workers: int = -1,
):
    all_qm_entries = []
    for data_set in data_sets:
        with open(data_set, "r") as file:
            contents = json.load(file)
        all_qm_entries.extend(
            contents["entries"]["https://api.qcarchive.molssi.org:443/"]
        )

    print(f"Loaded {len(all_qm_entries)} QM entries")

    # Check for existing output
    output_directory = pathlib.Path(output_dataset)
    output_directory.mkdir(parents=True, exist_ok=True)
    start_index = 0

    with batch_distributed(
        all_qm_entries,
        batch_size=batch_size,
        worker_type=worker_type,
        queue=queue,
        conda_environment=conda_environment,
        memory=memory,
        walltime=walltime,
        n_workers=n_workers,
    ) as batcher:
        futures = list(batcher(
            batch_label,
            forcefield=forcefield
        ))
        for future in tqdm.tqdm(
            distributed.as_completed(futures, raise_errors=False),
            total=len(futures),
            desc="Updating entries",
        ):
            batch = future.result()
            batch_table = pa.Table.from_pylist(batch)
            table_path = output_directory / f"batch-{start_index:04d}.parquet"
            pq.write_table(batch_table, table_path)
            print(f"Wrote {len(batch)} to {table_path}")
            start_index += 1

    print(batch_table.schema)


if __name__ == "__main__":
    main()
