// Shared page chrome: translations, language switch, auth state in header, cart badge, toasts.
import { api, getToken, isAuthenticated, logout } from "./api.js";
import { applyTranslations, getLang, hasChosenLang, setLang } from "./i18n.js";
import { renderUnicorns } from "./unicorn.js";

export function toast(message, { error = false } = {}) {
  const region = document.querySelector(".toast-region");
  const el = document.createElement("div");
  el.className = `toast${error ? " is-error" : ""}`;
  el.textContent = message;
  region.append(el);
  setTimeout(() => el.remove(), 3200);
}

export async function refreshCartCount() {
  const badge = document.querySelector(".cart-count");
  if (!isAuthenticated()) {
    badge.hidden = true;
    return;
  }
  try {
    const cart = await api("/cart");
    badge.textContent = cart.total_quantity;
    badge.hidden = cart.total_quantity === 0;
  } catch {
    badge.hidden = true;
  }
}

let mePromise = null;

/** Cached GET /auth/me for the current page; null for guests. */
export function currentUser({ refresh = false } = {}) {
  if (!isAuthenticated()) return Promise.resolve(null);
  if (!mePromise || refresh) {
    mePromise = api("/auth/me").catch((error) => { mePromise = null; throw error; });
  }
  return mePromise;
}

export function displayName(user) {
  return [user.first_name, user.last_name].filter(Boolean).join(" ") || user.phone_number;
}

async function renderUser() {
  document.body.classList.toggle("is-authenticated", isAuthenticated());
  if (!isAuthenticated()) return;
  try {
    const me = await currentUser({ refresh: true });
    document.querySelector(".user-name").textContent = displayName(me);
    document.querySelectorAll("[data-requires-role]").forEach((link) => {
      link.hidden = !me.roles.includes(link.dataset.requiresRole);
    });
  } catch {
    // 401 already logged out via api(); anything else: keep the header usable
  }
}

function initLanguage() {
  const current = getLang();
  document.querySelectorAll("[data-lang]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === current);
    button.setAttribute("aria-pressed", String(button.dataset.lang === current));
    button.addEventListener("click", () => {
      if (button.dataset.lang === getLang()) return;
      setLang(button.dataset.lang);
      window.location.reload();  // simplest way to re-fetch translated API data
    });
  });

  const picker = document.querySelector(".lang-picker");
  if (!hasChosenLang()) {
    picker.hidden = false;
    picker.querySelectorAll("[data-pick-lang]").forEach((button) => {
      button.addEventListener("click", () => {
        const changed = button.dataset.pickLang !== getLang();
        setLang(button.dataset.pickLang);
        picker.hidden = true;
        if (changed) window.location.reload();
      });
    });
  }
}

function initUserMenu() {
  const toggle = document.querySelector(".user-menu-toggle");
  const list = document.querySelector(".user-menu-list");
  toggle.addEventListener("click", () => {
    list.hidden = !list.hidden;
    toggle.setAttribute("aria-expanded", String(!list.hidden));
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".user-menu")) {
      list.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    }
  });
  document.querySelector("[data-action=logout]").addEventListener("click", () => {
    logout();
    window.location.href = "/";
  });
}

function initSearch() {
  const input = document.querySelector(".header-search input");
  const q = new URLSearchParams(window.location.search).get("q");
  if (q) input.value = q;
}

applyTranslations();
renderUnicorns();
document.documentElement.classList.remove("i18n-pending");
initLanguage();
initUserMenu();
initSearch();
renderUser();
refreshCartCount();

window.addEventListener("auth:change", () => {
  renderUser();
  refreshCartCount();
});

export { getToken };
