// The frame's entry: the URL's parameters, Canvas's theme over its dark defaults, then the app.

import { render } from "preact";

import { DEFAULT_THEME, readFrameParams } from "../shared/protocol";
import { App } from "./app";
import "./styles.css";

const params = readFrameParams(
  window.location.search,
  window.parent === window,
);
const theme = { ...DEFAULT_THEME, ...params.theme };
for (const [token, value] of Object.entries(theme)) {
  document.documentElement.style.setProperty(token, value);
}
render(<App params={params} />, document.getElementById("app")!);
