// Courier dashboard placeholder (full dashboard is stage 11).
import { t } from "../i18n.js";
import { currentUser } from "../layout.js";
import { h, loading, message, requireAuth } from "../ui.js";

const app = document.getElementById("app");
const kind = app.dataset.kind;
document.title = `${t(`${kind}.title`)} — Treyreri Unicorn Store`;

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  const me = await currentUser();
  if (!me.roles.includes(kind)) {
    window.location.replace(`/${kind}/login`);
    return;
  }
  app.replaceChildren(h("div", { class: "page-head" }, h("h1", { text: t(`${kind}.title`) })),
    message(t("soon.text"), h("a", { class: "btn btn-primary", href: "/account", text: t("nav.profile") })));
}

load();
