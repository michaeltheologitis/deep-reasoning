// What every tab receives from the app.

import type { FrameParams, TabId } from "../../shared/protocol";
import type { OnBackendLost } from "../load";
import type { Health } from "../types";

export interface TabProps {
  params: FrameParams;
  health: Health;
  /** The Library's revision: a tab refetches its data when it moves. */
  rev: number;
  navigateTab: (tab: TabId, focus: string | null) => void;
  onBackendLost: OnBackendLost;
}
