// The frame's entry: the URL's parameters, Canvas's theme, then the app.

import { render } from "preact";

import { readFrameParams } from "../shared/protocol";
import { App } from "./app";
import "./styles.css";
import { applyTheme } from "./theme";

const params = readFrameParams(
  window.location.search,
  window.parent === window,
);
applyTheme(params.theme, document.documentElement);
render(<App params={params} />, document.getElementById("app")!);
