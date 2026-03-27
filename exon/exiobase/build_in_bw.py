import logging
from itertools import chain
from typing import Any, Dict, Generator, List, Literal, Tuple, TypedDict, cast
from uuid import uuid4

import bw2data as bd
import pandas as pd
from bw2data.backends.iotable import IOTableBackend
from packaging.version import Version
from tqdm import tqdm

from exon.exiobase.constants import (
    BW_PROCESS_TYPE,
    CONDITIONS_FOR_EXIOBASE_BIOSPHERE,
    EURO_UNIT,
    EXIOBASE_NAME,
)
from exon.exiobase.extract import ExiobaseRelevantData


def build_exiobase_in_bw(
    exiobase_data: ExiobaseRelevantData,
    version: str,
    reference_year: str,
    culling_thresholds: List[float],
) -> None:
    exiobase_technosphere_names = [
        f"{EXIOBASE_NAME}-{version}-{reference_year}-{culling_threshold}"
        for culling_threshold in culling_thresholds
    ]
    if any(name in bd.databases for name in exiobase_technosphere_names):
        logging.error(
            "Exiobase databases already exist in your project"
            " for version %s and reference year %s. If you wish to overwrite,"
            "delete them manually and relaunch code.",
            version,
            reference_year,
        )

    if Version(version) >= Version("3.9"):
        exiobase_biosphere_name = f"{EXIOBASE_NAME}-3.9-and-more-biosphere"
    else:
        exiobase_biosphere_name = f"{EXIOBASE_NAME}-3.8.2-and-less-biosphere"

    units = exiobase_data["units"]
    if not need_to_create_biosphere(exiobase_biosphere_name, version):
        del bd.databases[exiobase_biosphere_name]

    exiobase_biosphere_data = build_exiobase_biosphere(units, exiobase_biosphere_name)
    logging.info("✅ Successfully imported exiobase biosphere to brightway")
    build_exiobase_technospheres(
        a_matrix=exiobase_data["a"],
        s_matrix=exiobase_data["s"],
        exiobase_biosphere_data={
            "biosphere_name_to_code_mapping": exiobase_biosphere_data,
            "biosphere_name": exiobase_biosphere_name,
        },
        version=version,
        reference_year=reference_year,
        culling_thresholds=culling_thresholds,
    )


def need_to_create_biosphere(exiobase_biosphere_name: str, version: str) -> bool:
    if exiobase_biosphere_name in bd.databases:
        logging.warning(
            "A biosphere (%s) corresponding to the exiobase version (%s) you are importing "
            "already exists in your project. Deleting it a rebuilding. This is because "
            "exiobase biosphere can differ from version to version and from a reference year"
            " to another within a single version.",
            version,
            exiobase_biosphere_name,
        )
        return False
    else:
        logging.info(
            "No biosphere corresponding to the exiobase version (%s) your are importing. "
            "Generating biosphere (%s)",
            version,
            exiobase_biosphere_name,
        )
        return True


class ExiobaseBiosphereData(TypedDict):
    biosphere_name_to_code_mapping: dict[str, int]
    biosphere_name: str


def build_exiobase_biosphere(
    units: pd.DataFrame, exiobase_biosphere_name: str
) -> dict[str, int]:
    exiobase_biosphere = {}

    for stressor in tqdm(units.index, desc="creating biosphere data for db writing"):
        code = str(uuid4())  # create unique id for stressor

        for check, stressor_type, categories in CONDITIONS_FOR_EXIOBASE_BIOSPHERE:
            if check(stressor):
                exiobase_biosphere[(exiobase_biosphere_name, code)] = {
                    "type": stressor_type,
                    "unit": units.loc[stressor, "unit"],
                    "categories": categories,
                    "name": stressor,
                    "code": code,
                }
    biosphere_bw_db = bd.Database(exiobase_biosphere_name)
    biosphere_bw_db.register(format="EXIOBASE 3 Biosphere")
    logging.info("creating exiobase biosphere in brightway[...]")
    biosphere_bw_db.write(exiobase_biosphere)
    return {
        s["name"]: s["id"] for s in biosphere_bw_db
    }  # pyright: ignore[reportGeneralTypeIssues]


def build_exiobase_technospheres(
    a_matrix: pd.DataFrame,
    s_matrix: pd.DataFrame,
    exiobase_biosphere_data: ExiobaseBiosphereData,
    version: str,
    reference_year: str,
    culling_thresholds: List[float],
) -> None:
    exiobase_technosphere_base_name = f"{EXIOBASE_NAME}-{version}-{reference_year}"
    for culling_threshold in culling_thresholds:
        logging.info(
            "⚙️ creating exiobase technosphere database for culling threshold %s",
            culling_threshold,
        )
        logging.info(
            "creating exiobase technosphere without exchanges in brightway for[...]"
        )
        exiobase_technosphere_name = (
            exiobase_technosphere_base_name + f"-{culling_threshold}"
        )
        technosphere_mapping = get_initial_exiobase_technosphere_data(
            a_matrix, exiobase_technosphere_name
        )
        additional_data = cast(
            ExiobaseExchangesPopulationData,
            {
                "biosphere_mapping": exiobase_biosphere_data[
                    "biosphere_name_to_code_mapping"
                ],
                "technosphere_mapping": technosphere_mapping,
            },
        )

        technosphere_iterator = get_exiobase_exchanges_iterator(
            exchange_type="technosphere",
            exchange_matrix=a_matrix,
            additional_data=additional_data,
            culling=float(culling_threshold),
        )
        biosphere_iterator = get_exiobase_exchanges_iterator(
            exchange_type="biosphere",
            exchange_matrix=s_matrix,
            additional_data=additional_data,
        )
        technosphere = chain(
            (
                {
                    "row": x,
                    "col": y,
                    "amount": z,
                    "flip": True,
                    "uncertainty_type": 0,
                }
                for x, y, z in technosphere_iterator
            ),
            (
                {
                    "row": x,
                    "col": x,
                    "amount": 1,
                    "flip": False,
                    "uncertainty_type": 0,
                }
                for x in technosphere_mapping.values()
            ),
        )
        biosphere = (
            {
                "row": x,
                "col": y,
                "amount": z,
                "flip": False,
                "uncertainty_type": 0,
            }
            for x, y, z in biosphere_iterator
        )
        logging.info("Writing exiobase exchanges to brightway[...]")
        IOTableBackend(exiobase_technosphere_name).write_exchanges(
            technosphere,
            biosphere,
            dependents=[exiobase_biosphere_data["biosphere_name"]],
        )


def get_initial_exiobase_technosphere_data(
    a_matrix: pd.DataFrame,
    exiobase_technosphere_name: str,
) -> Dict[Tuple[str, str], str]:
    """
    Initializes the technosphere brightway database by writing
    all the processes with their metadata but without any exchange
    as an IOTableBackend database.

    Exchanges will populated later on as np.arrays to save storage
    and speed up writing process.
    """
    technosphere_bw_db = IOTableBackend(exiobase_technosphere_name)
    exiobase_technosphere = {}
    # initialize technosphere processes - exchanges will be populated afterward
    for product_per_region in tqdm(
        a_matrix.columns, desc="creating initial technosphere data for db writing"
    ):
        product_name = product_per_region[1]
        location = product_per_region[0]
        code = str(uuid4())
        exiobase_technosphere[(exiobase_technosphere_name, code)] = {
            "type": BW_PROCESS_TYPE,
            "unit": EURO_UNIT,
            "location": location,
            "name": product_name,
            "reference product": product_name,
            "database": exiobase_technosphere_name,
            "code": code,
            "exchanges": [],
        }
    technosphere_bw_db.register(format="EXIOBASE 3 Technosphere")
    technosphere_bw_db.write(exiobase_technosphere)
    return {(p["name"], p["location"]): p["id"] for p in technosphere_bw_db}


class ExiobaseExchangesPopulationData(TypedDict):
    biosphere_mapping: dict[str, str]
    technosphere_mapping: dict[Tuple[str, str], str]


def get_exiobase_exchanges_iterator(
    exchange_type: Literal["technosphere", "biosphere"],
    exchange_matrix: pd.DataFrame,
    additional_data: ExiobaseExchangesPopulationData,
    culling: float = 1e-15,
) -> Generator[Tuple[str, str, float], None, None]:
    technosphere_mapping = additional_data["technosphere_mapping"]
    flattened_exchange_matrix = cast(pd.Series, exchange_matrix.stack().stack())
    if exchange_type == "technosphere":
        flattened_exchange_matrix_as_dict = flattened_exchange_matrix[
            abs(flattened_exchange_matrix) > culling
        ].to_dict()
        # for technosphere, exchanges lines of the dict look like
        # ('AT', 'Wheat', 'Wheat', 'WE'): 2.82e-06
    else:
        flattened_exchange_matrix_as_dict = flattened_exchange_matrix[
            flattened_exchange_matrix != 0
        ].to_dict()
        # for biosphere, exchanges lines of the dict look like
        # ('Co2', 'Wheat', 'WE): 1e-7
    flattened_exchange_matrix_as_dict = cast(
        Dict[Any, Any], flattened_exchange_matrix_as_dict
    )
    for exchange, amount in tqdm(
        flattened_exchange_matrix_as_dict.items(),
        desc=f"populating {exchange_type} exchanges",
    ):
        if exchange_type == "technosphere":
            parent_id = technosphere_mapping[exchange[2], exchange[3]]
            yield (
                technosphere_mapping[exchange[1], exchange[0]],
                parent_id,
                amount,
            )
        else:
            parent_id = technosphere_mapping[exchange[1], exchange[2]]
            yield (
                additional_data["biosphere_mapping"][exchange[0]],
                parent_id,
                amount,
            )
