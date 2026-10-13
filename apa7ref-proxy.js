/**
 * apa7ref-proxy — Cloudflare Worker
 *
 * Reenvía una URL de destino y agrega los headers CORS necesarios para
 * que apa7ref pueda leerla desde el navegador. Es tu propio proxy: no
 * depende de allorigins.win / codetabs.com / corsproxy.io, así que no
 * comparte límites de uso con miles de otros usuarios.
 *
 * USO:
 *   https://<tu-worker>.workers.dev?url=https://ejemplo.com/pagina
 *
 * DESPLIEGUE (gratis, ~5 minutos):
 *   1. Entra a https://dash.cloudflare.com y crea una cuenta si no
 *      tienes una (el plan gratuito incluye Workers).
 *   2. Ve a "Workers & Pages" -> "Create" -> "Create Worker".
 *   3. Ponle un nombre, ej: apa7ref-proxy. Anota la URL que te asigna,
 *      algo como https://apa7ref-proxy.tu-usuario.workers.dev
 *   4. Haz clic en "Edit code" y pega TODO el contenido de este
 *      archivo, reemplazando lo que venga por defecto.
 *   5. Clic en "Deploy".
 *   6. Copia la URL del Worker y pégala en index.html, en la
 *      constante OWN_WORKER_URL (busca esa línea cerca de
 *      "proxyBuilders").
 *
 * LÍMITES DEL PLAN GRATUITO: 100,000 solicitudes/día, más que
 * suficiente para uso personal.
 *
 * NOTA: esto NO resuelve bloqueos que el sitio de destino aplique por
 * su cuenta (ej. YouTube puede seguir rechazando tráfico de
 * datacenter). Lo que sí resuelve es dejar de depender de la
 * disponibilidad y los límites de proxies públicos compartidos.
 */

const ALLOWED_ORIGINS = [
  "https://efrabuilder.github.io",
  "http://localhost:8000",
  "http://127.0.0.1:8000"
]; // agrega aquí otros orígenes desde los que uses la app

export default {
  async fetch(request) {
    const origin = request.headers.get("Origin") || "";
    const cors = corsHeaders(origin);
    const requestUrl = new URL(request.url);
    const target = requestUrl.searchParams.get("url");

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors });
    }

    if (!target) {
      return jsonResponse({ error: "Falta el parámetro ?url=" }, 400, cors);
    }

    let targetUrl;
    try {
      targetUrl = new URL(target);
    } catch (e) {
      return jsonResponse({ error: "URL inválida." }, 400, cors);
    }

    if (targetUrl.protocol !== "http:" && targetUrl.protocol !== "https:") {
      return jsonResponse({ error: "Solo se permiten URLs http/https." }, 400, cors);
    }

    try {
      const upstream = await fetch(targetUrl.toString(), {
        method: "GET",
        headers: {
          // Un user-agent de navegador normal ayuda a que algunos
          // sitios no rechacen la solicitud de entrada por parecer
          // tráfico de bot genérico.
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
          "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8"
        },
        redirect: "follow"
      });

      const contentType = upstream.headers.get("content-type") || "application/octet-stream";
      const body = await upstream.arrayBuffer();

      return new Response(body, {
        status: upstream.status,
        headers: {
          ...cors,
          "Content-Type": contentType
        }
      });
    } catch (err) {
      return jsonResponse({ error: "No se pudo descargar la URL de destino: " + err.message }, 502, cors);
    }
  }
};

/**
 * Solo refleja el origen si está en la lista permitida.
 * @param {string} origin
 * @returns {Record<string, string>}
 */
function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin"
  };
}

/**
 * @param {object} obj
 * @param {number} status
 * @param {Record<string, string>} cors
 * @returns {Response}
 */
function jsonResponse(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { ...cors, "Content-Type": "application/json" }
  });
}
