from tap import Tap

from exopt.exiobase import VALID_DATABASES


class ExoptParser(Tap):
    bw_project_name: str
    database: str
    method: str
    culling_thresholds: list[float]
    steps: list[str]
    nb_activities: int = 5
    nb_indicators: int = 1

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
            help="name of the exiobase database to use for imports. "
            "This arg should be a valid choice among options listed above",
            dest="database",
            choices=VALID_DATABASES,
        )

        self.add_argument(
            "-m",
            "--method",
            help="name of the lcia method to use for impact computations. "
            "This arg should be a valid choice amon options listed above. "
            "Useless if `method` or `compute` steps are not used. See below.",
            dest="method",
            choices=["iwp-2.2.1"],
        )

        self.add_argument(
            "-t",
            "--culling-thresholds",
            help="list of culling thresholds values. "
            "The code will generate one exiobase database per input culling threshold. "
            "A culling threshold of 1e-15 means all technosphere exchanges with a "
            "lower amount will be ignored when writing exchanges of the brightway "
            "database.",
            dest="culling_thresholds",
            default=[1e-15],
            nargs="+",
        )

        self.add_argument(
            "-s",
            "--steps",
            help="Can be used to only perform some steps of the script."
            "`all` will perform all steps. `build` will extract data and "
            "build brightway databases. `method` will import the given "
            "method to brightway. `compute` will run lca computations.",
            dest="steps",
            nargs="*",
            choices=["all", "build", "method", "compute"],
        )

        self.add_argument(
            "-a",
            "--nb-activities",
            help="Number of random activities to select to run computations.",
            dest="nb_activities",
            default=5,
            required=False,
        )

        self.add_argument(
            "-i",
            "--nb-indicators",
            help="Number of random indicators to select to run computations.",
            dest="nb_indicators",
            default=1,
            required=False,
        )
