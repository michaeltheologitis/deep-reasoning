// The settings panel: the providers, the default model and the default folder, as UI to agree before it's wired. What it holds lives in the page and resets on reload; a typed key is never kept or sent.
import { PANEL_CLOSE, caret, closeOtherPanels, element, folderPicker, modelMenu, renderComposer, settings } from "./app.js";

const ENV_FILE = "~/.deep-reasoning/.env";
const NEW_NAME = "vllm";
const NEW_URL = "http://localhost:8000/v1";
const WEB_PROTOCOLS = ["http:", "https:"];
const ADDING = "adding";
const NO_FOLDER = "each chat's own scratch folder";
const KEYS = {
  saved: { row: "key ✓", note: "set" },
  shell: { row: "key from your shell", note: "not set: OPENAI_API_KEY from your shell is used" },
  none: { row: "no key", note: "not set" },
};

const panel = document.getElementById("settings");
const toggleButton = document.getElementById("settings-toggle");
// the provider whose form shows, or ADDING for the new one's
let opened = null;
let cancelRemove = null;

const providerRows = element("div", { class: "lib-rows" });
const addToggle = element(
  "button",
  { type: "button", class: "lib-action", "aria-expanded": "false", "aria-controls": "provider-new-form", "data-key": "add", onclick: () => flip(ADDING, opened === ADDING ? "add" : "name") },
  "+ Add provider",
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
  providerRows.replaceChildren(...settings.providers.map(providerRow));
  addToggle.setAttribute("aria-expanded", String(opened === ADDING));
  addArea.replaceChildren(addToggle, opened === ADDING ? providerForm(null) : "");
  modelName.textContent = settings.defaultModel?.name ?? "…";
  if (focused) panel.querySelector(`[data-key="${focused}"]`)?.focus();
}

function flip(target, focusKey) {
  opened = opened === target ? null : target;
  render(focusKey);
}

function providerRow(provider, index) {
  const open = opened === provider;
  const key = `row:${index}`;
  return element(
    "div",
    { class: "lib-entry" },
    element(
      "button",
      { type: "button", class: "row", "aria-expanded": String(open), "data-key": key, onclick: () => flip(provider, key) },
      caret(open),
      element("span", { class: "lib-name" }, provider.name, " ", element("span", { class: "lib-detail" }, provider.url)),
      element("span", { class: "meta" }, KEYS[provider.key].row),
    ),
    open && providerForm(provider),
  );
}

// method="dialog" never navigates, so a typed key can't end up in a URL even if this script failed.
function providerForm(provider) {
  const id = provider ? "provider" : "provider-new";
  const input = (field, props) => element("input", { id: `${id}-${field}`, class: "set-input", autocomplete: "off", spellcheck: "false", ...props });
  const label = (field, text) => element("label", { for: `${id}-${field}` }, text);
  const name = input("name", { value: provider?.name ?? "", placeholder: NEW_NAME, "data-key": "name" });
  const url = input("url", { type: "url", value: provider?.url ?? "", placeholder: NEW_URL });
  const key = input("key", { type: "password", "aria-describedby": `${id}-key-note` });
  const problem = element("div", { class: "lib-problems", "aria-live": "polite" });
  return element(
    "form",
    { id: `${id}-form`, class: "children lib-open lib-form", method: "dialog", novalidate: "", onsubmit: (e) => save(e, provider, { name, url, key, problem }) },
    element(
      "div",
      { class: "set-fields" },
      [label("name", "name"), name, label("url", "base URL"), url, label("key", "API key"), key],
      element("span", { id: `${id}-key-note`, class: "set-note" }, KEYS[provider?.key ?? "none"].note),
    ),
    problem,
    element(
      "div",
      { class: "lib-actions" },
      element("button", { type: "submit", class: "lib-action lib-primary" }, provider ? "Save" : "Add"),
      provider
        ? element("button", { type: "button", class: "lib-action", onclick: (e) => confirmRemove(provider, e.currentTarget.parentElement) }, "Remove")
        : element("button", { type: "button", class: "lib-action", onclick: () => flip(ADDING, "add") }, "Cancel"),
    ),
  );
}

function save(e, provider, { name, url, key, problem }) {
  e.preventDefault();
  const typed = { name: name.value.trim(), url: url.value.trim() };
  problem.textContent = providerProblem(typed, provider) ?? "";
  if (problem.textContent) return;
  // only that a key was given is kept: the key itself is dropped here
  const keyState = key.value ? "saved" : (provider?.key ?? "none");
  key.value = "";
  if (provider) Object.assign(provider, typed, { key: keyState });
  else settings.providers.push({ ...typed, key: keyState, models: null });
  const index = provider ? settings.providers.indexOf(provider) : settings.providers.length - 1;
  opened = null;
  render(`row:${index}`);
}

function providerProblem({ name, url }, provider) {
  if (!name) return `Name the provider, like ${NEW_NAME}.`;
  if (settings.providers.some((other) => other !== provider && other.name.toLowerCase() === name.toLowerCase())) return `There is a provider named ${name} already.`;
  if (!URL.canParse(url) || !WEB_PROTOCOLS.includes(new URL(url).protocol)) return `The base URL should be an http:// or https:// address, like ${NEW_URL}.`;
  return null;
}

// The confirm takes the buttons' place, as the chat list's does, leaving what was typed alone.
function confirmRemove(provider, buttons) {
  const keep = element("button", { type: "button", class: "no" }, "Keep");
  const confirm = element("div", { class: "lib-actions confirm" }, `Remove ${provider.name}?`, element("button", { type: "button", class: "yes", onclick: () => remove(provider) }, "Remove"), keep);
  cancelRemove = () => {
    cancelRemove = null;
    confirm.replaceWith(buttons);
    buttons.lastElementChild.focus();
  };
  keep.addEventListener("click", cancelRemove);
  buttons.replaceWith(confirm);
  keep.focus();
}

function remove(provider) {
  const index = settings.providers.indexOf(provider);
  settings.providers.splice(index, 1);
  opened = null;
  render(index < settings.providers.length ? `row:${index}` : "add");
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
  render(settings.providers.length ? "row:0" : "add");
}

toggleButton.addEventListener("click", () => setOpen(panel.hidden));
panel.addEventListener(PANEL_CLOSE, () => setOpen(false));
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
