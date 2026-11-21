// Reusable UI pieces built with DOM APIs (textContent only, no HTML injection of API data).
import { api, isAuthenticated } from "./api.js";
import { formatPrice, t } from "./i18n.js";
import { refreshCartCount, toast } from "./layout.js";

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export async function addToCart(button, productId, quantity = 1) {
  if (!isAuthenticated()) {
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
    return false;
  }
  button.classList.add("is-loading");
  button.disabled = true;
  try {
    await api("/cart/items", { method: "POST", body: { product_id: productId, quantity } });
    toast(t("toast.added_to_cart"));
    refreshCartCount();
    return true;
  } catch (error) {
    toast(error.message, { error: true });
    return false;
  } finally {
    button.classList.remove("is-loading");
    button.disabled = false;
  }
}

/**
 * Product card (spec 7): image, name, price, short description, category, seller, add-to-cart.
 * No stickers or badges over the image.
 */
export function productCard(product) {
  const href = `/product/${product.id}`;
  const card = el("article", "product-card");

  const media = el("a", "product-media");
  media.href = href;
  media.tabIndex = -1;
  media.setAttribute("aria-hidden", "true");
  if (product.image_url) {
    const img = el("img");
    img.src = product.image_url;
    img.alt = "";
    img.loading = "lazy";
    img.decoding = "async";
    media.append(img);
  } else {
    media.classList.add("is-empty");
    media.append(el("span", "product-media-placeholder", t("product.no_image")));
  }

  const body = el("div", "product-body");
  const category = el("p", "product-category", product.category.name);
  const title = el("h3", "product-title");
  const link = el("a", "", product.name);
  link.href = href;
  title.append(link);
  const description = el("p", "product-description", product.description || "");
  const seller = el("p", "product-seller", `${t("product.seller")}: ${product.seller.name}`);

  const footer = el("div", "product-footer");
  const price = el("span", "product-price", formatPrice(product.price));
  const button = el("button", "btn btn-primary btn-sm");
  button.type = "button";
  if (product.quantity > 0) {
    button.textContent = t("product.add_to_cart");
    button.addEventListener("click", () => addToCart(button, product.id));
  } else {
    button.textContent = t("product.out_of_stock");
    button.disabled = true;
  }
  footer.append(price, button);

  body.append(category, title, description, seller, footer);
  card.append(media, body);
  return card;
}

export function skeletonCards(count) {
  return Array.from({ length: count }, () => {
    const card = el("div", "product-card is-skeleton");
    card.innerHTML = '<div class="product-media"></div><div class="product-body"><span></span><span></span><span></span></div>';
    return card;
  });
}
