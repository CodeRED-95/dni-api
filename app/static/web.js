const form = document.getElementById("ruc-form");
const output = document.getElementById("output");
const statusEl = document.getElementById("status");
const httpStatusEl = document.getElementById("httpStatus");

function render(value) {
  output.textContent = JSON.stringify(value, null, 2);
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#fb7185" : "";
}

function setHttpStatus(value) {
  httpStatusEl.textContent = value;
}

function validateForm(dni, apiKey) {
  if (!dni) return "El DNI es obligatorio.";
  if (!/^\d{8}$/.test(dni)) return "El DNI debe tener 8 dígitos numéricos.";
  if (!apiKey) return "La API Key es obligatoria.";
  return "";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const apiKey = document.getElementById("apiKey").value.trim();
  const dni = document.getElementById("dni").value.trim();
  const error = validateForm(dni, apiKey);

  if (error) {
    setHttpStatus("-");
    setStatus(error, true);
    render({ detail: error });
    return;
  }

  setStatus("Consultando...");
  setHttpStatus("...");

  try {
    const url = `/dni/${encodeURIComponent(dni)}?apikey=${encodeURIComponent(apiKey)}`;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    let data;
    try {
      data = await response.json();
    } catch {
      data = {};
    }

    setHttpStatus(String(response.status));

    if (!response.ok) {
      setStatus(data.detail || `Error ${response.status}`, true);
      render(data);
      return;
    }

    setStatus("Consulta exitosa");
    render(data);
  } catch (error) {
    setHttpStatus("ERR");
    setStatus("Error de red o servidor", true);
    render({ error: String(error) });
  }
});
