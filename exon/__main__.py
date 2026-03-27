from exon.args import ExonParser
from exon.exiobase import (
    EXIOBASE_DATABASES,
    build_exiobase_in_bw,
    extract_exiobase_data,
)
from exon.logger import configure_logger

if __name__ == "__main__":
    configure_logger()
    args = ExonParser(description="""TO WRITE""").parse_args()
    exiobase = EXIOBASE_DATABASES[args.database]
    steps = args.steps
    if "extract_only" in steps or "all" in steps:
        exiobase_data = extract_exiobase_data(
            exiobase["version"], exiobase["reference_year"]
        )
    if "extract_and_build" in steps or "all" in steps:
        exiobase_data = extract_exiobase_data(
            exiobase["version"], exiobase["reference_year"]
        )
        build_exiobase_in_bw(
            exiobase_data,
            exiobase["version"],
            exiobase["reference_year"],
            args.culling_thresholds,
        )
    if "lcia_method" in steps or all in steps:
        pass
