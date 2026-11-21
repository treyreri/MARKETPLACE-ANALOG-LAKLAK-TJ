// ru/en dictionaries and helpers (spec section 3).
const STORAGE_KEY = "pu_lang";
export const LANGUAGES = ["ru", "en"];

const DICT = {
  ru: {
    "a11y.skip": "Перейти к содержимому",
    "search.placeholder": "Поиск товаров...",
    "search.button": "Найти",
    "auth.login": "Войти",
    "auth.register": "Регистрация",
    "auth.logout": "Выйти",
    "nav.home": "Главная",
    "nav.categories": "Категории",
    "nav.cart": "Корзина",
    "nav.orders": "Мои заказы",
    "footer.tagline": "Маркетплейс для повседневной жизни",
    "footer.customer": "Покупателям",
    "footer.about": "О нас",
    "footer.contact": "Контакты",
    "footer.seller": "Продавцам",
    "footer.become_seller": "Стать продавцом",
    "footer.seller_login": "Вход для продавцов",
    "footer.courier": "Курьерам",
    "footer.become_courier": "Стать курьером",
    "footer.courier_login": "Вход для курьеров",
    "home.hero.title": "Добро пожаловать в Treyreri Unicorn Store",
    "home.hero.subtitle": "Товары для повседневной жизни от проверенных продавцов",
    "home.hero.cta": "Смотреть товары",
    "home.categories": "Категории",
    "home.popular": "Популярные товары",
    "home.new": "Новинки каталога",
    "home.see_all": "Смотреть все",
    "product.add_to_cart": "В корзину",
    "product.out_of_stock": "Нет в наличии",
    "product.seller": "Продавец",
    "product.no_image": "Нет фото",
    "toast.added_to_cart": "Товар добавлен в корзину",
    "common.loading": "Загрузка...",
    "common.retry": "Повторить",
    "empty.products": "Здесь пока нет товаров",
    "empty.categories": "Категории пока не добавлены",
    "error.generic": "Что-то пошло не так. Попробуйте ещё раз.",
    "error.network": "Нет соединения с сервером",
    "error.session_expired": "Сессия истекла, войдите снова",
    "auth.login_title": "Вход",
    "auth.register_title": "Регистрация",
    "auth.no_account": "Ещё нет аккаунта?",
    "auth.have_account": "Уже есть аккаунт?",
    "form.phone": "Номер телефона",
    "form.password": "Пароль",
    "form.password_confirm": "Подтверждение пароля",
    "form.password_hint": "Не менее 6 символов",
    "form.first_name_optional": "Имя (необязательно)",
    "form.last_name_optional": "Фамилия (необязательно)",
    "form.error_phone": "Введите номер в формате +992XXXXXXXXX",
    "form.error_password_short": "Пароль должен быть не короче 6 символов",
    "form.error_password_mismatch": "Пароли не совпадают",
    "form.error_required": "Заполните это поле",
    "soon.title": "Скоро здесь что-то появится",
    "soon.text": "Эта страница ещё в разработке.",
    "soon.home": "На главную",
    "product.brand": "Бренд",
    "product.stock": "В наличии",
    "product.pcs": "шт.",
    "product.quantity": "Количество",
    "product.buy_now": "Купить",
    "product.description": "Описание",
    "product.not_found": "Товар не найден или больше не продаётся",
  },
  en: {
    "a11y.skip": "Skip to content",
    "search.placeholder": "Search products...",
    "search.button": "Search",
    "auth.login": "Login",
    "auth.register": "Register",
    "auth.logout": "Logout",
    "nav.home": "Home",
    "nav.categories": "Categories",
    "nav.cart": "Cart",
    "nav.orders": "My orders",
    "footer.tagline": "Marketplace for everyday life",
    "footer.customer": "Customer",
    "footer.about": "About us",
    "footer.contact": "Contact",
    "footer.seller": "Seller",
    "footer.become_seller": "Become a Seller",
    "footer.seller_login": "Seller Login",
    "footer.courier": "Courier",
    "footer.become_courier": "Become a Courier",
    "footer.courier_login": "Courier Login",
    "home.hero.title": "Welcome to Treyreri Unicorn Store",
    "home.hero.subtitle": "Discover products for your everyday life",
    "home.hero.cta": "Explore Products",
    "home.categories": "Categories",
    "home.popular": "Popular Products",
    "home.new": "New Products",
    "home.see_all": "See all",
    "product.add_to_cart": "Add to cart",
    "product.out_of_stock": "Out of stock",
    "product.seller": "Seller",
    "product.no_image": "No photo",
    "toast.added_to_cart": "Added to cart",
    "common.loading": "Loading...",
    "common.retry": "Retry",
    "empty.products": "No products here yet",
    "empty.categories": "No categories yet",
    "error.generic": "Something went wrong. Please try again.",
    "error.network": "Cannot reach the server",
    "error.session_expired": "Session expired, please log in again",
    "auth.login_title": "Log in",
    "auth.register_title": "Create an account",
    "auth.no_account": "No account yet?",
    "auth.have_account": "Already have an account?",
    "form.phone": "Phone number",
    "form.password": "Password",
    "form.password_confirm": "Confirm password",
    "form.password_hint": "At least 6 characters",
    "form.first_name_optional": "First name (optional)",
    "form.last_name_optional": "Last name (optional)",
    "form.error_phone": "Enter the number as +992XXXXXXXXX",
    "form.error_password_short": "Password must be at least 6 characters",
    "form.error_password_mismatch": "Passwords do not match",
    "form.error_required": "This field is required",
    "soon.title": "Coming soon",
    "soon.text": "This page is still being built.",
    "soon.home": "Back to home",
    "product.brand": "Brand",
    "product.stock": "In stock",
    "product.pcs": "pcs",
    "product.quantity": "Quantity",
    "product.buy_now": "Buy now",
    "product.description": "Description",
    "product.not_found": "Product not found or no longer available",
  },
};

// Known API error messages (English in the backend) -> Russian
const API_ERRORS_RU = {
  "could not validate credentials": "Требуется вход в аккаунт",
  "invalid phone number or password": "Неверный номер телефона или пароль",
  "account is blocked": "Аккаунт заблокирован",
  "phone number is already registered": "Этот номер уже зарегистрирован",
  "not enough permissions": "Недостаточно прав",
  "Product not found or unavailable": "Товар не найден или недоступен",
  "You cannot buy your own product": "Нельзя купить собственный товар",
  "Cart is empty": "Корзина пуста",
  "Cart item not found": "Позиция корзины не найдена",
  "Only pending orders can be cancelled": "Отменить можно только заказ в статусе «Ожидает»",
};
const API_ERROR_PATTERNS_RU = [
  [/^Only (\d+) items available$/, (m) => `Доступно только ${m[1]} шт.`],
  [/^Not enough stock for '(.+)'$/, (m) => `Недостаточно товара «${m[1]}» на складе`],
  [/^Product '(.+)' is no longer available$/, (m) => `Товар «${m[1]}» больше недоступен`],
];

export function getLang() {
  try {
    const lang = localStorage.getItem(STORAGE_KEY);
    return LANGUAGES.includes(lang) ? lang : "ru";
  } catch {
    return "ru";
  }
}

export function hasChosenLang() {
  try {
    return LANGUAGES.includes(localStorage.getItem(STORAGE_KEY));
  } catch {
    return true; // storage blocked: don't nag on every page
  }
}

export function setLang(lang) {
  if (!LANGUAGES.includes(lang)) return;
  try { localStorage.setItem(STORAGE_KEY, lang); } catch { /* ignore */ }
  document.documentElement.lang = lang;
}

export function t(key) {
  return DICT[getLang()][key] ?? DICT.en[key] ?? key;
}

export function translateApiError(message) {
  if (!message) return t("error.generic");
  if (getLang() !== "ru") return message;
  if (API_ERRORS_RU[message]) return API_ERRORS_RU[message];
  for (const [pattern, build] of API_ERROR_PATTERNS_RU) {
    const match = message.match(pattern);
    if (match) return build(match);
  }
  return message;
}

/** Fill [data-i18n], [data-i18n-placeholder] and [data-i18n-aria] in root. */
export function applyTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  root.querySelectorAll("[data-i18n-aria]").forEach((el) => { el.setAttribute("aria-label", t(el.dataset.i18nAria)); });
}

export function formatPrice(value) {
  const number = Number(value);
  const formatted = new Intl.NumberFormat(getLang() === "ru" ? "ru-RU" : "en-US", {
    minimumFractionDigits: Number.isInteger(number) ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(number);
  return `${formatted} TJS`;
}
