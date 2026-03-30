import logging
import time
from typing import List

import numpy as np
import pandas as pd
from tqdm import tqdm


def run_manual_computation(
    a_matrix: pd.DataFrame,
    s_matrix: pd.DataFrame,
    c_matrix: pd.DataFrame,
    activities: List[int],
    methods: List[str],
) -> None:

    a_matrix_np = a_matrix.to_numpy()
    s_matrix_np = s_matrix.to_numpy()
    identity_matrix = np.identity(len(a_matrix_np))
    tech_matrix = identity_matrix - a_matrix_np
    y = np.zeros((len(a_matrix_np), 1))
    for activity_index in tqdm(activities):
        y[activity_index] = 1
        for method in methods:
            c_matrix_filtered = c_matrix.loc[method, :]
            c_matrix_np = c_matrix_filtered.to_numpy()
            start = time.time()
            lca_score = c_matrix_np.dot(
                s_matrix_np.dot(np.linalg.inv(tech_matrix).dot(y))
            )
            logging.info(
                "Manual computation: Time = %s seconds | Score = %s",
                start - time.time(),
                lca_score,
            )
