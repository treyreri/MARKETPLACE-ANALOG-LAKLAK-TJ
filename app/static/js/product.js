// Product page (spec section 8).
import { api } from "./api.js";
import { addToCart } from "./components.js";
import { formatPrice, t } from "./i18n.js";
import { emptyState, loadingState } from "./unicorn.js";

const MAX_PER_ADD = 100;  // CartItemAdd.quantity limit in the API

const root = document.querySelector("[data-product-page]");
const page = root.querySelector(".product-page");
const state = root.querySelector("[data-state]");
const field = (name) => root.querySelector(`[data-field="${name}"]`);

function setupQuantity(maxQuantity) {
  const input = root.querySelector(".qty-input");
  const minus = root.querySelector('[data-qty="-1"]');
  const plus = root.querySelector('[data-qty="1"]');
  input.max = String(maxQuantity);

  const clamp = (value) => Math.min(Math.max(1, Number.parseInt(value, 10) || 1), maxQuantity);
  const sync = () => {
    input.value = String(clamp(input.value));
    minus.disabled = Number(input.value) <= 1;
    plus.disabled = Number(input.value) >= maxQuantity;
  };
  minus.addEventListener("click", () => { input.value = String(Number(input.value) - 1); sync(); });
  plus.addEventListener("click", () => { input.value = String(Number(input.value) + 1); sync(); });
  input.addEventListener("change", sync);
  sync();
  return () => Number(input.value);
}

function render(product) {
  document.title = `${product.name} — Treyreri Unicorn Store`;
  field("category-link").textContent = product.category.name;
  field("category-link").href = `/catalog?category_id=${product.category.id}`;
  field("category").textContent = product.category.name;
  field("name").textContent = product.name;
  field("price").textContent = formatPrice(product.price);
  field("seller").textContent = product.seller.name;
  field("brand").textContent = product.brand || "";
  field("brand-row").hidden = !product.brand;
  field("description").textContent = product.description || "—";

  const media = field("media");
  if (product.image_url) {
    const img = document.createElement("img");
    img.src = product.image_url;
    img.alt = product.name;
    media.replaceChildren(img);
  } else {
    media.classList.add("is-empty");
    media.replaceChildren(Object.assign(document.createElement("span"), {
      className: "product-media-placeholder", textContent: t("product.no_image") }));
  }

  const inStock = product.quantity > 0;
  field("stock").textContent = inStock ? `${product.quantity} ${t("product.pcs")}` : t("product.out_of_stock");
  field("stock").classList.toggle("is-out", !inStock);

  const addButton = root.querySelector('[data-action="add"]');
  const buyButton = root.querySelector('[data-action="buy"]');
  if (!inStock) {
    root.querySelector(".qty").hidden = true;
    addButton.disabled = true;
    buyButton.disabled = true;
    return;
  }
  const quantity = setupQuantity(Math.min(product.quantity, MAX_PER_ADD));
  addButton.addEventListener("click", () => addToCart(addButton, product.id, quantity()));
  buyButton.addEventListener("click", async () => {
    if (await addToCart(buyButton, product.id, quantity())) window.location.href = "/shopping-cart";
  });
}

async function load() {
  state.replaceChildren(loadingState(t("common.loading")));
  try {
    const product = await api(`/products/${root.dataset.productId}`);
    render(product);
    page.hidden = false;
    state.replaceChildren();
  } catch (error) {
    const message = error.status === 404 ? t("product.not_found") : error.message;
    const block = emptyState(message);
    const home = Object.assign(document.createElement("a"), {
      className: "btn btn-primary", href: "/catalog", textContent: t("home.hero.cta") });
    block.append(home);
    state.replaceChildren(block);
  }
}

load();
