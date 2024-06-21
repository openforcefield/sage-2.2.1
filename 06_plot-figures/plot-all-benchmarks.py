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

def get_ddes(
    dataset,
    threshold: float = 0.4
):
    # need to recalculate ddE without outlier IDs
    expression = pc.field("RMSD_AA") <= threshold
    dataset = dataset.filter(expression)

    columns = [
        "name",
        "inchi",
        "qcarchive_id",
        "molecule_id",
        # "all_qcarchive_ids",
        "qm_energy",
        "mm_energy",
        "RMSD_AA"
    ]

    table = dataset.to_table(columns=columns)
    df = table.to_pandas()

    new_dfs = []

    for _, subdf in df.groupby(["name", "molecule_id"]):
        # make a new dataframe to avoid messiness
        subdf = pd.DataFrame(subdf)
        minimum_qm_row = subdf.iloc[subdf.qm_energy.argmin()]
        subdf["minimum_qcarchive_id"] = minimum_qm_row.qcarchive_id

        dQM = subdf.qm_energy - minimum_qm_row.qm_energy
        dMM = subdf.mm_energy - minimum_qm_row.mm_energy
        subdf["ddE"] = dQM - dMM
        # set the minimum ddE to NaN
        minimum_index = subdf[subdf.qcarchive_id == minimum_qm_row.qcarchive_id].index[0]
        subdf.loc[minimum_index, "ddE"] = np.nan
        # subdf[subdf.qcarchive_id == minimum_qm_row.qcarchive_id].ddE = np.nan
        
        new_dfs.append(subdf)
    
    df = pd.concat(new_dfs).drop_duplicates()
    df["abs_ddE"] = np.abs(df["ddE"].values)
    df["Force field"] = [rename_forcefield(name) for name in df["name"]]
    return df


@click.command()
@click.option(
    "--input",
    "input_dataset",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
)
@click.option(
    "--images",
    "image_directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
)
@click.option(
    "--output",
    "output_directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
)
@click.option(
    "--outlier-ids",
    "outlier_id_files",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    multiple=True,
)
@click.option(
    "--chemical-group",
    type=str,
    help="The chemical group to filter for.",
    required=False,
    default=None,
)
def main(
    input_dataset: str,
    image_directory: str,
    output_directory: str,
    outlier_id_files: list[str] = [],
    chemical_group: str = None,
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

    if chemical_group:
        expression = pc.field(chemical_group)
        dataset = dataset.filter(expression)
        print(f"Ending # rows after filtering for {chemical_group}: {dataset.count_rows()}")

    # filter to only contain qcarchive IDs that are calculated
    # for all FFs of interest
    forcefields = [
        'openff_unconstrained-1.3.1',
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
        

    output_directory = pathlib.Path(output_directory)
    output_directory.mkdir(exist_ok=True, parents=True)
    image_directory = pathlib.Path(image_directory)
    image_directory.mkdir(exist_ok=True, parents=True)

    ddes_df = get_ddes(dataset)
    ddes_df.to_csv(output_directory / "ddes.csv", index=False)

    base_columns = [
        "name",
        "inchi",
        "qcarchive_id",
        "molecule_id",
    ]
    rmsds_df = dataset.to_table(
        columns=list(base_columns) + ["RMSD", "RMSD_AA"]
    ).to_pandas().drop_duplicates()
    rmsds_df["Force field"] = [rename_forcefield(name) for name in rmsds_df["name"]]
    rmsds_df.to_csv(output_directory / "rmsds.csv", index=False)

    tfds_df = dataset.to_table(
        columns=list(base_columns) + ["TFD"]
    ).to_pandas().drop_duplicates()
    tfds_df["Force field"] = [rename_forcefield(name) for name in tfds_df["name"]]
    tfds_df.to_csv(output_directory / "tfds.csv", index=False)

    icrmsds_df = dataset.to_table(
        columns=list(base_columns) + ["Bond", "Angle", "Dihedral", "Improper"]
    ).to_pandas().drop_duplicates()
    icrmsds_df["Force field"] = [rename_forcefield(name) for name in icrmsds_df["name"]]
    icrmsds_df.to_csv(output_directory / "ic_rmsds.csv", index=False)

    # plot figures
    figsize = (6.5, 4)
    linewidth = 1

    # plot ddEs
    _, ax = plt.subplots(figsize=figsize)
    ax = sns.histplot(
        ax=ax,
        data=ddes_df,
        x="ddE",
        hue="Force field",
        element="step",
        palette=PALETTE,
        hue_order=list(PALETTE),
        fill=False,
        binwidth=0.5,
        binrange=(-5.25, 5.25),
        lw=linewidth,
        legend=False,
    )
    ax.set_xlabel("DDE [kcal/mol]")
    ax.set_xlim((-5, 5))
    ax.axvline(0, color="black", linestyle="--", lw=1)
    plt.tight_layout()
    plt.savefig(image_directory / "dde.png", dpi=300)
    print(f"Saved {image_directory / 'dde.png'}")
    plt.close()

    # plot absolute ddEs
    _, ax = plt.subplots(figsize=figsize)
    ax = sns.ecdfplot(
        data=ddes_df,
        ax=ax,
        x="abs_ddE",
        hue="Force field",
        palette=PALETTE,
        hue_order=list(PALETTE),
        lw=linewidth,
    )
    ax.set_xlabel("Abs DDE [kcal/mol]")
    ax.set_xlim((0, 10))
    plt.tight_layout()
    plt.savefig(image_directory / "abs_dde.png", dpi=300)
    print(f"Saved {image_directory / 'abs_dde.png'}")
    plt.close()

    dde_stats = ddes_df.groupby("Force field")[["ddE", "abs_ddE"]].describe()
    dde_stats.columns = dde_stats.columns.map("_".join)

    # plot rmsds
    fig, ax = plt.subplots(figsize=figsize)
    ax = sns.ecdfplot(
        data=rmsds_df,
        ax=ax,
        x="RMSD",
        hue="Force field",
        palette=PALETTE,
        hue_order=list(PALETTE),
        lw=linewidth,
    )
    ax.set_xlabel("RMSD [Å]")
    ax.set_xlim((0, 1))
    plt.tight_layout()
    plt.savefig(image_directory / "rmsds.png", dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=figsize)
    ax = sns.ecdfplot(
        data=rmsds_df,
        ax=ax,
        x="RMSD_AA",
        hue="Force field",
        palette=PALETTE,
        hue_order=list(PALETTE),
        lw=linewidth,
    )
    ax.set_xlabel("AA RMSD [Å]")
    ax.set_xlim((0, 1))
    plt.tight_layout()
    plt.savefig(image_directory / "aa_rmsds.png", dpi=300)
    plt.close()

    rmsd_stats = rmsds_df.groupby("Force field")[["RMSD", "RMSD_AA"]].describe()
    rmsd_stats.columns = rmsd_stats.columns.map("_".join)


    # plot tfds
    fig, ax = plt.subplots(figsize=figsize)
    ax = sns.ecdfplot(
        ax=ax,
        data=tfds_df,
        x="TFD",
        hue="Force field",
        palette=PALETTE,
        hue_order=list(PALETTE),
        lw=linewidth,
    )
    ax.set_xlabel("TFD")
    ax.set_xlim((0, 0.25))
    plt.tight_layout()
    plt.savefig(image_directory / "tfds.png", dpi=300)
    plt.close()

    tfd_stats = tfds_df.groupby("Force field")[["TFD"]].describe()
    tfd_stats.columns = tfd_stats.columns.map("_".join)

    melted = icrmsds_df.melt(
        id_vars=base_columns + ["Force field"],
        value_vars=["Bond", "Angle", "Dihedral", "Improper"],
        var_name="Parameter type",
        value_name="Difference",
    )

    # plot IC RMSDs
    g = sns.catplot(
        kind="box",
        data=melted,
        col="Parameter type",
        col_wrap=2,
        x="Difference",
        hue="Force field",
        y="Force field",
        order=list(PALETTE)[::-1],
        palette=PALETTE,
        hue_order=list(PALETTE),
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
        sharex=False,
        sharey=False,
    )
    g.set_titles(col_template="{col_name}")

    for ax in g.axes.flatten():
        ax.axvline(0, color="black", linestyle="--", lw=1)
        ax.set_xlabel("RMSD [°]")
    
    ax = list(g.axes.flatten())[0]
    ax.set_xlabel("RMSD [Å]")
    plt.tight_layout()
    plt.savefig(image_directory / "ic_rmsds.png", dpi=300)
    plt.close()

    ic_rmsd_stats = icrmsds_df.groupby("Force field")[["Bond", "Angle", "Dihedral", "Improper"]].describe()


    stats = pd.concat([dde_stats, rmsd_stats, tfd_stats, ic_rmsd_stats], axis=1)
    stats.to_csv(output_directory / "stats.csv")

if __name__ == "__main__":
    main()


