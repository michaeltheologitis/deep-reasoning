const O = ["browse", "create", "namespaces", "tools"], R = {
  browse: "Decompositions",
  create: "Create decomposition",
  namespaces: "Namespaces",
  tools: "Tools"
}, M = {
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
}, v = Object.keys(M), x = 200, _ = "5", B = /^[#\w\s(),.%'"-]*$/, U = /^\d{1,6}(\.\d{1,2})?$/;
function j(e) {
  return O.includes(e);
}
function $(e) {
  return e.length <= x && B.test(e) && !/url\(/i.test(e);
}
function G(e) {
  const t = {};
  for (const n of v) {
    const r = e[n];
    typeof r == "string" && r !== "" && $(r) && (t[n] = r);
  }
  return t;
}
function H(e) {
  const t = new URLSearchParams({ tab: e.tab });
  return e.parent && t.set("parent", e.parent), e.namespace && t.set("namespace", e.namespace), e.started && t.set("started", "1"), t.set("cap", e.cap), e.focus && t.set("focus", e.focus), Object.keys(e.theme).length > 0 && t.set("theme", JSON.stringify(e.theme)), e.mcp !== null && t.set("mcp", JSON.stringify(e.mcp)), `?${t.toString()}`;
}
function K(e) {
  return U.test(e) && Number(e) > 0;
}
function S(e, ...t) {
  return Object.keys(e).sort().join() === [...t].sort().join();
}
function V(e) {
  if (!e || typeof e != "object") return !1;
  const t = e;
  return t.type === "dr-library/reload" ? S(t, "type") : t.type === "dr-library/set-spend-cap" ? S(t, "type", "cap") && typeof t.cap == "string" && K(t.cap) : t.type === "dr-library/select-tab" && j(t.tab) && (t.focus === null || typeof t.focus == "string");
}
const W = "Opening the Library…", k = "Starting the Library's backend…", b = (e) => `The Library's backend did not start: ${e}`, Y = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", X = (e) => `This agent-server cannot run the Library's backend: ${e}`, z = "This version of Canvas cannot show an App's own pages. Update the app.", J = "Try again", q = "it was still starting after 45 seconds.", Q = "Deep Reasoning's agent profile is missing. Restart Deep Reasoning, which creates it again.", Z = "The key proxy is off for Deep Reasoning (--no-key-proxy), so there is no cap to set.", ee = (e) => `The cap was not saved: ${e}`, C = "/api/canvas-extensions/installed/dr-library/backend", te = 500, N = 45e3;
async function ne(e, t, n) {
  let r = Date.now() + N;
  const s = () => e({ path: C });
  let o;
  try {
    o = await s();
    let i = !1;
    for (; ; ) {
      if (t.throwIfAborted(), o.state === "ready") return { ok: !0 };
      if (o.state === "missing" || o.state === "unsupported")
        return {
          ok: !1,
          message: X(o.detail ?? o.state)
        };
      if (o.state === "starting") {
        if (n(k), Date.now() >= r)
          return { ok: !1, message: b(q) };
        await se(te, t), o = await s();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: b(o.detail ?? o.state)
        };
      if (o.revision === null || o.prepared_revision !== o.revision)
        return { ok: !1, message: Y };
      n(k), i = !0, o = await e({
        method: "POST",
        path: `${C}/start`,
        body: { revision: o.revision }
      }).catch((u) => {
        if (re(u)) throw u;
        return r = Date.now() + N, s();
      });
    }
  } catch (i) {
    return t.throwIfAborted(), { ok: !1, message: b(P(i)) };
  }
}
function re(e) {
  return typeof e?.status == "number";
}
function P(e) {
  const t = e?.response;
  return typeof t?.detail == "string" ? t.detail : e instanceof Error ? e.message : String(e);
}
function se(e, t) {
  return new Promise((n, r) => {
    const s = setTimeout(() => {
      t.removeEventListener("abort", o), n();
    }, e), o = () => {
      clearTimeout(s), r(t.reason);
    };
    t.addEventListener("abort", o, { once: !0 });
  });
}
const m = "/api/agent-profiles/deep_reasoner", p = "--spend-cap-usd", oe = "--no-key-proxy", ae = 404, ie = "/api/settings", ce = /^\d+(\.\d+)?$/, ue = "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent";
async function le(e, t) {
  if (t === null) return null;
  const n = `/api/conversations/${encodeURIComponent(t)}/events/search?kind=${ue}&sort_order=TIMESTAMP_DESC&limit=1`;
  try {
    const s = (await e({ path: n })).items?.[0]?.config_options?.find(
      (o) => o.id === "namespace"
    );
    return typeof s?.current_value != "string" || !Array.isArray(s.options) ? null : {
      namespace: s.current_value,
      started: s.options.length === 1
    };
  } catch {
    return null;
  }
}
async function de(e) {
  try {
    const n = (await e({
      path: m
    })).profile?.acp_args;
    return pe(
      Array.isArray(n) ? n.filter((r) => typeof r == "string") : null
    );
  } catch {
    return _;
  }
}
function pe(e) {
  if (!e) return _;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((r) => r.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && ce.test(n) ? n : _;
}
function fe(e, t) {
  if (e.includes(oe)) return null;
  const n = e.indexOf(p);
  if (n >= 0)
    return [...e.slice(0, n), p, t, ...e.slice(n + 2)];
  const r = e.findIndex((s) => s.startsWith(`${p}=`));
  return r >= 0 ? [
    ...e.slice(0, r),
    p,
    t,
    ...e.slice(r + 1)
  ] : [...e, p, t];
}
async function ye(e, t) {
  try {
    const n = await e({ path: m }), r = Array.isArray(n.profile.acp_args) ? n.profile.acp_args.filter((o) => typeof o == "string") : [], s = fe(r, t);
    return s === null ? { ok: !1, message: Z } : (await e({
      method: "POST",
      path: m,
      body: { ...n.profile, acp_args: s }
    }), { ok: !0, cap: t });
  } catch (n) {
    return {
      ok: !1,
      message: n?.status === ae ? Q : ee(P(n))
    };
  }
}
function he(e) {
  const t = getComputedStyle(e);
  return G(
    Object.fromEntries(
      v.map((n) => [
        n,
        t.getPropertyValue(n).trim()
      ])
    )
  );
}
const d = (e) => typeof e == "object" && e !== null && !Array.isArray(e), A = (e) => typeof e == "string" && e !== "";
function me(e) {
  return A(e.command) ? "stdio" : A(e.url) ? e.transport === "sse" ? "sse" : "http" : null;
}
function ge(e) {
  if (!d(e)) return [];
  switch (e.strategy) {
    case "bearer":
    case "basic":
      return ["Authorization"];
    case "api_key":
      return [A(e.header_name) ? e.header_name : "Authorization"];
    case "header":
      return d(e.headers) ? Object.keys(e.headers) : [];
    default:
      return [];
  }
}
function be(e, t) {
  return Object.entries(e).flatMap(([n, r]) => {
    const s = d(r) ? r : {}, o = me(s);
    if (o === null) return [];
    const i = s.enabled === !1 ? "disabled" : t !== null && !t.includes(n) ? "not_in_profile" : null;
    return [
      {
        name: n,
        transport: o,
        command: o === "stdio" ? s.command : null,
        args: Array.isArray(s.args) ? s.args.filter((u) => typeof u == "string") : [],
        url: o === "stdio" ? null : s.url,
        env: d(s.env) ? Object.keys(s.env) : [],
        headers: [
          .../* @__PURE__ */ new Set([
            ...d(s.headers) ? Object.keys(s.headers) : [],
            ...ge(s.auth)
          ])
        ],
        forwarded: i === null,
        why_not: i
      }
    ];
  });
}
async function _e(e) {
  try {
    const [t, n] = await Promise.all([
      e({
        path: ie
      }),
      e({
        path: m
      })
    ]), r = t.agent_settings?.mcp_config, s = n.profile?.mcp_server_refs;
    return be(
      d(r) ? r : {},
      Array.isArray(s) ? s.filter((o) => typeof o == "string") : null
    );
  } catch {
    return null;
  }
}
const E = /* @__PURE__ */ new Map();
function Ae(e, t) {
  E.set(e, t);
}
function Ee(e) {
  const t = E.get(e) ?? null;
  return E.delete(e), t;
}
function h(e, t, n = !1, r) {
  const s = document.createElement("p");
  if (s.dataset.testid = n ? "dr-library-error" : "dr-library-loading", s.textContent = t, s.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(s), !r) return;
  const o = document.createElement("button");
  o.type = "button", o.dataset.testid = "dr-library-retry", o.textContent = J, o.style.cssText = "margin: 0 16px;", o.addEventListener("click", r), e.append(o);
}
function Te(e, t, n) {
  const { container: r } = n, s = new AbortController(), o = Ee(t);
  let i = null, u = !1;
  const T = (a) => {
    const c = r.querySelector("iframe");
    !c || a.source !== c.contentWindow || !V(a.data) || (a.data.type === "dr-library/reload" ? f() : a.data.type === "dr-library/set-spend-cap" ? D(c, a.data.cap) : n.surface.kind === "conversation-panel" && (Ae(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  };
  async function D(a, c) {
    const l = await ye(e.agentServer.request, c), y = l.ok ? { type: "dr-library/spend-cap-saved", cap: l.cap } : { type: "dr-library/spend-cap-refused", message: l.message }, g = new URL(a.src, window.location.href).origin;
    a.contentWindow?.postMessage(y, g);
  }
  const L = (a) => {
    a.reason !== "not-ready" || u || (u = !0, f());
  };
  function w() {
    window.removeEventListener("message", T), i?.(), i = null;
  }
  async function f() {
    w(), h(r, W);
    const a = e.agentServer.request, [c, l, y, g] = await Promise.all([
      ne(
        a,
        s.signal,
        (I) => h(r, I)
      ),
      le(a, n.conversationId),
      de(a),
      t === "tools" ? _e(a) : null
    ]).catch(() => [null, null, null, null]);
    if (s.signal.aborted || c === null || y === null) return;
    if (!c.ok)
      return h(r, c.message, !0, () => {
        f();
      });
    if (!e.appBackend) return h(r, z, !0);
    const F = {
      tab: t,
      parent: window.location.origin,
      namespace: l?.namespace ?? null,
      started: l?.started ?? !1,
      cap: y,
      focus: o,
      theme: he(r),
      mcp: g
    };
    r.replaceChildren(), i = e.appBackend.mountFrame(r, {
      path: `/ui/${H(F)}`,
      title: R[t],
      onError: L
    }), window.addEventListener("message", T);
  }
  return f(), () => {
    s.abort(), w(), r.replaceChildren();
  };
}
function we(e) {
  const t = O.map(
    (n) => e.registerPage(n, (r) => Te(e, n, r))
  );
  return () => t.forEach((n) => n());
}
export {
  we as activate
};
