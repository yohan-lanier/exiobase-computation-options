import logging
from random import sample
from time import strftime
from typing import List

import pandas as pd

from exon.args import ExonParser
from exon.exiobase import (
    EXIOBASE_DATABASES,
    build_exiobase_in_bw,
    extract_exiobase_data,
)
from exon.lcia_computations import run_bw_computations, run_direct_matrix_computation
from exon.lcia_methods import LCIA_METHODS
from exon.logger import configure_logger
from exon.paths import DATA
from exon.utils import (
    MIN_VALUE_CULLING_FOR_LCA_BASE_COMP,
    ResultsLogValue,
    get_biosphere_version,
    get_database_biosphere_name,
)

if __name__ == "__main__":
    configure_logger()
    args = ExonParser(
        description="""A python pipeline importing exiobase to brightway for different
        culling trehshold values and running lca computations for different computation
        modes. Output present results and computation times in a .csv file"""
    ).parse_args()
    exiobase = EXIOBASE_DATABASES[args.database]
    method = LCIA_METHODS[args.method]
    steps = args.steps
    bw_project = args.bw_project_name
    if "build" in steps or "all" in steps:
        exiobase_data = extract_exiobase_data(
            exiobase["version"], exiobase["reference_year"]
        )
        build_exiobase_in_bw(
            exiobase_data,
            exiobase["version"],
            exiobase["reference_year"],
            args.culling_thresholds,
            bw_project,
        )
    if "method" in steps or "all" in steps:
        method["import_in_bw"](bw_project)

    if "compute" in steps or "all" in steps:
        exiobase_data = extract_exiobase_data(
            exiobase["version"], exiobase["reference_year"]
        )
        BIOSPHERE_VERSION = get_biosphere_version(
            get_database_biosphere_name("exiobase", bw_project)
        )
        c_matrix = method["extract_cfs"](BIOSPHERE_VERSION)
        nb_indicators = c_matrix.shape[0]
        # drop all categories for which all cfs are null
        c_matrix = c_matrix.loc[~(c_matrix == 0).all(axis=1)]
        if c_matrix.shape[0] < nb_indicators:
            logging.warning(
                "Dropping %i impact indicators because all cfs are null.",
                (nb_indicators - c_matrix.shape[0]),
            )
        exiobase_data["c"] = c_matrix
        activities_list = exiobase_data["a"].index.to_list()
        random_activities = sample(activities_list, int(args.nb_activities))
        random_activities_index = [
            activities_list.index(act) for act in random_activities
        ]
        random_methods = sample(c_matrix.index.to_list(), int(args.nb_indicators))
        results_log: List[ResultsLogValue] = []

        results_log.extend(
            run_direct_matrix_computation(
                exiobase_data,
                activities_list,
                random_activities_index,
                random_methods,
                mode="iterative",
            )
        )
        results_log.extend(
            run_direct_matrix_computation(
                exiobase_data,
                activities_list,
                random_activities_index,
                random_methods,
                mode="aggregated",
            )
        )

        results_log.extend(
            run_bw_computations(
                exiobase,
                args.culling_thresholds,
                random_activities,
                random_methods,
                bw_project,
                mode="lca_jacobi",
                rtol=1e-6,
            )
        )

        results_log.extend(
            run_bw_computations(
                exiobase,
                args.culling_thresholds,
                random_activities,
                random_methods,
                bw_project,
                mode="lca_base",
                min_value_culling_lca_base=MIN_VALUE_CULLING_FOR_LCA_BASE_COMP,
            )
        )

        # change to use built-in csv module later
        pd.DataFrame.from_records(results_log).to_csv(
            DATA / "output" / f"{strftime("%Y%m%d-%H%M%S")}-results_log.csv"
        )
