// Application status: pending / rejected (with admin comment, apply again) / approved.
import { api } from "../api.js";
import { t } from "../i18n.js";
import { currentUser } from "../layout.js";
import { formatDate, h, loading, message, requireAuth, statusChip, unicornBlock } from "../ui.js";

const app = document.getElementById("app");
const kind = app.dataset.kind;
document.title = `${t(`appstatus.${kind}`)} — Treyreri Unicorn Store`;

function details(application) {
  const rows = kind === "seller"
    ? [[t("apply.store_name"), application.store_name], [t("form.address"), application.address]]
    : [[t("apply.transport"), t(`transport.${application.transport_type}`)], [t("form.address"), application.address]];
  return h("dl", { class: "meta" },
    rows.map(([label, value]) => [h("dt", { text: label }), h("dd", { text: value })]),
    h("dt", { text: t("appstatus.submitted_at") }), h("dd", { text: formatDate(application.created_at) }),
    application.reviewed_at
      ? [h("dt", { text: t("appstatus.reviewed_at") }), h("dd", { text: formatDate(application.reviewed_at) })]
      : null);
}

async function load() {
  if (!requireAuth()) return;
  app.replaceChildren(loading());
  try {
    const me = await currentUser();
    let application = null;
    try {
      application = await api(`/${kind}/applications/me`);
    } catch (error) {
      if (error.status !== 404) throw error;
    }

    const head = h("div", { class: "page-head" }, h("h1", { text: t(`appstatus.${kind}`) }));
    if (!application) {
      app.replaceChildren(head, message(t("appstatus.none"),
        h("a", { class: "btn btn-primary", href: `/become-${kind}`, text: t("appstatus.apply") })));
      return;
    }

    const approved = application.status === "approved" && me.roles.includes(kind);
    const text = approved ? t("appstatus.approved_text") : t(`appstatus.${application.status}_text`);
    const block = unicornBlock("empty",
      statusChip("application.status", application.status),
      h("p", { class: "lead", text }),
      application.admin_comment
        ? h("blockquote", { class: "admin-comment" },
          h("strong", { text: `${t("appstatus.admin_comment")}: ` }), application.admin_comment)
        : null,
      h("div", { class: "form-actions center" },
        approved ? h("a", { class: "btn btn-primary", href: `/dashboard/${kind}`, text: t("apply.go_dashboard") }) : null,
        application.status === "rejected"
          ? h("a", { class: "btn btn-primary", href: `/become-${kind}`, text: t("appstatus.apply_again") }) : null));
    app.replaceChildren(head, h("div", { class: "grid-2" }, h("section", { class: "card" }, block),
      h("section", { class: "card" }, details(application))));
  } catch (error) {
    app.replaceChildren(message(error.message));
  }
}

load();
