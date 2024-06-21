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

def get_best_all_atom_rmsd(molecule, qm_coordinates, mm_coordinates):
    from openff.toolkit.topology import Molecule
    from openff.units import unit
    from openeye import oechem

    molecule1 = Molecule(molecule)
    molecule1._conformers = [
        np.array(qm_coordinates).reshape((-1, 3)) * unit.angstrom
    ]
    molecule2 = Molecule(molecule)
    molecule2._conformers = [
        np.array(mm_coordinates).reshape((-1, 3)) * unit.angstrom
    ]
    return oechem.OERMSD(
        molecule1.to_openeye(),
        molecule2.to_openeye(),
        True,  # automorph
        False, # heavyOnly
        True,  # overlay
    )
    

def benchmark_single(
    store: MoleculeStore,
    force_field: str,
    inchi_key: str,
    name: str,
    ff_name: str,
):
    from openff.units import unit
    from openff.toolkit import Molecule, ForceField
    from openff.interchange.drivers import get_openmm_energies
    from yammbs.analysis import get_rmsd, get_tfd, get_internal_coordinate_rmsds

    molecule_id = store.get_molecule_id_by_inchi_key(inchi_key)

    # get all existing QM records
    qm_conformer_records = {
        record.qcarchive_id: record
        for record in store.get_qm_conformer_records_by_molecule_id(molecule_id)
    }
    mm_conformer_records = {
        record.qcarchive_id: record
        for record in store.get_mm_conformer_records_by_molecule_id(molecule_id, ff_name)
    }
    
    # label molecule with parameters (for QM vs MM dashboard or parameter splits)
    mapped_smiles = list(qm_conformer_records.values())[0].mapped_smiles
    ff = ForceField(force_field, allow_cosmetic_attributes=True)
    molecule = Molecule.from_smiles(mapped_smiles, allow_undefined_stereo=True)
    parameter_labels = {}
    for parameter_name, handler in ff._parameter_handlers.items():
        for parameter in handler.parameters:
            # key = f"{parameter_name}_{parameter.smirks}"
            key = parameter.id
            parameter_labels[key] = False
    
    labels = ff.label_molecules(molecule.to_topology())[0]
    for parameter_name, assigned in labels.items():
        for value in assigned.values():
            # key = f"{parameter_name}_{value.smirks}"
            key = value.id
            parameter_labels[key] = True


    # patterns from 2.2.0 repo
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
        parameter_labels[key] = bool(molecule.chemical_environment_matches(pattern))

    result_entries = []
    all_qca_ids = sorted(qm_conformer_records)

    threshold = 0.4  # hardcode for now

    # compute actual metrics, e.g. ddE, RMSD, internal RMSDs, etc
    for qcarchive_id, mm_record in mm_conformer_records.items():
        qm_record = qm_conformer_records[qcarchive_id]

        molecule = Molecule.from_mapped_smiles(
            mm_record.mapped_smiles,
            allow_undefined_stereo=True,
        )
        n_heavy_atoms = sum(1 for atom in molecule.atoms if atom.atomic_number > 1)

        entry = {
            "name": name,
            "inchi": inchi_key,
            "qcarchive_id": qcarchive_id,
            "all_qcarchive_ids": all_qca_ids,
            "molecule_id": mm_record.molecule_id,
            "mapped_smiles": mm_record.mapped_smiles,
            "n_atoms": len(molecule.atoms),
            "n_heavy_atoms": n_heavy_atoms,
            "mm_coordinates": mm_record.coordinates.flatten(),
            "qm_coordinates": qm_record.coordinates.flatten(),
        }

        rmsd_aa = get_best_all_atom_rmsd(
            molecule, qm_record.coordinates,
            mm_record.coordinates
        )
        
        try:
            rmsd = get_rmsd(molecule, qm_record.coordinates, mm_record.coordinates)
            tfd = get_tfd(molecule, qm_record.coordinates, mm_record.coordinates)
        except BaseException as e:
            print(str(e))
            continue

        internal_coordinate_rmsds = get_internal_coordinate_rmsds(
            molecule,
            qm_record.coordinates,
            mm_record.coordinates
        )

        molecule._conformers = [mm_record.coordinates.reshape((-1, 3)) * unit.angstrom]
        ic = ff.create_interchange(molecule.to_topology())
        energies = get_openmm_energies(ic)

        entry["qm_energy"] = qm_record.energy
        entry["mm_energy"] = mm_record.energy
        for key, value in energies.energies.items():
            entry[f"energy_{key}"] = value.m_as(unit.kilocalories_per_mole)
        # set ddE relevant quantities now so column order comes before SMARTS etc
        entry["minimum_qcarchive_id"] = -1
        entry[f"minimum_qcarchive_id_{threshold}"] = -1
        entry["ddE"] = np.nan
        entry[f"ddE_{threshold}"] = np.nan
        entry["RMSD"] = rmsd
        entry["RMSD_AA"] = rmsd_aa
        entry["TFD"] = tfd

        entry.update(internal_coordinate_rmsds)
        entry.update(parameter_labels)
        result_entries.append(entry)

    # compute ddEs
    try:
        minimum_entry = min(result_entries, key=lambda x: x["qm_energy"])
        for entry in result_entries:
            entry["minimum_qcarchive_id"] = minimum_entry["qcarchive_id"]
            dQM = entry["qm_energy"] - minimum_entry["qm_energy"]
            dMM = entry["mm_energy"] - minimum_entry["mm_energy"]
            entry["ddE"] = dQM - dMM
        minimum_entry["ddE"] = np.nan
    except Exception as e:
        print(str(e))

    # now compute ddEs with RMSD threshold
    relevant_entries = [e for e in result_entries if e["RMSD_AA"] <= threshold]
    if len(relevant_entries):
        minimum_entry = min(relevant_entries, key=lambda x: x["qm_energy"])
        for entry in relevant_entries:
            entry[f"minimum_qcarchive_id_{threshold}"] = minimum_entry["qcarchive_id"]
            dQM = entry["qm_energy"] - minimum_entry["qm_energy"]
            dMM = entry["mm_energy"] - minimum_entry["mm_energy"]
            entry[f"ddE_{threshold}"] = dQM - dMM
        minimum_entry[f"ddE_{threshold}"] = np.nan

    return result_entries


def batch_compute(
    inchi_keys: list[str],
    input_store_path: str = None,
    force_field: str = None,
    name: str = None,
):

    store = MoleculeStore(input_store_path)
    forcefields = store.get_force_fields()
    assert len(forcefields) == 1

    results = []
    errors = []

    for inchi_key in tqdm.tqdm(inchi_keys):
        try:
            inchi_results = benchmark_single(store, force_field, inchi_key, name, ff_name=forcefields[0])
        except Exception as e:
            errors.append(str(e))
        else:
            results.extend(inchi_results)
    return results, errors


@click.command()
@click.option(
    "--store",
    "store_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
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
    "--name",
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
    store_path: str,
    output_dataset_path: str,
    forcefield: str,
    name: str,
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
    
    store = MoleculeStore(store_path)

    inchi_keys = store.get_inchi_keys()
    print(f"Found {len(inchi_keys)} molecules in the store")

    output_directory = pathlib.Path(output_dataset_path)
    output_directory.mkdir(exist_ok=True, parents=True)

    start_index = 0
    exclude_inchis = []
    try:
        print(f"Querying {output_directory}")
        existing = ds.dataset(output_directory)
        if existing.count_rows():
            exclude_inchis.extend(
                existing.to_table(
                    columns=["inchi"]
                ).to_pydict()["inchi"]
            )
            start_index = len(existing.files)
            exclude_inchis = set(exclude_inchis)
    except BaseException as e:
        print(e)
    print(f"Loaded {len(exclude_inchis)} inchis already calculated")

    inchi_keys = sorted(set(inchi_keys) - set(exclude_inchis))


    with batch_distributed(
        inchi_keys,
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
            force_field=forcefield,
            input_store_path=store_path,
            name=name,
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
