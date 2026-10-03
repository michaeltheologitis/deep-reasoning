const w = ["browse", "create", "namespaces", "tools"], L = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools"
}, v = [
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
], C = 200, p = "5", D = /^[#\w\s(),.%'"-]*$/;
function N(e) {
  return w.includes(e);
}
function P(e) {
  return e.length <= C && D.test(e) && !/url\(/i.test(e);
}
function I(e) {
  const t = {};
  for (const n of v) {
    const r = e[n];
    typeof r == "string" && r !== "" && P(r) && (t[n] = r);
  }
  return t;
}
function O(e) {
  const t = new URLSearchParams({ tab: e.tab });
  return e.parent && t.set("parent", e.parent), e.namespace && t.set("namespace", e.namespace), e.started && t.set("started", "1"), t.set("cap", e.cap), e.focus && t.set("focus", e.focus), Object.keys(e.theme).length > 0 && t.set("theme", JSON.stringify(e.theme)), `?${t.toString()}`;
}
function M(e) {
  if (!e || typeof e != "object") return !1;
  const t = e;
  return t.type === "dr-library/reload" ? Object.keys(t).length === 1 : t.type === "dr-library/select-tab" && N(t.tab) && (t.focus === null || typeof t.focus == "string");
}
const F = "Opening the Library…", T = "Starting the Library's backend…", f = (e) => `The Library's backend did not start: ${e}`, R = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", B = (e) => `This agent-server cannot run the Library's backend: ${e}`, x = "This version of Canvas cannot show an App's own pages. Update the app.", U = "Try again", $ = "it was still starting after 45 seconds.", E = "/api/canvas-extensions/installed/dr-library/backend", H = 500, A = 45e3;
async function K(e, t, n) {
  let r = Date.now() + A;
  const o = () => e({ path: E });
  let s;
  try {
    s = await o();
    let i = !1;
    for (; ; ) {
      if (t.throwIfAborted(), s.state === "ready") return { ok: !0 };
      if (s.state === "missing" || s.state === "unsupported")
        return {
          ok: !1,
          message: B(s.detail ?? s.state)
        };
      if (s.state === "starting") {
        if (n(T), Date.now() >= r)
          return { ok: !1, message: f($) };
        await j(H, t), s = await o();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: f(s.detail ?? s.state)
        };
      if (s.revision === null || s.prepared_revision !== s.revision)
        return { ok: !1, message: R };
      n(T), i = !0, s = await e({
        method: "POST",
        path: `${E}/start`,
        body: { revision: s.revision }
      }).catch((u) => {
        if (G(u)) throw u;
        return r = Date.now() + A, o();
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
  return new Promise((n, r) => {
    const o = setTimeout(() => {
      t.removeEventListener("abort", s), n();
    }, e), s = () => {
      clearTimeout(o), r(t.reason);
    };
    t.addEventListener("abort", s, { once: !0 });
  });
}
const q = "/api/agent-profiles/deep_reasoner", W = /^\d+(\.\d+)?$/;
async function J(e, t) {
  if (t === null) return null;
  const n = `/api/conversations/${encodeURIComponent(t)}/events/search?kind=ACPSessionControlsEvent&sort_order=TIMESTAMP_DESC&limit=1`;
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
async function X(e) {
  try {
    const n = (await e({
      path: q
    })).profile?.acp_args;
    return Y(
      Array.isArray(n) ? n.filter((r) => typeof r == "string") : null
    );
  } catch {
    return p;
  }
}
function Y(e) {
  if (!e) return p;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((r) => r.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && W.test(n) ? n : p;
}
function z(e) {
  const t = getComputedStyle(e);
  return I(
    Object.fromEntries(
      v.map((n) => [
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
function l(e, t, n = !1, r) {
  const o = document.createElement("p");
  if (o.dataset.testid = n ? "dr-library-error" : "dr-library-loading", o.textContent = t, o.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(o), !r) return;
  const s = document.createElement("button");
  s.type = "button", s.dataset.testid = "dr-library-retry", s.textContent = U, s.style.cssText = "margin: 0 16px;", s.addEventListener("click", r), e.append(s);
}
function ee(e, t, n) {
  const { container: r } = n, o = new AbortController(), s = Z(t);
  let i = null, u = !1;
  const m = (a) => {
    const c = r.querySelector("iframe");
    !c || a.source !== c.contentWindow || !M(a.data) || (a.data.type === "dr-library/reload" ? d() : n.surface.kind === "conversation-panel" && (Q(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  }, _ = (a) => {
    a.reason !== "not-ready" || u || (u = !0, d());
  };
  function y() {
    window.removeEventListener("message", m), i?.(), i = null;
  }
  async function d() {
    y(), l(r, F);
    const a = e.agentServer.request, [c, g, b] = await Promise.all([
      K(
        a,
        o.signal,
        (k) => l(r, k)
      ),
      J(a, n.conversationId),
      X(a)
    ]).catch(() => [null, null, null]);
    if (o.signal.aborted || c === null || b === null) return;
    if (!c.ok)
      return l(r, c.message, !0, () => {
        d();
      });
    if (!e.appBackend) return l(r, x, !0);
    const S = {
      tab: t,
      parent: window.location.origin,
      namespace: g?.namespace ?? null,
      started: g?.started ?? !1,
      cap: b,
      focus: s,
      theme: z(r)
    };
    r.replaceChildren(), i = e.appBackend.mountFrame(r, {
      path: `/ui/${O(S)}`,
      title: L[t],
      onError: _
    }), window.addEventListener("message", m);
  }
  return d(), () => {
    o.abort(), y(), r.replaceChildren();
  };
}
function te(e) {
  const t = w.map(
    (n) => e.registerPage(n, (r) => ee(e, n, r))
  );
  return () => t.forEach((n) => n());
}
export {
  te as activate
};
