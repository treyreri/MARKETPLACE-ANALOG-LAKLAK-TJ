// Login and register forms (spec section 9).
import { api, isAuthenticated, setToken } from "./api.js";
import { t } from "./i18n.js";

const PHONE_RE = /^\+\d{10,15}$/;

/** Only same-site relative paths, so ?next= cannot redirect to another site. */
export function safeNext() {
  const next = new URLSearchParams(window.location.search).get("next");
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/";
}

function setFieldError(form, name, message) {
  const input = form.elements[name];
  const error = input?.closest(".field")?.querySelector(".field-error");
  if (!error) return;
  error.textContent = message || "";
  error.hidden = !message;
  input.setAttribute("aria-invalid", message ? "true" : "false");
}

function clearErrors(form) {
  form.querySelectorAll(".field-error").forEach((el) => { el.hidden = true; el.textContent = ""; });
  form.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  form.querySelector(".form-error").hidden = true;
}

function showFormError(form, message) {
  const box = form.querySelector(".form-error");
  box.textContent = message;
  box.hidden = false;
}

function validate(form, mode) {
  const values = Object.fromEntries(new FormData(form));
  values.phone_number = values.phone_number.replace(/[\s()-]/g, "");
  const errors = {};
  if (!PHONE_RE.test(values.phone_number)) errors.phone_number = t("form.error_phone");
  if (mode === "register") {
    if (values.password.length < 6) errors.password = t("form.error_password_short");
    if (values.password !== values.password_confirm) errors.password_confirm = t("form.error_password_mismatch");
  } else if (!values.password) {
    errors.password = t("form.error_required");
  }
  return { values, errors };
}

async function login(phone_number, password) {
  const { access_token } = await api("/auth/login", { method: "POST", body: { phone_number, password } });
  setToken(access_token);
}

async function submit(form, mode) {
  clearErrors(form);
  const { values, errors } = validate(form, mode);
  if (Object.keys(errors).length) {
    Object.entries(errors).forEach(([name, message]) => setFieldError(form, name, message));
    form.querySelector("[aria-invalid=true]")?.focus();
    return;
  }

  const button = form.querySelector("[type=submit]");
  button.classList.add("is-loading");
  button.disabled = true;
  try {
    if (mode === "register") {
      await api("/auth/register", {
        method: "POST",
        body: {
          phone_number: values.phone_number,
          password: values.password,
          password_confirm: values.password_confirm,
          first_name: values.first_name.trim() || null,
          last_name: values.last_name.trim() || null,
        },
      });
    }
    await login(values.phone_number, values.password);
    window.location.href = safeNext();
  } catch (error) {
    if (error.status === 409) setFieldError(form, "phone_number", error.message);
    else showFormError(form, error.message);
    button.classList.remove("is-loading");
    button.disabled = false;
  }
}

const form = document.querySelector("[data-auth-form]");
if (form) {
  if (isAuthenticated()) window.location.replace(safeNext());
  const mode = form.dataset.authForm;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submit(form, mode);
  });
  // carry ?next= over when switching between login and register
  const next = new URLSearchParams(window.location.search).get("next");
  if (next) {
    document.querySelectorAll("[data-keep-next]").forEach((link) => {
      link.href = `${link.getAttribute("href")}?next=${encodeURIComponent(next)}`;
    });
  }
}
