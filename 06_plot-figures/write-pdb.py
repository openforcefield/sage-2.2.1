import pathlib
import typing
import click

import MDAnalysis as mda
import pyarrow.dataset as ds
import pyarrow.compute as pc
import numpy as np

from openff.toolkit import Molecule
from openff.units import unit


@click.command()
@click.option(
    "--input",
    "input_dataset",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.option(
    "--output",
    "output_directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
)
@click.option(
    "--qcarchive-id",
    type=int,
    required=True,
)
@click.option(
    "--name",
    type=click.Choice([
        'openff_unconstrained-2.1.0',
        'openff_unconstrained-2.2.0-rc1',
        'openff_unconstrained-2.2.1-rc1',
        "qm",
    ]),
    required=True,
)
def main(
    input_dataset: str,
    output_directory: str,
    qcarchive_id: int,
    name: typing.Literal[
        'openff_unconstrained-2.2.0-rc1',
        'openff_unconstrained-2.2.1-rc1',
        "qm",
    ]
):
    dataset = ds.dataset(input_dataset, format="parquet")
    expression = pc.field("qcarchive_id") == qcarchive_id
    if name != "qm":
        expression = expression & (pc.field("name") == name)
    dataset = dataset.filter(expression)
    row = dataset.to_table(
        columns=["mapped_smiles", "mm_coordinates", "qm_coordinates"]
    ).to_pylist()[0]


    mol = Molecule.from_mapped_smiles(
        row["mapped_smiles"],
        allow_undefined_stereo=True,
    )
    if name == "qm":
        coordinates = row["qm_coordinates"]
    else:
        coordinates = row["mm_coordinates"]
    coordinates = np.array(coordinates).reshape((-1, 3))
    mol._conformers = [coordinates * unit.angstrom]

    u = mda.Universe(mol.to_rdkit())

    output_directory = pathlib.Path(output_directory) / f"{qcarchive_id}"
    output_directory.mkdir(parents=True, exist_ok=True)
    pdbfile = output_directory / f"{name}.pdb"
    u.atoms.write(pdbfile)
    print(f"Wrote {pdbfile}")


if __name__ == "__main__":
    main()
