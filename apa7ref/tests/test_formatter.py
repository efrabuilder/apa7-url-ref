from apa7ref.formatter import (
    Metadata,
    build_in_text_citation,
    build_reference,
    format_author,
)


def test_format_author_persona():
    """Una persona con nombre y apellido se formatea 'Apellido, N.'."""
    assert format_author("Jane Doe") == "Doe, J."


def test_format_author_organizacion():
    """Un nombre con marcador de organización no se reformatea."""
    author = format_author("Reuters News Team")
    assert author == "Reuters News Team"


def test_format_author_canal_no_se_destroza():
    """Un nombre de canal de varias palabras (no persona) se deja tal cual."""
    author = format_author("Curiosidades India Play MX Emocionantes")
    assert author == "Curiosidades India Play MX Emocionantes"


def test_format_author_sigla_mayuscula_no_se_destroza():
    """Una palabra en mayúsculas sostenidas (sigla) no parece nombre de persona."""
    author = format_author("Rubius SUIKA GAME")
    assert author == "Rubius SUIKA GAME"


def test_build_reference_con_fecha_completa():
    """Con fecha completa, la referencia incluye año, mes y día en español."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Un título de prueba",
        author="Jane Doe",
        site_name="Ejemplo",
        published_date="2024-03-15",
    )
    reference = build_reference(meta)
    assert reference == (
        "Doe, J. (2024, marzo 15). Un título de prueba. "
        "Ejemplo. https://ejemplo.com/articulo"
    )


def test_build_reference_sin_fecha_usa_sf():
    """Sin fecha detectable, la referencia usa '(s.f.)'."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Sin fecha",
        author="Jane Doe",
        site_name="Ejemplo",
        published_date=None,
    )
    reference = build_reference(meta)
    assert "(s.f.)" in reference


def test_build_reference_sin_autor_usa_sitio():
    """Sin autor, el nombre del sitio actúa como autor corporativo."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Un artículo sin autor",
        author=None,
        site_name="Ejemplo",
        published_date="2023",
    )
    reference = build_reference(meta)
    assert reference.startswith("Ejemplo. (2023).")


def test_build_in_text_citation():
    """La cita en texto usa el apellido (o el sitio) y el año."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Un título",
        author="Jane Doe",
        site_name="Ejemplo",
        published_date="2024-03-15",
    )
    assert build_in_text_citation(meta) == "(Doe, 2024)"
