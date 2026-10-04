// The frame's app: the safety notice, the tab (with its own tab row on the standalone page), the
// Library's problems, the /health poll that refetches on a new revision, and the backend-loss footer.

import type { FunctionComponent } from "preact";
import { useEffect, useState } from "preact/hooks";

import {
  type FrameMessage,
  type FrameParams,
  type TabId,
  TAB_IDS,
  TAB_TITLES,
} from "../shared/protocol";
import { BackendUnavailable, getHealth } from "./api";
import { ProblemsBanner, SafetyNotice } from "./components/notices";
import { acknowledgeSafety, safetyAcknowledged } from "./drafts";
import { BrowseTab } from "./tabs/browse";
import { CreateTab } from "./tabs/create";
import type { TabProps } from "./tabs/props";
import { ToolsTab } from "./tabs/tools";
import { BACKEND_LOST, RELOAD, RESTART, SESSION_ENDED } from "./texts";
import type { Health } from "./types";

const TABS: Partial<Record<TabId, FunctionComponent<TabProps>>> = {
  browse: BrowseTab,
  create: CreateTab,
  tools: ToolsTab,
};
const SESSION_STATUS = 401;
const POLL_MS = 3_000;

function post(params: FrameParams, message: FrameMessage) {
  if (params.parent !== null) window.parent.postMessage(message, params.parent);
}

/** /health every POLL_MS while the frame is visible; health keeps its identity until rev moves. */
function useHealth(
  onBackendLost: (error: BackendUnavailable | null) => void,
): Health | null {
  const [health, setHealth] = useState<Health | null>(null);
  useEffect(() => {
    let alive = true;
    const poll = async () => {
      if (document.visibilityState !== "visible") return;
      try {
        const next = await getHealth();
        if (!alive) return;
        setHealth((before) => (before?.rev === next.rev ? before : next));
        onBackendLost(null);
      } catch (error) {
        if (alive && error instanceof BackendUnavailable) onBackendLost(error);
      }
    };
    void poll();
    const timer = setInterval(poll, POLL_MS);
    document.addEventListener("visibilitychange", poll);
    return () => {
      alive = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", poll);
    };
  }, []);
  return health;
}

export function App(props: { params: FrameParams }) {
  const { params } = props;
  const [acknowledged, setAcknowledged] = useState(safetyAcknowledged);
  const [tab, setTab] = useState<TabId>(params.tab);
  const [focus, setFocus] = useState<string | null>(params.focus);
  const [lost, setLost] = useState<BackendUnavailable | null>(null);
  const health = useHealth(setLost);

  if (!acknowledged) {
    return (
      <SafetyNotice
        cap={params.cap}
        variant="first-open"
        onUnderstood={() => {
          acknowledgeSafety();
          setAcknowledged(true);
        }}
      />
    );
  }

  const navigateTab = (next: TabId, nextFocus: string | null) => {
    if (params.parent !== null)
      return post(params, {
        type: "dr-library/select-tab",
        tab: next,
        focus: nextFocus,
      });
    setTab(next);
    setFocus(nextFocus);
  };
  const Tab = TABS[tab];
  const tabProps: TabProps | null = health && {
    params: { ...params, tab, focus },
    health,
    rev: health.rev,
    navigateTab,
    onBackendLost: setLost,
  };

  return (
    <div class="app">
      {params.parent === null && (
        <nav class="tab-row" role="tablist">
          {TAB_IDS.map((id) => (
            <button
              type="button"
              role="tab"
              aria-selected={id === tab}
              data-testid={`dr-tab-${id}`}
              onClick={() => navigateTab(id, null)}
            >
              {TAB_TITLES[id]}
            </button>
          ))}
        </nav>
      )}
      {health && <ProblemsBanner rev={health.rev} onBackendLost={setLost} />}
      <main>
        {tabProps && Tab && <Tab key={`${tab}:${focus ?? ""}`} {...tabProps} />}
      </main>
      {lost && <BackendLost status={lost.status} params={params} />}
    </div>
  );
}

function BackendLost(props: { status: number; params: FrameParams }) {
  const ended = props.status === SESSION_STATUS;
  const restart = () =>
    props.params.parent !== null
      ? post(props.params, { type: "dr-library/reload" })
      : window.location.reload();
  return (
    <footer
      class="banner error lost"
      role="alert"
      data-testid="dr-backend-lost"
    >
      <span>{ended ? SESSION_ENDED : BACKEND_LOST(props.status)}</span>{" "}
      <button type="button" data-testid="dr-restart" onClick={restart}>
        {ended ? RELOAD : RESTART}
      </button>
    </footer>
  );
}
