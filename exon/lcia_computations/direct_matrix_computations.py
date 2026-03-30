import logging
import time
from typing import List, Literal, Tuple

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
    nb_of_activities = len(activities_index)
    nb_of_methods = len(methods)

    logging.info("⚙️ Running manual computation in mode %s", mode)
    a_matrix_np = exiobase_data["a"].to_numpy()
    s_matrix_np = exiobase_data["s"].to_numpy()

    c_matrix = exiobase_data.get("c")
    if c_matrix is None:
        logging.error("Not characterization matrix found in input data.")
        raise NotImplementedError

    identity_matrix = np.identity(len(a_matrix_np))
    tech_matrix = identity_matrix - a_matrix_np

    if mode == "iterative":
        results_log: List[ResultsLogValue] = []
        logging.info(
            "Running computations activities by activities for %s activities"
            " and method by method for %s methods",
            nb_of_activities,
            nb_of_methods,
        )
        for activity_index in tqdm(activities_index):
            y = np.zeros((len(a_matrix_np), 1))
            y[activity_index] = 1
            for method in methods:
                c_matrix_filtered = c_matrix.loc[method, :]
                c_matrix_np = c_matrix_filtered.to_numpy()
                start = time.time()
                lca_score = c_matrix_np.dot(
                    s_matrix_np.dot(np.linalg.inv(tech_matrix).dot(y))
                )[0]
                end = time.time()
                if verbose:
                    logging.info(
                        "Manual computation: Time = %s seconds | Score = %s | Activity = %s | Indicator = %s",
                        end - start,
                        lca_score,
                        activity_index,
                        method,
                    )
                results_log.append(
                    {
                        "computation_type": "matrix_iterative",
                        "activity": str(all_activities[activity_index]),
                        "method": method,
                        "computation_time": end - start,
                        "score": lca_score,
                    }
                )
        return results_log

    if mode == "aggregated":
        logging.info(
            "Running all computations at once for %s activities" " and %s methods",
            nb_of_activities,
            nb_of_methods,
        )
        Y = np.zeros((len(a_matrix_np), nb_of_activities))
        for i, act_index in enumerate(activities_index):
            Y[act_index][i] = 1
        c_matrix_filtered = c_matrix.loc[methods, :]
        c_matrix_np = c_matrix_filtered.to_numpy()
        start = time.time()
        lca_scores = c_matrix_np.dot(s_matrix_np.dot(np.linalg.inv(tech_matrix).dot(Y)))
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
