// Seller Dashboard (spec section 13): My Products, Orders, Store Information, Statistics.
import { api } from "../api.js";
import { formatPrice, t } from "../i18n.js";
import { currentUser, toast } from "../layout.js";
import {
  checkRequired, confirmDialog, field, formError, formValues, formatDate, h, loading, message, openDialog,
  requireAuth, setFieldError, showApiError, statusChip, tabs, withLoading,
} from "../ui.js";

const PRICE_RE = /^\d{1,8}(\.\d{1,2})?$/;
const PHONE_RE = /^\+\d{10,15}$/;
const app = document.getElementById("app");
document.title = `${t("seller.title")} — Treyreri Unicorn Store`;
let categoriesPromise = null;
let ui = null;

const categories = () => (categoriesPromise ??= api("/categories"));

// products

async function uploadImage(productId, file) {
  const form = new FormData();
  form.append("file", file);
  return api(`/seller/products/${productId}/image`, { method: "POST", form });
}

async function productDialog(product) {
  const cats = await categories();
  const form = h("form", { class: "form", novalidate: true, id: "product-form" },
    formError(),
    field({ label: t("seller.name"), name: "name", value: product?.name, required: true, attrs: { maxlength: 200 } }),
    h("div", { class: "field-row" },
      field({ label: t("seller.price"), name: "price", type: "number", value: product ? Number(product.price) : "", required: true,
        attrs: { min: 0, step: "0.01", inputmode: "decimal" } }),
      field({ label: t("seller.stock"), name: "quantity", type: "number", value: product?.quantity ?? 1, required: true,
        attrs: { min: 0, step: 1, inputmode: "numeric" } })),
    h("div", { class: "field-row" },
      field({ label: t("seller.category"), name: "category_id", value: product ? String(product.category.id) : "", required: true,
        options: [["", "—"], ...cats.map((c) => [String(c.id), c.name])] }),
      field({ label: t("seller.brand"), name: "brand", value: product?.brand, attrs: { maxlength: 100 } })),
    field({ label: t("seller.description"), name: "description", value: product?.description, textarea: true }),
    field({ label: t("seller.image"), name: "image", type: "file", hint: t("seller.image_hint"),
      attrs: { accept: "image/jpeg,image/png,image/webp" } }));

  const submit = h("button", { type: "submit", form: "product-form", class: "btn btn-primary", text: t("common.save") });
  const dialog = openDialog({
    title: product ? t("seller.edit_product") : t("seller.new_product"),
    body: form,
    actions: [h("button", { type: "button", class: "btn btn-ghost", text: t("common.cancel"), onClick: () => dialog.close() }), submit],
    wide: true,
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!checkRequired(form)) return;
    const values = formValues(form);
    if (!PRICE_RE.test(values.price)) {
      setFieldError(form, "price", t("form.error_required"));
      return;
    }
    const body = {
      name: values.name, price: values.price, quantity: Number.parseInt(values.quantity, 10),
      category_id: Number(values.category_id), brand: values.brand, description: values.description,
    };
    const file = form.elements.image.files[0];
    try {
      await withLoading(submit, async () => {
        const saved = product
          ? await api(`/seller/products/${product.id}`, { method: "PATCH", body })
          : await api("/seller/products", { method: "POST", body });
        if (file) await uploadImage(saved.id, file);
      });
      dialog.close();
      toast(t("seller.product_saved"));
      ui.select("products");
    } catch (error) {
      showApiError(form, error);
    }
  });
}

function productRow(product) {
  const fileInput = h("input", { type: "file", accept: "image/jpeg,image/png,image/webp", hidden: true });
  const uploadButton = h("button", { type: "button", class: "btn btn-ghost btn-sm", text: t("seller.upload_image"),
    onClick: () => fileInput.click() });
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;
    try {
      await withLoading(uploadButton, () => uploadImage(product.id, file));
      toast(t("seller.image_uploaded"));
      ui.select("products");
    } catch (error) {
      toast(error.message, { error: true });
    }
  });

  const thumb = product.image_url
    ? h("img", { class: "thumb", src: product.image_url, alt: "" })
    : h("div", { class: "thumb" });
  return h("div", { class: "list-item data-row" },
    thumb,
    h("div", {},
      h("div", { class: "list-item-title" }, h("a", { href: `/product/${product.id}`, text: product.name })),
      h("div", { class: "muted", text: product.category.name }),
      product.is_active ? null : h("span", { class: "status status-hidden", text: t("seller.hidden_note") })),
    h("div", {},
      h("strong", { text: formatPrice(product.price) }),
      h("div", { class: product.quantity ? "muted" : "status status-cancelled",
        text: product.quantity ? `${t("seller.stock_short")}: ${product.quantity}` : t("product.out_of_stock") })),
    h("div", { class: "actions" },
      h("button", { type: "button", class: "btn btn-ghost btn-sm", text: t("common.edit"), onClick: () => productDialog(product) }),
      uploadButton, fileInput,
      h("button", { type: "button", class: "btn btn-danger btn-sm", text: t("common.delete"),
        onClick: async (event) => {
          const button = event.currentTarget;
          if (!await confirmDialog(t("seller.delete_confirm", { name: product.name }), { confirmLabel: t("common.delete"), danger: true })) return;
          try {
            await withLoading(button, () => api(`/seller/products/${product.id}`, { method: "DELETE" }));
            toast(t("seller.product_deleted"));
            ui.select("products");
          } catch (error) {
            toast(error.message, { error: true });
          }
        } })));
}

async function renderProducts(panel) {
  const products = await api("/seller/products");
  const toolbar = h("div", { class: "row-between", style: "margin-bottom:16px" },
    h("span", { class: "muted", text: `${t("stats.products")}: ${products.length}` }),
    h("button", { type: "button", class: "btn btn-primary", text: t("seller.add_product"), onClick: () => productDialog(null) }));
  panel.replaceChildren(toolbar,
    products.length ? h("div", { class: "list" }, products.map(productRow)) : message(t("seller.no_products")));
}

// orders

async function renderOrders(panel) {
  const orders = await api("/seller/orders");
  if (!orders.length) {
    panel.replaceChildren(message(t("seller.no_orders")));
    return;
  }
  panel.replaceChildren(h("div", { class: "list" }, orders.map((order) => h("article", { class: "list-item" },
    h("div", { class: "list-item-head" },
      h("div", { class: "row" },
        h("span", { class: "list-item-title", text: `${t("orders.order")} #${order.order_id}` }),
        statusChip("order.status", order.status)),
      h("span", { class: "muted", text: formatDate(order.created_at) })),
    h("ul", { class: "lines" }, order.items.map((item) => h("li", {},
      h("span", { text: `${item.product_name} × ${item.quantity}` }),
      h("span", { text: formatPrice(item.line_total) })))),
    h("div", { class: "row-between", style: "margin-top:10px" },
      h("span", { class: "muted", text: t("seller.your_total") }),
      h("strong", { text: formatPrice(order.total) }))))));
}

// store

async function renderStore(panel) {
  const store = await api("/seller/store");
  const form = h("form", { class: "form", novalidate: true },
    formError(),
    field({ label: t("seller.store_name"), name: "store_name", value: store.store_name, required: true, attrs: { maxlength: 100 } }),
    field({ label: t("seller.store_description"), name: "store_description", value: store.store_description, textarea: true }),
    h("div", { class: "field-row" },
      field({ label: t("form.address"), name: "address", value: store.address, required: true, attrs: { maxlength: 255 } }),
      field({ label: t("seller.phone"), name: "phone_number", type: "tel", value: store.phone_number, required: true })),
    h("div", { class: "form-actions" }, h("button", { type: "submit", class: "btn btn-primary", text: t("common.save") })));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!checkRequired(form)) return;
    const values = formValues(form);
    values.phone_number = values.phone_number.replace(/[\s()-]/g, "");
    if (!PHONE_RE.test(values.phone_number)) {
      setFieldError(form, "phone_number", t("form.error_phone"));
      return;
    }
    try {
      await withLoading(form.querySelector("[type=submit]"), () => api("/seller/store", { method: "PATCH", body: values }));
      toast(t("seller.store_saved"));
    } catch (error) {
      showApiError(form, error);
    }
  });
  panel.replaceChildren(h("section", { class: "card", style: "max-width:720px" }, form));
}

// statistics

async function renderStats(panel) {
  const s = await api("/seller/statistics");
  const tile = (value, label, sub) => h("div", { class: "stat" },
    h("div", { class: "stat-value", text: value }), h("div", { class: "stat-label", text: label }),
    sub ? h("div", { class: "muted", text: sub }) : null);
  const max = Math.max(1, ...Object.values(s.orders_by_status));
  panel.replaceChildren(
    h("div", { class: "stats" },
      tile(String(s.product_count), t("stats.products"), `${s.active_product_count} ${t("stats.active")}`),
      tile(String(s.out_of_stock_count), t("stats.out_of_stock")),
      tile(String(s.units_sold), t("stats.units_sold")),
      tile(formatPrice(s.revenue), t("stats.revenue")),
      tile(String(s.order_count), t("stats.orders"))),
    h("p", { class: "muted", style: "margin-top:12px", text: t("stats.delivered_note") }),
    h("section", { class: "card", style: "margin-top:16px" },
      h("h2", { class: "h3", text: t("stats.by_status") }),
      h("div", { class: "stack" }, Object.entries(s.orders_by_status).map(([status, count]) => h("div", { class: "bar-row" },
        h("span", { text: t(`order.status.${status}`) }),
        h("div", { class: "bar" }, h("span", { style: `width:${(count / max) * 100}%` })),
        h("strong", { text: String(count) }))))));
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    const me = await currentUser();
    if (!me.roles.includes("seller")) {
      window.location.replace("/seller/login");
      return;
    }
    const store = await api("/seller/store").catch(() => null);
    app.replaceChildren(h("div", { class: "page-head" },
      h("div", {}, h("h1", { text: t("seller.title") }), store ? h("p", { class: "muted", style: "margin:4px 0 0", text: store.store_name }) : null)));
    ui = tabs(app, [
      { id: "products", label: t("seller.tab_products"), render: renderProducts },
      { id: "orders", label: t("seller.tab_orders"), render: renderOrders },
      { id: "store", label: t("seller.tab_store"), render: renderStore },
      { id: "stats", label: t("seller.tab_stats"), render: renderStats },
    ]);
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
