// The settings panel: the providers, the default model and the default folder, as UI to agree before it's wired. What it holds lives in the page and resets on reload; a typed key is never kept or sent.
import { PANEL_CLOSE, PANEL_OPEN, caret, closeOtherPanels, element, folderPicker, modelMenu, renderComposer, settings } from "./app.js";

const ENV_FILE = "~/.deep-reasoning/.env";
const NEW_NAME = "vllm";
const NEW_URL = "http://localhost:8000/v1";
const WEB_PROTOCOLS = ["http:", "https:"];
const ADDING = "adding";
const NO_FOLDER = "each chat's own scratch folder";

const panel = document.getElementById("settings");
const toggleButton = document.getElementById("settings-toggle");
// the vendor or custom server whose form shows, or ADDING for a new server's
let opened = null;
let cancelRemove = null;

const providerRows = element("div", { class: "lib-rows" });
const addToggle = element(
  "button",
  { type: "button", class: "lib-action", "aria-expanded": "false", "aria-controls": "server-new-form", "data-key": "add", onclick: () => flip(ADDING, opened === ADDING ? "add" : "name") },
  "+ Custom server",
);
const addArea = element("div", { class: "lib-add" }, addToggle);
const modelName = element("span", { id: "default-model-name" });
const modelHost = element("div");
const modelButton = pickerButton("default-model", "listbox", modelName, pickDefault);
const folderName = element("span", { id: "default-folder-name" }, NO_FOLDER);
const folderHost = element("div");
const folderButton = pickerButton("default-folder", "dialog", folderName, pickDefaultFolder);

panel.append(
  element(
    "header",
    { class: "lib-head" },
    element("h2", { class: "lib-title" }, "Settings", element("span", { class: "lib-filename" }, ` · ${ENV_FILE}`)),
    element("button", { type: "button", class: "lib-close", "aria-label": "Close the settings", onclick: () => setOpen(false) }, "×"),
  ),
  element(
    "div",
    { class: "lib-body" },
    element("p", { class: "lib-note" }, "Not saved yet: this is the UI to agree."),
    element("section", { class: "lib-group" }, element("h3", { class: "lib-label" }, "Providers"), providerRows, addArea),
    element("p", { class: "lib-note" }, `Keys are kept in ${ENV_FILE}, readable only by you. Keys already set in your shell keep working.`),
    pickerSection("default-model", "Default model", modelButton, modelHost, "New chats start on it; each chat picks its own under its input."),
    pickerSection("default-folder", "Default folder", folderButton, folderHost, "New chats work in it; each chat can pick its own from the top bar."),
  ),
);

// A value with ▾ that opens its picker below it; focus stays in the open picker on mousedown, so a click toggles it.
function pickerButton(id, popup, value, onclick) {
  const props = { type: "button", class: "choice set-model", "aria-haspopup": popup, "aria-expanded": "false", "aria-labelledby": `${id}-label ${value.id}`, "aria-describedby": `${id}-note` };
  return element("button", { ...props, onmousedown: (e) => e.preventDefault(), onclick }, value, element("span", { "aria-hidden": "true" }, " ▾"));
}

function pickerSection(id, title, button, host, note) {
  return element(
    "section",
    { class: "lib-group" },
    element("h3", { class: "lib-label", id: `${id}-label` }, title),
    element("div", {}, button),
    host,
    element("p", { class: "lib-note", id: `${id}-note` }, note),
  );
}

function render(focusKey) {
  const focused = focusKey ?? document.activeElement?.dataset?.key;
  cancelRemove = null;
  providerRows.replaceChildren(...settings.vendors.map(vendorRow), ...settings.servers.map(serverRow));
  addToggle.setAttribute("aria-expanded", String(opened === ADDING));
  addArea.replaceChildren(addToggle, opened === ADDING ? serverForm(null) : "");
  modelName.textContent = settings.defaultModel?.name ?? "…";
  if (focused) panel.querySelector(`[data-key="${focused}"]`)?.focus();
}

function flip(target, focusKey) {
  opened = opened === target ? null : target;
  render(focusKey);
}

function keyStatus(provider) {
  if (provider.saved) return "key ✓";
  if (provider.shell) return "key from your shell";
  return provider.keyName ? "add key" : "no key";
}

function providerRow(provider, key, detail, form) {
  const open = opened === provider;
  return element(
    "div",
    { class: "lib-entry" },
    element(
      "button",
      { type: "button", class: "row", "aria-expanded": String(open), "data-key": key, onclick: () => flip(provider, key) },
      caret(open),
      element("span", { class: "lib-name" }, provider.name, detail && [" ", element("span", { class: "lib-detail" }, detail)]),
      element("span", { class: "meta" }, keyStatus(provider)),
    ),
    open && form(provider),
  );
}

// A known vendor's address is the app's to know: its row takes only a key.
const vendorRow = (vendor, index) => providerRow(vendor, `v:${index}`, null, vendorForm);
const serverRow = (server, index) => providerRow(server, `s:${index}`, server.url, serverForm);

// Both forms use method="dialog", which never navigates, so a typed key can't end up in a URL even if this script failed.
function vendorForm(vendor) {
  const key = keyInput("vendor-key", "vendor-key-where");
  const problem = element("div", { class: "lib-problems", "aria-live": "polite" });
  const remove = element("button", { type: "button", class: "lib-action", disabled: !vendor.saved, onclick: () => confirmRemove(`Remove the ${vendor.name} key?`, () => forgetKey(vendor), remove.parentElement) }, "Remove key");
  return element(
    "form",
    { class: "children lib-open lib-form", method: "dialog", novalidate: "", onsubmit: (e) => saveKey(e, vendor, key, problem) },
    element("div", { class: "set-fields" }, element("label", { for: key.id }, "API key"), key, element("span", { id: "vendor-key-where", class: "set-note" }, `${vendor.keyName} in `, element("span", { class: "set-path" }, ENV_FILE))),
    problem,
    element("div", { class: "lib-actions" }, element("button", { type: "submit", class: "lib-action lib-primary" }, "Save"), remove),
  );
}

const keyInput = (id, note) => element("input", { id, class: "set-input", type: "password", autocomplete: "off", spellcheck: "false", "aria-describedby": note, "data-key": "key" });

function serverForm(server) {
  const id = server ? "server" : "server-new";
  const input = (field, props) => element("input", { id: `${id}-${field}`, class: "set-input", autocomplete: "off", spellcheck: "false", ...props });
  const label = (field, text) => element("label", { for: `${id}-${field}` }, text);
  const name = input("name", { value: server?.name ?? "", placeholder: NEW_NAME, "data-key": "name" });
  const url = input("url", { type: "url", value: server?.url ?? "", placeholder: NEW_URL });
  const key = keyInput(`${id}-key`, `${id}-key-note`);
  const problem = element("div", { class: "lib-problems", "aria-live": "polite" });
  return element(
    "form",
    { id: `${id}-form`, class: "children lib-open lib-form", method: "dialog", novalidate: "", onsubmit: (e) => saveServer(e, server, { name, url, key, problem }) },
    element(
      "div",
      { class: "set-fields" },
      [label("name", "name"), name, label("url", "base URL"), url, label("key", "API key"), key],
      element("span", { id: `${id}-key-note`, class: "set-note" }, server?.saved ? "set" : "optional: most local servers need none"),
    ),
    problem,
    element(
      "div",
      { class: "lib-actions" },
      element("button", { type: "submit", class: "lib-action lib-primary" }, server ? "Save" : "Add"),
      server
        ? element("button", { type: "button", class: "lib-action", onclick: (e) => confirmRemove(`Remove ${server.name}?`, () => removeServer(server), e.currentTarget.parentElement) }, "Remove")
        : element("button", { type: "button", class: "lib-action", onclick: () => flip(ADDING, "add") }, "Cancel"),
    ),
  );
}

// Only that a key was given is kept: the key itself is dropped here, never stored or sent.
function saveKey(e, vendor, key, problem) {
  e.preventDefault();
  problem.textContent = key.value ? "" : `Paste the ${vendor.name} key first.`;
  if (!key.value) return;
  key.value = "";
  vendor.saved = true;
  opened = null;
  render(`v:${settings.vendors.indexOf(vendor)}`);
}

function forgetKey(vendor) {
  vendor.saved = false;
  opened = null;
  render(`v:${settings.vendors.indexOf(vendor)}`);
}

function saveServer(e, server, { name, url, key, problem }) {
  e.preventDefault();
  const typed = { name: name.value.trim(), url: url.value.trim() };
  problem.textContent = serverProblem(typed, server) ?? "";
  if (problem.textContent) return;
  const saved = Boolean(key.value) || Boolean(server?.saved);
  key.value = "";
  if (server) Object.assign(server, typed, { saved });
  else settings.servers.push({ ...typed, saved, models: null });
  const index = server ? settings.servers.indexOf(server) : settings.servers.length - 1;
  opened = null;
  render(`s:${index}`);
}

function serverProblem({ name, url }, server) {
  const names = [...settings.vendors, ...settings.servers].filter((other) => other !== server).map((other) => other.name.toLowerCase());
  if (!name) return `Name the server, like ${NEW_NAME}.`;
  if (names.includes(name.toLowerCase())) return `There is a provider named ${name} already.`;
  if (!URL.canParse(url) || !WEB_PROTOCOLS.includes(new URL(url).protocol)) return `The base URL should be an http:// or https:// address, like ${NEW_URL}.`;
  return null;
}

// The confirm takes the buttons' place, as the chat list's does, leaving what was typed alone.
function confirmRemove(question, action, buttons) {
  const keep = element("button", { type: "button", class: "no" }, "Keep");
  const confirm = element("div", { class: "lib-actions confirm" }, question, element("button", { type: "button", class: "yes", onclick: action }, "Remove"), keep);
  cancelRemove = () => {
    cancelRemove = null;
    confirm.replaceWith(buttons);
    buttons.lastElementChild.focus();
  };
  keep.addEventListener("click", cancelRemove);
  buttons.replaceWith(confirm);
  keep.focus();
}

function removeServer(server) {
  const index = settings.servers.indexOf(server);
  settings.servers.splice(index, 1);
  opened = null;
  render(index < settings.servers.length ? `s:${index}` : "add");
}

function pickDefault() {
  modelMenu(modelButton, modelHost, settings.defaultModel, (model) => {
    settings.defaultModel = model;
    modelName.textContent = model.name;
    renderComposer();
  });
}

function pickDefaultFolder() {
  folderPicker(folderButton, folderHost, {
    label: "Default folder for new chats",
    current: settings.defaultFolder,
    empty: "each chat gets its own scratch folder",
    note: "New chats start in it. A folder you choose is never deleted.",
    pick: (folder) => {
      settings.defaultFolder = folder;
      folderName.textContent = folder ?? NO_FOLDER;
    },
  });
}

function setOpen(open) {
  if (!open && panel.contains(document.activeElement)) toggleButton.focus();
  panel.hidden = !open;
  toggleButton.setAttribute("aria-expanded", String(open));
  if (!open) return;
  closeOtherPanels(panel);
  render("v:0");
}

toggleButton.addEventListener("click", () => setOpen(panel.hidden));
panel.addEventListener(PANEL_CLOSE, () => setOpen(false));
panel.addEventListener(PANEL_OPEN, () => setOpen(true));
// Esc inside the panel takes back a Remove first, else closes it, and stops there, so it never also stops a run.
panel.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  e.stopPropagation();
  if (cancelRemove) cancelRemove();
  else setOpen(false);
});
// Elsewhere, Esc closes the panel unless the chat used it, to stop its run or keep a chat; app.js's handler runs first.
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !e.defaultPrevented && !panel.hidden) setOpen(false);
});
