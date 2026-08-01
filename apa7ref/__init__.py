"""apa7ref: genera referencias bibliográficas APA 7 a partir de URLs."""

from .extractor import FetchError, fetch_metadata
from .formatter import (
    Metadata,
    build_in_text_citation,
    build_reference,
    format_author,
    format_date_apa,
    parse_date,
)

__version__ = "0.1.0"

__all__ = [
    "fetch_metadata",
    "FetchError",
    "Metadata",
    "build_reference",
    "build_in_text_citation",
    "format_author",
    "format_date_apa",
    "parse_date",
]
