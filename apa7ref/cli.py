"""Interfaz de línea de comandos: apa7ref <url> [<url> ...]"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, TextIO

from .extractor import FetchError, fetch_metadata
from .formatter import build_in_text_citation, build_reference


def _read_urls_from_file(path: str) -> List[str]:
    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apa7ref",
        description="Genera referencias bibliográficas en formato APA 7 a partir de URLs.",
    )
    parser.add_argument(
        "urls", nargs="*", default=[],
        help="Una o varias URLs a procesar.",
    )
    parser.add_argument(
        "--file", metavar="ARCHIVO",
        help="Archivo de texto con una URL por línea (líneas que empiezan con # se ignoran).",
    )
    parser.add_argument(
        "--output", metavar="ARCHIVO",
        help="Archivo de salida donde escribir las referencias generadas. "
             "Si se omite, se imprimen en pantalla.",
    )
    parser.add_argument(
        "--in-text", action="store_true",
        help="Incluir también la cita en texto (Autor, Año) junto a cada referencia.",
    )
    return parser


def _process(url: str, include_in_text: bool) -> str:
    try:
        meta = fetch_metadata(url)
    except FetchError as exc:
        return f"[ERROR] {url}: {exc}"

    reference = build_reference(meta)
    if include_in_text:
        return f"{reference}  {build_in_text_citation(meta)}"
    return reference


def run(argv: Optional[List[str]] = None, stdout: TextIO = sys.stdout) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    urls: List[str] = list(args.urls)
    if args.file:
        urls.extend(_read_urls_from_file(args.file))

    if not urls:
        parser.print_help(stdout)
        return 1

    lines = [_process(url, args.in_text) for url in urls]
    output_text = "\n\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output_text + "\n")
    else:
        print(output_text, file=stdout)

    had_errors = any(line.startswith("[ERROR]") for line in lines)
    return 1 if had_errors else 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
