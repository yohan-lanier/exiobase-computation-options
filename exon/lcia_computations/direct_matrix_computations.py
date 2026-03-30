import logging
import time
from typing import List

import numpy as np
import pandas as pd
from tqdm import tqdm


def run_direct_matrix_computation(
    a_matrix: pd.DataFrame,
    s_matrix: pd.DataFrame,
    c_matrix: pd.DataFrame,
    activities: List[int],
    methods: List[str],
) -> None:
    logging.info("⚙️ Running manual computation")
    a_matrix_np = a_matrix.to_numpy()
    s_matrix_np = s_matrix.to_numpy()
    identity_matrix = np.identity(len(a_matrix_np))
    tech_matrix = identity_matrix - a_matrix_np
    logging.info(
        "Running computations activities by activities for %s activities"
        " and method by method for %s methods",
        len(activities),
        len(methods),
    )
    for activity_index in tqdm(activities):
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
    logging.info(
        "Running all computations at once for %s activities" " and %s methods",
        len(activities),
        len(methods),
    )
    Y = np.zeros((len(a_matrix_np), len(activities)))
    for i, act_index in enumerate(activities):
        Y[act_index][i] = 1
    c_matrix_filtered = c_matrix.loc[methods, :]
    c_matrix_np = c_matrix_filtered.to_numpy()
    start = time.time()
    lca_scores = c_matrix_np.dot(s_matrix_np.dot(np.linalg.inv(tech_matrix).dot(Y)))
    logging.info("Runned all computations in %s seconds", time.time() - start)
    print(pd.DataFrame(lca_scores, index=methods, columns=activities))
    activity_list = a_matrix.index.to_list()
    logging.info(
        "Activity index correspondance %s", [activity_list[i] for i in activities]
    )
