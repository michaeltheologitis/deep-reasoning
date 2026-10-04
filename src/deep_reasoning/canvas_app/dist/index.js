const _ = ["browse", "create", "namespaces", "tools"], k = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools"
}, L = {
  "--oh-surface": "#21252F",
  "--oh-surface-raised": "#2C313F",
  "--oh-surface-deep": "#05070A",
  "--oh-foreground": "#EEF2F7",
  "--oh-muted": "#A3B0C4",
  "--oh-text-secondary": "#C3CDDC",
  "--oh-text-dim": "#7E8A9E",
  "--oh-border": "#4B5468",
  "--oh-border-subtle": "#383F50",
  "--oh-border-input": "#4B5468",
  "--oh-color-primary": "#c9b974",
  "--oh-accent": "#c9b974",
  "--oh-accent-foreground": "#0B0E14",
  "--oh-danger": "#e76a5e",
  "--oh-success": "#a5e75e",
  "--oh-warning": "#c9b974",
  "--oh-interactive-hover": "#4B5468",
  "--oh-interactive-active": "#383F50",
  "--oh-focus": "#ffffff",
  "--oh-radius": "8px",
  "--oh-field-radius": "8px",
  "color-scheme": "dark",
  "font-family": '-apple-system, "SF Pro", BlinkMacSystemFont, "Segoe UI", "Roboto", "Ubuntu", sans-serif'
}, w = Object.keys(L), D = 200, p = "5", N = /^[#\w\s(),.%'"-]*$/;
function F(e) {
  return _.includes(e);
}
function O(e) {
  return e.length <= D && N.test(e) && !/url\(/i.test(e);
}
function I(e) {
  const t = {};
  for (const n of w) {
    const r = e[n];
    typeof r == "string" && r !== "" && O(r) && (t[n] = r);
  }
  return t;
}
function P(e) {
  const t = new URLSearchParams({ tab: e.tab });
  return e.parent && t.set("parent", e.parent), e.namespace && t.set("namespace", e.namespace), e.started && t.set("started", "1"), t.set("cap", e.cap), e.focus && t.set("focus", e.focus), Object.keys(e.theme).length > 0 && t.set("theme", JSON.stringify(e.theme)), `?${t.toString()}`;
}
function B(e) {
  if (!e || typeof e != "object") return !1;
  const t = e;
  return t.type === "dr-library/reload" ? Object.keys(t).length === 1 : t.type === "dr-library/select-tab" && F(t.tab) && (t.focus === null || typeof t.focus == "string");
}
const M = "Opening the Library…", g = "Starting the Library's backend…", f = (e) => `The Library's backend did not start: ${e}`, R = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", x = (e) => `This agent-server cannot run the Library's backend: ${e}`, U = "This version of Canvas cannot show an App's own pages. Update the app.", $ = "Try again", H = "it was still starting after 45 seconds.", T = "/api/canvas-extensions/installed/dr-library/backend", K = 500, A = 45e3;
async function V(e, t, n) {
  let r = Date.now() + A;
  const o = () => e({ path: T });
  let s;
  try {
    s = await o();
    let i = !1;
    for (; ; ) {
      if (t.throwIfAborted(), s.state === "ready") return { ok: !0 };
      if (s.state === "missing" || s.state === "unsupported")
        return {
          ok: !1,
          message: x(s.detail ?? s.state)
        };
      if (s.state === "starting") {
        if (n(g), Date.now() >= r)
          return { ok: !1, message: f(H) };
        await q(K, t), s = await o();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: f(s.detail ?? s.state)
        };
      if (s.revision === null || s.prepared_revision !== s.revision)
        return { ok: !1, message: R };
      n(g), i = !0, s = await e({
        method: "POST",
        path: `${T}/start`,
        body: { revision: s.revision }
      }).catch((u) => {
        if (j(u)) throw u;
        return r = Date.now() + A, o();
      });
    }
  } catch (i) {
    return t.throwIfAborted(), { ok: !1, message: f(G(i)) };
  }
}
function j(e) {
  return typeof e?.status == "number";
}
function G(e) {
  const t = e?.response;
  return typeof t?.detail == "string" ? t.detail : e instanceof Error ? e.message : String(e);
}
function q(e, t) {
  return new Promise((n, r) => {
    const o = setTimeout(() => {
      t.removeEventListener("abort", s), n();
    }, e), s = () => {
      clearTimeout(o), r(t.reason);
    };
    t.addEventListener("abort", s, { once: !0 });
  });
}
const W = "/api/agent-profiles/deep_reasoner", J = /^\d+(\.\d+)?$/, X = "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent";
async function Y(e, t) {
  if (t === null) return null;
  const n = `/api/conversations/${encodeURIComponent(t)}/events/search?kind=${X}&sort_order=TIMESTAMP_DESC&limit=1`;
  try {
    const o = (await e({ path: n })).items?.[0]?.config_options?.find(
      (s) => s.id === "namespace"
    );
    return typeof o?.current_value != "string" || !Array.isArray(o.options) ? null : {
      namespace: o.current_value,
      started: o.options.length === 1
    };
  } catch {
    return null;
  }
}
async function z(e) {
  try {
    const n = (await e({
      path: W
    })).profile?.acp_args;
    return Q(
      Array.isArray(n) ? n.filter((r) => typeof r == "string") : null
    );
  } catch {
    return p;
  }
}
function Q(e) {
  if (!e) return p;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((r) => r.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && J.test(n) ? n : p;
}
function Z(e) {
  const t = getComputedStyle(e);
  return I(
    Object.fromEntries(
      w.map((n) => [
        n,
        t.getPropertyValue(n).trim()
      ])
    )
  );
}
const h = /* @__PURE__ */ new Map();
function ee(e, t) {
  h.set(e, t);
}
function te(e) {
  const t = h.get(e) ?? null;
  return h.delete(e), t;
}
function l(e, t, n = !1, r) {
  const o = document.createElement("p");
  if (o.dataset.testid = n ? "dr-library-error" : "dr-library-loading", o.textContent = t, o.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(o), !r) return;
  const s = document.createElement("button");
  s.type = "button", s.dataset.testid = "dr-library-retry", s.textContent = $, s.style.cssText = "margin: 0 16px;", s.addEventListener("click", r), e.append(s);
}
function ne(e, t, n) {
  const { container: r } = n, o = new AbortController(), s = te(t);
  let i = null, u = !1;
  const m = (a) => {
    const c = r.querySelector("iframe");
    !c || a.source !== c.contentWindow || !B(a.data) || (a.data.type === "dr-library/reload" ? d() : n.surface.kind === "conversation-panel" && (ee(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  }, S = (a) => {
    a.reason !== "not-ready" || u || (u = !0, d());
  };
  function y() {
    window.removeEventListener("message", m), i?.(), i = null;
  }
  async function d() {
    y(), l(r, M);
    const a = e.agentServer.request, [c, b, E] = await Promise.all([
      V(
        a,
        o.signal,
        (C) => l(r, C)
      ),
      Y(a, n.conversationId),
      z(a)
    ]).catch(() => [null, null, null]);
    if (o.signal.aborted || c === null || E === null) return;
    if (!c.ok)
      return l(r, c.message, !0, () => {
        d();
      });
    if (!e.appBackend) return l(r, U, !0);
    const v = {
      tab: t,
      parent: window.location.origin,
      namespace: b?.namespace ?? null,
      started: b?.started ?? !1,
      cap: E,
      focus: s,
      theme: Z(r)
    };
    r.replaceChildren(), i = e.appBackend.mountFrame(r, {
      path: `/ui/${P(v)}`,
      title: k[t],
      onError: S
    }), window.addEventListener("message", m);
  }
  return d(), () => {
    o.abort(), y(), r.replaceChildren();
  };
}
function re(e) {
  const t = _.map(
    (n) => e.registerPage(n, (r) => ne(e, n, r))
  );
  return () => t.forEach((n) => n());
}
export {
  re as activate
};
