const STORAGE_KEY = "dni_admin_key";
const el = (id) => document.getElementById(id);
const adminKeyInput = el("adminKey");
const saveBtn = el("saveAdminKey");
const clearBtn = el("clearAdminKey");
const refreshBtn = el("refreshBtn");
const createTokenForm = el("createTokenForm");
const tokenName = el("tokenName");
const tokenDescription = el("tokenDescription");
const tokenDailyLimit = el("tokenDailyLimit");
const tokenMinuteLimit = el("tokenMinuteLimit");
const tokensBody = el("tokensBody");
const statusBox = el("statusBox");
const adminHint = el("adminHint");
const tokenDialog = el("tokenDialog");
const tokenDialogText = el("tokenDialogText");
const tokenDialogCopy = el("tokenDialogCopy");
const tokenDialogClose = el("tokenDialogClose");
const apiHealthPill = el("apiHealthPill");
const dbHealthPill = el("dbHealthPill");
const sidebarBadge = el("sidebarBadge");

function getAdminKey() {
  return (localStorage.getItem(STORAGE_KEY) || adminKeyInput?.value || "").trim();
}

function syncHint(message, error = false) {
  if (!adminHint) return;
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
  if (!statusBox) return;
  if (typeof message === "string") {
    statusBox.innerHTML = `<span>Mensaje</span><div class="status-inline"><strong>${message}</strong></div>`;
    statusBox.dataset.error = error ? "1" : "0";
    return;
  }
  const blocks = [
    message.status || "-",
    `${message.api_keys?.active ?? 0}/${message.api_keys?.total ?? 0} keys`,
    `${message.logs?.total ?? 0} logs`,
    `D ${message.config?.default_daily_limit ?? "-"} / M ${message.config?.default_minute_limit ?? "-"}`,
  ];
  statusBox.innerHTML = `<span>Estado del servicio</span><div class="status-inline">${blocks.map((value) => `<strong>${value}</strong>`).join("")}</div>`;
  statusBox.dataset.error = error ? "1" : "0";
}

function setSidebarBadge(status, hasKeys = false) {
  if (!sidebarBadge) return;
  sidebarBadge.classList.remove("sidebar-badge--ok", "sidebar-badge--warn", "sidebar-badge--error");
  let label = "SYSTEM ONLINE";
  let variant = "sidebar-badge--ok";

  if (status !== "ok") {
    variant = status === "degraded" ? "sidebar-badge--warn" : "sidebar-badge--error";
    label = status === "degraded" ? "SYSTEM DEGRADED" : "SYSTEM OFFLINE";
  } else if (!hasKeys) {
    variant = "sidebar-badge--warn";
    label = "SYSTEM READY";
  }

  sidebarBadge.classList.add(variant);
  sidebarBadge.textContent = label;
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "-";
}

function row(token) {
  const preview = token.api_key_preview || "—";
  return `<tr>
    <td data-label="Nombre"><strong>${token.nombre || ""}</strong><div class="hint">${formatDate(token.fecha_creacion)}</div></td>
    <td data-label="Preview"><code>${preview}</code></td>
    <td data-label="Estado">${token.activo ? '<span class="pill ok">Active</span>' : '<span class="pill off">Revoked</span>'}</td>
    <td data-label="Acciones">
      <div class="actions">
        <button type="button" data-action="copy" data-token="${preview}">Copiar</button>
        <button type="button" data-action="${token.activo ? "deactivate" : "activate"}" data-id="${token.id}">${token.activo ? "Desactivar" : "Activar"}</button>
        <button type="button" data-action="delete" data-id="${token.id}">Eliminar</button>
      </div>
    </td>
  </tr>`;
}

async function loadStatus() {
  const data = await apiFetch("/admin/status", { method: "GET" });
  setStatus(data);
  if (apiHealthPill) apiHealthPill.textContent = `API: ${data.status || "ok"}`;
  if (dbHealthPill) dbHealthPill.textContent = `DB: ${data.api_keys?.total ?? 0} keys`;
  setSidebarBadge(data.status, (data.api_keys?.total ?? 0) > 0);
}

async function loadTokens() {
  const tokens = await apiFetch("/admin/api-keys", { method: "GET" });
  tokensBody.innerHTML = tokens.length ? tokens.map(row).join("") : '<tr><td colspan="4">Sin tokens</td></tr>';
}

async function createToken() {
  const nombre = tokenName?.value.trim() || "";
  if (!nombre) throw new Error("El nombre del token es obligatorio.");
  const token = await apiFetch("/admin/api-keys", {
    method: "POST",
    body: JSON.stringify({
      nombre,
      descripcion: tokenDescription?.value.trim() || "",
      limite_diario: tokenDailyLimit?.value ? Number(tokenDailyLimit.value) : null,
      limite_por_minuto: tokenMinuteLimit?.value ? Number(tokenMinuteLimit.value) : null,
    }),
  });
  tokenDialogText.textContent = token.api_key || "";
  tokenDialog.showModal();
  if (createTokenForm) createTokenForm.reset();
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
    if (!tokenValue) throw new Error("El backend no expuso el token completo.");
    await navigator.clipboard.writeText(tokenValue);
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
  if (saved && adminKeyInput) adminKeyInput.value = saved;
  syncHint(saved ? "X-Admin-Key cargada desde almacenamiento local." : "La clave solo se usa en este navegador.");
}

saveBtn?.addEventListener("click", () => {
  const value = adminKeyInput.value.trim();
  if (!value) return;
  localStorage.setItem(STORAGE_KEY, value);
  syncHint("X-Admin-Key guardada localmente.");
  loadTokens().catch((error) => setStatus(error.message, true));
});

clearBtn?.addEventListener("click", () => {
  localStorage.removeItem(STORAGE_KEY);
  if (adminKeyInput) adminKeyInput.value = "";
  syncHint("Clave eliminada del navegador.");
});

refreshBtn?.addEventListener("click", () => loadTokens().catch((error) => setStatus(error.message, true)));
createTokenForm?.addEventListener("submit", (event) => {
  event.preventDefault();
  createToken().catch((error) => setStatus(error.message, true));
});

tokensBody?.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  try {
    await runAction(button.dataset.action, button.dataset.id, button.dataset.token);
  } catch (error) {
    setStatus(error.message, true);
  }
});

tokenDialogClose?.addEventListener("click", () => tokenDialog.close());
tokenDialog?.addEventListener("click", (event) => {
  if (event.target === tokenDialog) tokenDialog.close();
});
tokenDialogCopy?.addEventListener("click", async () => {
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
