const STORAGE_KEY = "dni_admin_key";
const el = (id) => document.getElementById(id);
const adminKeyInput = el("adminKey");
const saveBtn = el("saveAdminKey");
const clearBtn = el("clearAdminKey");
const clearAdminBtn = el("clearAdminBtn");
const refreshBtn = el("refreshBtn");
const newTokenBtn = el("newTokenBtn");
const newTokenBtn2 = el("newTokenBtn2");
const tokensBody = el("tokensBody");
const statusBox = el("statusBox");
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
  adminHint.style.color = error ? "#ffb4ab" : "";
}

function authHeaders(extra = {}) {
  const adminKey = getAdminKey();
  if (!adminKey) throw new Error("Ingresa una X-Admin-Key.");
  return { "X-Admin-Key": adminKey, "Content-Type": "application/json", ...extra };
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, { ...options, headers: authHeaders(options.headers || {}) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Error HTTP ${response.status}`);
  return data;
}

function setStatus(message, error = false) {
  statusBox.textContent = message;
  statusBox.style.color = error ? "#ffb4ab" : "";
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "-";
}

function row(token) {
  const preview = token.api_key_preview || token.preview || "—";
  return `<tr>
    <td><div class="flex-col"><strong>${token.nombre || ""}</strong><span class="muted">${formatDate(token.fecha_creacion)}</span></div></td>
    <td><code class="token-preview">${preview}</code></td>
    <td>${token.activo ? '<span class="pill ok">ACTIVE</span>' : '<span class="pill off">REVOKED</span>'}</td>
    <td>
      <div class="actions">
        <button type="button" data-action="copy" data-token="${preview}" data-preview="${preview}">Copiar</button>
        <button type="button" data-action="${token.activo ? "deactivate" : "activate"}" data-id="${token.id}">${token.activo ? "Desactivar" : "Activar"}</button>
        <button type="button" data-action="delete" data-id="${token.id}">Eliminar</button>
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
  tokensBody.innerHTML = tokens.length ? tokens.map(row).join("") : '<tr><td colspan="4">Sin tokens</td></tr>';
}

async function createToken() {
  const payload = {
    nombre: prompt("Nombre del token") || "",
    descripcion: "",
    limite_diario: null,
    limite_por_minuto: null,
  };
  if (!payload.nombre.trim()) return;
  const token = await apiFetch("/admin/api-keys", { method: "POST", body: JSON.stringify(payload) });
  tokenDialogText.textContent = token.api_key || "";
  tokenDialog.showModal();
  await loadTokens();
  await loadStatus();
}

async function runAction(action, id, tokenValue) {
  const map = {
    activate: { url: `/admin/api-keys/${id}/activate`, method: "PATCH" },
    deactivate: { url: `/admin/api-keys/${id}/deactivate`, method: "PATCH" },
    delete: { url: `/admin/api-keys/${id}`, method: "DELETE" },
  };
  if (action === "copy") {
    const text = tokenValue || "";
    if (!text) throw new Error("El backend no expuso el token completo.");
    await navigator.clipboard.writeText(text);
    setStatus("Token copiado.");
    return;
  }
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
  if (!value) return;
  localStorage.setItem(STORAGE_KEY, value);
  syncHint("X-Admin-Key guardada localmente.");
  loadTokens().catch((error) => setStatus(error.message, true));
});

clearBtn.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  adminKeyInput.value = "";
  syncHint("Clave eliminada del navegador.");
});

clearAdminBtn?.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  adminKeyInput.value = "";
  syncHint("Sesión administrativa cerrada.");
});

refreshBtn?.addEventListener("click", () => loadTokens().catch((error) => setStatus(error.message, true)));
newTokenBtn?.addEventListener("click", () => createToken().catch((error) => setStatus(error.message, true)));
newTokenBtn2?.addEventListener("click", () => createToken().catch((error) => setStatus(error.message, true)));

tokensBody.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  try {
    await runAction(button.dataset.action, button.dataset.id, button.dataset.token);
  } catch (error) {
    setStatus(error.message, true);
  }
});

tokenDialogClose.addEventListener("click", () => tokenDialog.close());
tokenDialog.addEventListener("click", (event) => {
  if (event.target === tokenDialog) tokenDialog.close();
});
tokenDialogCopy.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(tokenDialogText.textContent || "");
    setStatus("Token copiado.");
  } catch {
    setStatus("No se pudo copiar el token.", true);
  }
});

loadSavedKey();
loadStatus().catch((error) => setStatus(error.message, true));
loadTokens().catch((error) => setStatus(error.message, true));
