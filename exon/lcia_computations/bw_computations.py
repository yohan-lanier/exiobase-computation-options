import logging
from time import perf_counter
from typing import Any, Dict, List, Literal, Tuple

import bw2calc as bc
import bw2data as bd
from tqdm import tqdm

from exon.utils import EXIOBASE_NAME, EeioDatabase, ResultsLogValue

BwComputationMode = Literal[
    "lca_base",
    "lca_factorized",
    "lca_jacobi",
    "lca_jacobi_cold",
    "lca_jacobi_warm",
    "multi_lca_base",
]

LEGACY_ISOLATED_MODES = {"lca_base", "lca_jacobi"}
REUSED_SOLVER_MODES = {"lca_factorized", "lca_jacobi_cold", "lca_jacobi_warm"}
CONVENTIONAL_LCA_MODES = {"lca_base", "lca_factorized", "multi_lca_base"}


def run_bw_computations(
    exiobase_data: EeioDatabase,
    culling_thresholds: List[float],
    activities_to_compute: List[Tuple[str, str]],
    methods: List[str],
    bw_project: str,
    mode: BwComputationMode = "lca_base",
    rtol: float = 1e-6,
    min_value_culling_lca_base: float = 1e-5,
) -> List[ResultsLogValue]:
    bd.projects.set_current(bw_project)
    check_all_databases_are_in_bw(exiobase_data, culling_thresholds)
    bw_methods = get_bw_methods(methods)
    exiobase_db_base_name = (
        f"{EXIOBASE_NAME}-{exiobase_data['version']}-{exiobase_data['reference_year']}"
    )
    results_log: List[ResultsLogValue] = []
    logging.info("⚙️ Running brightway computation in mode %s", mode)
    for culling_threshold in tqdm(
        culling_thresholds,
        desc="Running computation for the different exiobase databases",
    ):
        if float(culling_threshold) < min_value_culling_lca_base and (
            mode in CONVENTIONAL_LCA_MODES
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
                run_multi_lca_computation(
                    bw_activities, bw_methods, exiobase_db_name, culling_threshold
                )
            )
        elif mode in REUSED_SOLVER_MODES:
            results_log.extend(
                run_reused_solver_lca_computations(
                    bw_activities,
                    bw_methods,
                    exiobase_db_name,
                    culling_threshold,
                    mode,
                    rtol,
                )
            )
        else:
            results_log.extend(
                run_isolated_lca_computations(
                    bw_activities,
                    bw_methods,
                    exiobase_db_name,
                    culling_threshold,
                    mode,
                    rtol,
                )
            )
    return results_log


def check_all_databases_are_in_bw(
    exiobase_data: EeioDatabase, culling_thresholds: List[float]
) -> None:
    if not all(
        f"{EXIOBASE_NAME}-{exiobase_data['version']}-{exiobase_data['reference_year']}-{culling_threshold}"
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
    culling_threshold: float,
) -> List[ResultsLogValue]:
    results_log: List[ResultsLogValue] = []
    functional_units = {
        format_activity_label((activity["location"], activity["name"])): {
            int(activity["id"]): 1.0
        }
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

    start = perf_counter()
    multi_lca.lci()
    multi_lca.lcia()
    end = perf_counter()

    method_by_bw_method = {value: key for key, value in bw_methods.items()}

    for label, score in multi_lca.scores.items():
        bw_method, activity = label
        method = method_by_bw_method[bw_method]
        nb_of_computations = len(bw_methods) * len(bw_activities)
        results_log.append(
            {
                "computation_type": "multi_lca_base",
                "activity": activity,
                "method": method,
                "score": score,
                "computation_time": (end - start) / nb_of_computations,
                "db_name": exiobase_db_name,
                "culling_threshold": culling_threshold,
            }
        )
    return results_log


def run_isolated_lca_computations(
    bw_activities: Dict[Tuple[str, str], Any],
    bw_methods: Dict[str, Any],
    exiobase_db_name: str,
    culling_threshold: float,
    mode: Literal["lca_base", "lca_jacobi"],
    rtol: float = 1e-6,
) -> List[ResultsLogValue]:
    results_log: List[ResultsLogValue] = []
    for method in tqdm(bw_methods.values(), desc="Going through methods"):
        for activity in tqdm(bw_activities.values(), desc="Going through activities"):
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
            start = perf_counter()
            lca.lci()
            lca.lcia()
            end = perf_counter()

            results_log.append(
                {
                    "computation_type": mode,
                    "activity": format_activity_label(
                        (activity["location"], activity["name"])
                    ),
                    "method": list(bw_methods.keys())[
                        list(bw_methods.values()).index(method)
                    ],
                    "score": lca.score,
                    "computation_time": end - start,
                    "db_name": exiobase_db_name,
                    "culling_threshold": culling_threshold,
                }
            )
    return results_log


def run_reused_solver_lca_computations(
    bw_activities: Dict[Tuple[str, str], Any],
    bw_methods: Dict[str, Any],
    exiobase_db_name: str,
    culling_threshold: float,
    mode: Literal["lca_factorized", "lca_jacobi_cold", "lca_jacobi_warm"],
    rtol: float = 1e-6,
) -> List[ResultsLogValue]:
    results_log: List[ResultsLogValue] = []
    activity_items = list(bw_activities.items())
    method_items = list(bw_methods.items())
    if not activity_items or not method_items:
        return results_log

    first_activity_label, first_activity = activity_items[0]
    first_method_name, first_method = method_items[0]
    lca = get_reused_solver_instance(
        mode=mode,
        first_activity=first_activity,
        first_method=first_method,
        rtol=rtol,
    )
    current_method_name = first_method_name
    nb_methods = len(method_items)

    for i, (activity_label, activity) in enumerate(
        tqdm(activity_items, desc="Going through activities")
    ):
        start = perf_counter()
        if mode == "lca_factorized":
            if i == 0:
                lca.lci(factorize=True)
            else:
                lca.lci(demand={activity.id: 1})
        elif i == 0:
            lca.lci()
        else:
            lca.lci(demand={activity.id: 1})
        end = perf_counter()
        lci_share = (end - start) / nb_methods

        for method_name, bw_method in tqdm(method_items, desc="Going through methods"):
            if method_name != current_method_name:
                lca.switch_method(bw_method)
                current_method_name = method_name
            start = perf_counter()
            lca.lcia()
            end = perf_counter()
            results_log.append(
                {
                    "computation_type": mode,
                    "activity": format_activity_label(activity_label),
                    "method": method_name,
                    "score": lca.score,
                    "computation_time": lci_share + (end - start),
                    "db_name": exiobase_db_name,
                    "culling_threshold": culling_threshold,
                }
            )

    return results_log


def get_reused_solver_instance(
    mode: Literal["lca_factorized", "lca_jacobi_cold", "lca_jacobi_warm"],
    first_activity: Any,
    first_method: Any,
    rtol: float,
) -> bc.LCA:
    if mode == "lca_factorized":
        return bc.LCA(demand={first_activity: 1}, method=first_method)
    if mode == "lca_jacobi_cold":
        return bc.JacobiGMRESLCA(
            demand={first_activity: 1},
            method=first_method,
            rtol=rtol,
            use_guess=False,
        )
    if mode == "lca_jacobi_warm":
        return bc.JacobiGMRESLCA(
            demand={first_activity: 1},
            method=first_method,
            rtol=rtol,
            use_guess=True,
        )

    logging.error("Computation mode %s is unknown and not supported", mode)
    raise NotImplementedError


def format_activity_label(activity: Tuple[str, str]) -> str:
    return str(activity)
