// About us, Contact, Terms: static RU/EN text from the dictionaries.
import { t } from "../i18n.js";
import { h, unicornBlock } from "../ui.js";

const app = document.getElementById("app");
const kind = app.dataset.kind;  // about | contact | terms
document.title = `${t(`static.${kind}.title`)} — Treyreri Unicorn Store`;

const paragraphs = t(`static.${kind}.body`).split("\n\n").map((text) => h("p", { text }));

const contacts = kind === "contact"
  ? h("dl", { class: "meta contact-list" },
    h("dt", { text: t("static.contact.email") }), h("dd", {}, h("a", { href: "mailto:support@treyreri.example", text: "support@treyreri.example" })),
    h("dt", { text: t("static.contact.phone") }), h("dd", {}, h("a", { href: "tel:+992900100000", text: "+992 900 10 00 00" })),
    h("dt", { text: t("static.contact.address") }), h("dd", { text: t("static.contact.address_value") }))
  : null;

app.replaceChildren(h("div", { class: "grid-2 static-page" },
  h("article", { class: "card prose" }, h("h1", { class: "h2", text: t(`static.${kind}.title`) }), paragraphs, contacts),
  kind === "about" ? unicornBlock("hero") : null));
