// The App's entrypoint, as Canvas imports it: activate registers the four tabs.

import { TAB_IDS } from "../shared/protocol";
import type { CanvasExtensionDispose, CanvasExtensionHost } from "./host";
import { mountTab } from "./mount";

export function activate(host: CanvasExtensionHost): CanvasExtensionDispose {
  const registrations = TAB_IDS.map((tab) =>
    host.registerPage(tab, (context) => mountTab(host, tab, context)),
  );
  return () => registrations.forEach((dispose) => dispose());
}
