# apa7ref

Genera referencias bibliográficas en formato **APA 7** a partir de una o varias URLs. La herramienta descarga la página, extrae metadatos (autor, título, sitio, fecha de publicación) y construye la referencia siguiendo el formato de publicaciones web de APA 7.

```
Autor, A. A. (Año, Mes Día). Título de la página. Nombre del sitio. URL
```

## Instalación

```bash
git clone https://github.com/tu-usuario/apa7ref.git
cd apa7ref
pip install -e .
```

O solo las dependencias, sin instalar el paquete:

```bash
pip install -r requirements.txt
```

## Uso por línea de comandos

Una URL:

```bash
apa7ref https://www.ejemplo.com/articulo
```

Varias URLs:

```bash
apa7ref https://sitio1.com/a https://sitio2.com/b
```

Desde un archivo de texto (una URL por línea, líneas que empiezan con `#` se ignoran):

```bash
apa7ref --file urls.txt --output referencias.txt
```

Incluir también la cita en texto `(Autor, Año)`:

```bash
apa7ref https://www.ejemplo.com/articulo --in-text
```

Si no instalaste el paquete, puedes ejecutarlo como módulo:

```bash
python -m apa7ref.cli https://www.ejemplo.com/articulo
```

## Uso como librería

```python
from apa7ref import fetch_metadata, build_reference

meta = fetch_metadata("https://www.ejemplo.com/articulo")
print(build_reference(meta))
```

## Cómo funciona

1. **Extracción** (`apa7ref/extractor.py`): descarga el HTML con `requests` y usa `BeautifulSoup` para buscar metadatos comunes (`og:title`, `article:author`, `citation_author`, `article:published_time`, etc.), con respaldos como la etiqueta `<title>` o el primer `<h1>`.
2. **Formateo** (`apa7ref/formatter.py`): normaliza fecha y autor al estilo APA 7 (`Apellido, N. N.`), detecta si el autor parece ser una organización (para no reformatear nombres corporativos), y arma la cadena final. Si falta el autor, usa el nombre del sitio como autor corporativo; si falta la fecha, usa `(s.f.)`.
3. **CLI** (`apa7ref/cli.py`): interfaz de línea de comandos con soporte para múltiples URLs, lectura desde archivo y exportación a archivo de salida.

## Limitaciones

- La calidad de la referencia depende de los metadatos que el sitio web publique; páginas sin metadatos claros pueden requerir revisión manual.
- No resuelve JavaScript: sitios que renderizan contenido dinámicamente en el cliente pueden no exponer metadatos en el HTML inicial.
- La detección de "autor individual vs. organización" es heurística y puede fallar en casos ambiguos.

## Pruebas

```bash
pip install pytest
pytest tests/
```

## Licencia

MIT
