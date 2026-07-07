const STORAGE_KEY = "dni_admin_key";
const el = (id) => document.getElementById(id);
const adminKeyInput = el("adminKey");
const saveBtn = el("saveAdminKey");
const clearBtn = el("clearAdminKey");
const refreshStatusBtn = el("refreshStatusBtn");
const refreshBtn = el("refreshBtn");
const createForm = el("createForm");
const tokensBody = el("tokensBody");
const statusBox = el("statusBox");
const createMessage = el("createMessage");
const adminHint = el("adminHint");
const tokenDialog = el("tokenDialog");
const tokenDialogText = el("tokenDialogText");
const tokenDialogCopy = el("tokenDialogCopy");
const tokenDialogClose = el("tokenDialogClose");

function getAdminKey() {
  return (localStorage.getItem(STORAGE_KEY) || adminKeyInput.value || "").trim();
}

function syncHint(message, error = false) {
  adminHint.textContent = message;
  adminHint.style.color = error ? "#b91c1c" : "";
}

function setStatus(message, error = false) {
  statusBox.textContent = message;
  statusBox.style.color = error ? "#b91c1c" : "";
}

function setCreateMessage(message, error = false) {
  createMessage.textContent = message;
  createMessage.style.color = error ? "#b91c1c" : "";
}

function authHeaders() {
  const adminKey = getAdminKey();
  if (!adminKey) throw new Error("Ingresa una X-Admin-Key.");
  return {
    "X-Admin-Key": adminKey,
    "Content-Type": "application/json",
  };
}

async function apiFetch(url, options = {}) {
  const headers = { ...(options.headers || {}), ...authHeaders() };
  const response = await fetch(url, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Error HTTP ${response.status}`);
  return data;
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "-";
}

function pill(active) {
  return active ? '<span class="pill ok">Activo</span>' : '<span class="pill off">Inactivo</span>';
}

function row(token) {
  return `<tr>
    <td>${token.id}</td>
    <td>${token.nombre || ""}</td>
    <td>${pill(token.activo)}</td>
    <td>${token.consultas_realizadas ?? 0}</td>
    <td>${token.limite_diario ?? "-"}</td>
    <td>${token.limite_por_minuto ?? "-"}</td>
    <td>${formatDate(token.ultimo_uso)}</td>
    <td>
      <div class="actions">
        <button type="button" data-action="${token.activo ? "deactivate" : "activate"}" data-id="${token.id}">${token.activo ? "Desactivar" : "Activar"}</button>
        <button type="button" class="secondary" data-action="delete" data-id="${token.id}">Eliminar</button>
      </div>
    </td>
  </tr>`;
}

async function loadStatus() {
  const data = await apiFetch("/admin/status", { method: "GET" });
  setStatus(JSON.stringify(data, null, 2));
}

async function loadTokens() {
  const tokens = await apiFetch("/admin/api-keys", { method: "GET" });
  tokensBody.innerHTML = tokens.length ? tokens.map(row).join("") : '<tr><td colspan="8">Sin API keys</td></tr>';
}

async function runAction(action, id) {
  const map = {
    activate: { url: `/admin/api-keys/${id}/activate`, method: "PATCH" },
    deactivate: { url: `/admin/api-keys/${id}/deactivate`, method: "PATCH" },
    delete: { url: `/admin/api-keys/${id}`, method: "DELETE" },
  };
  const item = map[action];
  if (!item) return;
  if (action === "delete" && !confirm("¿Eliminar esta API Key?")) return;
  await apiFetch(item.url, { method: item.method });
  await loadTokens();
  await loadStatus();
}

function loadSavedKey() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) adminKeyInput.value = saved;
  syncHint(saved ? "X-Admin-Key cargada desde almacenamiento local." : "La clave solo se usa en este navegador para llamar a /admin.");
}

saveBtn.addEventListener("click", () => {
  const value = adminKeyInput.value.trim();
  if (!value) {
    localStorage.removeItem(STORAGE_KEY);
    syncHint("No hay clave para guardar.", true);
    return;
  }
  localStorage.setItem(STORAGE_KEY, value);
  syncHint("X-Admin-Key guardada localmente.");
  loadStatus().catch((error) => setStatus(error.message, true));
});

clearBtn.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  adminKeyInput.value = "";
  syncHint("Clave eliminada del navegador.");
});

refreshStatusBtn.addEventListener("click", () => loadStatus().catch((error) => setStatus(error.message, true)));
refreshBtn.addEventListener("click", () => loadTokens().catch((error) => setStatus(error.message, true)));

tokensBody.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  try {
    await runAction(button.dataset.action, button.dataset.id);
  } catch (error) {
    setStatus(error.message, true);
  }
});

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = {
      nombre: el("nombre").value.trim(),
      descripcion: el("descripcion").value.trim(),
      limite_diario: el("dailyLimit").value ? Number(el("dailyLimit").value) : null,
      limite_por_minuto: el("minuteLimit").value ? Number(el("minuteLimit").value) : null,
    };
    const token = await apiFetch("/admin/api-keys", { method: "POST", body: JSON.stringify(payload) });
    tokenDialogText.textContent = token.api_key || "";
    tokenDialog.showModal();
    setCreateMessage("API Key generada correctamente.");
    await loadTokens();
    await loadStatus();
  } catch (error) {
    setCreateMessage(error.message, true);
  }
});

tokenDialogClose.addEventListener("click", () => tokenDialog.close());
tokenDialog.addEventListener("click", (event) => {
  if (event.target === tokenDialog) tokenDialog.close();
});
tokenDialogCopy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(tokenDialogText.textContent || "");
    setCreateMessage("API Key copiada.");
  } catch {
    setCreateMessage("No se pudo copiar la API Key.", true);
  }
});

loadSavedKey();
loadStatus().catch((error) => setStatus(error.message, true));
loadTokens().catch((error) => setStatus(error.message, true));
