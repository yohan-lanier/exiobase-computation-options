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
    extrat_cfs_for_method_and_drop_null_cfs,
    generate_random_samples_for_computations,
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
        exiobase_data["c"] = extrat_cfs_for_method_and_drop_null_cfs(bw_project, method)
        lists_for_computations = generate_random_samples_for_computations(
            exiobase_data, args
        )
        all_activities, random_activities, random_activities_index, random_methods = (
            lists_for_computations["all_activities"],
            lists_for_computations["random_activities"],
            lists_for_computations["random_activities_index"],
            lists_for_computations["random_methods"],
        )
        results_log: List[ResultsLogValue] = []

        results_log.extend(
            run_direct_matrix_computation(
                exiobase_data,
                all_activities,
                random_activities_index,
                random_methods,
                mode="iterative",
            )
        )
        results_log.extend(
            run_direct_matrix_computation(
                exiobase_data,
                all_activities,
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
