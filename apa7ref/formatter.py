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

# Conjunciones que unen varios nombres/autores; si aparecen sueltas dentro
# de lo que se está evaluando como UN solo nombre de persona, es señal de
# que en realidad es una lista sin separar (p. ej. "Ciencia y Tecnología")
# y no debe tratarse como "Nombre Y." con "Y" como inicial.
_LIST_CONJUNCTIONS = {"y", "e", "and", "&"}

YEAR_RE = re.compile(r"(19|20)\d{2}")
ONLY_YEAR_RE = re.compile(r"^(19|20)\d{2}$")

# Partículas que en español, portugués, neerlandés, etc. forman parte del
# apellido y no deben tratarse como nombre de pila (p. ej. "de la Cruz",
# "van der Berg", "von Neumann"). Se usan para extender automáticamente el
# apellido detectado hacia atrás cuando aparecen justo antes del último
# término del nombre.
SURNAME_CONNECTORS = {
    "de", "del", "la", "las", "los", "van", "der", "von", "di", "do",
    "dos", "da", "das", "mac", "mc", "bin", "ibn", "al",
}

# Separadores que unen varios autores dentro de un mismo campo "autor"
# (p. ej. "Juan Pérez y María López", "A. Gómez, B. Ruiz & C. Solís").
_AUTHOR_LIST_SEP_RE = re.compile(r"\s*(?:;|&)\s*")
_AUTHOR_Y_AND_RE = re.compile(r"\s+(?:y|and)\s+(?=[A-ZÀ-ÖØ-Þ])")


def _looks_like_person_name(parts: list) -> bool:
    """Heurística: ¿esta lista de palabras parece nombre de una persona?"""
    if not (2 <= len(parts) <= MAX_PERSON_NAME_WORDS):
        return False
    for part in parts:
        if not NAME_PART_RE.match(part):
            return False
        if part.isupper() and len(part) > 1:
            return False
        if part.lower() in _LIST_CONJUNCTIONS:
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
    # Fuerza cuántas palabras finales de CADA autor forman el apellido
    # (p. ej. 2 para apellidos dobles en español sin partícula, como
    # "Rojas Artavia"). None = detección automática (solo por partícula).
    author_surname_words: Optional[int] = None


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


def _extract_surname(parts: list, surname_words: Optional[int] = None):
    """Separa `parts` (nombre completo ya dividido en palabras) en
    (apellido, nombres_de_pila).

    Si `surname_words` se indica, se usan siempre esas últimas N palabras
    como apellido (para apellidos compuestos sin partícula conectora, como
    los dos apellidos en español: "Rojas Artavia"). Si no se indica, se
    detecta automáticamente extendiendo el apellido hacia atrás mientras la
    palabra anterior sea una partícula conocida (ver SURNAME_CONNECTORS),
    p. ej. "de la Cruz".
    """
    if surname_words and surname_words > 0:
        n = max(1, min(surname_words, len(parts) - 1))
        return " ".join(parts[-n:]), parts[:-n]

    end = len(parts) - 1
    start = end
    while start > 0 and parts[start - 1].lower().rstrip(".") in SURNAME_CONNECTORS:
        start -= 1
    return " ".join(parts[start:]), parts[:start]


def format_author(author: Optional[str], surname_words: Optional[int] = None) -> Optional[str]:
    """Normaliza el autor a 'Apellido, N. N.' salvo que parezca organización.

    `surname_words`, si se indica, fuerza cuántas palabras finales del
    nombre forman el apellido (útil para apellidos compuestos sin
    partícula, como los apellidos dobles en español).
    """
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

    last_name, first_names = _extract_surname(parts, surname_words)
    if not first_names:
        return trimmed_author
    initials = " ".join(n[0].upper() + "." for n in first_names if n)
    return f"{last_name}, {initials}"


def _split_authors(raw: str) -> list:
    """Separa un campo "autor" que puede contener varias personas.

    Reconoce separadores comunes: ";", "&", ", ", " y " / " and " (estas
    últimas dos solo cuando preceden a una palabra con mayúscula inicial,
    para no partir organizaciones como "Ciencia y Tecnología"). Si el
    resultado no parece una lista de nombres de persona válidos, se
    descarta la separación y se devuelve el texto original sin tocar
    (más seguro que arriesgarse a destrozar un nombre de organización).
    """
    if not raw:
        return []
    trimmed = raw.strip()
    if not trimmed:
        return []
    if ORG_MARKERS.search(trimmed):
        return [trimmed]

    normalized = _AUTHOR_LIST_SEP_RE.sub(", ", trimmed)
    normalized = _AUTHOR_Y_AND_RE.sub(", ", normalized)
    candidates = [p.strip() for p in normalized.split(",") if p.strip()]

    if len(candidates) < 2:
        return [trimmed]

    for candidate in candidates:
        candidate_parts = candidate.split()
        if not (ORG_MARKERS.search(candidate) or _looks_like_person_name(candidate_parts)):
            return [trimmed]

    return candidates


def format_authors_list(author: Optional[str], surname_words: Optional[int] = None) -> list:
    """Divide y formatea todos los autores de un campo "autor" a la vez."""
    names = _split_authors(author or "")
    return [a for a in (format_author(n, surname_words) for n in names) if a]


def join_authors_apa(formatted_authors: list) -> Optional[str]:
    """Une una lista de autores ya formateados con las reglas de lista de APA 7:
    2 autores van unidos con "&"; de 3 a 20, todos separados por comas con
    "&" antes del último; con 21 o más, los primeros 19, puntos suspensivos
    y el último (regla APA 7 para autoría muy numerosa)."""
    authors = [a for a in formatted_authors if a]
    if not authors:
        return None
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]}, & {authors[1]}"
    if len(authors) <= 20:
        return ", ".join(authors[:-1]) + f", & {authors[-1]}"
    return ", ".join(authors[:19]) + f", ... {authors[-1]}"


def in_text_authors_apa(formatted_authors: list) -> Optional[str]:
    """Arma la parte de autor de una cita en texto: apellido único, "A & B"
    para dos autores, o "A et al." desde tres autores en adelante (regla de
    APA 7ª edición, válida incluso en la primera cita)."""
    surnames = [a.split(",")[0] for a in formatted_authors if a]
    if not surnames:
        return None
    if len(surnames) == 1:
        return surnames[0]
    if len(surnames) == 2:
        return f"{surnames[0]} & {surnames[1]}"
    return f"{surnames[0]} et al."


def build_reference(meta: Metadata) -> str:
    """Arma la referencia APA 7 completa a partir de los metadatos."""
    parsed_date = parse_date(meta.published_date)
    date_str = format_date_apa(parsed_date)

    title = (meta.title or "Sin título").strip()
    if not re.search(r"[.?!]$", title):
        title += "."

    site_name = (meta.site_name or "").strip()
    formatted_authors = format_authors_list(meta.author, meta.author_surname_words)
    author = join_authors_apa(formatted_authors)

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
    """Arma la cita en texto: '(Apellido, Año)', '(A & B, Año)' o
    '(A et al., Año)' según el número de autores detectados."""
    parsed_date = parse_date(meta.published_date)
    year = parsed_date.year if parsed_date else "s.f."
    formatted_authors = format_authors_list(meta.author, meta.author_surname_words)
    author_intext = in_text_authors_apa(formatted_authors) or meta.site_name or "Autor desconocido"
    return f"({author_intext}, {year})"
