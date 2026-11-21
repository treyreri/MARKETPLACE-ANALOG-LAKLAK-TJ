// Become a seller / courier: application forms (spec sections 12 and 14).
import { api } from "../api.js";
import { t } from "../i18n.js";
import { currentUser } from "../layout.js";
import {
  checkRequired, field, formError, formValues, h, loading, message, requireAuth, setFieldError, showApiError,
  unicornBlock, withLoading,
} from "../ui.js";

const PHONE_RE = /^\+\d{10,15}$/;
const TRANSPORTS = ["foot", "bicycle", "motorcycle", "car"];
const app = document.getElementById("app");
const kind = app.dataset.kind;  // "seller" | "courier"
document.title = `${t(`apply.${kind}.title`)} — Treyreri Unicorn Store`;

async function previousApplication() {
  try {
    return await api(`/${kind}/applications/me`);
  } catch (error) {
    if (error.status === 404) return null;
    throw error;
  }
}

function sellerFields(prev, categories) {
  return [
    field({ label: t("apply.store_name"), name: "store_name", value: prev?.store_name, required: true, attrs: { maxlength: 100 } }),
    field({ label: t("apply.store_description"), name: "store_description", value: prev?.store_description, textarea: true }),
    field({ label: t("form.address"), name: "address", value: prev?.address, required: true, attrs: { maxlength: 255, autocomplete: "street-address" } }),
    field({ label: t("apply.category"), name: "category_id", value: prev?.category_id ?? "",
      options: [["", t("apply.category_any")], ...categories.map((c) => [String(c.id), c.name])] }),
  ];
}

function courierFields(prev) {
  return [
    field({ label: t("form.address"), name: "address", value: prev?.address, required: true, attrs: { maxlength: 255, autocomplete: "street-address" } }),
    field({ label: t("apply.transport"), name: "transport_type", value: prev?.transport_type ?? "bicycle", required: true,
      options: TRANSPORTS.map((v) => [v, t(`transport.${v}`)]) }),
    field({ label: t("apply.experience"), name: "experience", value: prev?.experience, textarea: true }),
  ];
}

function buildForm(me, prev, categories) {
  const form = h("form", { class: "form", novalidate: true },
    formError(),
    h("div", { class: "field-row" },
      field({ label: t("form.first_name"), name: "first_name", value: prev?.first_name ?? me.first_name, required: true, attrs: { maxlength: 50 } }),
      field({ label: t("form.last_name"), name: "last_name", value: prev?.last_name ?? me.last_name, required: true, attrs: { maxlength: 50 } })),
    field({ label: t("form.phone"), name: "phone_number", type: "tel", value: prev?.phone_number ?? me.phone_number, required: true,
      attrs: { placeholder: "+992XXXXXXXXX", inputmode: "tel" } }),
    kind === "seller" ? sellerFields(prev, categories) : courierFields(prev),
    field({ label: t("apply.additional_info"), name: "additional_info", value: prev?.additional_info, textarea: true }),
    h("div", { class: "form-actions" }, h("button", { type: "submit", class: "btn btn-primary", text: t("apply.submit") })));

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!checkRequired(form)) return;
    const values = formValues(form);
    values.phone_number = values.phone_number.replace(/[\s()-]/g, "");
    if (!PHONE_RE.test(values.phone_number)) {
      setFieldError(form, "phone_number", t("form.error_phone"));
      return;
    }
    if (kind === "seller") values.category_id = values.category_id ? Number(values.category_id) : null;
    try {
      await withLoading(form.querySelector("[type=submit]"),
        () => api(`/${kind}/applications`, { method: "POST", body: values }));
      window.location.href = `/application/${kind}`;
    } catch (error) {
      if (error.status === 409) window.location.href = `/application/${kind}`;
      else showApiError(form, error);
    }
  });
  return form;
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    const me = await currentUser();
    if (me.roles.includes(kind)) {
      app.replaceChildren(message(t(`apply.already_${kind}`),
        h("a", { class: "btn btn-primary", href: `/dashboard/${kind}`, text: t("apply.go_dashboard") })));
      return;
    }
    const [prev, categories] = await Promise.all([
      previousApplication(), kind === "seller" ? api("/categories") : Promise.resolve([])]);
    if (prev?.status === "pending") {
      window.location.replace(`/application/${kind}`);
      return;
    }
    const intro = unicornBlock("empty", h("p", { text: t(`apply.${kind}.intro`) }));
    intro.classList.add("apply-intro");
    app.replaceChildren(
      h("div", { class: "page-head" }, h("h1", { text: t(`apply.${kind}.title`) })),
      h("div", { class: "grid-2 apply-layout" },
        h("section", { class: "card" }, buildForm(me, prev, categories)),
        intro));
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
