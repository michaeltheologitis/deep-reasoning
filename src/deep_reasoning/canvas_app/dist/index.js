const w = ["browse", "create", "namespaces", "tools"], D = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools"
}, F = {
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
}, v = Object.keys(F), P = 200, h = "5", I = /^[#\w\s(),.%'"-]*$/;
function M(e) {
  return w.includes(e);
}
function B(e) {
  return e.length <= P && I.test(e) && !/url\(/i.test(e);
}
function R(e) {
  const t = {};
  for (const n of v) {
    const s = e[n];
    typeof s == "string" && s !== "" && B(s) && (t[n] = s);
  }
  return t;
}
function x(e) {
  const t = new URLSearchParams({ tab: e.tab });
  return e.parent && t.set("parent", e.parent), e.namespace && t.set("namespace", e.namespace), e.started && t.set("started", "1"), t.set("cap", e.cap), e.focus && t.set("focus", e.focus), Object.keys(e.theme).length > 0 && t.set("theme", JSON.stringify(e.theme)), e.mcp !== null && t.set("mcp", JSON.stringify(e.mcp)), `?${t.toString()}`;
}
function U(e) {
  if (!e || typeof e != "object") return !1;
  const t = e;
  return t.type === "dr-library/reload" ? Object.keys(t).length === 1 : t.type === "dr-library/select-tab" && M(t.tab) && (t.focus === null || typeof t.focus == "string");
}
const j = "Opening the Library…", T = "Starting the Library's backend…", p = (e) => `The Library's backend did not start: ${e}`, H = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", $ = (e) => `This agent-server cannot run the Library's backend: ${e}`, K = "This version of Canvas cannot show an App's own pages. Update the app.", G = "Try again", V = "it was still starting after 45 seconds.", _ = "/api/canvas-extensions/installed/dr-library/backend", z = 500, S = 45e3;
async function J(e, t, n) {
  let s = Date.now() + S;
  const o = () => e({ path: _ });
  let r;
  try {
    r = await o();
    let i = !1;
    for (; ; ) {
      if (t.throwIfAborted(), r.state === "ready") return { ok: !0 };
      if (r.state === "missing" || r.state === "unsupported")
        return {
          ok: !1,
          message: $(r.detail ?? r.state)
        };
      if (r.state === "starting") {
        if (n(T), Date.now() >= s)
          return { ok: !1, message: p(V) };
        await X(z, t), r = await o();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: p(r.detail ?? r.state)
        };
      if (r.revision === null || r.prepared_revision !== r.revision)
        return { ok: !1, message: H };
      n(T), i = !0, r = await e({
        method: "POST",
        path: `${_}/start`,
        body: { revision: r.revision }
      }).catch((c) => {
        if (W(c)) throw c;
        return s = Date.now() + S, o();
      });
    }
  } catch (i) {
    return t.throwIfAborted(), { ok: !1, message: p(q(i)) };
  }
}
function W(e) {
  return typeof e?.status == "number";
}
function q(e) {
  const t = e?.response;
  return typeof t?.detail == "string" ? t.detail : e instanceof Error ? e.message : String(e);
}
function X(e, t) {
  return new Promise((n, s) => {
    const o = setTimeout(() => {
      t.removeEventListener("abort", r), n();
    }, e), r = () => {
      clearTimeout(o), s(t.reason);
    };
    t.addEventListener("abort", r, { once: !0 });
  });
}
const k = "/api/agent-profiles/deep_reasoner", Y = "/api/settings", Q = /^\d+(\.\d+)?$/, Z = "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent";
async function ee(e, t) {
  if (t === null) return null;
  const n = `/api/conversations/${encodeURIComponent(t)}/events/search?kind=${Z}&sort_order=TIMESTAMP_DESC&limit=1`;
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
async function te(e) {
  try {
    const n = (await e({
      path: k
    })).profile?.acp_args;
    return ne(
      Array.isArray(n) ? n.filter((s) => typeof s == "string") : null
    );
  } catch {
    return h;
  }
}
function ne(e) {
  if (!e) return h;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((s) => s.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && Q.test(n) ? n : h;
}
function re(e) {
  const t = getComputedStyle(e);
  return R(
    Object.fromEntries(
      v.map((n) => [
        n,
        t.getPropertyValue(n).trim()
      ])
    )
  );
}
const l = (e) => typeof e == "object" && e !== null && !Array.isArray(e), m = (e) => typeof e == "string" && e !== "";
function se(e) {
  return m(e.command) ? "stdio" : m(e.url) ? e.transport === "sse" ? "sse" : "http" : null;
}
function oe(e) {
  if (!l(e)) return [];
  switch (e.strategy) {
    case "bearer":
    case "basic":
      return ["Authorization"];
    case "api_key":
      return [m(e.header_name) ? e.header_name : "Authorization"];
    case "header":
      return l(e.headers) ? Object.keys(e.headers) : [];
    default:
      return [];
  }
}
function ae(e, t) {
  return Object.entries(e).flatMap(([n, s]) => {
    const o = l(s) ? s : {}, r = se(o);
    if (r === null) return [];
    const i = o.enabled === !1 ? "disabled" : t !== null && !t.includes(n) ? "not_in_profile" : null;
    return [
      {
        name: n,
        transport: r,
        command: r === "stdio" ? o.command : null,
        args: Array.isArray(o.args) ? o.args.filter((c) => typeof c == "string") : [],
        url: r === "stdio" ? null : o.url,
        env: l(o.env) ? Object.keys(o.env) : [],
        headers: [
          .../* @__PURE__ */ new Set([
            ...l(o.headers) ? Object.keys(o.headers) : [],
            ...oe(o.auth)
          ])
        ],
        forwarded: i === null,
        why_not: i
      }
    ];
  });
}
async function ie(e) {
  try {
    const [t, n] = await Promise.all([
      e({
        path: Y
      }),
      e({
        path: k
      })
    ]), s = t.agent_settings?.mcp_config, o = n.profile?.mcp_server_refs;
    return ae(
      l(s) ? s : {},
      Array.isArray(o) ? o.filter((r) => typeof r == "string") : null
    );
  } catch {
    return null;
  }
}
const y = /* @__PURE__ */ new Map();
function ce(e, t) {
  y.set(e, t);
}
function ue(e) {
  const t = y.get(e) ?? null;
  return y.delete(e), t;
}
function f(e, t, n = !1, s) {
  const o = document.createElement("p");
  if (o.dataset.testid = n ? "dr-library-error" : "dr-library-loading", o.textContent = t, o.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(o), !s) return;
  const r = document.createElement("button");
  r.type = "button", r.dataset.testid = "dr-library-retry", r.textContent = G, r.style.cssText = "margin: 0 16px;", r.addEventListener("click", s), e.append(r);
}
function le(e, t, n) {
  const { container: s } = n, o = new AbortController(), r = ue(t);
  let i = null, c = !1;
  const g = (a) => {
    const u = s.querySelector("iframe");
    !u || a.source !== u.contentWindow || !U(a.data) || (a.data.type === "dr-library/reload" ? d() : n.surface.kind === "conversation-panel" && (ce(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  }, C = (a) => {
    a.reason !== "not-ready" || c || (c = !0, d());
  };
  function b() {
    window.removeEventListener("message", g), i?.(), i = null;
  }
  async function d() {
    b(), f(s, j);
    const a = e.agentServer.request, [u, E, A, L] = await Promise.all([
      J(
        a,
        o.signal,
        (O) => f(s, O)
      ),
      ee(a, n.conversationId),
      te(a),
      t === "tools" ? ie(a) : null
    ]).catch(() => [null, null, null, null]);
    if (o.signal.aborted || u === null || A === null) return;
    if (!u.ok)
      return f(s, u.message, !0, () => {
        d();
      });
    if (!e.appBackend) return f(s, K, !0);
    const N = {
      tab: t,
      parent: window.location.origin,
      namespace: E?.namespace ?? null,
      started: E?.started ?? !1,
      cap: A,
      focus: r,
      theme: re(s),
      mcp: L
    };
    s.replaceChildren(), i = e.appBackend.mountFrame(s, {
      path: `/ui/${x(N)}`,
      title: D[t],
      onError: C
    }), window.addEventListener("message", g);
  }
  return d(), () => {
    o.abort(), b(), s.replaceChildren();
  };
}
function de(e) {
  const t = w.map(
    (n) => e.registerPage(n, (s) => le(e, n, s))
  );
  return () => t.forEach((n) => n());
}
export {
  de as activate
};
