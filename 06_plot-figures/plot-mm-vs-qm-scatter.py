import pathlib
import click

import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib as mpl

import pyarrow.compute as pc
import pyarrow.dataset as ds

sns.set_context("talk")
mpl.rcParams['font.sans-serif'] = ["muli"]

OPENFF_BLUE = "#015480"
OPENFF_LIGHT_BLUE = "#2F9ED2"
OPENFF_ORANGE = "#F08521"
OPENFF_RED = "#F03A21"
OPENFF_GRAY = "#3E424A"

COLORS = {
    "blue": OPENFF_BLUE,
    "cyan": OPENFF_LIGHT_BLUE,
    "orange": OPENFF_ORANGE,
    "red": OPENFF_RED,
    "gray": OPENFF_GRAY
}

PALETTE = {
    "OpenFF 2.2.1-rc1": COLORS["red"],
    "OpenFF 2.2.0": COLORS["orange"],
    "OpenFF 2.1.0": COLORS["blue"],
    # "OpenFF 2.0.0": COLORS["cyan"],
    # "OpenFF 1.3.1": COLORS["gray"],
}



def rename_forcefield(forcefield: str) -> str:
    if forcefield.endswith("offxml"):
        return forcefield.replace(".offxml", "")

    forcefield = forcefield.replace("2.2.0-rc1", "2.2.0")
    
    return forcefield.replace("openff_unconstrained-", "OpenFF ")



def get_limits(data):
    min_ = min(data)
    min_ = min_ - 0.1 * abs(min_)
    max_ = max(data)
    max_ = max_ + 0.1 * abs(max_)
    return min_, max_


@click.command()
@click.option(
    "--input",
    "input_dataset",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(exists=False, dir_okay=False, file_okay=True),
    help="The path to the output plot (PNG)"
)
@click.option(
    "--outlier-ids",
    "outlier_id_files",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    multiple=True,
)
def main(
    input_dataset: str,
    outlier_id_files: list[str],
    output_file: str,
):
    outlier_ids = []
    for outlier_id_file in outlier_id_files:
        with open(outlier_id_file, "r") as file:
            outlier_ids.extend([
                int(line.strip()) for line in file.readlines()
            ])

    mm_vs_qm_dataset = ds.dataset(input_dataset)
    expression = ~pc.field("qcarchive_id").isin(outlier_ids)
    mm_vs_qm_dataset = mm_vs_qm_dataset.filter(expression)
    df = mm_vs_qm_dataset.to_table().to_pandas()


    df["Force field"] = [rename_forcefield(x) for x in df.name.values]

    g = sns.FacetGrid(
        data=df,
        col="Force field",
        col_order=list(PALETTE)[::-1],
        aspect=0.8
    )
    g.map(sns.scatterplot, "qm", "mm", s=5)

    lim = get_limits(
        list(df.qm.values) + list(df.mm.values)
    )
    for ax in g.axes.flatten():
        ax.set_xlim(lim)
        ax.set_ylim(lim)
        ax.plot(lim, lim, lw=1, ls="--", color="k")
        ax.set_xlabel("QM (°)")
        ax.set_ylabel("MM (°)")

    g.set_titles(col_template="{col_name}")
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    print(f"Saved plot to {output_file}")



if __name__ == "__main__":
    main()
