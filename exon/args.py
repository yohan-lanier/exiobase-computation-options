from tap import Tap

from exon.exiobase import VALID_DATABASES


class ExonParser(Tap):
    bw_project_name: str
    database: str
    method: str
    culling_thresholds: list[float]
    steps: list[str]

    def configure(self) -> None:
        self.add_argument(
            "-p",
            "--bw-project-name",
            help="name of the brightway project that will be used",
            dest="bw_project_name",
            required=True,
        )

        self.add_argument(
            "-d",
            "--database",
            help="name of the exiobase database to use for imports",
            dest="database",
            choices=VALID_DATABASES,
        )

        self.add_argument(
            "-m",
            "--method",
            help="name of the lcia method to use for impact computations",
            dest="method",
            choices=["iwp-2.2.1"],
        )

        self.add_argument(
            "-t",
            "--culling-thresholds",
            help="list of culling thresholds values. "
            "The code will generate one exiobase database per input culling threshold",
            dest="culling_thresholds",
            default=[1e-15],
            nargs="+",
        )

        self.add_argument(
            "-s",
            "--steps",
            help="Can be used to only perform some steps of the script.",
            dest="steps",
            nargs="*",
            choices=["all", "extract_only", "extract_and_build", "method"],
        )
