import logging
import time
from typing import List, Literal, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from exon.utils import ExiobaseRelevantData


def run_direct_matrix_computation(
    exiobase_data: ExiobaseRelevantData,
    activities: List[Tuple[str, str]],
    activities_index: List[int],
    methods: List[str],
    mode: Literal["iterative"] | Literal["aggregated"] = "aggregated",
) -> None:
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
        logging.info(
            "Running computations activities by activities for %s activities"
            " and method by method for %s methods",
            len(activities_index),
            len(methods),
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
                )
                logging.info(
                    "Manual computation: Time = %s seconds | Score = %s | Activity = %s | Indicator = %s",
                    time.time() - start,
                    lca_score,
                    activity_index,
                    method,
                )
    if mode == "aggregated":
        logging.info(
            "Running all computations at once for %s activities" " and %s methods",
            len(activities),
            len(methods),
        )
        Y = np.zeros((len(a_matrix_np), len(activities_index)))
        for i, act_index in enumerate(activities_index):
            Y[act_index][i] = 1
        c_matrix_filtered = c_matrix.loc[methods, :]
        c_matrix_np = c_matrix_filtered.to_numpy()
        start = time.time()
        lca_scores = c_matrix_np.dot(s_matrix_np.dot(np.linalg.inv(tech_matrix).dot(Y)))
        logging.info("Runned all computations in %s seconds", time.time() - start)
        print(
            pd.DataFrame(
                lca_scores,
                index=methods,
                columns=[activities[i] for i in activities_index],
            )
        )
