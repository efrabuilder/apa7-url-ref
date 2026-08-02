"""Formateo de metadatos a referencias APA 7.

Misma lógica que la versión JavaScript usada en index.html, para que la
CLI/librería y la página web produzcan resultados consistentes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# Palabras que sugieren que el "autor" es en realidad una organización, no
# una persona, y por lo tanto no debe reformatearse a "Apellido, N. N.".
ORG_MARKERS = re.compile(
    r"\b(inc|llc|ltd|corp|company|co\.|team|staff|editorial|"
    r"redacci[oó]n|news|noticias|university|universidad|department|"
    r"departamento|agency|agencia)\b",
    re.IGNORECASE,
)

# Un nombre de persona real casi siempre son 2-4 palabras compuestas solo por
# letras (con acentos/guiones/apóstrofes) en formato Título, sin mayúsculas
# sostenidas. Nombres de canal de YouTube, marcas, etc. suelen romper esto
# (más de 4 palabras, símbolos, siglas en mayúsculas como "MX" o "GAME") — en
# esos casos es mejor no reformatear el autor.
NAME_PART_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’-]+$")
MAX_PERSON_NAME_WORDS = 4

YEAR_RE = re.compile(r"(19|20)\d{2}")
ONLY_YEAR_RE = re.compile(r"^(19|20)\d{2}$")


def _looks_like_person_name(parts: list) -> bool:
    """Heurística: ¿esta lista de palabras parece nombre de una persona?"""
    if not (2 <= len(parts) <= MAX_PERSON_NAME_WORDS):
        return False
    for part in parts:
        if not NAME_PART_RE.match(part):
            return False
        if part.isupper() and len(part) > 1:
            return False
    return True


@dataclass
class ParsedDate:
    year: int
    month: Optional[int] = None
    day: Optional[int] = None
    only_year: bool = False


@dataclass
class Metadata:
    """Metadatos de una fuente, listos para formatear."""
    url: str = ""
    title: Optional[str] = None
    author: Optional[str] = None
    site_name: Optional[str] = None
    published_date: Optional[str] = None
    excerpt: str = ""


def parse_date(raw: Optional[str]) -> Optional[ParsedDate]:
    """Interpreta una fecha en texto libre (ISO, solo año, etc.)."""
    if not raw:
        return None
    trimmed = raw.strip()
    if not trimmed:
        return None

    if ONLY_YEAR_RE.match(trimmed):
        return ParsedDate(year=int(trimmed), only_year=True)

    # Intenta formatos ISO comunes (YYYY-MM-DD, con o sin hora/zona).
    iso_candidate = trimmed[:10]
    for fmt in ("%Y-%m-%d",):
        try:
            d = datetime.strptime(iso_candidate, fmt)
            return ParsedDate(year=d.year, month=d.month, day=d.day)
        except ValueError:
            pass

    # Último recurso: cualquier año de 4 dígitos dentro del texto.
    m = YEAR_RE.search(trimmed)
    if m:
        return ParsedDate(year=int(m.group(0)), only_year=True)

    return None


def format_date_apa(parsed: Optional[ParsedDate]) -> str:
    if parsed is None:
        return "s.f."
    if parsed.only_year or not parsed.month:
        return str(parsed.year)
    day = parsed.day or 1
    return f"{parsed.year}, {MONTHS_ES[parsed.month - 1]} {day}"


def format_author(author: Optional[str]) -> Optional[str]:
    """Normaliza el autor a 'Apellido, N. N.' salvo que parezca organización."""
    if not author:
        return None
    trimmed_author = author.strip()
    if not trimmed_author:
        return None
    if ORG_MARKERS.search(trimmed_author):
        return trimmed_author

    parts = trimmed_author.split()
    if len(parts) < 2 or not _looks_like_person_name(parts):
        return trimmed_author

    last_name = parts[-1]
    first_names = parts[:-1]
    initials = " ".join(n[0].upper() + "." for n in first_names if n)
    return f"{last_name}, {initials}"


def build_reference(meta: Metadata) -> str:
    """Arma la referencia APA 7 completa a partir de los metadatos."""
    parsed_date = parse_date(meta.published_date)
    date_str = format_date_apa(parsed_date)

    title = (meta.title or "Sin título").strip()
    if not re.search(r"[.?!]$", title):
        title += "."

    site_name = (meta.site_name or "").strip()
    author = format_author(meta.author)

    if author:
        sep = "" if author.endswith(".") else "."
        author_part = f"{author}{sep} ({date_str}). "
        site_part = f"{site_name}. " if site_name else ""
    else:
        author_part = f"{site_name}. ({date_str}). " if site_name else f"({date_str}). "
        site_part = ""

    url_part = meta.url or ""
    reference = f"{author_part}{title} {site_part}{url_part}"
    return re.sub(r"\s{2,}", " ", reference).strip()


def build_in_text_citation(meta: Metadata) -> str:
    """Arma la cita en texto '(Apellido, Año)'."""
    parsed_date = parse_date(meta.published_date)
    year = parsed_date.year if parsed_date else "s.f."
    author = format_author(meta.author) or meta.site_name or "Autor desconocido"
    last_name = author.split(",")[0]
    return f"({last_name}, {year})"
