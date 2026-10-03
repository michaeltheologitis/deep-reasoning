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
const U = "Opening the Library…", A = "Starting the Library's backend…", p = (e) => `The Library's backend did not start: ${e}`, j = "The Library's backend is not approved for this version of the App. Restart the app: its setup approves the App it installed.", $ = (e) => `This agent-server cannot run the Library's backend: ${e}`, H = "This version of Canvas cannot show an App's own pages. Update the app.", G = "Try again", K = "it was still starting after 45 seconds.", E = "/api/canvas-extensions/installed/dr-library/backend", V = 500, _ = 45e3;
async function J(e, t, n) {
  let s = Date.now() + _;
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
        if (n(A), Date.now() >= s)
          return { ok: !1, message: p(K) };
        await X(V, t), r = await o();
        continue;
      }
      if (i)
        return {
          ok: !1,
          message: p(r.detail ?? r.state)
        };
      if (r.revision === null || r.prepared_revision !== r.revision)
        return { ok: !1, message: j };
      n(A), i = !0, r = await e({
        method: "POST",
        path: `${E}/start`,
        body: { revision: r.revision }
      }).catch((c) => {
        if (W(c)) throw c;
        return s = Date.now() + _, o();
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
const k = "/api/agent-profiles/deep_reasoner", Y = "/api/settings", z = /^\d+(\.\d+)?$/;
async function Q(e, t) {
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
async function Z(e) {
  try {
    const n = (await e({
      path: k
    })).profile?.acp_args;
    return ee(
      Array.isArray(n) ? n.filter((s) => typeof s == "string") : null
    );
  } catch {
    return h;
  }
}
function ee(e) {
  if (!e) return h;
  if (e.includes("--no-key-proxy")) return "off";
  const t = e.indexOf("--spend-cap-usd"), n = t >= 0 ? e[t + 1] : e.find((s) => s.startsWith("--spend-cap-usd="))?.slice(16);
  return n !== void 0 && z.test(n) ? n : h;
}
function te(e) {
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
const f = (e) => typeof e == "object" && e !== null && !Array.isArray(e), w = (e) => typeof e == "string" && e !== "";
function ne(e) {
  return w(e.command) ? "stdio" : w(e.url) ? e.transport === "sse" ? "sse" : "http" : null;
}
function re(e, t) {
  return Object.entries(e).flatMap(([n, s]) => {
    const o = f(s) ? s : {}, r = ne(o);
    if (r === null) return [];
    const i = o.enabled === !1 ? "disabled" : t !== null && !t.includes(n) ? "not_in_profile" : null;
    return [
      {
        name: n,
        transport: r,
        command: r === "stdio" ? o.command : null,
        args: Array.isArray(o.args) ? o.args.filter((c) => typeof c == "string") : [],
        url: r === "stdio" ? null : o.url,
        env: f(o.env) ? Object.keys(o.env) : [],
        headers: f(o.headers) ? Object.keys(o.headers) : [],
        forwarded: i === null,
        why_not: i
      }
    ];
  });
}
async function se(e) {
  try {
    const [t, n] = await Promise.all([
      e({
        path: Y
      }),
      e({
        path: k
      })
    ]), s = t.agent_settings?.mcp_config, o = n.profile?.mcp_server_refs;
    return re(
      f(s) ? s : {},
      Array.isArray(o) ? o.filter((r) => typeof r == "string") : null
    );
  } catch {
    return null;
  }
}
const m = /* @__PURE__ */ new Map();
function oe(e, t) {
  m.set(e, t);
}
function ae(e) {
  const t = m.get(e) ?? null;
  return m.delete(e), t;
}
function d(e, t, n = !1, s) {
  const o = document.createElement("p");
  if (o.dataset.testid = n ? "dr-library-error" : "dr-library-loading", o.textContent = t, o.style.cssText = "margin: 0; padding: 12px 16px; color: var(--oh-muted, inherit);", e.replaceChildren(o), !s) return;
  const r = document.createElement("button");
  r.type = "button", r.dataset.testid = "dr-library-retry", r.textContent = G, r.style.cssText = "margin: 0 16px;", r.addEventListener("click", s), e.append(r);
}
function ie(e, t, n) {
  const { container: s } = n, o = new AbortController(), r = ae(t);
  let i = null, c = !1;
  const y = (a) => {
    const u = s.querySelector("iframe");
    !u || a.source !== u.contentWindow || !x(a.data) || (a.data.type === "dr-library/reload" ? l() : n.surface.kind === "conversation-panel" && (oe(a.data.tab, a.data.focus), n.surface.selectTab(a.data.tab)));
  }, L = (a) => {
    a.reason !== "not-ready" || c || (c = !0, l());
  };
  function g() {
    window.removeEventListener("message", y), i?.(), i = null;
  }
  async function l() {
    g(), d(s, U);
    const a = e.agentServer.request, [u, b, T, C] = await Promise.all([
      J(
        a,
        o.signal,
        (O) => d(s, O)
      ),
      Q(a, n.conversationId),
      Z(a),
      t === "tools" ? se(a) : null
    ]).catch(() => [null, null, null, null]);
    if (o.signal.aborted || u === null || T === null) return;
    if (!u.ok)
      return d(s, u.message, !0, () => {
        l();
      });
    if (!e.appBackend) return d(s, H, !0);
    const N = {
      tab: t,
      parent: window.location.origin,
      namespace: b?.namespace ?? null,
      started: b?.started ?? !1,
      cap: T,
      focus: r,
      theme: te(s),
      mcp: C
    };
    s.replaceChildren(), i = e.appBackend.mountFrame(s, {
      path: `/ui/${B(N)}`,
      title: D[t],
      onError: L
    }), window.addEventListener("message", y);
  }
  return l(), () => {
    o.abort(), g(), s.replaceChildren();
  };
}
function ce(e) {
  const t = S.map(
    (n) => e.registerPage(n, (s) => ie(e, n, s))
  );
  return () => t.forEach((n) => n());
}
export {
  ce as activate
};
