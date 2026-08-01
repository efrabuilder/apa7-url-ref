"""Descarga una URL y extrae metadatos comunes de autor, título, sitio y fecha.

Misma lógica que la versión JavaScript usada en index.html, incluyendo el
respaldo por microdatos schema.org (itemprop) para sitios que no publican
etiquetas <meta name=""> / <meta property=""> estándar (p. ej. YouTube).
"""

from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .formatter import Metadata

USER_AGENT = (
    "Mozilla/5.0 (compatible; apa7ref/0.1.0; "
    "+https://github.com/efrabuilder/apa7-url-ref)"
)

META_AUTHOR = [
    "author", "article:author", "og:author", "twitter:creator",
    "citation_author", "dc.creator", "parsely-author",
]
META_TITLE = ["og:title", "twitter:title", "citation_title"]
META_SITE = ["og:site_name", "application-name"]
META_DATE = [
    "article:published_time", "og:published_time",
    "citation_publication_date", "citation_date", "dc.date", "date",
    "publish-date", "parsely-pub-date",
]

# Respaldo para sitios que usan microdatos schema.org en vez de <meta>.
ITEMPROP_AUTHOR = ["author", "name"]
ITEMPROP_DATE = ["datePublished", "uploadDate"]


class FetchError(Exception):
    """Error al descargar o interpretar una URL."""


def _get_meta(soup: BeautifulSoup, names: List[str]) -> Optional[str]:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag:
            content = (tag.get("content") or "").strip()
            if content:
                return content
    return None


def _get_itemprop(soup: BeautifulSoup, names: List[str]) -> Optional[str]:
    for name in names:
        tag = soup.find(attrs={"itemprop": name})
        if tag:
            content = (tag.get("content") or tag.get_text() or "").strip()
            if content:
                return content
    return None


def _extract_author(soup: BeautifulSoup) -> Optional[str]:
    author = _get_meta(soup, META_AUTHOR)
    if author:
        if author.lower().startswith("http://") or author.lower().startswith("https://"):
            return None
        return author

    item_author = _get_itemprop(soup, ITEMPROP_AUTHOR)
    if item_author and not item_author.lower().startswith(("http://", "https://")):
        return item_author

    tag = soup.find(attrs={"rel": "author"}) or soup.find(class_=lambda c: c and "author" in c.lower())
    if tag and tag.get_text(strip=True):
        return tag.get_text(strip=True)
    return None


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    title = _get_meta(soup, META_TITLE)
    if title:
        return title
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    return None


def _extract_site_name(soup: BeautifulSoup, url: str) -> Optional[str]:
    site = _get_meta(soup, META_SITE)
    if site:
        return site
    hostname = urlparse(url).hostname
    if hostname:
        return hostname[4:] if hostname.startswith("www.") else hostname
    return None


def _extract_published_date(soup: BeautifulSoup) -> Optional[str]:
    date = _get_meta(soup, META_DATE)
    if date:
        return date
    return _get_itemprop(soup, ITEMPROP_DATE)


def _extract_excerpt(soup: BeautifulSoup, limit: int = 3000) -> str:
    if not soup.body:
        return ""
    text = " ".join(soup.body.get_text(separator=" ").split())
    return text[:limit]


def fetch_metadata(url: str, timeout: float = 15.0) -> Metadata:
    """Descarga `url` y devuelve sus metadatos como un `Metadata`.

    Lanza `FetchError` si la URL no se puede descargar o no parece HTML.
    """
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FetchError(f"no se pudo descargar la URL: {exc}") from exc

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type and not response.text.strip().startswith("<"):
        raise FetchError("la respuesta no parece HTML (usa un lector de PDF para archivos .pdf)")

    soup = BeautifulSoup(response.text, "html.parser")

    return Metadata(
        url=url,
        title=_extract_title(soup),
        author=_extract_author(soup),
        site_name=_extract_site_name(soup, url),
        published_date=_extract_published_date(soup),
        excerpt=_extract_excerpt(soup),
    )
