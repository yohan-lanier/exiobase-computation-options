from typing import Callable, Dict, TypedDict, cast

import pandas as pd

from exon.lcia_methods.constants import (
    IWP_EXIOBASE_FILE_MIDDLE,
    IWP_EXIOBASE_FILE_PREFIX,
    IWP_NAME,
)
from exon.lcia_methods.iwp import create_iwp_method_for_exio, load_cfs
from exon.utils import LciaMethod

LCIA_METHODS: Dict[str, LciaMethod] = {
    **{
        f"{IWP_NAME}-{version}": {
            "name": IWP_NAME,
            "method_version": version,
            "extract_cfs": cast(
                Callable[[str], pd.DataFrame],
                lambda biosphere_version, method_version=version: load_cfs(
                    method_version, biosphere_version
                ),
            ),
            "import_in_bw": cast(
                Callable[[str], None],
                lambda bw_project, version=version: create_iwp_method_for_exio(
                    version, bw_project
                ),
            ),
        }
        for version in ["2.2", "2.2.1"]
    }
}

VALID_SET_OF_LCIA_METHODS = LCIA_METHODS.keys()

__all__ = [
    "LCIA_METHODS",
    "VALID_SET_OF_LCIA_METHODS",
    "IWP_NAME",
    "IWP_EXIOBASE_FILE_MIDDLE",
    "IWP_EXIOBASE_FILE_PREFIX",
]
