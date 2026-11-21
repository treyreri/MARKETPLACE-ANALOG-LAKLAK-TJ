// Catalog / search (spec 5.2): query, category, price range, sort, pagination. State lives in the URL.
import { api } from "./api.js";
import { productCard, skeletonCards } from "./components.js";
import { t } from "./i18n.js";
import { emptyState } from "./unicorn.js";

const PAGE_SIZE = 12;
const SORTS = ["newest", "popular", "price_asc", "price_desc"];

const root = document.querySelector("[data-catalog]");
const searchForm = root.querySelector(".catalog-search");
const filtersForm = root.querySelector(".filters-form");
const results = root.querySelector("[data-results]");
const pagination = root.querySelector("[data-pagination]");
const countLabel = root.querySelector('[data-field="count"]');
const headerSearch = document.querySelector(".header-search input");

function readState() {
  const params = new URLSearchParams(window.location.search);
  const sort = params.get("sort");
  return {
    q: params.get("q") || "",
    category_id: params.get("category_id") || "",
    min_price: params.get("min_price") || "",
    max_price: params.get("max_price") || "",
    sort: SORTS.includes(sort) ? sort : "newest",
    page: Math.max(1, Number.parseInt(params.get("page"), 10) || 1),
  };
}

function writeState(state, { push = true } = {}) {
  const params = new URLSearchParams();
  Object.entries(state).forEach(([key, value]) => {
    if (value && !(key === "sort" && value === "newest") && !(key === "page" && value === 1)) params.set(key, value);
  });
  const url = `${window.location.pathname}${params.size ? `?${params}` : ""}`;
  if (push) window.history.pushState(null, "", url);
  else window.history.replaceState(null, "", url);
}

function fillForms(state) {
  searchForm.q.value = state.q;
  if (headerSearch) headerSearch.value = state.q;
  filtersForm.category_id.value = state.category_id;
  filtersForm.min_price.value = state.min_price;
  filtersForm.max_price.value = state.max_price;
  filtersForm.sort.value = state.sort;
}

function pageButton(label, page, { current = false, disabled = false } = {}) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `btn btn-sm ${current ? "btn-secondary" : "btn-ghost"}`;
  button.textContent = label;
  button.disabled = disabled;
  if (current) button.setAttribute("aria-current", "page");
  button.addEventListener("click", () => {
    const state = { ...readState(), page };
    writeState(state);
    load(state);
    root.scrollIntoView({ behavior: "smooth" });
  });
  return button;
}

function renderPagination(total, page) {
  const pages = Math.ceil(total / PAGE_SIZE);
  if (pages <= 1) {
    pagination.replaceChildren();
    return;
  }
  const buttons = [pageButton("←", page - 1, { disabled: page <= 1 })];
  const from = Math.max(1, page - 2);
  const to = Math.min(pages, page + 2);
  for (let p = from; p <= to; p += 1) buttons.push(pageButton(String(p), p, { current: p === page }));
  buttons.push(pageButton("→", page + 1, { disabled: page >= pages }));
  pagination.replaceChildren(...buttons);
}

let requestId = 0;
async function load(state) {
  const id = ++requestId;
  results.classList.remove("is-empty");
  results.replaceChildren(...skeletonCards(4));
  countLabel.textContent = t("common.loading");
  try {
    const data = await api("/products", {
      query: {
        q: state.q, category_id: state.category_id, min_price: state.min_price,
        max_price: state.max_price, sort: state.sort,
        limit: PAGE_SIZE, offset: (state.page - 1) * PAGE_SIZE,
      },
    });
    if (id !== requestId) return;  // a newer request superseded this one
    countLabel.textContent = `${t("catalog.found")}: ${data.total}`;
    if (!data.items.length) {
      results.classList.add("is-empty");
      results.replaceChildren(emptyState(t("catalog.nothing_found")));
    } else {
      results.replaceChildren(...data.items.map(productCard));
    }
    renderPagination(data.total, state.page);
  } catch (error) {
    if (id !== requestId) return;
    countLabel.textContent = "";
    results.classList.add("is-empty");
    results.replaceChildren(emptyState(error.message));
    pagination.replaceChildren();
  }
}

function apply(changes) {
  const state = { ...readState(), ...changes, page: 1 };
  const min = Number(state.min_price);
  const max = Number(state.max_price);
  const invalid = state.min_price !== "" && state.max_price !== "" && min > max;
  root.querySelector('[data-field="price-error"]').hidden = !invalid;
  if (invalid) return;
  writeState(state);
  fillForms(state);
  load(state);
}

async function loadCategories() {
  try {
    const categories = await api("/categories");
    const select = filtersForm.category_id;
    categories.forEach((category) => {
      select.append(new Option(category.name, String(category.id)));
    });
    select.value = readState().category_id;
    const current = categories.find((c) => String(c.id) === readState().category_id);
    if (current) document.title = `${current.name} — Treyreri Unicorn Store`;
  } catch { /* the filter just stays at "All categories" */ }
}

// The header search on this page filters in place instead of reloading
document.querySelector(".header-search")?.addEventListener("submit", (event) => {
  event.preventDefault();
  apply({ q: headerSearch.value.trim() });
});
searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  apply({ q: searchForm.q.value.trim() });
});
filtersForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(filtersForm));
  apply(data);
});
filtersForm.category_id.addEventListener("change", () => apply({ category_id: filtersForm.category_id.value }));
filtersForm.sort.addEventListener("change", () => apply({ sort: filtersForm.sort.value }));
root.querySelector('[data-action="reset"]').addEventListener("click", () => {
  apply({ category_id: "", min_price: "", max_price: "", sort: "newest" });
});
window.addEventListener("popstate", () => {
  const state = readState();
  fillForms(state);
  load(state);
});

if (window.matchMedia("(max-width: 860px)").matches) root.querySelector(".filters").open = false;
const initial = readState();
writeState(initial, { push: false });
fillForms(initial);
loadCategories();
load(initial);
