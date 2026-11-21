// Courier Dashboard (spec section 15): assigned deliveries, next-status buttons, history.
import { api } from "../api.js";
import { formatPrice, t } from "../i18n.js";
import { currentUser, toast } from "../layout.js";
import { formatDate, h, loading, message, requireAuth, statusChip, tabs, withLoading } from "../ui.js";

const NEXT = { assigned: "picked_up", picked_up: "in_delivery", in_delivery: "delivered" };
const app = document.getElementById("app");
document.title = `${t("courier.title")} — Treyreri Unicorn Store`;
let ui = null;

function deliveryCard(order, { active }) {
  const next = NEXT[order.delivery_status];
  const button = active && next
    ? h("button", { type: "button", class: "btn btn-primary btn-block", text: t(`courier.next.${next}`),
      onClick: async (event) => {
        try {
          await withLoading(event.currentTarget,
            () => api(`/courier/orders/${order.id}/status`, { method: "PATCH", body: { status: next } }));
          toast(t("courier.status_updated"));
          ui.select("active");
        } catch (error) {
          toast(error.message, { error: true });
        }
      } })
    : null;

  return h("article", { class: "list-item delivery-card" },
    h("div", { class: "list-item-head" },
      h("span", { class: "list-item-title", text: `${t("orders.order")} #${order.id}` }),
      statusChip("delivery.status", order.delivery_status)),
    h("dl", { class: "meta" },
      h("dt", { text: t("orders.recipient") }), h("dd", { text: order.recipient_name }),
      h("dt", { text: t("orders.phone") }),
      h("dd", {}, h("a", { href: `tel:${order.phone_number}`, text: order.phone_number })),
      h("dt", { text: t("orders.address") }), h("dd", { class: "delivery-address", text: order.address }),
      order.comment ? [h("dt", { text: t("orders.comment") }), h("dd", { text: order.comment })] : null,
      active
        ? null
        : [h("dt", { text: t("courier.delivered_at") }), h("dd", { text: formatDate(order.delivered_at) })]),
    h("ul", { class: "lines" }, order.items.map((item) => h("li", {},
      h("span", { text: `${item.product_name} × ${item.quantity}` }),
      h("span", { text: formatPrice(item.line_total) })))),
    h("div", { class: "row-between collect" },
      h("span", { text: active ? t("courier.to_collect") : t("orders.total") }),
      h("strong", { text: formatPrice(order.total_price) })),
    active ? h("div", { class: "row", style: "margin-top:12px" },
      h("a", { class: "btn btn-ghost", href: `tel:${order.phone_number}`, text: t("courier.call") }), button) : null);
}

async function renderActive(panel) {
  const orders = await api("/courier/orders");
  panel.replaceChildren(orders.length
    ? h("div", { class: "list delivery-grid" }, orders.map((o) => deliveryCard(o, { active: true })))
    : message(t("courier.no_active")));
}

async function renderHistory(panel) {
  const orders = (await api("/courier/orders", { query: { active_only: false } }))
    .filter((o) => o.delivery_status === "delivered");
  panel.replaceChildren(orders.length
    ? h("div", { class: "list delivery-grid" }, orders.map((o) => deliveryCard(o, { active: false })))
    : message(t("courier.no_history")));
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    const me = await currentUser();
    if (!me.roles.includes("courier")) {
      window.location.replace("/courier/login");
      return;
    }
    const profile = await api("/courier/profile").catch(() => null);
    app.replaceChildren(h("div", { class: "page-head" },
      h("div", {}, h("h1", { text: t("courier.title") }),
        profile ? h("p", { class: "muted", style: "margin:4px 0 0",
          text: `${t("courier.transport")}: ${t(`transport.${profile.transport_type}`)} · ${profile.address}` }) : null)));
    ui = tabs(app, [
      { id: "active", label: t("courier.tab_active"), render: renderActive },
      { id: "history", label: t("courier.tab_history"), render: renderHistory },
    ]);
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
