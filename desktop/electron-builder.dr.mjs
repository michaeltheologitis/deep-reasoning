// The Canvas fork's electron-builder config under our name. No fork commit: the build points --config here.
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const env = process.env;
const fork = await import(pathToFileURL(join(env.DR_CANVAS_DIR, "electron-builder.config.mjs")).href);
const base = fork.default;
const productName = env.DR_APP_PRODUCT_NAME;
const executableName = env.DR_APP_EXECUTABLE_NAME;
const version = env.DR_APP_VERSION;
const artifactName = executableName + "-${version}-${arch}.${ext}"; // electron-builder macros, not JS

export default {
  ...base,
  appId: env.DR_APP_ID,
  productName,
  extraMetadata: { ...base.extraMetadata, name: executableName, productName, version },
  // The oldest macOS the runtime's arm64 wheels install on: macOS refuses to open the app on an older one.
  mac: { ...base.mac, minimumSystemVersion: "14.0" },
  dmg: { ...base.dmg, title: productName, artifactName },
  linux: { ...base.linux, executableName, artifactName, maintainer: env.DR_APP_MAINTAINER },
  win: undefined,
  nsis: undefined,
};
