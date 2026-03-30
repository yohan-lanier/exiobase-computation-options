from typing import Callable, TypedDict, cast

from exon.lcia_methods.constants import (
    IWP_EXIOBASE_FILE_MIDDLE,
    IWP_EXIOBASE_FILE_PREFIX,
    IWP_NAME,
)
from exon.lcia_methods.iwp import create_iwp_method_for_exio


class LciaMethod(TypedDict):
    name: str
    method_version: str
    import_in_bw: Callable[[str], None]


LCIA_METHODS: dict[str, LciaMethod] = {
    **{
        f"{IWP_NAME}-{version}": {
            "name": IWP_NAME,
            "method_version": version,
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
