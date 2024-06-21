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




def barplot(
    df,
    parameter_type: str,
    parameter_name: str,
    parameter_unit: str,
    images_directory: pathlib.Path,
):
    subdf = df[
        (df.parameter_type == parameter_type)
        & (df.parameter_name == parameter_name)
    ]
    print(f"{parameter_type} {parameter_name}")
    width = len(subdf.parameter_id.unique()) * 0.22
    _, ax = plt.subplots(figsize=(width, 4))

    sns.barplot(
        ax=ax,
        data=subdf,
        x="parameter_id",
        y="difference",
    )
    plt.xticks(rotation=90)
    ax.set_title(parameter_name)
    ax.set_xlabel("")
    ax.axhline(0, ls="--", lw=1, color="k")
    ax.set_ylabel(f"2.2.1-rc1 - 2.2.0\n({parameter_unit})")
    plt.tight_layout()
    filename = images_directory / f"{parameter_type}_{parameter_name}.png"
    plt.savefig(filename, dpi=300)
    print(f"Saved plot to {filename}")
    plt.close()


@click.command()
@click.option(
    "--images",
    "images_directory",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    required=True,
    help="The path to the output images directory.",
)
@click.option(
    "--original",
    "original_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default="../openff_unconstrained-2.2.0.offxml",
    help="The path to the original force field file.",
)
@click.option(
    "--new",
    "new_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default="../openff_unconstrained-2.2.1-rc1.offxml",
    help="The path to the new force field file.",
)
def main(
    images_directory: str,
    original_path: str = "../openff_unconstrained-2.2.0.offxml",
    new_path: str = "../openff_unconstrained-2.2.1-rc1.offxml",
):
    from openff.toolkit import ForceField

    images_directory = pathlib.Path(images_directory)
    images_directory.mkdir(exist_ok=True, parents=True)

    original  = ForceField(original_path, allow_cosmetic_attributes=True)
    new = ForceField(new_path, allow_cosmetic_attributes=True)

    PARAMETER_NAMES = {
        "Bonds": ("k", "length"),
        "Angles": ("k", "angle"),
    }
    

    all_entries = []

    # get all parameters
    for parameter_type in ["Bonds", "Angles", "ProperTorsions", "ImproperTorsions"]:
        original_handler = original.get_parameter_handler(parameter_type)
        new_handler = new.get_parameter_handler(parameter_type)

        for old_parameter, new_parameter in zip(
            original_handler.parameters,
            new_handler.parameters,
        ):
            assert old_parameter.id == new_parameter.id
            if parameter_type in PARAMETER_NAMES:
                for parameter_name in PARAMETER_NAMES[parameter_type]:
                    entry = {
                        "parameter_type": parameter_type,
                        "parameter_id": old_parameter.id,
                        "parameter_smirks": old_parameter.smirks,
                        "parameter_name": parameter_name,
                        "parameter_units": str(getattr(old_parameter, parameter_name).units),
                        "old_parameter_value": getattr(old_parameter, parameter_name).m,
                        "new_parameter_value": getattr(new_parameter, parameter_name).m,
                    }
                    all_entries.append(entry)
            else:
                for i, old_k in enumerate(old_parameter.k, 1):
                    entry = {
                        "parameter_type": parameter_type,
                        "parameter_id": old_parameter.id,
                        "parameter_smirks": old_parameter.smirks,
                        "parameter_name": f"k{i}",
                        "parameter_units": str(old_k.units),
                        "old_parameter_value": old_k.m,
                        "new_parameter_value": new_parameter.k[i - 1].m,
                    }
                    all_entries.append(entry)
    
    df = pd.DataFrame(all_entries)
    df["difference"] = df.new_parameter_value - df.old_parameter_value

    UNITS = {
    ("Bonds", "k"): "kcal/mol/$\AA$",
    ("Bonds", "length"): "$\AA$",
    ("Angles", "k"): "kcal/mol/rad$^{2}$",
    ("Angles", "angle"): "degrees",
}

    # plot bonds and angles
    for parameter_type, parameter_names in PARAMETER_NAMES.items():
        for parameter_name in parameter_names:
            parameter_unit = UNITS[(parameter_type, parameter_name)]
            barplot(df, parameter_type, parameter_name, parameter_unit, images_directory)
    
    # plot torsions
    barplot(
        df,
        "ImproperTorsions",
        "k1",
        "kcal/mol",
        images_directory,
    )
    
    for i in range(1, 4):
        barplot(
            df,
            "ProperTorsions",
            f"k{i}",
            "kcal/mol",
            images_directory,
        )


if __name__ == "__main__":
    main()


