// Seller / Courier Login (spec section 17):
// approved -> dashboard, pending/rejected -> application status, no application -> form, guest -> login/register.
import { api, isAuthenticated } from "../api.js";
import { t } from "../i18n.js";
import { currentUser } from "../layout.js";
import { h, loading, message, unicornBlock } from "../ui.js";

const app = document.getElementById("app");
const kind = app.dataset.kind;
const here = `/${kind}/login`;
document.title = `${t(`rolelogin.${kind}_title`)} — Treyreri Unicorn Store`;

function guestCard() {
  const block = unicornBlock("empty",
    h("h1", { class: "h2", text: t(`rolelogin.${kind}_title`) }),
    h("p", { text: t("rolelogin.text") }),
    h("div", { class: "form-actions center" },
      h("a", { class: "btn btn-primary", href: `/login?next=${encodeURIComponent(here)}`, text: t("auth.login") }),
      h("a", { class: "btn btn-secondary", href: `/register?next=${encodeURIComponent(`/become-${kind}`)}`, text: t("auth.register") })));
  return h("div", { class: "auth-card" }, block);
}

async function route() {
  if (!isAuthenticated()) {
    app.replaceChildren(guestCard());
    return;
  }
  app.replaceChildren(loading());
  try {
    const me = await currentUser();
    if (me.roles.includes(kind)) {
      window.location.replace(`/dashboard/${kind}`);
      return;
    }
    try {
      await api(`/${kind}/applications/me`);
      window.location.replace(`/application/${kind}`);
    } catch (error) {
      if (error.status !== 404) throw error;
      window.location.replace(`/become-${kind}`);
    }
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

route();
