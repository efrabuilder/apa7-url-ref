from apa7ref.formatter import (
    Metadata,
    build_in_text_citation,
    build_reference,
    format_author,
    format_authors_list,
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


def test_format_author_apellido_compuesto_con_particula():
    """Apellidos con partícula (de, la, van, von...) se detectan solos,
    sin necesidad de indicar surname_words."""
    assert format_author("María de la Cruz") == "de la Cruz, M."
    assert format_author("Ludwig van der Berg") == "van der Berg, L."


def test_format_author_apellido_compuesto_sin_particula_requiere_override():
    """Sin partícula, un apellido doble (p. ej. en español) no se detecta
    automáticamente..."""
    assert format_author("Efraín Sebastián Rojas Artavia") == "Artavia, E. S. R."
    # ...pero surname_words permite indicarlo explícitamente.
    assert (
        format_author("Efraín Sebastián Rojas Artavia", surname_words=2)
        == "Rojas Artavia, E. S."
    )


def test_format_authors_list_varios_autores():
    """Un campo de autor con varias personas se separa en autores
    individuales, cada uno formateado 'Apellido, N.'."""
    authors = format_authors_list("Juan Pérez y María López")
    assert authors == ["Pérez, J.", "López, M."]


def test_format_authors_list_no_destroza_organizacion_con_y():
    """Una organización que contiene ' y ' (p. ej. 'Ciencia y Tecnología')
    no se parte en dos autores porque las partes resultantes no parecen
    nombres de persona válidos."""
    authors = format_authors_list("Ciencia y Tecnología")
    assert authors == ["Ciencia y Tecnología"]


def test_build_reference_dos_autores_usa_ampersand():
    """Con dos autores, la referencia los une con '&' antes del último."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Un estudio",
        author="Juan Pérez y María López",
        site_name="Ejemplo",
        published_date="2024",
    )
    reference = build_reference(meta)
    assert reference.startswith("Pérez, J., & López, M. (2024).")


def test_build_in_text_citation_tres_autores_usa_et_al():
    """Con tres autores o más, la cita en texto usa 'et al.' (regla de
    APA 7, aplicable incluso en la primera cita)."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Un estudio",
        author="Ana Gómez, Luis Ruiz y Carla Solís",
        site_name="Ejemplo",
        published_date="2024",
    )
    assert build_in_text_citation(meta) == "(Gómez et al., 2024)"


def test_build_in_text_citation_dos_autores_usa_ampersand():
    """Con dos autores, la cita en texto los une con '&'."""
    meta = Metadata(
        url="https://ejemplo.com/articulo",
        title="Un estudio",
        author="Juan Pérez y María López",
        site_name="Ejemplo",
        published_date="2024",
    )
    assert build_in_text_citation(meta) == "(Pérez & López, 2024)"
