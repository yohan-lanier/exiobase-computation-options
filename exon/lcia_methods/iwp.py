import logging
from typing import Any, Dict, cast

import bw2data as bd
import pandas as pd
from packaging.version import Version
from tqdm import tqdm

from exon.lcia_methods.constants import (
    IWP_EXIOBASE_FILE_MIDDLE,
    IWP_EXIOBASE_FILE_PREFIX,
    IWP_NAME,
    IWP_UNIT_TO_AREA_OF_PROTECTION,
)
from exon.paths import LCIA_METHODS


def create_iwp_method_for_exio(version: str) -> None:
    exiobase_biosphere = get_database_biosphere_name(db_name="exiobase")
    biosphere_version = get_biosphere_version(exiobase_biosphere)
    # cfs: characterization factors
    cfs = load_cfs(method_version=version, biosphere_version=biosphere_version)

    assert_method_is_not_already_imported(biosphere_version, method_version=version)
    write_method_to_bw(
        match_impact_cat_label_to_exio_cf_values(exiobase_biosphere, exio_cfs=cfs),
        exio_version=biosphere_version,
        method_version=version,
    )


def get_database_biosphere_name(db_name: str) -> str:
    biospheres = [db for db in bd.databases if db_name in db and "biosphere" in db]
    if not biospheres:
        logging.error(
            "No biospheres found for database %s, cannot import LCIA method", db_name
        )
        raise NotImplementedError
    if len(biospheres) > 1:
        logging.error(
            "More than one biosphere found for database %s. "
            "Please make sure only one biosphere per brightway project for database %s is defined.",
            db_name,
            db_name,
        )
        raise NotImplementedError
    logging.info("✅ Found a unique biosphere for database %s", db_name)
    return biospheres[0]


def get_biosphere_version(exiobase_biosphere: str) -> str:
    # Name is always "db_name-{version}-biosphere"
    # per construction. Hence version is element one after splitting on "-"
    # For exiobase, determine if version is lower or equal than 3.8.2
    if Version(exiobase_biosphere.split("-")[1]) >= Version("3.9"):
        return "3.9_and_after"
    return "3.8.2_and_before"


def load_cfs(method_version: str, biosphere_version: str) -> pd.Series:
    lcia_exio = cast(
        pd.Series,
        pd.read_excel(
            LCIA_METHODS
            / IWP_NAME
            / method_version
            / (
                IWP_EXIOBASE_FILE_PREFIX
                + method_version
                + IWP_EXIOBASE_FILE_MIDDLE
                + biosphere_version
                + ".xlsx"
            ),
            index_col=0,
        )
        .stack()
        .astype(float),
    )
    return lcia_exio[lcia_exio.iloc[:] != 0]


def assert_method_is_not_already_imported(
    biosphere_version: str, method_version: str
) -> None:
    matching_pattern = f"exiobase v{biosphere_version}"
    matching_methods = [
        m
        for m in bd.methods
        if (
            matching_pattern in m[0]
            and "IMPACT World+" in m[0]
            and method_version in m[0]
        )
    ]
    if matching_methods:
        logging.warning(
            "Found %i Impact World+ methods in your current brightway "
            "project that match your biosphere. Methods will be "
            "deleted and imported again.",
            len(matching_methods),
        )
        for m in matching_methods:
            del bd.methods[m]


def match_impact_cat_label_to_exio_cf_values(
    exiobase_biosphere: str, exio_cfs: pd.Series
) -> Dict[Any, Any]:
    # first match elementary flow names to their id in the bw db
    exio_biosphere_name_to_code_mapping = {
        act.as_dict()["name"]: act.as_dict()[
            "id"
        ]  # -> bw25 defining method through elem flow ids
        for act in bd.Database(
            exiobase_biosphere
        )  # pyright: ignore[reportGeneralTypeIssues]
    }
    # then match impact cat label to a list containing a tuple ("elem_flow_id", cf_value)
    # this tuple is what brightway 2.5 needs to write the method
    return {
        impact_cat: list(
            zip(
                map(
                    exio_biosphere_name_to_code_mapping.get,
                    cat_cf_values.index.get_level_values(1),
                ),
                cat_cf_values.values,
            )
        )
        for impact_cat, cat_cf_values in exio_cfs.groupby(level=0)
    }


def write_method_to_bw(
    exio_category_name_to_cf_values_dict: Dict[Any, Any],
    exio_version: str,
    method_version: str,
) -> None:
    for indicator, cfs in tqdm(
        exio_category_name_to_cf_values_dict.items(),
        desc="Writing impact methods to brightway",
    ):
        # indicator names end by unit between bracket
        # Climate change, ecosystem quality, marine ecosystem, long term (beta) (PDF.m2.yr)
        unit = indicator.split("(")[-1].strip(")")
        bw_method = bd.Method(
            (
                f"IMPACT World+ v{method_version} for exiobase v{exio_version}",
                IWP_UNIT_TO_AREA_OF_PROTECTION.get(unit, "Midpoint"),
                indicator,
            )
        )
        bw_method.register()
        bw_method.metadata["unit"] = unit
        bw_method.write(cfs)
    logging.info(
        "✅ Successfully imported a hybrid version of Impact World+ v%s", method_version
    )
