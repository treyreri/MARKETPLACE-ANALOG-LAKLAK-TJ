// Small UI toolkit shared by account and dashboard pages.
import { isAuthenticated } from "./api.js";
import { getLang, t } from "./i18n.js";
import { renderUnicorns } from "./unicorn.js";

/** h("button", { class: "btn", onClick }, "text", childNode) */
export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(props || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") el.className = value;
    else if (key === "text") el.textContent = value;
    else if (key === "dataset") Object.assign(el.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === "value") el.value = value;
    else if (value === true) el.setAttribute(key, "");
    else el.setAttribute(key, value);
  }
  for (const child of children.flat(Infinity)) {
    if (child === null || child === undefined || child === false) continue;
    el.append(child instanceof Node ? child : String(child));
  }
  return el;
}

export async function withLoading(button, action) {
  button.classList.add("is-loading");
  button.disabled = true;
  try {
    return await action();
  } finally {
    button.classList.remove("is-loading");
    button.disabled = false;
  }
}

export function requireAuth() {
  if (isAuthenticated()) return true;
  window.location.replace(`/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`);
  return false;
}

export function formatDate(iso, { time = true } = {}) {
  if (!iso) return "";
  const options = { day: "numeric", month: "short", year: "numeric" };
  if (time) Object.assign(options, { hour: "2-digit", minute: "2-digit" });
  return new Intl.DateTimeFormat(getLang() === "ru" ? "ru-RU" : "en-GB", options).format(new Date(iso));
}

/** Status chip, e.g. statusChip("order.status", "pending"). */
export function statusChip(prefix, value) {
  return h("span", { class: `status status-${value}`, text: t(`${prefix}.${value}`) });
}

export function unicornBlock(variant, ...children) {
  const block = h("div", { class: "empty-state" }, h("span", { dataset: { unicorn: variant } }), ...children);
  renderUnicorns(block);
  return block;
}

export function message(text, ...actions) {
  return unicornBlock("empty", h("p", { text }), actions.length ? h("div", { class: "form-actions center" }, actions) : null);
}

export function loading() {
  const block = h("div", { class: "loading-state", role: "status" },
    h("span", { dataset: { unicorn: "loading" } }), h("p", { text: t("common.loading") }));
  renderUnicorns(block);
  return block;
}

// forms

/**
 * field({ label, name, type, value, required, textarea, options: [[value, label]], hint, attrs })
 */
export function field({ label, name, type = "text", value = "", required = false, textarea = false,
  options = null, hint = null, attrs = {} }) {
  let control;
  if (options) {
    control = h("select", { class: "input", name, ...attrs },
      options.map(([v, text]) => h("option", { value: v, text })));
    control.value = value ?? "";
  } else if (textarea) {
    control = h("textarea", { class: "input", name, ...attrs });
    control.value = value ?? "";
  } else {
    control = h("input", { class: "input", name, type, ...attrs });
    control.value = value ?? "";
  }
  if (required) control.required = true;
  return h("label", { class: "field" },
    h("span", { text: label + (required ? " *" : "") }),
    control,
    hint ? h("small", { class: "field-hint", text: hint }) : null,
    h("small", { class: "field-error", hidden: true }));
}

export function formError() {
  return h("div", { class: "form-error", role: "alert", hidden: true });
}

export function clearErrors(form) {
  form.querySelectorAll(".field-error").forEach((el) => { el.hidden = true; el.textContent = ""; });
  form.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  const box = form.querySelector(".form-error");
  if (box) box.hidden = true;
}

export function setFieldError(form, name, text) {
  const control = form.elements[name];
  const error = control?.closest(".field")?.querySelector(".field-error");
  if (!error) return false;
  error.textContent = text;
  error.hidden = false;
  control.setAttribute("aria-invalid", "true");
  return true;
}

/** Client check for required fields. Returns true when the form is valid. */
export function checkRequired(form) {
  clearErrors(form);
  let ok = true;
  form.querySelectorAll("[required]").forEach((control) => {
    if (!String(control.value).trim()) {
      setFieldError(form, control.name, t("form.error_required"));
      ok = false;
    }
  });
  if (!ok) form.querySelector("[aria-invalid=true]")?.focus();
  return ok;
}

/** Show an ApiError: 422 details go to their fields, everything else to the form box. */
export function showApiError(form, error) {
  let placed = false;
  if (Array.isArray(error.detail)) {
    error.detail.forEach((item) => {
      const name = item.loc?.[item.loc.length - 1];
      if (typeof name === "string" && setFieldError(form, name, item.msg.replace(/^Value error, /, ""))) placed = true;
    });
  }
  if (!placed) {
    const box = form.querySelector(".form-error");
    if (box) {
      box.textContent = error.message;
      box.hidden = false;
    }
  }
}

/** Form values with trimmed strings; empty optional strings become null. */
export function formValues(form) {
  const values = {};
  for (const [key, value] of new FormData(form)) {
    if (value instanceof File) continue;
    const trimmed = String(value).trim();
    values[key] = trimmed === "" ? null : trimmed;
  }
  return values;
}

// dialogs

export function openDialog({ title, body, actions = [], wide = false }) {
  const dialog = h("dialog", { class: `dialog${wide ? " dialog-wide" : ""}` },
    h("div", { class: "dialog-head" },
      h("h2", { class: "h3", text: title }),
      h("button", { type: "button", class: "dialog-close", "aria-label": t("common.close"), text: "×",
        onClick: () => dialog.close() })),
    h("div", { class: "dialog-body" }, body),
    actions.length ? h("div", { class: "dialog-actions" }, actions) : null);
  dialog.addEventListener("close", () => dialog.remove());
  document.body.append(dialog);
  dialog.showModal();
  return dialog;
}

export function confirmDialog(text, { confirmLabel = t("common.confirm"), danger = false } = {}) {
  return new Promise((resolve) => {
    let result = false;
    const dialog = openDialog({
      title: t("common.are_you_sure"),
      body: h("p", { text }),
      actions: [
        h("button", { type: "button", class: "btn btn-ghost", text: t("common.cancel"), onClick: () => dialog.close() }),
        h("button", { type: "button", class: `btn ${danger ? "btn-danger" : "btn-primary"}`, text: confirmLabel,
          onClick: () => { result = true; dialog.close(); } }),
      ],
    });
    dialog.addEventListener("close", () => resolve(result));
  });
}

// tabs (state in location.hash so reload keeps the tab)

export function tabs(container, items) {
  const bar = h("div", { class: "tabs", role: "tablist" });
  const panel = h("div", { class: "tab-panel", role: "tabpanel" });
  const buttons = new Map();

  async function select(id, { push = true } = {}) {
    const item = items.find((i) => i.id === id) ?? items[0];
    buttons.forEach((button, key) => {
      button.setAttribute("aria-selected", String(key === item.id));
      button.classList.toggle("is-active", key === item.id);
    });
    if (push) history.replaceState(null, "", `#${item.id}`);
    panel.replaceChildren(loading());
    try {
      await item.render(panel);
    } catch (error) {
      panel.replaceChildren(message(error.message));
    }
  }

  items.forEach((item) => {
    const button = h("button", { type: "button", class: "tab", role: "tab", text: item.label,
      onClick: () => select(item.id) });
    buttons.set(item.id, button);
    bar.append(button);
  });
  container.append(bar, panel);
  select(window.location.hash.slice(1), { push: false });
  return { select, panel };
}

export function pager({ total, limit, offset, onChange }) {
  if (total <= limit) return null;
  const page = Math.floor(offset / limit) + 1;
  const pages = Math.ceil(total / limit);
  return h("div", { class: "pagination" },
    h("button", { type: "button", class: "btn btn-ghost btn-sm", text: "←", disabled: page <= 1,
      onClick: () => onChange(offset - limit) }),
    h("span", { class: "muted", text: `${page} / ${pages}` }),
    h("button", { type: "button", class: "btn btn-ghost btn-sm", text: "→", disabled: page >= pages,
      onClick: () => onChange(offset + limit) }));
}
