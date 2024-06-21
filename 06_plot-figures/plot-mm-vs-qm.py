import pathlib
import click
import pandas as pd

import seaborn as sns
from matplotlib import pyplot as plt
import matplotlib as mpl
import numpy as np

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
    
    return forcefield.replace("openff_unconstrained-", "OpenFF ")



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
)
@click.option(
    "--outlier-ids",
    "outlier_id_files",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    multiple=True,
)
@click.option(
    "--parameter-id",
    type=str,
    help="The parameter ID to filter for.",
    required=True,
)
def main(
    input_dataset: str,
    output_file: str,
    parameter_id: str,
    outlier_id_files: list[str] = [],
):

    dataset = ds.dataset(input_dataset, format="parquet")
    print(f"Starting # rows: {dataset.count_rows()}")

    outlier_ids = []
    for outlier_id_file in outlier_id_files:
        with open(outlier_id_file, "r") as file:
            outlier_ids.extend([
                int(line.strip()) for line in file.readlines()
            ])
    
    # filter out outlier ids
    expression = ~pc.field("qcarchive_id").isin(outlier_ids)
    dataset = dataset.filter(expression)
    print(f"After filtering outliers # rows: {dataset.count_rows()}")

    if parameter_id:
        expression = pc.field("parameter") == parameter_id
        dataset = dataset.filter(expression)
        print(f"Ending # rows after filtering for {parameter_id}: {dataset.count_rows()}")

    # filter to only contain qcarchive IDs that are calculated
    # for all FFs of interest
    forcefields = [
        'openff_unconstrained-2.1.0',
        'openff_unconstrained-2.2.0',
        'openff_unconstrained-2.2.1-rc1'
    ]
    n_forcefields = len(forcefields)
    subexpression = pc.field("name").isin(forcefields)
    subset = dataset.filter(subexpression)
    subset_df = subset.to_table(columns=["qcarchive_id", "name"]).to_pandas().drop_duplicates()
    counts = subset_df.groupby("qcarchive_id").count().reset_index()
    qcarchive_ids = counts[counts["name"] == n_forcefields]["qcarchive_id"].values
    expression = pc.field("qcarchive_id").isin(qcarchive_ids)
    dataset = dataset.filter(expression)
    print(f"After filtering for common qcarchive IDs # rows: {dataset.count_rows()}")
        

    columns = [
        "name",
        "qcarchive_id",
        "smirks",
        "indices",
        "qm",
        "mm"
    ]

    df = dataset.to_table(columns=columns).to_pandas()
    df["MM - QM"] = df["mm"] - df["qm"]
    df["Force field"] = [rename_forcefield(x) for x in df["name"].values]

    UNIT_SYMBOLS = {
        "a": "°",
        "b": "Å",
        "t": "°",
        "i": "°",
    }


    # plot ddEs
    g = sns.catplot(
        kind="box",
        data=df,
        x="MM - QM",
        y="Force field",
        order=list(PALETTE.keys())[::-1],
        hue="Force field",
        hue_order=list(PALETTE.keys()),
        palette=PALETTE,
        legend=False,
        # ax=ax,
        fliersize=2,
        flierprops={"marker": "o", "markerfacecolor": "none", "linewidth": 1,},
        linewidth=1.5,
        # alpha=0.5,
        # fill=False,
        aspect=2,
        height=3,
        # boxprops={"fill": False}
    )
    ax = list(g.axes.flatten())[0]
    ax.set_title(parameter_id)
    ax.set_xlabel(f"MM - QM ({UNIT_SYMBOLS[parameter_id[0]]})")
    ax.axvline(0, color="black", linestyle="--", lw=1)
    plt.tight_layout()

    plt.savefig(output_file, dpi=300)
    print(f"Saved plot to {output_file}")




if __name__ == "__main__":
    main()


