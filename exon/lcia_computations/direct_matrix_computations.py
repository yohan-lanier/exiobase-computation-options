import logging
import time
from typing import Any, List, Literal, Tuple, TypedDict

import numpy as np
import pandas as pd
from tqdm import tqdm

from exon.utils import ExiobaseRelevantData, ResultsLogValue


def run_direct_matrix_computation(
    exiobase_data: ExiobaseRelevantData,
    all_activities: List[Tuple[str, str]],
    activities_index: List[int],
    methods: List[str],
    mode: Literal["iterative"] | Literal["aggregated"] = "aggregated",
    verbose: bool = False,
) -> List[ResultsLogValue]:

    logging.info("⚙️ Running direct matrix computation in mode %s", mode)

    if mode == "iterative":
        return run_iterative_matrix_computations(
            exiobase_data, all_activities, activities_index, methods, verbose=verbose
        )

    if mode == "aggregated":
        return run_aggregated_matrix_computations(
            exiobase_data, all_activities, activities_index, methods, verbose=verbose
        )


def run_iterative_matrix_computations(
    exiobase_data: ExiobaseRelevantData,
    all_activities: List[Tuple[str, str]],
    activities_index: List[int],
    methods: List[str],
    verbose: bool = False,
) -> List[ResultsLogValue]:
    results_log: List[ResultsLogValue] = []
    nb_of_activities = len(activities_index)
    nb_of_methods = len(methods)
    logging.info(
        "Running computations activities by activities for %s activities"
        " and method by method for %s methods",
        nb_of_activities,
        nb_of_methods,
    )
    a_matrix_np, s_matrix_np, c_matrix, tech_matrix_np = prepare_data_for_computations(
        exiobase_data
    )
    for activity_index in tqdm(activities_index, desc="Going through activities"):
        y = np.zeros((len(a_matrix_np), 1))
        y[activity_index] = 1
        for method in tqdm(methods, desc="Going through methods"):
            results_log.append(
                compute_one_lca(
                    {
                        "tech_matrix_np": tech_matrix_np,
                        "s_matrix_np": s_matrix_np,
                        "c_matrix": c_matrix,
                        "y_np": y,
                    },
                    activity_index,
                    method,
                    all_activities,
                    verbose=verbose,
                )
            )
    return results_log


def prepare_data_for_computations(
    exiobase_data: ExiobaseRelevantData,
) -> Tuple[Any, Any, Any, Any]:
    a_matrix_np = exiobase_data["a"].to_numpy()
    c_matrix = exiobase_data.get("c")
    if c_matrix is None:
        logging.error("No characterization matrix found in input data.")
        raise NotImplementedError
    tech_matrix_np = np.identity(len(a_matrix_np)) - a_matrix_np
    return (a_matrix_np, exiobase_data["s"].to_numpy(), c_matrix, tech_matrix_np)


class ComputationMatrices(TypedDict):
    tech_matrix_np: np.ndarray
    s_matrix_np: np.ndarray
    c_matrix: pd.DataFrame
    y_np: np.ndarray


def compute_one_lca(
    matrices: ComputationMatrices,
    activity_index: int,
    method: str,
    all_activities: List[Tuple[str, str]],
    verbose: bool = False,
) -> ResultsLogValue:
    c_matrix_filtered = matrices["c_matrix"].loc[method, :]
    c_matrix_np = c_matrix_filtered.to_numpy()
    start = time.time()
    lca_score = c_matrix_np.dot(
        matrices["s_matrix_np"].dot(
            np.linalg.inv(matrices["tech_matrix_np"]).dot(matrices["y_np"])
        )
    )[0]
    end = time.time()
    if verbose:
        logging.info(
            "Manual computation: Time = %s seconds | Score = %s | "
            "Activity = %s | Indicator = %s",
            end - start,
            lca_score,
            activity_index,
            method,
        )
    return {
        "computation_type": "matrix_iterative",
        "activity": str(all_activities[activity_index]),
        "method": method,
        "computation_time": end - start,
        "score": lca_score,
    }


def run_aggregated_matrix_computations(
    exiobase_data: ExiobaseRelevantData,
    all_activities: List[Tuple[str, str]],
    activities_index: List[int],
    methods: List[str],
    verbose: bool = False,
) -> List[ResultsLogValue]:
    nb_of_activities = len(activities_index)
    nb_of_methods = len(methods)
    logging.info(
        "Running all computations at once for %s activities and %s methods",
        nb_of_activities,
        nb_of_methods,
    )
    a_matrix_np, s_matrix_np, c_matrix, tech_matrix_np = prepare_data_for_computations(
        exiobase_data
    )
    y_matrix_np = np.zeros((len(a_matrix_np), nb_of_activities))
    for i, act_index in enumerate(activities_index):
        y_matrix_np[act_index][i] = 1
    c_matrix_filtered = c_matrix.loc[methods, :]
    c_matrix_np = c_matrix_filtered.to_numpy()
    start = time.time()
    lca_scores = c_matrix_np.dot(
        s_matrix_np.dot(np.linalg.inv(tech_matrix_np).dot(y_matrix_np))
    )
    end = time.time()
    if verbose:
        logging.info("Runned all computations in %s seconds", end - start)
        print(
            pd.DataFrame(
                lca_scores,
                index=methods,
                columns=[all_activities[i] for i in activities_index],
            )
        )
    nb_of_computed_scores = nb_of_activities * nb_of_methods
    return [
        {
            "computation_type": "matrix_aggregated",
            "activity": str(all_activities[act_index]),
            "method": method,
            "computation_time": (end - start) / nb_of_computed_scores,
            "score": lca_scores[j][i],
        }
        for i, act_index in enumerate(activities_index)
        for j, method in enumerate(methods)
    ]
