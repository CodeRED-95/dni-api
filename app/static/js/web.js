const dniForm = document.getElementById("dniForm");
const dniInput = document.getElementById("dni");
const apiKeyInput = document.getElementById("apiKey");
const submitBtn = document.getElementById("submitBtn");
const refreshBtn = document.getElementById("refreshBtn");
const copyCurlBtn = document.getElementById("copyCurlBtn");
const copyCurlSmallBtn = document.getElementById("copyCurlSmallBtn");
const requestState = document.getElementById("requestState");
const resultMeta = document.getElementById("resultMeta");
const resultBox = document.getElementById("resultBox");
const formHint = document.getElementById("formHint");
const curlPreview = document.getElementById("curlPreview");

function setState(text, tone = "idle") {
  requestState.textContent = text;
  requestState.className = tone === "error" ? "status-pill status-pill--error" : tone === "ok" ? "status-pill status-pill--accent" : "status-pill";
}

function renderCurl(dni, apiKey) {
  curlPreview.textContent = `curl -H "X-API-Key: ${apiKey || "TU_API_KEY"}" http://127.0.0.1:8000/dni/${dni || "12345678"}`;
}

function renderMeta(data) {
  const items = [
    ["DNI", data.dni],
    ["Nombres", data.nombres],
    ["Apellido paterno", data.apellido_paterno || "-"],
    ["Apellido materno", data.apellido_materno || "-"],
    ["Nombre completo", data.nombre_completo || "-"],
    ["Género", data.genero || "-"],
    ["Nacimiento", data.fecha_nacimiento || "-"],
    ["Verificación", data.codigo_verificacion || "-"],
  ];
  resultMeta.innerHTML = items.map(([label, value]) => `<div class="result-item"><span>${label}</span><strong>${value ?? "-"}</strong></div>`).join("");
}

function validate(dni, apiKey) {
  if (!/^\d{8}$/.test(dni)) return "El DNI debe tener exactamente 8 dígitos.";
  if (!apiKey) return "Debes ingresar una API Key.";
  return "";
}

async function queryDni(forceRefresh = false) {
  const dni = dniInput.value.trim();
  const apiKey = apiKeyInput.value.trim();
  renderCurl(dni, apiKey);
  const error = validate(dni, apiKey);
  if (error) {
    setState("Error", "error");
    resultMeta.innerHTML = "";
    resultBox.textContent = error;
    formHint.textContent = error;
    return;
  }

  submitBtn.disabled = true;
  setState(forceRefresh ? "Actualizando..." : "Consultando...", "idle");
  resultBox.textContent = "Consultando la API...";

  try {
    const response = await fetch(forceRefresh ? `/dni/${encodeURIComponent(dni)}/refresh` : `/dni/${encodeURIComponent(dni)}?apikey=${encodeURIComponent(apiKey)}`, {
      headers: forceRefresh ? { "X-API-Key": apiKey, Accept: "application/json" } : { Accept: "application/json" },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = data.detail || `Error HTTP ${response.status}`;
      setState("Error", "error");
      resultMeta.innerHTML = "";
      resultBox.textContent = message;
      formHint.textContent = message;
      return;
    }

    setState("OK", "ok");
    renderMeta(data);
    resultBox.textContent = JSON.stringify(data, null, 2);
    formHint.textContent = "Consulta completada correctamente.";
  } catch {
    setState("Error", "error");
    resultBox.textContent = "No se pudo conectar con la API.";
    formHint.textContent = "Revisa la conexión o la disponibilidad del servidor.";
  } finally {
    submitBtn.disabled = false;
  }
}

dniForm.addEventListener("submit", (event) => {
  event.preventDefault();
  queryDni(false);
});

refreshBtn?.addEventListener("click", () => queryDni(true));
const copyCurl = async () => {
  try {
    await navigator.clipboard.writeText(curlPreview.textContent || "");
    formHint.textContent = "Comando curl copiado.";
  } catch {
    formHint.textContent = "No se pudo copiar el comando curl.";
  }
};
copyCurlBtn?.addEventListener("click", copyCurl);
copyCurlSmallBtn?.addEventListener("click", copyCurl);

renderCurl("12345678", "TU_API_KEY");
