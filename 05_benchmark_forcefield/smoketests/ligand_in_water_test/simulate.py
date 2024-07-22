import click
import pathlib
import time

import pandas as pd
import numpy
import openmm
import openmm.app
import openmm.unit
from openff.toolkit import ForceField, Molecule, Topology
from openff.units import unit

from openff.interchange import Interchange
from openff.interchange.components._packmol import RHOMBIC_DODECAHEDRON, pack_box
from openff.interchange.interop.openmm import to_openmm_positions

import MDAnalysis as mda
import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib as mpl

sns.set_context("talk")
mpl.rcParams['font.sans-serif'] = ["muli"]

def create_simulation(
    interchange: Interchange,
    pdb_stride: int = 500,
    data_name: str = "data.csv",
    trajectory_name: str = "trajectory.pdb",
) -> openmm.app.Simulation:
    integrator = openmm.LangevinIntegrator(
        300 * openmm.unit.kelvin,
        1 / openmm.unit.picosecond,
        1 * openmm.unit.femtoseconds,
    )

    barostat = openmm.MonteCarloBarostat(
        1.0 * openmm.unit.bar, 293.15 * openmm.unit.kelvin, 25
    )

    simulation = interchange.to_openmm_simulation(
        combine_nonbonded_forces=True,
        integrator=integrator,
    )

    simulation.system.addForce(barostat)

    # https://github.com/openmm/openmm/wiki/Frequently-Asked-Questions#why-does-it-ignore-changes-i-make-to-a-system-or-force
    simulation.context.reinitialize(preserveState=True)

    # https://github.com/openmm/openmm/issues/3736#issuecomment-1217250635
    simulation.minimizeEnergy()

    simulation.context.setVelocitiesToTemperature(300 * openmm.unit.kelvin)
    simulation.context.computeVirtualSites()

    pdb_reporter = openmm.app.PDBReporter(trajectory_name, pdb_stride)
    state_data_reporter = openmm.app.StateDataReporter(
        data_name,
        10,
        step=True,
        potentialEnergy=True,
        temperature=True,
        density=True,
    )
    simulation.reporters.append(pdb_reporter)
    simulation.reporters.append(state_data_reporter)

    return simulation


def run_simulation(simulation: openmm.app.Simulation, n_steps: int = 5000):
    print("Starting simulation")
    start_time = time.process_time()

    print("Step, volume (nm^3)")

    for step in range(n_steps):
        simulation.step(1)
        if step % 500 == 0:
            box_vectors = simulation.context.getState().getPeriodicBoxVectors()
            print(step, numpy.linalg.det(box_vectors._value).round(3))

    end_time = time.process_time()
    print(f"Elapsed time: {(end_time - start_time):.2f} seconds")


@click.command()
@click.option(
    "--input-geometry",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
)
@click.option(
    "--forcefield",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
)
@click.option(
    "--output-directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
)
def main(
    input_geometry: str,
    forcefield: str,
    output_directory: str,
):
    ligand = Molecule.from_file(input_geometry, allow_undefined_stereo=True)
    water = Molecule.from_mapped_smiles("[H:2][O:1][H:3]")

    topology = pack_box(
        molecules=[ligand, water],
        number_of_copies=[1, 1000],
        box_vectors=3.5 * RHOMBIC_DODECAHEDRON * unit.nanometer,
    )
    print(f"Topology # molecules: {topology.n_molecules}")
    print(f"Topology box vectors: {topology.box_vectors}")
    print(f"Topology positions shape: {topology.get_positions().shape}")

    sage = ForceField(forcefield)
    interchange: Interchange = Interchange.from_smirnoff(
        force_field=sage, topology=topology
    )

    output_directory = pathlib.Path(output_directory)
    output_directory.mkdir(exist_ok=True, parents=True)
    
    trajectory_name = str(output_directory / "trajectory.pdb")
    data_name = str(output_directory / "data.csv")
    simulation = create_simulation(
        interchange,
        trajectory_name=trajectory_name,
        data_name=data_name,
    )

    run_simulation(simulation, n_steps=100000)

    # strip water
    u = mda.Universe(trajectory_name)
    nowater_name = str(output_directory / "trajectory_noh2o.pdb")
    with mda.Writer(nowater_name, len(u.residues[0].atoms)) as writer:
        for _ in u.trajectory:
            writer.write(u.residues[0].atoms)
    
    # plot data
    df = pd.read_csv(data_name)
    df = df.rename(columns={'#"Step"': "Step"})
    melted = df.melt(id_vars=["Step"], var_name="Property", value_name="Value")
    g = sns.FacetGrid(data=melted, col="Property", sharey=False, aspect=1.5)
    g.map(sns.lineplot, "Step", "Value")
    g.set_titles(col_template="{col_name}")
    plt.tight_layout()
    plt.savefig(str(output_directory / "data.png"), dpi=300)


if __name__ == "__main__":
    main()