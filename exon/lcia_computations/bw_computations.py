import logging
import time
from typing import Any, Dict, List, Literal, Tuple

import bw2calc as bc
import bw2data as bd
from tqdm import tqdm

from exon.utils import EXIOBASE_NAME, EeioDatabase, ResultsLogValue


def run_bw_computations(
    exiobase_data: EeioDatabase,
    culling_thresholds: List[float],
    activities_to_compute: List[Tuple[str, str]],
    methods: List[str],
    bw_project: str,
    mode: Literal["lca_base", "lca_jacobi", "multi_lca_base"] = "lca_base",
    rtol: float = 1e-6,
    min_value_culling_lca_base: float = 1e-5,
) -> List[ResultsLogValue]:
    bd.projects.set_current(bw_project)
    check_all_databases_are_in_bw(exiobase_data, culling_thresholds)
    bw_methods = get_bw_methods(methods)
    exiobase_db_base_name = (
        f"{EXIOBASE_NAME}-{exiobase_data["version"]}-{exiobase_data["reference_year"]}"
    )
    results_log: List[ResultsLogValue] = []
    logging.info("⚙️ Running brightway computation in mode %s", mode)
    for culling_threshold in tqdm(
        culling_thresholds,
        desc="Running computation for the different exiobase databases",
    ):
        if float(culling_threshold) < min_value_culling_lca_base and (
            mode == "lca_base" or mode == "multi_lca_base"
        ):
            logging.warning(
                "Culling threshold %s is too small for conventional bw "
                "lca computation on exiobase. Skipping these computations",
                culling_threshold,
            )
            continue
        exiobase_db_name = exiobase_db_base_name + f"-{culling_threshold}"
        bw_activities = get_bw_activities(activities_to_compute, exiobase_db_name)
        if mode == "multi_lca_base":
            results_log.extend(
                run_multi_lca_computation(bw_activities, bw_methods, exiobase_db_name)
            )
        else:
            for method in tqdm(bw_methods.values(), desc="Going through methods"):
                for activity in tqdm(
                    bw_activities.values(), desc="Going through activities"
                ):
                    if mode == "lca_base":
                        lca = bc.LCA(demand={activity: 1}, method=method)
                    elif mode == "lca_jacobi":
                        lca = bc.JacobiGMRESLCA(
                            demand={activity: 1},
                            method=method,
                            rtol=rtol,
                        )
                    else:
                        logging.error(
                            "Computation mode %s is unknown and not supported, terminating script.",
                            mode,
                        )
                        raise NotImplementedError
                    start = time.time()
                    lca.lci()
                    lca.lcia()
                    end = time.time()

                    results_log.append(
                        {
                            "computation_type": mode,
                            "activity": str(activity),
                            "method": method,
                            "score": lca.score,
                            "computation_time": end - start,
                            "db_name": exiobase_db_name,
                            "culling_threshold": culling_threshold,
                        }
                    )

    return results_log


def check_all_databases_are_in_bw(
    exiobase_data: EeioDatabase, culling_thresholds: List[float]
) -> None:
    if not all(
        f"{EXIOBASE_NAME}-{exiobase_data["version"]}-{exiobase_data["reference_year"]}-{culling_threshold}"
        in bd.databases
        for culling_threshold in culling_thresholds
    ):
        logging.error(
            "Some input culling threshold do not have corresponding databases"
            " in bw. Terminating script"
        )
        raise NotImplementedError


def get_bw_methods(methods: List[str]) -> Dict[str, Any]:
    bw_methods = {}
    for method in methods:
        bw_method_to_compute = [
            m
            for m in bd.methods
            if (
                len(m) > 2
                and "exiobase" in m[0].lower()
                and m[2].lower() == method.lower()
            )
        ]
        assert len(bw_method_to_compute) == 1, (
            "More or less than exactly one method found",
            f" for method header {method}. This is not normal",
        )
        bw_methods[method] = bw_method_to_compute[0]
    return bw_methods


def get_bw_activities(
    activities_to_compute: List[Tuple[str, str]], exiobase_db_name: str
) -> Dict[Tuple[str, str], Any]:
    bw_activities = {}
    for activity in activities_to_compute:
        bw_act_to_compute = [
            act
            for act in bd.Database(
                exiobase_db_name
            )  # pyright: ignore[reportGeneralTypeIssues]
            if act["name"] == activity[1] and act["location"] == activity[0]
        ]
        assert len(bw_act_to_compute) == 1, (
            f"More or less than one activity found for activity tupple {activity} in exiobase. ",
            "This is not normal",
        )
        bw_activities[activity] = bw_act_to_compute[0]
    return bw_activities


def run_multi_lca_computation(
    bw_activities: Dict[Tuple[str, str], Any],
    bw_methods: Dict[str, Any],
    exiobase_db_name: str,
) -> List[ResultsLogValue]:
    results_log: List[ResultsLogValue] = []
    functional_units = {
        f"('{activity["name"]}', '{activity["location"]}')": {int(activity["id"]): 1.0}
        for activity in bw_activities.values()
    }
    method_config = {"impact_categories": list(bw_methods.values())}
    data_objs = bd.get_multilca_data_objs(
        functional_units=functional_units,  # pyright: ignore[reportArgumentType]
        method_config=method_config,  # pyright: ignore[reportArgumentType]
    )
    multi_lca = bc.MultiLCA(
        demands=functional_units, method_config=method_config, data_objs=data_objs
    )

    start = time.time()
    multi_lca.lci()
    multi_lca.lcia()
    end = time.time()

    for label, score in multi_lca.scores.items():
        bw_method, activity = label
        method = list(bw_methods.keys())[list(bw_methods.values()).index(bw_method)]
        nb_of_computations = len(bw_methods) * len(bw_activities)
        results_log.append(
            {
                "computation_type": "multi_lca_base",
                "activity": activity,
                "method": method,
                "score": score,
                "computation_time": (end - start) / nb_of_computations,
                "db_name": exiobase_db_name,
            }
        )
    return results_log
