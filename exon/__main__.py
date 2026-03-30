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
from exon.lcia_methods import (
    IWP_EXIOBASE_FILE_MIDDLE,
    IWP_EXIOBASE_FILE_PREFIX,
    IWP_NAME,
    LCIA_METHODS,
)
from exon.logger import configure_logger
from exon.paths import DATA, LCIA_METHODS_PATH
from exon.utils import (
    MIN_VALUE_CULLING_FOR_LCA_BASE_COMP,
    ResultsLogValue,
    get_biosphere_version,
    get_database_biosphere_name,
)

if __name__ == "__main__":
    configure_logger()
    args = ExonParser(description="""TO WRITE""").parse_args()
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
        c_matrix = pd.read_excel(
            LCIA_METHODS_PATH
            / IWP_NAME
            / method["method_version"]
            / (
                IWP_EXIOBASE_FILE_PREFIX
                + method["method_version"]
                + IWP_EXIOBASE_FILE_MIDDLE
                + BIOSPHERE_VERSION
                + ".xlsx"
            ),
            index_col=0,
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
