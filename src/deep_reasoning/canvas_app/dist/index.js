const A = ["browse", "create", "namespaces", "tools"], k = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools"
}, w = [
  "--oh-surface",
  "--oh-surface-raised",
  "--oh-surface-deep",
  "--oh-foreground",
  "--oh-muted",
  "--oh-text-secondary",
  "--oh-text-dim",
  "--oh-border",
  "--oh-border-subtle",
  "--oh-border-input",
  "--oh-color-primary",
  "--oh-accent",
  "--oh-accent-foreground",
  "--oh-danger",
  "--oh-success",
  "--oh-warning",
  "--oh-interactive-hover",
  "--oh-interactive-active",
  "--oh-focus",
  "--oh-radius",
  "--oh-field-radius",
  "color-scheme",
  "font-family"
], L = 200, p = "5", C = /^[#\w\s(),.%'"-]*$/;
function N(e) {
  return A.includes(e);
}
function D(e) {
  return e.length <= L && C.test(e) && !/url\(/i.test(e);
}
function P(e) {
  const t = {};
  for (const n of w) {
    const s = e[n];
    typeof s == "string" && s !== "" && D(s) && (t[n] = s);
  }
  return t;
}
function I(e) {
  const t = new URLSearchParams({ tab: e.tab });
  return e.parent && t.set("parent", e.parent), e.namespace && t.set("namespace", e.namespace), e.started && t.set("started", "1"), t.set("cap", e.cap), e.focus && t.set("focus", e.focus), Object.keys(e.theme).length > 0 && t.set("theme", JSON.stringify(e.theme)), `?${t.toString()}`;
}
function O(e) {
  if (!e || typeof e != "object") return !1;
  const t = e;
  return t.type === "dr-library/reload" ? Object.keys(t).length === 1 : t.type === "dr-library/select-tab" && N(t.tab) && (t.focus === null || typeof t.focus == "string");
}
const M = "Opening the Library…", T = "Starting the Library's backend…", f = (e) => `The Library's backend did not start: ${e}`, F = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", R = (e) => `This agent-server cannot run the Library's backend: ${e}`, B = "This version of Canvas cannot show an App's own pages. Update the app.", x = "Try again", U = "it was still starting after 45 seconds.", E = "/api/canvas-extensions/installed/dr-library/backend", $ = 500, H = 45e3;
async function K(e, t, n) {
  const s = Date.now() + H, o = () => e({ path: E });
  let r;
  try {
    r = await o();
    let i = !1;
    for (; ; ) {
      if (t.throwIfAborted(), r.state === "ready") return { ok: !0 };
      if (r.state === "missing" || r.state === "unsupported")
        return {
          ok: !1,
          message: R(r.detail ?? r.state)
        };
      if (r.state === "starting") {
        if (n(T), Date.now() >= s)
          return { ok: !1, message: f(U) };
        await j($, t), r = await o();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: f(r.detail ?? r.state)
        };
      if (r.revision === null || r.prepared_revision !== r.revision)
        return { ok: !1, message: F };
      n(T), i = !0, r = await e({
        method: "POST",
        path: `${E}/start`,
        body: { revision: r.revision }
      }).catch((u) => {
        if (G(u)) throw u;
        return o();
      });
    }
  } catch (i) {
    return t.throwIfAborted(), { ok: !1, message: f(V(i)) };
  }
}
function G(e) {
  return typeof e?.status == "number";
}
function V(e) {
  const t = e?.response;
  return typeof t?.detail == "string" ? t.detail : e instanceof Error ? e.message : String(e);
}
function j(e, t) {
  return new Promise((n, s) => {
    const o = setTimeout(() => {
      t.removeEventListener("abort", r), n();
    }, e), r = () => {
      clearTimeout(o), s(t.reason);
    };
    t.addEventListener("abort", r, { once: !0 });
  });
}
const q = "/api/agent-profiles/deep_reasoner", W = /^\d+(\.\d+)?$/;
async function J(e, t) {
  if (t === null) return null;
  const n = `/api/conversations/${encodeURIComponent(t)}/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`;
  try {
    const o = (await e({ path: n })).items?.[0]?.config_options?.find(
      (r) => r.id === "namespace"
    );
    return typeof o?.current_value != "string" || !Array.isArray(o.options) ? null : {
      namespace: o.current_value,
      started: o.options.length === 1
    };
  } catch {
    return null;
  }
}
async function X(e) {
  try {
    const n = (await e({
      path: q
    })).profile?.acp_args;
    return Y(
      Array.isArray(n) ? n.filter((s) => typeof s == "string") : null
    );
  } catch {
    return p;
  }
}
function Y(e) {
  if (!e) return p;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((s) => s.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && W.test(n) ? n : p;
}
function z(e) {
  const t = getComputedStyle(e);
  return P(
    Object.fromEntries(
      w.map((n) => [
        n,
        t.getPropertyValue(n).trim()
      ])
    )
  );
}
const h = /* @__PURE__ */ new Map();
function Q(e, t) {
  h.set(e, t);
}
function Z(e) {
  const t = h.get(e) ?? null;
  return h.delete(e), t;
}
function l(e, t, n = !1, s) {
  const o = document.createElement("p");
  if (o.dataset.testid = n ? "dr-library-error" : "dr-library-loading", o.textContent = t, o.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(o), !s) return;
  const r = document.createElement("button");
  r.type = "button", r.dataset.testid = "dr-library-retry", r.textContent = x, r.style.cssText = "margin: 0 16px;", r.addEventListener("click", s), e.append(r);
}
function ee(e, t, n) {
  const { container: s } = n, o = new AbortController(), r = Z(t);
  let i = null, u = !1;
  const m = (a) => {
    const c = s.querySelector("iframe");
    !c || a.source !== c.contentWindow || !O(a.data) || (a.data.type === "dr-library/reload" ? d() : n.surface.kind === "conversation-panel" && (Q(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  }, v = (a) => {
    a.reason !== "not-ready" || u || (u = !0, d());
  };
  function y() {
    window.removeEventListener("message", m), i?.(), i = null;
  }
  async function d() {
    y(), l(s, M);
    const a = e.agentServer.request, [c, g, b] = await Promise.all([
      K(
        a,
        o.signal,
        (S) => l(s, S)
      ),
      J(a, n.conversationId),
      X(a)
    ]).catch(() => [null, null, null]);
    if (o.signal.aborted || c === null || b === null) return;
    if (!c.ok)
      return l(s, c.message, !0, () => {
        d();
      });
    if (!e.appBackend) return l(s, B, !0);
    const _ = {
      tab: t,
      parent: window.location.origin,
      namespace: g?.namespace ?? null,
      started: g?.started ?? !1,
      cap: b,
      focus: r,
      theme: z(s)
    };
    s.replaceChildren(), i = e.appBackend.mountFrame(s, {
      path: `/ui/${I(_)}`,
      title: k[t],
      onError: v
    }), window.addEventListener("message", m);
  }
  return d(), () => {
    o.abort(), y(), s.replaceChildren();
  };
}
function te(e) {
  const t = A.map(
    (n) => e.registerPage(n, (s) => ee(e, n, s))
  );
  return () => t.forEach((n) => n());
}
export {
  te as activate
};
