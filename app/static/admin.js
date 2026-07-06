// Adapted from api-ruc admin UX, adjusted for DNI API fields.
const STORAGE_KEY = "dni_admin_key";
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
function setStatus(message, error = false) { statusBox.textContent = message; statusBox.style.color = error ? "#fb7185" : ""; }
function setCreateMessage(message, error = false) { createMessage.textContent = message; createMessage.style.color = error ? "#fb7185" : ""; }
function getAdminKey() { return adminKeyInput.value.trim(); }
function saveLocalAdminKey() { localStorage.setItem(STORAGE_KEY, getAdminKey()); setStatus("Admin key guardada localmente en el navegador."); }
function loadLocalAdminKey() { const saved = localStorage.getItem(STORAGE_KEY); if (saved) adminKeyInput.value = saved; }
function clearLocalAdminKey() { localStorage.removeItem(STORAGE_KEY); adminKeyInput.value = ""; setStatus("Admin key eliminada del navegador."); }
function adminHeaders() { const key = getAdminKey(); if (!key) throw new Error("Debes ingresar X-Admin-Key"); return { "Content-Type": "application/json", "X-Admin-Key": key }; }
async function apiFetch(url, options = {}) { const headers = { ...(options.headers || {}), ...adminHeaders() }; const response = await fetch(url, { ...options, headers }); const data = await response.json().catch(() => ({})); if (!response.ok) throw new Error(data.detail || data.message || `Error ${response.status}`); return data; }
function formatDate(value) { return value ? new Date(value).toLocaleString() : "-"; }
function statusPill(active) { return active ? '<span class="pill ok">Activo</span>' : '<span class="pill off">Desactivado</span>'; }
function rowHtml(token) { return `<tr><td>${token.id}</td><td>${token.nombre || ""}</td><td><code>${token.token_preview || ""}</code></td><td>${statusPill(token.activo)}</td><td>${token.consultas_realizadas ?? 0}</td><td>${token.limite_diario ?? "-"}</td><td>${token.limite_por_minuto ?? "-"}</td><td>${formatDate(token.fecha_creacion)}</td><td>${formatDate(token.ultimo_uso)}</td><td><div class="actions-cell"><button type="button" data-action="${token.activo ? "deactivate" : "activate"}" data-id="${token.id}">${token.activo ? "Desactivar" : "Activar"}</button><button type="button" data-action="delete" data-id="${token.id}">Eliminar</button></div></td></tr>`; }
async function loadTokens() { setStatus("Cargando tokens..."); const tokens = await apiFetch("/admin/api-keys", { method: "GET" }); tokensBody.innerHTML = tokens.map(rowHtml).join("") || `<tr><td colspan="10">Sin tokens</td></tr>`; setStatus(`Tokens cargados: ${tokens.length}`); }
async function createToken(payload) { const token = await apiFetch("/admin/api-keys", { method: "POST", body: JSON.stringify(payload) }); tokenDialogText.textContent = token.api_key || ""; tokenDialog.showModal(); setCreateMessage("Token generado correctamente."); await loadTokens(); }
async function runAction(action, id) { const map = { deactivate: { url: `/admin/api-keys/${id}/deactivate`, method: "PATCH" }, activate: { url: `/admin/api-keys/${id}/activate`, method: "PATCH" }, delete: { url: `/admin/api-keys/${id}`, method: "DELETE" } }; const item = map[action]; if (!item) return; if (action === "delete" && !confirm("¿Eliminar esta API Key?")) return; await apiFetch(item.url, { method: item.method }); setStatus(`Acción aplicada: ${action} sobre token ${id}.`); await loadTokens(); }
tokensBody.addEventListener("click", async (event) => { const button = event.target.closest("button[data-action]"); if (!button) return; const { action, id } = button.dataset; try { await runAction(action, id); } catch (error) { setStatus(error.message, true); } });
createForm.addEventListener("submit", async (event) => { event.preventDefault(); try { await createToken({ nombre: el("nombre").value.trim(), descripcion: el("descripcion").value.trim(), limite_diario: Number(el("dailyLimit").value || 1000), limite_por_minuto: Number(el("minuteLimit").value || 60) }); } catch (error) { setCreateMessage(error.message, true); } });
saveAdminKeyBtn.addEventListener("click", saveLocalAdminKey); clearAdminKeyBtn.addEventListener("click", clearLocalAdminKey); refreshBtn.addEventListener("click", async () => { try { await loadTokens(); } catch (error) { setStatus(error.message, true); } }); tokenDialogClose.addEventListener("click", () => tokenDialog.close()); tokenDialog.addEventListener("click", (event) => { if (event.target === tokenDialog) tokenDialog.close(); }); tokenDialogCopy.addEventListener("click", async () => { try { await navigator.clipboard.writeText(tokenDialogText.textContent || ""); setCreateMessage("Token generado copiado."); } catch (error) { setCreateMessage("No se pudo copiar.", true); } });
loadLocalAdminKey(); loadTokens().catch((error) => setStatus(error.message, true));
