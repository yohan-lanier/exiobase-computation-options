import logging
from typing import Literal, NotRequired, TypedDict

import bw2data as bd
import pandas as pd
from packaging.version import Version


def get_database_biosphere_name(db_name: str, bw_project: str) -> str:
    bd.projects.set_current(bw_project)
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


class ExiobaseRelevantData(TypedDict):
    a: pd.DataFrame
    s: pd.DataFrame
    units: pd.DataFrame
    reference_year: str
    c: NotRequired[pd.DataFrame]


class ResultsLogValue(TypedDict):
    computation_type: Literal[
        "matrix_iterative", "matrix_aggregated", "lca_base", "lca_jacobi"
    ]
    activity: str
    method: str
    score: float
    computation_time: float
    db_name: NotRequired[str]
    culling_threshold: NotRequired[str]
