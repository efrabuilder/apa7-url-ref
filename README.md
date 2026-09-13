# apa7ref

Genera referencias bibliográficas en formato **APA 7** a partir de una o varias URLs, de archivos PDF locales (con o sin URL) o de datos escritos a mano. Extrae metadatos (autor, título, sitio, fecha de publicación) y construye la referencia siguiendo el formato de publicaciones web de APA 7, incluyendo listas de varios autores y apellidos compuestos.

```
Autor, A. A. (Año, Mes Día). Título de la página. Nombre del sitio. URL
Autor, A. A., & Autor, B. B. (Año). Título. Sitio. URL
Autor, A. A., Autor, B. B., & Autor, C. C. (Año). Título. Sitio. URL
```

Hay dos formas de usarlo: la **página web** (`index.html`, funciona directo en el navegador, sin instalar nada) y la **CLI/librería en Python** (`apa7ref/`).

## Página web (`index.html`)

Abre el archivo en el navegador. Tiene tres modos, elegibles con las pestañas de arriba:

- **Extractivo (local):** pega una o varias URLs (una por línea) y la página las descarga a través de un proxy público, lee sus metadatos y arma la referencia con reglas fijas, sin enviar nada a ningún servidor externo.
- **Con IA (tu clave):** igual que el anterior, pero en vez de reglas fijas, los metadatos (y un fragmento del contenido) se envían directo desde tu navegador a la API de Anthropic con tu propia clave, para resolver casos ambiguos (autores organizacionales, varios autores, apellidos compuestos, fechas incompletas). La clave nunca pasa por un servidor de apa7ref y se pierde al recargar la página.
- **Manual:** escribes los datos a mano (autor, fecha, título, sitio, URL opcional) y la página arma la referencia localmente, sin descargar nada. Útil para fuentes que los otros modos no logran leer (YouTube, contenido tras un muro de pago, sitios que bloquean el acceso automatizado).

Además, en los modos Extractivo y Con IA:

- **Archivos PDF sin enlace:** puedes añadir uno o varios PDF locales (tesis, capítulos, actas, etc.) junto a la lista de URLs. Se procesan leyendo su metadata interna (con pdf.js) y generan su referencia sin necesitar ninguna URL — la referencia final simplemente no lleva enlace.
- Si una URL de PDF falla al descargarse por el proxy, la tarjeta de error te deja subir ese mismo PDF directamente para generar la referencia sin depender de ningún proxy.
- **Palabras del apellido:** campo opcional (también disponible en Manual) para forzar cuántas palabras finales del nombre de cada autor forman el apellido — útil para apellidos dobles sin partícula, como los apellidos compuestos en español (p. ej. escribe `2` para que "Efraín Sebastián Rojas Artavia" se formatee como `Rojas Artavia, E. S.`). Ver "Autores y apellidos" más abajo para cuándo hace falta.

## Instalación (CLI / librería en Python)

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

Forzar apellidos dobles sin partícula (aplica a todos los autores de la ejecución):

```bash
apa7ref https://www.ejemplo.com/mi-tesis --surname-words 2
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

## Autores y apellidos

El formateo de autor sigue estas reglas, tanto en la CLI/librería (`apa7ref/formatter.py`) como en la página web (misma lógica, en JavaScript):

- **Organizaciones:** si el nombre trae marcadores de organización (`equipo`, `redacción`, `universidad`, `departamento`, etc.) se deja tal cual, sin reformatear.
- **Apellidos con partícula:** se detectan automáticamente — "María de la Cruz" → `de la Cruz, M.`; "Ludwig van der Berg" → `van der Berg, L.`.
- **Apellidos dobles sin partícula:** como no hay forma confiable de adivinar dónde empieza el apellido en un nombre como "Efraín Sebastián Rojas Artavia" (¿1, 2 o 3 palabras?), por defecto solo se toma la última palabra. Para que se tomen las últimas *N* palabras como apellido, usa `--surname-words N` en la CLI o el campo "Palabras del apellido" en la web (ej. `2` → `Rojas Artavia, E. S.`).
- **Varios autores en un mismo campo:** se separan automáticamente por `;`, `&`, `,` o " y " / " and " (estas dos últimas solo antes de una palabra con mayúscula inicial, para no partir organizaciones como "Ciencia y Tecnología") y se listan con las reglas de APA 7: 2 autores unidos con "&"; de 3 a 20, todos con "&" antes del último; 21 o más, los primeros 19 seguidos de puntos suspensivos y el último.
- **Cita en texto:** un autor → `(Apellido, Año)`; dos → `(Apellido1 & Apellido2, Año)`; tres o más → `(Apellido1 et al., Año)`, válido desde la primera cita (regla de la 7ª edición).
- El modo **Con IA** de la página web recibe instrucciones explícitas de respetar apellidos completos y estas mismas reglas, útil cuando la separación automática no da con el resultado correcto (por ejemplo, varios autores con apellido doble en el mismo campo).

## Cómo funciona

1. **Extracción** (`apa7ref/extractor.py`, o su equivalente en JavaScript dentro de `index.html`): descarga el HTML con `requests` (o `fetch` vía proxy en el navegador) y busca metadatos comunes (`og:title`, `article:author`, `citation_author`, `article:published_time`, etc.), con respaldos como la etiqueta `<title>`, el primer `<h1>` o microdatos schema.org. Para PDF, lee la metadata interna con `pdf.js` (en la web) — con o sin URL asociada.
2. **Formateo** (`apa7ref/formatter.py`): normaliza fecha y autor(es) al estilo APA 7, separa varios autores y aplica las reglas de lista/"et al." descritas arriba, detecta apellidos con partícula, y detecta si el autor parece ser una organización (para no reformatear nombres corporativos). Si falta el autor, usa el nombre del sitio como autor corporativo; si falta la fecha, usa `(s.f.)`; si no hay URL (archivo local), la referencia simplemente no la incluye.
3. **CLI** (`apa7ref/cli.py`): interfaz de línea de comandos con soporte para múltiples URLs, lectura desde archivo, exportación a archivo de salida y ajuste de apellidos compuestos.

## Limitaciones

- La calidad de la referencia depende de los metadatos que el sitio web publique; páginas sin metadatos claros pueden requerir revisión manual.
- No resuelve JavaScript: sitios que renderizan contenido dinámicamente en el cliente pueden no exponer metadatos en el HTML inicial.
- La detección de "autor individual vs. organización" es heurística y puede fallar en casos ambiguos.
- La separación de varios autores y la detección de apellidos compuestos son heurísticas basadas en patrones comunes; en campos de autor poco convencionales (o con varios autores de apellido doble mezclados) puede hacer falta el modo Con IA o corregir la referencia a mano.
- La CLI no lee PDF locales sin URL (esa función solo está en la página web, `index.html`, con `pdf.js`).

## Pruebas

```bash
pip install pytest
pytest tests/
```

## Licencia

MIT
