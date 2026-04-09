import logging
from random import sample
from typing import Callable, List, Literal, NotRequired, Tuple, TypedDict

import bw2data as bd
import pandas as pd
from packaging.version import Version

from exon.args import ExonParser


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
    culling_threshold: NotRequired[float]


EXIOBASE_NAME = "exiobase"


class EeioDatabase(TypedDict):
    name: str
    version: str
    reference_year: str


MIN_VALUE_CULLING_FOR_LCA_BASE_COMP = 1e-5


class LciaMethod(TypedDict):
    name: str
    method_version: str
    extract_cfs: Callable[[str], pd.DataFrame]
    import_in_bw: Callable[[str], None]


def extrat_cfs_for_method_and_drop_null_cfs(
    bw_project: str, method: LciaMethod
) -> pd.DataFrame:
    biosphere_version = get_biosphere_version(
        get_database_biosphere_name("exiobase", bw_project)
    )
    c_matrix = method["extract_cfs"](biosphere_version)
    nb_indicators = c_matrix.shape[0]
    # drop all categories for which all cfs are null
    c_matrix = c_matrix.loc[~(c_matrix == 0).all(axis=1)]
    if c_matrix.shape[0] < nb_indicators:
        logging.warning(
            "Dropping %i impact indicators because all cfs are null.",
            (nb_indicators - c_matrix.shape[0]),
        )
    return c_matrix


class ListsForComputations(TypedDict):
    all_activities: List[Tuple[str, str]]
    random_activities: List[Tuple[str, str]]
    random_activities_index: List[int]
    random_methods: List[str]


def generate_random_samples_for_computations(
    exiobase_data: ExiobaseRelevantData, args: ExonParser
) -> ListsForComputations:
    activities_list = exiobase_data["a"].index.to_list()
    random_activities = sample(activities_list, int(args.nb_activities))
    random_activities_index = [activities_list.index(act) for act in random_activities]
    c_matrix = exiobase_data.get("c")
    if c_matrix is None:
        logging.error(
            "No c matrix found in exiobase data, cannot sample random methods for computations"
        )
        raise NotImplementedError
    random_methods = sample(c_matrix.index.to_list(), int(args.nb_indicators))
    return {
        "all_activities": activities_list,
        "random_activities": random_activities,
        "random_activities_index": random_activities_index,
        "random_methods": random_methods,
    }
