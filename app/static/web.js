const form = document.getElementById("dniForm");
const dniInput = document.getElementById("dni");
const apiKeyInput = document.getElementById("apiKey");
const submitBtn = document.getElementById("submitBtn");
const requestState = document.getElementById("requestState");
const resultTitle = document.getElementById("resultTitle");
const resultMeta = document.getElementById("resultMeta");
const resultBox = document.getElementById("resultBox");
const formHint = document.getElementById("formHint");

function setState(text, tone = "idle") {
  requestState.textContent = text;
  requestState.className = tone === "error" ? "pill status-bad" : tone === "ok" ? "pill status-ok" : "pill";
}

function renderMeta(data) {
  const items = [
    ["DNI", data.dni],
    ["Nombres", data.nombres],
    ["Apellido paterno", data.apellido_paterno || "-"],
    ["Apellido materno", data.apellido_materno || "-"],
    ["Nombre completo", data.nombre_completo || "-"],
    ["Fuente", data.fuente || "-"],
    ["Género", data.genero || "-"],
    ["Nacimiento", data.fecha_nacimiento || "-"],
    ["Verificación", data.codigo_verificacion || "-"],
  ];
  resultMeta.innerHTML = items
    .map(([label, value]) => `<div class="meta-item"><span>${label}</span><strong>${value ?? "-"}</strong></div>`)
    .join("");
}

function validate(dni, apiKey) {
  if (!/^\d{8}$/.test(dni)) return "El DNI debe tener exactamente 8 dígitos.";
  if (!apiKey) return "Debes ingresar una API Key.";
  return "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const dni = dniInput.value.trim();
  const apiKey = apiKeyInput.value.trim();
  const error = validate(dni, apiKey);

  if (error) {
    setState("Error", "error");
    resultTitle.textContent = "Consulta inválida";
    resultMeta.innerHTML = "";
    resultBox.textContent = error;
    formHint.textContent = error;
    return;
  }

  submitBtn.disabled = true;
  setState("Consultando...");
  resultTitle.textContent = `Buscando ${dni}`;
  resultBox.textContent = "Consultando la API...";
  resultMeta.innerHTML = "";

  try {
    const response = await fetch(`/dni/${encodeURIComponent(dni)}?apikey=${encodeURIComponent(apiKey)}`, {
      headers: { Accept: "application/json" },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message = data.detail || `Error HTTP ${response.status}`;
      setState("Error", "error");
      resultTitle.textContent = "No se pudo completar la consulta";
      resultBox.textContent = message;
      formHint.textContent = message;
      return;
    }

    setState("OK", "ok");
    resultTitle.textContent = data.nombre_completo || `DNI ${dni}`;
    renderMeta(data);
    resultBox.textContent = JSON.stringify(data, null, 2);
    formHint.textContent = `Consulta completada correctamente. Origen: ${data.fuente || "desconocido"}.`;
  } catch {
    setState("Error", "error");
    resultTitle.textContent = "Error de conexión";
    resultBox.textContent = "No se pudo conectar con la API.";
    formHint.textContent = "Revisa tu conexión o la disponibilidad del servidor.";
  } finally {
    submitBtn.disabled = false;
  }
});
