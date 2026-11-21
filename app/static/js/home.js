import { api } from "./api.js";
import { t } from "./i18n.js";
import { productCard, skeletonCards } from "./components.js";
import { emptyState } from "./unicorn.js";

const HOME_LIMIT = 8;

function errorBlock(message, retry) {
  const block = document.createElement("div");
  block.className = "error-state";
  const text = document.createElement("p");
  text.textContent = message;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "btn btn-ghost btn-sm";
  button.textContent = t("common.retry");
  button.addEventListener("click", retry);
  block.append(text, button);
  return block;
}

async function loadCategories() {
  const strip = document.querySelector("[data-categories]");
  strip.replaceChildren(...Array.from({ length: 6 }, () => {
    const chip = document.createElement("span");
    chip.className = "category-chip is-skeleton";
    return chip;
  }));
  try {
    const categories = await api("/categories");
    if (!categories.length) {
      strip.replaceChildren(emptyState(t("empty.categories")));
      return;
    }
    strip.replaceChildren(...categories.map((category) => {
      const chip = document.createElement("a");
      chip.className = "category-chip";
      chip.href = `/catalog?category_id=${category.id}`;
      chip.textContent = category.name;
      return chip;
    }));
  } catch (error) {
    strip.replaceChildren(errorBlock(error.message, loadCategories));
  }
}

async function loadProducts(grid) {
  const sort = grid.dataset.products;
  grid.replaceChildren(...skeletonCards(4));
  try {
    const { items } = await api("/products", { query: { sort, limit: HOME_LIMIT } });
    if (!items.length) {
      grid.replaceChildren(emptyState(t("empty.products")));
      grid.classList.add("is-empty");
      return;
    }
    grid.replaceChildren(...items.map(productCard));
  } catch (error) {
    grid.replaceChildren(errorBlock(error.message, () => loadProducts(grid)));
  }
}

loadCategories();
document.querySelectorAll("[data-products]").forEach(loadProducts);
