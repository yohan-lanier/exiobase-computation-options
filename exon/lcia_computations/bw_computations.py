import logging
import time
from typing import List, Literal, Tuple

import bw2calc as bc
import bw2data as bd
from tqdm import tqdm

from exon.utils import EXIOBASE_NAME, EeioDatabase, ResultsLogValue

MAX_CULLING_FOR_LCA_BASE_COMP = 1e-5


def run_bw_computations(
    exiobase_data: EeioDatabase,
    culling_thresholds: List[float],
    activities_to_compute: List[Tuple[str, str]],
    methods: List[str],
    bw_project: str,
    mode: Literal["lca_base", "lca_jacobi"] = "lca_base",
    rtol: float = 1e-6,
) -> List[ResultsLogValue]:
    bd.projects.set_current(bw_project)
    exiobase_db_base_name = (
        f"{EXIOBASE_NAME}-{exiobase_data["version"]}-{exiobase_data["reference_year"]}"
    )
    results_log: List[ResultsLogValue] = []

    for culling_threshold in tqdm(
        culling_thresholds,
        desc="Running computation for the different exiobase databases",
    ):
        if (
            float(culling_threshold) < MAX_CULLING_FOR_LCA_BASE_COMP
            and mode == "lca_base"
        ):
            logging.warning(
                "Culling threshold %s is too small for conventional bw lca computation on exiobase. "
                "Skipping these computations",
                culling_threshold,
            )
        exiobase_db_name = exiobase_db_base_name + f"-{culling_threshold}"
        for method in tqdm(methods, desc="Going through methods"):
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
                "More than one method found for 1 method header ",
                "This is not normal",
            )
            method_to_compute = bw_method_to_compute[0]
            for activity in tqdm(
                activities_to_compute, desc="Going through activities"
            ):
                bw_act_to_compute = [
                    act
                    for act in bd.Database(
                        exiobase_db_name
                    )  # pyright: ignore[reportGeneralTypeIssues]
                    if act["name"] == activity[1] and act["location"] == activity[0]
                ]
                assert len(bw_act_to_compute) == 1, (
                    "More than one activity found for 1 (location, name) tupple in exiobase. ",
                    "This is not normal",
                )
                activity_to_compute = bw_act_to_compute[0]

                if mode == "lca_base":
                    lca = bc.LCA(
                        demand={activity_to_compute: 1}, method=method_to_compute
                    )
                if mode == "lca_jacobi":
                    lca = bc.JacobiGMRESLCA(
                        demand={activity_to_compute: 1},
                        method=method_to_compute,
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
