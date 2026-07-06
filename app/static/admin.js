// Adapted from api-ruc admin UX, adjusted for DNI API fields.
const STORAGE_KEY = "adminKey";
const el = (id) => document.getElementById(id);
const adminKeyInput = el("adminKey");
const saveAdminKeyBtn = el("saveAdminKey");
const clearAdminKeyBtn = el("clearAdminKey");
const createForm = el("createForm");
const tokensBody = el("tokensBody");
const statusBox = el("status");
const createMessage = el("createMessage");
const tokenDialog = el("tokenDialog");
const tokenDialogText = el("tokenDialogText");
const tokenDialogCopy = el("tokenDialogCopy");
const tokenDialogClose = el("tokenDialogClose");
const refreshBtn = el("refreshBtn");
const adminHint = document.createElement("div");
adminHint.id = "adminHint";
adminHint.className = "message muted";
adminHint.textContent = "Ingresa tu API_ADMIN_KEY";
adminKeyInput.insertAdjacentElement("afterend", adminHint);

function setStatus(message, error = false) { statusBox.textContent = message; statusBox.style.color = error ? "#fb7185" : ""; }
function setCreateMessage(message, error = false) { createMessage.textContent = message; createMessage.style.color = error ? "#fb7185" : ""; }
function getAdminHeaders() {
  const adminKey = (localStorage.getItem("adminKey") || document.getElementById("adminKey")?.value || "").trim();
  if (!adminKey) {
    adminHint.textContent = "Ingresa tu API_ADMIN_KEY";
    adminHint.style.color = "#fb7185";
  } else {
    adminHint.textContent = "API_ADMIN_KEY cargada";
    adminHint.style.color = "";
  }
  return {
    "X-Admin-Key": adminKey,
    "Content-Type": "application/json"
  };
}
function saveLocalAdminKey() {
  const adminKey = (adminKeyInput.value || "").trim();
  localStorage.setItem(STORAGE_KEY, adminKey);
  adminKeyInput.value = adminKey;
  getAdminHeaders();
  setStatus("Admin key guardada localmente en el navegador.");
  loadTokens().catch((error) => setStatus(error.message, true));
}
function loadLocalAdminKey() { const saved = localStorage.getItem(STORAGE_KEY); if (saved) adminKeyInput.value = saved; getAdminHeaders(); }
function clearLocalAdminKey() { localStorage.removeItem(STORAGE_KEY); adminKeyInput.value = ""; getAdminHeaders(); setStatus("Admin key eliminada del navegador."); }
async function apiFetch(url, options = {}) {
  const headers = { ...(options.headers || {}), ...getAdminHeaders() };
  if (!headers["X-Admin-Key"]) throw new Error("Ingresa tu API_ADMIN_KEY");
  const response = await fetch(url, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Error ${response.status}`);
  return data;
}
function formatDate(value) { return value ? new Date(value).toLocaleString() : "-"; }
function statusPill(active) { return active ? '<span class="pill ok">Activo</span>' : '<span class="pill off">Desactivado</span>'; }
function rowHtml(token) { return `<tr><td>${token.id}</td><td>${token.nombre || ""}</td><td><code>${token.token_preview || ""}</code></td><td>${statusPill(token.activo)}</td><td>${token.consultas_realizadas ?? 0}</td><td>${token.limite_diario ?? "-"}</td><td>${token.limite_por_minuto ?? "-"}</td><td>${formatDate(token.fecha_creacion)}</td><td>${formatDate(token.ultimo_uso)}</td><td><div class="actions-cell"><button type="button" data-action="${token.activo ? "deactivate" : "activate"}" data-id="${token.id}">${token.activo ? "Desactivar" : "Activar"}</button><button type="button" data-action="delete" data-id="${token.id}">Eliminar</button></div></td></tr>`; }
async function loadTokens() { setStatus("Cargando tokens..."); const tokens = await apiFetch("/admin/api-keys", { method: "GET" }); tokensBody.innerHTML = tokens.map(rowHtml).join("") || `<tr><td colspan="10">Sin tokens</td></tr>`; setStatus(`Tokens cargados: ${tokens.length}`); }
async function createToken(payload) { const token = await apiFetch("/admin/api-keys", { method: "POST", body: JSON.stringify(payload) }); tokenDialogText.textContent = token.api_key || ""; tokenDialog.showModal(); setCreateMessage("Token generado correctamente."); await loadTokens(); }
async function runAction(action, id) { const map = { deactivate: { url: `/admin/api-keys/${id}/deactivate`, method: "PATCH" }, activate: { url: `/admin/api-keys/${id}/activate`, method: "PATCH" }, delete: { url: `/admin/api-keys/${id}`, method: "DELETE" } }; const item = map[action]; if (!item) return; if (action === "delete" && !confirm("¿Eliminar esta API Key?")) return; await apiFetch(item.url, { method: item.method }); setStatus(`Acción aplicada: ${action} sobre token ${id}.`); await loadTokens(); }
tokensBody.addEventListener("click", async (event) => { const button = event.target.closest("button[data-action]"); if (!button) return; const { action, id } = button.dataset; try { await runAction(action, id); } catch (error) { setStatus(error.message, true); } });
createForm.addEventListener("submit", async (event) => { event.preventDefault(); try { await createToken({ nombre: el("nombre").value.trim(), descripcion: el("descripcion").value.trim(), limite_diario: Number(el("dailyLimit").value || 1000), limite_por_minuto: Number(el("minuteLimit").value || 60) }); } catch (error) { setCreateMessage(error.message, true); } });
saveAdminKeyBtn.addEventListener("click", saveLocalAdminKey); clearAdminKeyBtn.addEventListener("click", clearLocalAdminKey); refreshBtn.addEventListener("click", async () => { try { await loadTokens(); } catch (error) { setStatus(error.message, true); } }); tokenDialogClose.addEventListener("click", () => tokenDialog.close()); tokenDialog.addEventListener("click", (event) => { if (event.target === tokenDialog) tokenDialog.close(); }); tokenDialogCopy.addEventListener("click", async () => { try { await navigator.clipboard.writeText(tokenDialogText.textContent || ""); setCreateMessage("Token generado copiado."); } catch (error) { setCreateMessage("No se pudo copiar.", true); } });
loadLocalAdminKey();
loadTokens().catch((error) => setStatus(error.message, true));
