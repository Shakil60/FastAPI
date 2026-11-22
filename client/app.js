// Client de l'API Recipe : HTML/JS sans framework, le token JWT est gardé dans localStorage.
const API = window.API_URL;
const $ = (id) => document.getElementById(id);

let token = localStorage.getItem("token");
let me = null;

// --- Appels à l'API -------------------------------------------------------

async function api(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(API + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && token) {
    logout();
    throw new Error("Session expirée, reconnectez-vous");
  }
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorText(data, response.status));
  return data;
}

// FastAPI renvoie soit {detail: "..."} soit {detail: [{msg, loc}, ...]} (erreurs de validation)
function errorText(data, status) {
  const detail = data && data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => `${d.loc.at(-1)} : ${d.msg}`).join(" · ");
  return `Erreur ${status}`;
}

// --- Affichage ------------------------------------------------------------

function showMessage(text, type = "error") {
  const el = $("message");
  el.textContent = text;
  el.className = `message ${type}`;
  el.hidden = false;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => (el.hidden = true), 4000);
}

function li(html) {
  const item = document.createElement("li");
  item.innerHTML = html;
  return item;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

// Exécute une action et affiche l'erreur éventuelle au lieu de la laisser remonter
function guarded(fn) {
  return async (event) => {
    if (event) event.preventDefault();
    try {
      await fn(event);
    } catch (error) {
      showMessage(error.message);
    }
  };
}

// --- Authentification -----------------------------------------------------

async function login(username, password) {
  const data = await api("/auth/login", { method: "POST", body: { username, password } });
  token = data.access_token;
  localStorage.setItem("token", token);
  await start();
}

function logout() {
  token = null;
  me = null;
  localStorage.removeItem("token");
  $("app-view").hidden = true;
  $("session").hidden = true;
  $("auth-view").hidden = false;
}

// --- Recettes -------------------------------------------------------------

async function loadRecipes() {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(formData($("search-form")))) {
    if (value) params.set(key, value);
  }
  const recipes = await api(`/recipes${params.size ? "?" + params : ""}`);

  const list = $("recipes");
  list.replaceChildren();
  if (recipes.length === 0) {
    list.append(li('<span class="empty">Aucune recette</span>'));
    return;
  }

  for (const recipe of recipes) {
    const mine = recipe.owner_id === me.id;
    const item = li(`
      <div>
        <strong>${escapeHtml(recipe.title)}</strong>
        <span class="badge">${mine ? "à moi" : "partagée"}</span>
        <div class="meta">${recipe.duration} min · ${recipe.servings} pers.</div>
      </div>
      <div class="actions">
        <button class="small ghost" data-action="edit">Modifier</button>
        ${mine ? '<button class="small ghost" data-action="delete">Supprimer</button>' : ""}
      </div>`);
    item.querySelector('[data-action="edit"]').onclick = () => editRecipe(recipe);
    const del = item.querySelector('[data-action="delete"]');
    if (del) del.onclick = guarded(() => deleteRecipe(recipe));
    list.append(item);
  }
}

function editRecipe(recipe) {
  const fields = $("recipe-form").elements;
  fields.recipe_id.value = recipe.id;
  fields.title.value = recipe.title;
  fields.duration.value = recipe.duration;
  fields.servings.value = recipe.servings;
  $("recipe-form-title").textContent = "Modifier la recette";
  $("cancel-edit").hidden = false;
  $("recipe-form").scrollIntoView({ behavior: "smooth", block: "center" });
}

function resetRecipeForm() {
  $("recipe-form").reset();
  $("recipe-form").elements.recipe_id.value = "";
  $("recipe-form-title").textContent = "Nouvelle recette";
  $("cancel-edit").hidden = true;
}

async function saveRecipe() {
  const { recipe_id: id, title, duration, servings } = formData($("recipe-form"));
  const body = { title, duration: Number(duration), servings: Number(servings) };
  if (id) {
    await api(`/recipes/${id}`, { method: "PUT", body });
    showMessage("Recette modifiée", "ok");
  } else {
    await api("/recipes", { method: "POST", body });
    showMessage("Recette créée", "ok");
  }
  resetRecipeForm();
  await loadRecipes();
}

async function deleteRecipe(recipe) {
  if (!confirm(`Supprimer « ${recipe.title} » ?`)) return;
  await api(`/recipes/${recipe.id}`, { method: "DELETE" });
  showMessage("Recette supprimée", "ok");
  await loadRecipes();
}

// --- Partage --------------------------------------------------------------

async function loadAccesses() {
  const [granted, received] = await Promise.all([
    api("/users/me/accesses"),
    api("/users/me/accesses/received"),
  ]);

  const grantedList = $("granted");
  grantedList.replaceChildren();
  if (granted.length === 0) grantedList.append(li('<span class="empty">Aucun accès accordé</span>'));
  for (const access of granted) {
    const item = li(`
      <span>Utilisateur n°${access.grantee_id}
        <span class="badge">${access.can_edit ? "lecture et modification" : "lecture seule"}</span></span>
      <div class="actions"><button class="small ghost">Retirer</button></div>`);
    item.querySelector("button").onclick = guarded(async () => {
      await api(`/users/me/accesses/${access.grantee_id}`, { method: "DELETE" });
      showMessage("Accès retiré", "ok");
      await loadAccesses();
    });
    grantedList.append(item);
  }

  const receivedList = $("received");
  receivedList.replaceChildren();
  if (received.length === 0) receivedList.append(li('<span class="empty">Aucun accès reçu</span>'));
  for (const access of received) {
    receivedList.append(li(`
      <span>Recettes de l'utilisateur n°${access.owner_id}
        <span class="badge">${access.can_edit ? "lecture et modification" : "lecture seule"}</span></span>`));
  }
}

async function share() {
  const form = $("share-form");
  const fields = form.elements;
  await api("/users/me/accesses", {
    method: "POST",
    body: { username: fields.username.value, can_edit: fields.can_edit.checked },
  });
  form.reset();
  showMessage("Accès accordé", "ok");
  await loadAccesses();
}

// --- Démarrage ------------------------------------------------------------

async function start() {
  me = await api("/users/me");
  $("whoami").textContent = `Connecté : ${me.username}`;
  $("auth-view").hidden = true;
  $("session").hidden = false;
  $("app-view").hidden = false;
  await Promise.all([loadRecipes(), loadAccesses()]);
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.onclick = () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
      $("login-form").hidden = tab.dataset.tab !== "login";
      $("register-form").hidden = tab.dataset.tab !== "register";
    };
  });

  $("login-form").onsubmit = guarded(async (event) => {
    const { username, password } = formData(event.target);
    await login(username, password);
  });

  $("register-form").onsubmit = guarded(async (event) => {
    const { username, email, password } = formData(event.target);
    await api("/auth/register", { method: "POST", body: { username, email, password } });
    showMessage("Compte créé", "ok");
    await login(username, password);
  });

  $("logout").onclick = logout;
  $("search-form").onsubmit = guarded(loadRecipes);
  $("search-form").onreset = () => setTimeout(guarded(loadRecipes));
  $("recipe-form").onsubmit = guarded(saveRecipe);
  $("cancel-edit").onclick = resetRecipeForm;
  $("share-form").onsubmit = guarded(share);
}

$("api-link").href = API + "/docs";
$("api-link").textContent = API;
bindEvents();

if (token) {
  start().catch((error) => {
    logout();
    showMessage(error.message);
  });
} else {
  logout();
}
