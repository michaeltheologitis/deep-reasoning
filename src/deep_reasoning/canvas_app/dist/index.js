const S = ["browse", "create", "namespaces", "tools"], D = {
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
], P = 200, h = "5", I = /^[#\w\s(),.%'"-]*$/;
function M(e) {
  return S.includes(e);
}
function F(e) {
  return e.length <= P && I.test(e) && !/url\(/i.test(e);
}
function R(e) {
  const t = {};
  for (const n of v) {
    const s = e[n];
    typeof s == "string" && s !== "" && F(s) && (t[n] = s);
  }
  return t;
}
function B(e) {
  const t = new URLSearchParams({ tab: e.tab });
  return e.parent && t.set("parent", e.parent), e.namespace && t.set("namespace", e.namespace), e.started && t.set("started", "1"), t.set("cap", e.cap), e.focus && t.set("focus", e.focus), Object.keys(e.theme).length > 0 && t.set("theme", JSON.stringify(e.theme)), e.mcp !== null && t.set("mcp", JSON.stringify(e.mcp)), `?${t.toString()}`;
}
function x(e) {
  if (!e || typeof e != "object") return !1;
  const t = e;
  return t.type === "dr-library/reload" ? Object.keys(t).length === 1 : t.type === "dr-library/select-tab" && M(t.tab) && (t.focus === null || typeof t.focus == "string");
}
const j = "Opening the Library…", _ = "Starting the Library's backend…", p = (e) => `The Library's backend did not start: ${e}`, U = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", $ = (e) => `This agent-server cannot run the Library's backend: ${e}`, H = "This version of Canvas cannot show an App's own pages. Update the app.", K = "Try again", G = "it was still starting after 45 seconds.", E = "/api/canvas-extensions/installed/dr-library/backend", V = 500, w = 45e3;
async function z(e, t, n) {
  let s = Date.now() + w;
  const o = () => e({ path: E });
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
        if (n(_), Date.now() >= s)
          return { ok: !1, message: p(G) };
        await q(V, t), r = await o();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: p(r.detail ?? r.state)
        };
      if (r.revision === null || r.prepared_revision !== r.revision)
        return { ok: !1, message: U };
      n(_), i = !0, r = await e({
        method: "POST",
        path: `${E}/start`,
        body: { revision: r.revision }
      }).catch((c) => {
        if (J(c)) throw c;
        return s = Date.now() + w, o();
      });
    }
  } catch (i) {
    return t.throwIfAborted(), { ok: !1, message: p(W(i)) };
  }
}
function J(e) {
  return typeof e?.status == "number";
}
function W(e) {
  const t = e?.response;
  return typeof t?.detail == "string" ? t.detail : e instanceof Error ? e.message : String(e);
}
function q(e, t) {
  return new Promise((n, s) => {
    const o = setTimeout(() => {
      t.removeEventListener("abort", r), n();
    }, e), r = () => {
      clearTimeout(o), s(t.reason);
    };
    t.addEventListener("abort", r, { once: !0 });
  });
}
const k = "/api/agent-profiles/deep_reasoner", X = "/api/settings", Y = /^\d+(\.\d+)?$/, Q = "openhands.sdk.event.acp_session_controls.ACPSessionControlsEvent";
async function Z(e, t) {
  if (t === null) return null;
  const n = `/api/conversations/${encodeURIComponent(t)}/events/search?kind=${Q}&sort_order=TIMESTAMP_DESC&limit=1`;
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
async function ee(e) {
  try {
    const n = (await e({
      path: k
    })).profile?.acp_args;
    return te(
      Array.isArray(n) ? n.filter((s) => typeof s == "string") : null
    );
  } catch {
    return h;
  }
}
function te(e) {
  if (!e) return h;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((s) => s.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && Y.test(n) ? n : h;
}
function ne(e) {
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
function re(e) {
  return m(e.command) ? "stdio" : m(e.url) ? e.transport === "sse" ? "sse" : "http" : null;
}
function se(e) {
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
function oe(e, t) {
  return Object.entries(e).flatMap(([n, s]) => {
    const o = l(s) ? s : {}, r = re(o);
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
            ...se(o.auth)
          ])
        ],
        forwarded: i === null,
        why_not: i
      }
    ];
  });
}
async function ae(e) {
  try {
    const [t, n] = await Promise.all([
      e({
        path: X
      }),
      e({
        path: k
      })
    ]), s = t.agent_settings?.mcp_config, o = n.profile?.mcp_server_refs;
    return oe(
      l(s) ? s : {},
      Array.isArray(o) ? o.filter((r) => typeof r == "string") : null
    );
  } catch {
    return null;
  }
}
const y = /* @__PURE__ */ new Map();
function ie(e, t) {
  y.set(e, t);
}
function ce(e) {
  const t = y.get(e) ?? null;
  return y.delete(e), t;
}
function f(e, t, n = !1, s) {
  const o = document.createElement("p");
  if (o.dataset.testid = n ? "dr-library-error" : "dr-library-loading", o.textContent = t, o.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(o), !s) return;
  const r = document.createElement("button");
  r.type = "button", r.dataset.testid = "dr-library-retry", r.textContent = K, r.style.cssText = "margin: 0 16px;", r.addEventListener("click", s), e.append(r);
}
function ue(e, t, n) {
  const { container: s } = n, o = new AbortController(), r = ce(t);
  let i = null, c = !1;
  const g = (a) => {
    const u = s.querySelector("iframe");
    !u || a.source !== u.contentWindow || !x(a.data) || (a.data.type === "dr-library/reload" ? d() : n.surface.kind === "conversation-panel" && (ie(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  }, N = (a) => {
    a.reason !== "not-ready" || c || (c = !0, d());
  };
  function b() {
    window.removeEventListener("message", g), i?.(), i = null;
  }
  async function d() {
    b(), f(s, j);
    const a = e.agentServer.request, [u, T, A, C] = await Promise.all([
      z(
        a,
        o.signal,
        (O) => f(s, O)
      ),
      Z(a, n.conversationId),
      ee(a),
      t === "tools" ? ae(a) : null
    ]).catch(() => [null, null, null, null]);
    if (o.signal.aborted || u === null || A === null) return;
    if (!u.ok)
      return f(s, u.message, !0, () => {
        d();
      });
    if (!e.appBackend) return f(s, H, !0);
    const L = {
      tab: t,
      parent: window.location.origin,
      namespace: T?.namespace ?? null,
      started: T?.started ?? !1,
      cap: A,
      focus: r,
      theme: ne(s),
      mcp: C
    };
    s.replaceChildren(), i = e.appBackend.mountFrame(s, {
      path: `/ui/${B(L)}`,
      title: D[t],
      onError: N
    }), window.addEventListener("message", g);
  }
  return d(), () => {
    o.abort(), b(), s.replaceChildren();
  };
}
function le(e) {
  const t = S.map(
    (n) => e.registerPage(n, (s) => ue(e, n, s))
  );
  return () => t.forEach((n) => n());
}
export {
  le as activate
};
