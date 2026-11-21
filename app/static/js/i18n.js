// ru/en dictionaries and helpers (spec section 3).
import { EXTRA } from "./locales.js";
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
    "cart.title": "Корзина",
    "cart.items": "Товаров",
    "cart.total": "Итого",
    "cart.checkout": "Оформить заказ",
    "cart.remove": "Удалить",
    "cart.empty": "Корзина пока пуста",
    "cart.unavailable": "Товар недоступен — удалите его из корзины",
    "cart.only_left": "Осталось только",
    "cart.invalid_items": "Некоторые товары недоступны или их больше, чем на складе. Измените их, чтобы продолжить.",
    "checkout.title": "Данные для доставки",
    "checkout.name": "Имя получателя",
    "checkout.address": "Адрес доставки",
    "checkout.comment": "Комментарий к заказу",
    "checkout.payment": "Способ оплаты",
    "checkout.cod": "Оплата при получении",
    "checkout.back": "Назад в корзину",
    "checkout.place_order": "Подтвердить заказ",
    "checkout.success_title": "Спасибо! Заказ оформлен",
    "checkout.order_number": "Номер заказа",
    "checkout.continue": "Продолжить покупки",
    "catalog.filters": "Фильтры",
    "catalog.category": "Категория",
    "catalog.all_categories": "Все категории",
    "catalog.min_price": "Цена от",
    "catalog.max_price": "Цена до",
    "catalog.sort": "Сортировка",
    "catalog.sort_newest": "Сначала новые",
    "catalog.sort_popular": "Популярные",
    "catalog.sort_price_asc": "Сначала дешевле",
    "catalog.sort_price_desc": "Сначала дороже",
    "catalog.price_error": "Минимальная цена не может быть больше максимальной",
    "catalog.reset": "Сбросить",
    "catalog.apply": "Применить",
    "catalog.found": "Найдено товаров",
    "catalog.nothing_found": "Ничего не найдено. Попробуйте изменить запрос или фильтры.",
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
    "cart.title": "Shopping cart",
    "cart.items": "Items",
    "cart.total": "Total",
    "cart.checkout": "Checkout",
    "cart.remove": "Remove",
    "cart.empty": "Your cart is empty",
    "cart.unavailable": "Unavailable — please remove it from the cart",
    "cart.only_left": "Only left:",
    "cart.invalid_items": "Some items are unavailable or exceed stock. Update them to continue.",
    "checkout.title": "Delivery details",
    "checkout.name": "Recipient name",
    "checkout.address": "Delivery address",
    "checkout.comment": "Comment to the order",
    "checkout.payment": "Payment method",
    "checkout.cod": "Cash on delivery",
    "checkout.back": "Back to cart",
    "checkout.place_order": "Place order",
    "checkout.success_title": "Thank you! Your order is placed",
    "checkout.order_number": "Order number",
    "checkout.continue": "Continue shopping",
    "catalog.filters": "Filters",
    "catalog.category": "Category",
    "catalog.all_categories": "All categories",
    "catalog.min_price": "Min price",
    "catalog.max_price": "Max price",
    "catalog.sort": "Sort",
    "catalog.sort_newest": "Newest first",
    "catalog.sort_popular": "Popular",
    "catalog.sort_price_asc": "Price: low to high",
    "catalog.sort_price_desc": "Price: high to low",
    "catalog.price_error": "Min price cannot be greater than max price",
    "catalog.reset": "Reset",
    "catalog.apply": "Apply",
    "catalog.found": "Products found",
    "catalog.nothing_found": "Nothing found. Try another query or filters.",
  },
};

Object.assign(DICT.ru, EXTRA.ru);
Object.assign(DICT.en, EXTRA.en);

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
  "You are already a seller": "Вы уже продавец",
  "You are already a courier": "Вы уже курьер",
  "You already have a pending application": "У вас уже есть заявка на рассмотрении",
  "Application already reviewed": "Заявка уже рассмотрена",
  "Category does not exist": "Категория не найдена",
  "Category name already exists": "Категория с таким названием уже есть",
  "Category contains products": "В категории есть товары — её нельзя удалить",
  "Courier not found or inactive": "Курьер не найден или заблокирован",
  "Courier can only be assigned to confirmed or processing orders": "Курьера можно назначить только на подтверждённый заказ или заказ в обработке",
  "Delivery has already started": "Доставка уже началась",
  "Delivery is managed by the assigned courier": "Статусом доставки управляет назначенный курьер",
  "You cannot block yourself": "Нельзя заблокировать самого себя",
  "Image must be smaller than 5 MB": "Изображение должно быть меньше 5 МБ",
  "File is not a valid JPEG, PNG or WEBP image": "Файл не является изображением JPEG, PNG или WEBP",
  "Only JPEG, PNG and WEBP images are allowed": "Разрешены только JPEG, PNG и WEBP",
};
const API_ERROR_PATTERNS_RU = [
  [/^Only (\d+) items available$/, (m) => `Доступно только ${m[1]} шт.`],
  [/^Not enough stock for '(.+)'$/, (m) => `Недостаточно товара «${m[1]}» на складе`],
  [/^Product '(.+)' is no longer available$/, (m) => `Товар «${m[1]}» больше недоступен`],
  [/^Cannot change status from '(.+)' to '(.+)'$/, (m) => `Нельзя сменить статус «${DICT.ru[`order.status.${m[1]}`] ?? m[1]}» на «${DICT.ru[`order.status.${m[2]}`] ?? m[2]}»`],
  [/^Cannot change delivery status from '(.+)' to '(.+)'$/, (m) => `Нельзя сменить статус доставки «${m[1]}» на «${m[2]}»`],
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

/** t("seller.delete_confirm", { name }) replaces {name} placeholders. */
export function t(key, params) {
  const text = DICT[getLang()][key] ?? DICT.en[key] ?? key;
  return params ? text.replace(/\{(\w+)\}/g, (_, name) => String(params[name] ?? "")) : text;
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
