from typing import Callable, Dict

from exon.exiobase.build_in_bw import build_exiobase_in_bw
from exon.exiobase.extract import extract_exiobase_data
from exon.utils import EeioDatabase

EXIOBASE_DATABASES: Dict[str, EeioDatabase] = {
    **{
        f"exiobase-{version}-{ref_year}": {
            "name": "exiobase",
            "version": version,
            "reference_year": ref_year,
        }
        for version in ["3.8.2", "3.9.6", "3.10.1"]
        for ref_year in ["2020", "2022", "2023", "2024"]
    }
}

VALID_DATABASES = list(EXIOBASE_DATABASES.keys())


__all__ = ["EXIOBASE_DATABASES", "extract_exiobase_data", "VALID_DATABASES"]
