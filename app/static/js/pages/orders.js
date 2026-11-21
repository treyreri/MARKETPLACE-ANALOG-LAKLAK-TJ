// My orders: list, details, cancel pending, delivery progress.
import { api } from "../api.js";
import { formatPrice, t } from "../i18n.js";
import { toast } from "../layout.js";
import { confirmDialog, formatDate, h, loading, message, requireAuth, statusChip, withLoading } from "../ui.js";

const DELIVERY_STEPS = ["assigned", "picked_up", "in_delivery", "delivered"];
const app = document.getElementById("app");
document.title = `${t("orders.title")} — Treyreri Unicorn Store`;

function stepper(current) {
  const reached = DELIVERY_STEPS.indexOf(current);
  return h("div", { class: "stepper", "aria-label": t("orders.delivery") },
    DELIVERY_STEPS.map((step, index) => h("div", {
      class: `step${index <= reached ? " is-done" : ""}`, text: t(`delivery.status.${step}`) })));
}

function orderCard(order) {
  const card = h("article", { class: "list-item" });
  const render = (o) => {
    const cancel = o.status === "pending"
      ? h("button", { type: "button", class: "btn btn-danger btn-sm", text: t("orders.cancel"),
        onClick: async (event) => {
          const button = event.currentTarget;
          if (!await confirmDialog(t("orders.cancel_confirm"), { confirmLabel: t("orders.cancel"), danger: true })) return;
          try {
            const updated = await withLoading(button, () => api(`/orders/${o.id}/cancel`, { method: "POST" }));
            toast(t("orders.cancelled"));
            render(updated);
          } catch (error) {
            toast(error.message, { error: true });
          }
        } })
      : null;

    card.replaceChildren(
      h("div", { class: "list-item-head" },
        h("div", { class: "row" },
          h("span", { class: "list-item-title", text: `${t("orders.order")} #${o.id}` }),
          statusChip("order.status", o.status)),
        h("span", { class: "muted", text: formatDate(o.created_at) })),
      h("div", { class: "row-between", style: "margin-top:8px" },
        h("span", {}, `${t("orders.total")}: `, h("strong", { text: formatPrice(o.total_price) })),
        cancel),
      o.delivery_status && o.status !== "cancelled" ? stepper(o.delivery_status) : null,
      h("details", { style: "margin-top:12px" },
        h("summary", { class: "link-btn", text: t("orders.details") }),
        h("ul", { class: "lines" }, o.items.map((item) => h("li", {},
          h("span", { text: `${item.product_name} × ${item.quantity}` }),
          h("strong", { text: formatPrice(item.line_total) })))),
        h("dl", { class: "meta" },
          h("dt", { text: t("orders.recipient") }), h("dd", { text: o.recipient_name }),
          h("dt", { text: t("orders.phone") }), h("dd", { text: o.phone_number }),
          h("dt", { text: t("orders.address") }), h("dd", { text: o.address }),
          o.comment ? [h("dt", { text: t("orders.comment") }), h("dd", { text: o.comment })] : null,
          h("dt", { text: t("orders.payment") }), h("dd", { text: t("checkout.cod") }))));
  };
  render(order);
  return card;
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    const orders = await api("/orders");
    const head = h("div", { class: "page-head" }, h("h1", { text: t("orders.title") }));
    if (!orders.length) {
      app.replaceChildren(head, message(t("orders.empty"),
        h("a", { class: "btn btn-primary", href: "/catalog", text: t("home.hero.cta") })));
      return;
    }
    app.replaceChildren(head, h("div", { class: "list" }, orders.map(orderCard)));
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
