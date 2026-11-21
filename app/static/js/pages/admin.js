// Admin Panel (spec section 16): applications, orders, users, products, categories.
import { api } from "../api.js";
import { formatPrice, t } from "../i18n.js";
import { currentUser, displayName, toast } from "../layout.js";
import {
  checkRequired, clearErrors, confirmDialog, field, formError, formValues, formatDate, h, loading, message, pager,
  requireAuth, showApiError, statusChip, tabs, withLoading,
} from "../ui.js";

const PAGE = 20;
// Mirrors ALLOWED_TRANSITIONS in order_service; shipped/delivered belong to the courier once assigned
const NEXT_STATUS = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["processing", "cancelled"],
  processing: ["shipped", "cancelled"],
  shipped: ["delivered"],
  delivered: [],
  cancelled: [],
};
const app = document.getElementById("app");
document.title = `${t("admin.title")} — Treyreri Unicorn Store`;
let me = null;

const option = (value, label) => [value, label];
const select = (name, value, options, onChange) => {
  const control = h("select", { class: "input", name, onChange }, options.map(([v, l]) => h("option", { value: v, text: l })));
  control.value = value;
  return control;
};
const labeled = (label, control) => h("label", { class: "field" }, h("span", { text: label }), control);
const meta = (rows) => h("dl", { class: "meta" },
  rows.filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([label, value]) => [h("dt", { text: label }), h("dd", { text: String(value) })]));

async function act(button, request, success, refresh) {
  try {
    await withLoading(button, request);
    toast(success);
    refresh();
  } catch (error) {
    toast(error.message, { error: true });
  }
}

// applications

const appState = { kind: "seller", status: "pending" };

function applicationCard(application, refresh) {
  const isSeller = appState.kind === "seller";
  const details = meta([
    [t("orders.phone"), application.phone_number],
    [t("form.address"), application.address],
    ...(isSeller
      ? [[t("apply.store_name"), application.store_name], [t("apply.store_description"), application.store_description]]
      : [[t("apply.transport"), t(`transport.${application.transport_type}`)], [t("apply.experience"), application.experience]]),
    [t("apply.additional_info"), application.additional_info],
    [t("appstatus.submitted_at"), formatDate(application.created_at)],
    [t("appstatus.reviewed_at"), application.reviewed_at ? formatDate(application.reviewed_at) : null],
    [t("appstatus.admin_comment"), application.admin_comment],
  ]);

  let review = null;
  if (application.status === "pending") {
    const comment = h("textarea", { class: "input", name: "admin_comment", maxlength: 1000 });
    const decide = (status) => (event) => act(event.currentTarget,
      () => api(`/admin/${appState.kind}-applications/${application.id}`, {
        method: "PATCH", body: { status, admin_comment: comment.value.trim() || null } }),
      t("admin.reviewed"), refresh);
    review = h("div", { class: "stack", style: "margin-top:12px" },
      labeled(t("admin.comment"), comment),
      h("div", { class: "row" },
        h("button", { type: "button", class: "btn btn-primary btn-sm", text: t("admin.approve"), onClick: decide("approved") }),
        h("button", { type: "button", class: "btn btn-danger btn-sm", text: t("admin.reject"), onClick: decide("rejected") })));
  }

  return h("article", { class: "list-item" },
    h("div", { class: "list-item-head" },
      h("span", { class: "list-item-title", text: `#${application.id} · ${application.first_name} ${application.last_name}` }),
      statusChip("application.status", application.status)),
    details, review);
}

async function renderApplications(panel) {
  const refresh = () => renderApplications(panel);
  const items = await api(`/admin/${appState.kind}-applications`, { query: { status: appState.status } });
  const kindSwitch = h("div", { class: "segmented", role: "group" }, ["seller", "courier"].map((kind) =>
    h("button", { type: "button", class: kind === appState.kind ? "is-active" : "", text: t(`admin.${kind}s`),
      onClick: () => { appState.kind = kind; refresh(); } })));
  const statusFilter = select("status", appState.status, [
    option("", t("common.all")), ...["pending", "approved", "rejected"].map((s) => option(s, t(`application.status.${s}`)))],
  (event) => { appState.status = event.target.value; refresh(); });
  panel.replaceChildren(
    h("div", { class: "toolbar" }, kindSwitch, labeled(t("admin.status"), statusFilter)),
    items.length ? h("div", { class: "list" }, items.map((a) => applicationCard(a, refresh))) : message(t("admin.no_applications")));
}

// orders

const orderState = { status: "" };

function orderCard(order, couriers, refresh) {
  const courier = couriers.find((c) => c.id === order.courier_id);
  const next = NEXT_STATUS[order.status].filter((s) => !(order.courier_id && ["shipped", "delivered"].includes(s)));

  const statusSelect = select("status", next[0] ?? "", next.map((s) => option(s, t(`order.status.${s}`))));
  const statusControl = next.length
    ? h("div", { class: "row" }, labeled(t("admin.change_status"), statusSelect),
      h("button", { type: "button", class: "btn btn-secondary btn-sm", text: t("admin.apply"),
        onClick: (event) => act(event.currentTarget,
          () => api(`/admin/orders/${order.id}`, { method: "PATCH", body: { status: statusSelect.value } }),
          t("admin.status_changed"), refresh) }))
    : null;

  const canAssign = ["confirmed", "processing"].includes(order.status)
    && [null, "assigned"].includes(order.delivery_status);
  let assign = null;
  if (canAssign) {
    if (!couriers.length) {
      assign = h("p", { class: "muted", text: t("admin.no_couriers") });
    } else {
      const courierSelect = select("courier_id", order.courier_id ? String(order.courier_id) : "", [
        option("", t("admin.choose_courier")),
        ...couriers.map((c) => option(String(c.id), `${c.name} · ${c.phone_number}${c.transport_type ? ` · ${t(`transport.${c.transport_type}`)}` : ""}`))]);
      assign = h("div", { class: "row" }, labeled(t("admin.assign_courier"), courierSelect),
        h("button", { type: "button", class: "btn btn-primary btn-sm", text: t("admin.assign"),
          onClick: (event) => {
            if (!courierSelect.value) return;
            act(event.currentTarget,
              () => api(`/admin/orders/${order.id}/assign-courier`, { method: "POST", body: { courier_id: Number(courierSelect.value) } }),
              t("admin.courier_assigned"), refresh);
          } }));
    }
  }

  return h("article", { class: "list-item" },
    h("div", { class: "list-item-head" },
      h("div", { class: "row" },
        h("span", { class: "list-item-title", text: `${t("orders.order")} #${order.id}` }),
        statusChip("order.status", order.status),
        order.delivery_status ? statusChip("delivery.status", order.delivery_status) : null),
      h("span", { class: "muted", text: formatDate(order.created_at) })),
    meta([
      [t("orders.recipient"), order.recipient_name],
      [t("orders.phone"), order.phone_number],
      [t("orders.address"), order.address],
      [t("orders.comment"), order.comment],
      [t("admin.courier"), courier ? `${courier.name} · ${courier.phone_number}` : (order.courier_id ? `#${order.courier_id}` : null)],
      [t("orders.total"), formatPrice(order.total_price)],
    ]),
    h("details", { style: "margin-top:8px" },
      h("summary", { class: "link-btn", text: t("orders.details") }),
      h("ul", { class: "lines" }, order.items.map((item) => h("li", {},
        h("span", { text: `${item.product_name} × ${item.quantity}` }),
        h("span", { text: formatPrice(item.line_total) }))))),
    statusControl || assign
      ? h("div", { class: "stack", style: "margin-top:12px" }, statusControl, assign,
        order.courier_id && order.status !== "delivered" ? h("small", { class: "muted", text: t("admin.by_courier_note") }) : null)
      : null);
}

async function renderOrders(panel) {
  const refresh = () => renderOrders(panel);
  const [orders, couriers] = await Promise.all([
    api("/admin/orders", { query: { status: orderState.status } }), api("/admin/couriers")]);
  const statusFilter = select("status", orderState.status, [
    option("", t("common.all")), ...Object.keys(NEXT_STATUS).map((s) => option(s, t(`order.status.${s}`)))],
  (event) => { orderState.status = event.target.value; refresh(); });
  panel.replaceChildren(
    h("div", { class: "toolbar" }, labeled(t("admin.status"), statusFilter)),
    orders.length ? h("div", { class: "list" }, orders.map((o) => orderCard(o, couriers, refresh))) : message(t("admin.no_orders")));
}

// users

const userState = { q: "", role: "", is_active: "", offset: 0 };

async function renderUsers(panel) {
  const refresh = () => renderUsers(panel);
  const data = await api("/admin/users", { query: { ...userState, limit: PAGE } });

  const search = h("form", { class: "toolbar", onSubmit: (event) => {
    event.preventDefault();
    Object.assign(userState, formValuesRaw(event.currentTarget), { offset: 0 });
    refresh();
  } },
  labeled(t("admin.search_users"), h("input", { class: "input", name: "q", type: "search", value: userState.q })),
  labeled(t("admin.role"), select("role", userState.role, [option("", t("common.all")),
    ...["seller", "courier", "admin"].map((r) => option(r, t(`role.${r}`)))])),
  labeled(t("admin.status"), select("is_active", userState.is_active, [option("", t("common.all")),
    option("true", t("user.status.active")), option("false", t("user.status.blocked"))])),
  h("button", { type: "submit", class: "btn btn-secondary", text: t("common.search") }));

  const rows = data.items.map((user) => {
    const self = user.id === me.id;
    const toggle = self ? h("span", { class: "muted", text: `(${t("admin.you")})` }) : h("button", {
      type: "button", class: `btn btn-sm ${user.is_active ? "btn-danger" : "btn-primary"}`,
      text: user.is_active ? t("admin.block") : t("admin.unblock"),
      onClick: async (event) => {
        const button = event.currentTarget;
        if (user.is_active && !await confirmDialog(t("admin.block_confirm", { name: displayName(user) }), { confirmLabel: t("admin.block"), danger: true })) return;
        act(button, () => api(`/admin/users/${user.id}`, { method: "PATCH", body: { is_active: !user.is_active } }),
          t("common.saved"), refresh);
      } });
    return h("div", { class: "list-item data-row user-row" },
      h("span", { class: "muted", text: `#${user.id}` }),
      h("div", {},
        h("div", { class: "list-item-title", text: displayName(user) }),
        h("div", { class: "muted", text: `${user.phone_number} · ${formatDate(user.created_at, { time: false })}` })),
      h("div", { class: "chips" },
        statusChip("user.status", user.is_active ? "active" : "blocked"),
        [...user.roles].map((r) => h("span", { class: "chip", text: t(`role.${r}`) }))),
      h("div", { class: "actions" }, toggle));
  });

  panel.replaceChildren(search,
    h("p", { class: "muted", text: `${t("catalog.found")}: ${data.total}` }),
    rows.length ? h("div", { class: "list" }, rows) : message(t("admin.no_users")),
    pager({ ...data, onChange: (offset) => { userState.offset = offset; refresh(); } }));
}

function formValuesRaw(form) {
  return Object.fromEntries([...new FormData(form)].map(([k, v]) => [k, String(v).trim()]));
}

// products

const productState = { q: "", is_active: "", seller_id: "", offset: 0 };

async function renderProducts(panel) {
  const refresh = () => renderProducts(panel);
  const data = await api("/admin/products", { query: { ...productState, limit: PAGE } });

  const search = h("form", { class: "toolbar", onSubmit: (event) => {
    event.preventDefault();
    Object.assign(productState, formValuesRaw(event.currentTarget), { offset: 0 });
    refresh();
  } },
  labeled(t("admin.search_products"), h("input", { class: "input", name: "q", type: "search", value: productState.q })),
  labeled(t("admin.visibility"), select("is_active", productState.is_active, [option("", t("common.all")),
    option("true", t("product.status.active")), option("false", t("product.status.hidden"))])),
  labeled(t("admin.seller_id"), h("input", { class: "input", name: "seller_id", type: "number", min: 1, value: productState.seller_id })),
  h("button", { type: "submit", class: "btn btn-secondary", text: t("common.search") }));

  const rows = data.items.map((product) => h("div", { class: "list-item data-row" },
    product.image_url ? h("img", { class: "thumb", src: product.image_url, alt: "" }) : h("div", { class: "thumb" }),
    h("div", {},
      h("div", { class: "list-item-title" }, h("a", { href: `/product/${product.id}`, text: product.name })),
      h("div", { class: "muted", text: `${product.seller.name} (#${product.seller.id}) · ${product.category.name}` })),
    h("div", {},
      h("strong", { text: formatPrice(product.price) }),
      h("div", { class: "muted", text: `${t("seller.stock_short")}: ${product.quantity}` }),
      statusChip("product.status", product.is_active ? "active" : "hidden")),
    h("div", { class: "actions" },
      h("button", { type: "button", class: "btn btn-ghost btn-sm", text: product.is_active ? t("admin.hide") : t("admin.show"),
        onClick: (event) => act(event.currentTarget,
          () => api(`/admin/products/${product.id}`, { method: "PATCH", body: { is_active: !product.is_active } }),
          t("common.saved"), refresh) }),
      h("button", { type: "button", class: "btn btn-danger btn-sm", text: t("common.delete"),
        onClick: async (event) => {
          const button = event.currentTarget;
          if (!await confirmDialog(t("admin.delete_product_confirm", { name: product.name }), { confirmLabel: t("common.delete"), danger: true })) return;
          act(button, () => api(`/admin/products/${product.id}`, { method: "DELETE" }), t("seller.product_deleted"), refresh);
        } }))));

  panel.replaceChildren(search,
    h("p", { class: "muted", text: `${t("catalog.found")}: ${data.total}` }),
    rows.length ? h("div", { class: "list" }, rows) : message(t("admin.no_products")),
    pager({ ...data, onChange: (offset) => { productState.offset = offset; refresh(); } }));
}

// categories

async function renderCategories(panel) {
  const refresh = () => renderCategories(panel);
  const categories = await api("/categories");

  const create = h("form", { class: "form card", novalidate: true },
    h("h2", { class: "h3", text: t("admin.add_category") }),
    formError(),
    h("div", { class: "field-row" },
      field({ label: t("admin.name_ru"), name: "name_ru", required: true, attrs: { maxlength: 100 } }),
      field({ label: t("admin.name_en"), name: "name_en", required: true, attrs: { maxlength: 100 } })),
    h("div", { class: "form-actions" }, h("button", { type: "submit", class: "btn btn-primary", text: t("admin.add_category") })));
  create.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!checkRequired(create)) return;
    try {
      await withLoading(create.querySelector("[type=submit]"),
        () => api("/categories", { method: "POST", body: formValues(create) }));
      toast(t("admin.category_saved"));
      refresh();
    } catch (error) {
      showApiError(create, error);
    }
  });

  const rows = categories.map((category) => {
    const form = h("form", { class: "list-item category-row", novalidate: true },
      h("span", { class: "muted", text: `#${category.id}` }),
      field({ label: t("admin.name_ru"), name: "name_ru", value: category.name_ru, required: true, attrs: { maxlength: 100 } }),
      field({ label: t("admin.name_en"), name: "name_en", value: category.name_en, required: true, attrs: { maxlength: 100 } }),
      h("div", { class: "actions" },
        h("button", { type: "submit", class: "btn btn-secondary btn-sm", text: t("common.save") }),
        h("button", { type: "button", class: "btn btn-danger btn-sm", text: t("common.delete"),
          onClick: async (event) => {
            const button = event.currentTarget;
            const name = category[`name_${document.documentElement.lang === "en" ? "en" : "ru"}`];
            if (!await confirmDialog(t("admin.delete_category_confirm", { name }), { confirmLabel: t("common.delete"), danger: true })) return;
            act(button, () => api(`/categories/${category.id}`, { method: "DELETE" }), t("common.saved"), refresh);
          } })),
      formError());
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!checkRequired(form)) return;
      clearErrors(form);
      try {
        await withLoading(form.querySelector("[type=submit]"),
          () => api(`/categories/${category.id}`, { method: "PATCH", body: formValues(form) }));
        toast(t("admin.category_saved"));
      } catch (error) {
        showApiError(form, error);
      }
    });
    return form;
  });

  panel.replaceChildren(create, h("div", { class: "list", style: "margin-top:16px" },
    rows.length ? rows : message(t("admin.no_categories"))));
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    me = await currentUser();
    if (!me.roles.includes("admin")) {
      app.replaceChildren(message(t("common.no_access"), h("a", { class: "btn btn-primary", href: "/", text: t("soon.home") })));
      return;
    }
    app.replaceChildren(h("div", { class: "page-head" }, h("h1", { text: t("admin.title") })));
    tabs(app, [
      { id: "applications", label: t("admin.tab_applications"), render: renderApplications },
      { id: "orders", label: t("admin.tab_orders"), render: renderOrders },
      { id: "users", label: t("admin.tab_users"), render: renderUsers },
      { id: "products", label: t("admin.tab_products"), render: renderProducts },
      { id: "categories", label: t("admin.tab_categories"), render: renderCategories },
    ]);
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
