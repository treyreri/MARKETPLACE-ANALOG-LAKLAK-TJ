// Profile: edit name, roles, links to sections the user has access to.
import { api } from "../api.js";
import { t } from "../i18n.js";
import { currentUser, toast } from "../layout.js";
import {
  clearErrors, field, formError, formValues, h, loading, message, requireAuth, showApiError, statusChip, withLoading,
} from "../ui.js";

const app = document.getElementById("app");
document.title = `${t("account.title")} — Treyreri Unicorn Store`;

async function latestApplication(kind) {
  try {
    return await api(`/${kind}/applications/me`);
  } catch (error) {
    if (error.status === 404) return null;
    throw error;
  }
}

function profileForm(me) {
  const form = h("form", { class: "form", novalidate: true },
    formError(),
    field({ label: t("form.phone"), name: "phone_number", value: me.phone_number, attrs: { readonly: true, disabled: true } }),
    h("div", { class: "field-row" },
      field({ label: t("form.first_name"), name: "first_name", value: me.first_name ?? "", attrs: { maxlength: 50, autocomplete: "given-name" } }),
      field({ label: t("form.last_name"), name: "last_name", value: me.last_name ?? "", attrs: { maxlength: 50, autocomplete: "family-name" } })),
    h("div", { class: "form-actions" }, h("button", { type: "submit", class: "btn btn-primary", text: t("common.save") })));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors(form);
    const { first_name, last_name } = formValues(form);
    try {
      await withLoading(form.querySelector("[type=submit]"),
        () => api("/auth/me", { method: "PATCH", body: { first_name, last_name } }));
      toast(t("common.saved"));
      window.dispatchEvent(new Event("auth:change"));  // refresh the name in the header
    } catch (error) {
      showApiError(form, error);
    }
  });
  return h("section", { class: "card" }, h("h2", { class: "h3", text: t("account.personal") }), form);
}

function roleSection(kind, me, application) {
  const role = kind;
  const dashboard = `/dashboard/${kind}`;
  const title = t(`account.${kind}_application`);
  if (me.roles.includes(role)) {
    return h("div", { class: "row-between" },
      h("span", {}, title, " "), h("a", { class: "btn btn-secondary btn-sm", href: dashboard, text: t(`nav.${kind}_dashboard`) }));
  }
  if (application) {
    return h("div", { class: "row-between" },
      h("span", { class: "row" }, title, statusChip("application.status", application.status)),
      h("a", { class: "btn btn-ghost btn-sm", href: `/application/${kind}`, text: t("account.view_status") }));
  }
  return h("div", { class: "row-between" },
    h("span", { text: title }),
    h("a", { class: "btn btn-ghost btn-sm", href: `/become-${kind}`, text: t(`footer.become_${kind}`) }));
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    const [me, sellerApp, courierApp] = await Promise.all([
      currentUser(), latestApplication("seller"), latestApplication("courier")]);
    const roles = ["customer", ...me.roles];
    const access = h("section", { class: "card" },
      h("h2", { class: "h3", text: t("account.access") }),
      h("div", { class: "stack" },
        h("div", { class: "row-between" }, h("span", { text: t("nav.orders") }),
          h("a", { class: "btn btn-ghost btn-sm", href: "/account/orders", text: t("nav.orders") })),
        roleSection("seller", me, sellerApp),
        roleSection("courier", me, courierApp),
        me.roles.includes("admin")
          ? h("div", { class: "row-between" }, h("span", { text: t("role.admin") }),
            h("a", { class: "btn btn-secondary btn-sm", href: "/dashboard/admin", text: t("nav.admin_panel") }))
          : null));

    app.replaceChildren(
      h("div", { class: "page-head" }, h("h1", { text: t("account.title") })),
      h("div", { class: "grid-2" },
        profileForm(me),
        h("div", {},
          h("section", { class: "card" },
            h("h2", { class: "h3", text: t("account.roles") }),
            h("div", { class: "chips" }, roles.map((role) => h("span", { class: "chip", text: t(`role.${role}`) })))),
          access)));
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
