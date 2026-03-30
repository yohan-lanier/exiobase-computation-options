import pandas as pd

from exon.args import ExonParser
from exon.exiobase import (
    EXIOBASE_DATABASES,
    build_exiobase_in_bw,
    extract_exiobase_data,
)
from exon.lcia_methods import (
    IWP_EXIOBASE_FILE_MIDDLE,
    IWP_EXIOBASE_FILE_PREFIX,
    IWP_NAME,
    LCIA_METHODS,
)
from exon.logger import configure_logger
from exon.paths import LCIA_METHODS_PATH
from exon.utils import get_biosphere_version, get_database_biosphere_name

if __name__ == "__main__":
    configure_logger()
    args = ExonParser(description="""TO WRITE""").parse_args()
    exiobase = EXIOBASE_DATABASES[args.database]
    method = LCIA_METHODS[args.method]
    steps = args.steps
    bw_project = args.bw_project_name
    if "extract_only" in steps or "all" in steps:
        exiobase_data = extract_exiobase_data(
            exiobase["version"], exiobase["reference_year"]
        )
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

    ### SPLIT HERE
    if "compute" in steps or "all" in steps:
        biosphere_version = get_biosphere_version(
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
                + biosphere_version
                + ".xlsx"
            ),
            index_col=0,
        )
