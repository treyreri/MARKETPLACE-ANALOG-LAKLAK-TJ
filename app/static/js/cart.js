// Cart (spec 10) and checkout (spec 11) on one page: cart -> checkout form -> success.
import { api, isAuthenticated } from "./api.js";
import { formatPrice, t } from "./i18n.js";
import { refreshCartCount, toast } from "./layout.js";
import { emptyState, loadingState } from "./unicorn.js";

const PHONE_RE = /^\+\d{10,15}$/;
const MAX_QTY = 100;  // CartItemUpdate limit

const root = document.querySelector("[data-cart-page]");
const state = root.querySelector("[data-state]");
const steps = Object.fromEntries([...root.querySelectorAll("[data-step]")].map((el) => [el.dataset.step, el]));
let cart = null;

function show(step) {
  Object.entries(steps).forEach(([name, el]) => { el.hidden = name !== step; });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderSummary() {
  root.querySelectorAll('[data-field="count"]').forEach((n) => { n.textContent = String(cart.total_quantity); });
  root.querySelectorAll('[data-field="total"]').forEach((n) => { n.textContent = formatPrice(cart.total_price); });
  root.querySelector('[data-field="warning"]').hidden = cart.can_checkout || !cart.items.length;
  root.querySelector('[data-action="checkout"]').disabled = !cart.can_checkout;
}

async function mutate(button, request) {
  button.classList.add("is-loading");
  root.querySelectorAll(".cart-item button, .cart-item input").forEach((b) => { b.disabled = true; });
  try {
    cart = await request();
    renderCart();
    refreshCartCount();
  } catch (error) {
    toast(error.message, { error: true });
    renderCart();
  }
}

function cartItem(item) {
  const { product } = item;
  const li = el("li", `cart-item${item.is_valid ? "" : " is-invalid"}`);

  const media = el("a", "cart-item-media product-media");
  media.href = `/product/${product.id}`;
  if (product.image_url) {
    const img = el("img");
    img.src = product.image_url;
    img.alt = "";
    media.append(img);
  } else {
    media.classList.add("is-empty");
  }

  const info = el("div", "cart-item-info");
  const name = el("a", "cart-item-name", product.name);
  name.href = `/product/${product.id}`;
  info.append(name, el("span", "muted", formatPrice(product.price)));
  if (!product.is_active || product.available_quantity === 0) {
    info.append(el("span", "cart-item-note", t("cart.unavailable")));
  } else if (item.quantity > product.available_quantity) {
    info.append(el("span", "cart-item-note", `${t("cart.only_left")} ${product.available_quantity} ${t("product.pcs")}`));
  }

  const max = Math.max(1, Math.min(product.available_quantity, MAX_QTY));
  const qty = el("div", "qty");
  const minus = el("button", "qty-btn", "−");
  const input = el("input", "qty-input");
  const plus = el("button", "qty-btn", "+");
  minus.type = plus.type = "button";
  minus.setAttribute("aria-label", "-");
  plus.setAttribute("aria-label", "+");
  input.type = "number";
  input.min = "1";
  input.max = String(max);
  input.value = String(item.quantity);
  input.setAttribute("aria-label", t("product.quantity"));
  minus.disabled = item.quantity <= 1;
  plus.disabled = item.quantity >= max;
  const update = (button, quantity) => {
    const value = Math.min(Math.max(1, quantity), max);
    if (value === item.quantity) { input.value = String(item.quantity); return; }
    mutate(button, () => api(`/cart/items/${item.id}`, { method: "PATCH", body: { quantity: value } }));
  };
  minus.addEventListener("click", () => update(minus, item.quantity - 1));
  plus.addEventListener("click", () => update(plus, item.quantity + 1));
  input.addEventListener("change", () => update(input, Number.parseInt(input.value, 10) || 1));
  qty.append(minus, input, plus);

  const total = el("strong", "cart-item-total", formatPrice(item.line_total));
  const remove = el("button", "link-btn cart-item-remove", t("cart.remove"));
  remove.type = "button";
  remove.addEventListener("click", () => mutate(remove, () => api(`/cart/items/${item.id}`, { method: "DELETE" })));

  const controls = el("div", "cart-item-controls");
  controls.append(qty, total, remove);
  li.append(media, info, controls);
  return li;
}

function renderCart() {
  if (!cart.items.length) {
    Object.values(steps).forEach((s) => { s.hidden = true; });
    const block = emptyState(t("cart.empty"));
    block.append(Object.assign(el("a", "btn btn-primary", t("home.hero.cta")), { href: "/catalog" }));
    state.replaceChildren(block);
    return;
  }
  state.replaceChildren();
  root.querySelector("[data-cart-items]").replaceChildren(...cart.items.map(cartItem));
  renderSummary();
  if (steps.cart.hidden && steps.checkout.hidden) show("cart");
}

// checkout

function setFieldError(form, name, message) {
  const input = form.elements[name];
  const error = input.closest(".field").querySelector(".field-error");
  error.textContent = message || "";
  error.hidden = !message;
  input.setAttribute("aria-invalid", message ? "true" : "false");
}

async function prefillCheckout(form) {
  if (form.dataset.prefilled) return;
  form.dataset.prefilled = "1";
  try {
    const me = await api("/auth/me");
    form.recipient_name.value ||= [me.first_name, me.last_name].filter(Boolean).join(" ");
    form.phone_number.value ||= me.phone_number;
  } catch { /* optional */ }
}

async function placeOrder(form) {
  form.querySelector(".form-error").hidden = true;
  const values = Object.fromEntries(new FormData(form));
  values.phone_number = values.phone_number.replace(/[\s()-]/g, "");
  const errors = {
    recipient_name: values.recipient_name.trim() ? "" : t("form.error_required"),
    phone_number: PHONE_RE.test(values.phone_number) ? "" : t("form.error_phone"),
    address: values.address.trim() ? "" : t("form.error_required"),
  };
  Object.entries(errors).forEach(([name, message]) => setFieldError(form, name, message));
  if (Object.values(errors).some(Boolean)) {
    form.querySelector("[aria-invalid=true]").focus();
    return;
  }

  const button = form.querySelector("[type=submit]");
  button.classList.add("is-loading");
  button.disabled = true;
  try {
    const order = await api("/orders", {
      method: "POST",
      body: {
        recipient_name: values.recipient_name.trim(),
        phone_number: values.phone_number,
        address: values.address.trim(),
        comment: values.comment.trim() || null,
        payment_method: values.payment_method,
      },
    });
    root.querySelector('[data-field="order-id"]').textContent = `#${order.id}`;
    root.querySelector('[data-field="order-total"]').textContent = formatPrice(order.total_price);
    show("success");
    refreshCartCount();
  } catch (error) {
    const box = form.querySelector(".form-error");
    box.textContent = error.message;
    box.hidden = false;
    // stock may have changed: refresh the cart so the user sees what to fix
    cart = await api("/cart").catch(() => cart);
    renderSummary();
  } finally {
    button.classList.remove("is-loading");
    button.disabled = false;
  }
}

async function load() {
  if (!isAuthenticated()) {
    window.location.replace(`/login?next=${encodeURIComponent("/shopping-cart")}`);
    return;
  }
  state.replaceChildren(loadingState(t("common.loading")));
  try {
    cart = await api("/cart");
    renderCart();
  } catch (error) {
    state.replaceChildren(emptyState(error.message));
  }
}

const form = root.querySelector(".checkout-form");
root.querySelector('[data-action="checkout"]').addEventListener("click", () => {
  prefillCheckout(form);
  show("checkout");
});
root.querySelector('[data-action="back"]').addEventListener("click", () => { renderCart(); show("cart"); });
form.addEventListener("submit", (event) => {
  event.preventDefault();
  placeOrder(form);
});

load();
