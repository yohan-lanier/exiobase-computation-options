import logging
from pathlib import Path
from typing import cast

import pandas as pd
from packaging.version import Version
from pymrio import Extension, IOSystem, parse_exiobase3

from exon.exiobase.constants import EURO_UNIT, EXIOBASE_MEURO
from exon.paths import DATABASES
from exon.utils import ExiobaseRelevantData


def extract_exiobase_data(version: str, reference_year: str) -> ExiobaseRelevantData:
    logging.info("Parsing exiobase version %s", version)
    folder_path = DATABASES / "exiobase" / f"{version}"
    s_file_path = folder_path / "S.csv"
    a_file_path = folder_path / "A.csv"
    units_file_path = folder_path / "units.csv"
    if s_file_path.exists() and a_file_path.exists() and units_file_path.exists():
        logging.info(
            "Good news, found existing a, s and units matrices. Skipping pymrio extract"
        )
        return {
            "a": pd.read_csv(
                a_file_path, sep=",", low_memory=False, header=[0, 1], index_col=[0, 1]
            ),
            "s": pd.read_csv(
                s_file_path, sep=",", low_memory=False, header=[0, 1], index_col=[0]
            ),
            "units": pd.read_csv(
                units_file_path, sep=",", low_memory=False, index_col=[0]
            ),
            "reference_year": reference_year,
        }
    else:
        if Version(version) >= Version("3.0"):  # TO DO, manage other years of exiobase
            exiobase = parse_exiobase3(folder_path / f"IOT_{reference_year}_pxp.zip")
        else:
            logging.error(
                "Parsing of version %s is not yet supported here, only >= v3 for now",
                version,
            )
            raise NotImplementedError
        exiobase_light_data = get_relevant_exiobase_data(
            exiobase, version, reference_year
        )
        # Exiobase object is heavy, drop it once useless
        del exiobase
        cache_useful_data(
            exiobase_light_data,
            {"a": a_file_path, "s": s_file_path, "units": units_file_path},
        )
        return exiobase_light_data


def get_relevant_exiobase_data(
    parsed_exiobase: IOSystem | Extension, version: str, reference_year: str
) -> ExiobaseRelevantData:

    if Version(version) >= Version("3.9"):
        logging.warning(
            "After version 3.9, exiobase archives do not include A "
            "and S matrix anymore. They need to be computed, this might take a bit"
            " of time..."
        )
        cast(IOSystem, parsed_exiobase).calc_all()
        extensions = list(cast(IOSystem, parsed_exiobase).get_extensions())
        logging.info(
            "Found %i extentions for version %s and reference year %s",
            len(extensions),
            version,
            reference_year,
        )

        s_matrix = pd.concat(
            [  # pylint: disable-next=unnecessary-dunder-call
                parsed_exiobase.__getattribute__(extension).S
                for extension in extensions
            ]
        )
        units = pd.concat(
            [  # pylint: disable-next=unnecessary-dunder-call
                parsed_exiobase.__getattribute__(extension).unit
                for extension in extensions
            ]
        )
        logging.info(
            "Found %i elementary flows for version %s and reference year %s",
            len(units),
            version,
            reference_year,
        )
    else:
        # Stressors are provided in unit/M.EUR -> for all stressors for which ref unit
        # is not M.EUR we convert them to unit/euro.
        # Stressors for which ref unit is M.EUR are in M.EUR/M.EUR so we don't convert them
        s_matrix = (
            parsed_exiobase.satellite.S.copy()  # pyright: ignore [reportAttributeAccessIssue]
        )
        units = (
            parsed_exiobase.satellite.unit.copy()  # pyright: ignore [reportAttributeAccessIssue]
        )
    mask = units["unit"] != EXIOBASE_MEURO
    s_matrix.loc[mask] /= 1e6
    ## but we do need to update their reference unit to euros
    units.loc[units["unit"] == EXIOBASE_MEURO] = EURO_UNIT
    # TO DO :
    #   - add an option for capital endogenization
    #   - x_io = exio.x.copy() to extract if background hybridisation is to be implemented
    return {
        "a": cast(pd.DataFrame, cast(IOSystem, parsed_exiobase).A).copy(),
        "s": s_matrix,
        "units": units,
        "reference_year": reference_year,
    }


def cache_useful_data(
    exiobase_light_data: ExiobaseRelevantData, file_paths: dict[str, Path]
) -> None:
    exiobase_light_data["s"].to_csv(file_paths["s"], sep=",", na_rep="#NA", index=True)
    exiobase_light_data["a"].to_csv(file_paths["a"], sep=",", na_rep="#NA", index=True)
    exiobase_light_data["units"].to_csv(
        file_paths["units"], sep=",", na_rep="#NA", index=True
    )
