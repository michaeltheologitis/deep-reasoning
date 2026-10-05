# deep-reasoning

deep-reasoning runs Dean's deep_reasoner as an agent you talk to in a desktop app,
**Deep Reasoning**: a build of OpenHands Agent Canvas (Michael's fork, at a pinned commit)
whose conversations go to `dr-acp`, deep_reasoner behind the Agent Client Protocol. The
app adds a Library panel (**Show decompositions**) for deep_reasoner's Library, and a key
proxy that keeps your model key out of the code deep_reasoner writes and stops a
conversation's spending at a cap.

This repository holds `dr-acp`, the Library (`dr-library` and its panel), the app's setup
command (`packages/dr-app`) and the build (`desktop/`). The app's design is
[docs/design/d5-desktop-app.md](docs/design/d5-desktop-app.md).

## Install

### What you need

- **A Mac with Apple silicon on macOS 14 or later, or a Linux computer on x86-64.** There
  is no build for Intel Macs or Windows.
- **git.** On macOS it comes with the Command Line Tools: `xcode-select --install`.
- **Read access to [DeanLight/deep_reasoner_beta](https://github.com/DeanLight/deep_reasoner_beta)**,
  which is private: ask Dean. The app installs deep_reasoner on your computer with your own
  git credentials, and it has no terminal to ask for them in, so git must read the
  repository over https without asking anything. Either run `gh auth login`, choose
  HTTPS and let it authenticate git; or use an SSH key that needs no typed passphrase (one
  in your ssh-agent) and send GitHub's https URLs through it:

  ```sh
  git config --global url."git@github.com:".insteadOf "https://github.com/"
  ```

  Then check it the way setup does. It must print one line and ask nothing:

  ```sh
  GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND='ssh -o BatchMode=yes' git ls-remote https://github.com/DeanLight/deep_reasoner_beta HEAD
  ```

  On a Mac, a credential helper git names without a path (`gh`, `git-credential-manager`)
  must be in Homebrew's `/opt/homebrew/bin` or `/usr/local/bin`: beyond the system's own
  folders, an app opened from Finder looks nowhere else.
- **The network**, on the first launch and the first launch after an update.

Nothing else: the app brings its own uv and Node, and uv brings Python 3.12.

### Download

A `v*` tag gets a release on the
[Releases page](https://github.com/michaeltheologitis/deep-reasoning/releases) with these
files; until the first tag, take them from a build run by hand (below).

| File | For |
|---|---|
| `deep-reasoning-<version>-arm64.dmg` | macOS 14 or later, Apple silicon |
| `deep-reasoning-<version>-amd64.deb` | Debian, Ubuntu and their kin, x86-64 |
| `deep-reasoning-<version>-x86_64.AppImage` | any other Linux, x86-64 |

A build run by hand (Actions → desktop-release → Run workflow) keeps the same files as the
run's artifacts, `desktop-macos` and `desktop-linux`, zipped; downloading them needs a
GitHub sign-in.

### macOS

1. Open the `.dmg` and drag **Deep Reasoning** to Applications.
2. The app is not signed, so macOS would refuse to open it. Clear the download's quarantine
   flag, once:

   ```sh
   xattr -dr com.apple.quarantine "/Applications/Deep Reasoning.app"
   ```

3. Open Deep Reasoning from Applications. On a macOS older than 14 it does not open: the
   packages its setup installs need macOS 14.

### Linux

- **`.deb`** (the package CI installs and drives end to end):
  `sudo apt install ./deep-reasoning-<version>-amd64.deb`, then open Deep Reasoning from your
  applications menu. It installs under `/opt/Deep Reasoning/`.
- **`.AppImage`**: `chmod +x deep-reasoning-<version>-x86_64.AppImage`, then run it.

### The first launch

A splash shows each line setup prints. Setup:

1. says where your data will live (`your data: …`);
2. checks git, and that your credentials can read deep_reasoner_beta;
3. says what the app protects and what it does not ([below](#what-the-app-protects-and-what-it-does-not)),
   with the spend cap;
4. installs deep-reasoning and deep_reasoner, at the commits this app was built with and
   every dependency at its locked version, into `~/.deep-reasoning/runtime/`. It says this
   takes a few minutes; on GitHub's macOS runner, with a fast network, the install takes
   under 20 s, and setup's two phases, with the agent-server starting between them, about a
   minute;
5. once the agent-server is up, makes the **deep_reasoner** agent profile the default, and
   installs, approves and starts the Library App (`App dr-library … installed · backend ready`).

A later launch with nothing changed installs nothing and needs no network. After an update,
setup installs once more.

If setup fails, the window stays on the failure, and setup's last line says why and what to
do. A setup still running at 15 minutes is stopped and the launch fails; the next launch
starts again, keeping what uv already downloaded. The splash does not show git waiting for a
credential: if setup stops moving, quit, and run the check under
[What you need](#what-you-need) in a terminal.

Then, in the window:

1. Onboarding opens on **Choose your agent** with **deep_reasoner** already chosen. Keep it
   and press **Next**: there is no model to set up, because deep_reasoner reads its key from
   Canvas's secrets.
2. On **Say hello**, press **Close** instead of sending, since deep_reasoner has no key yet:
   add `OPENAI_API_KEY` under **Settings → Secrets**, with your OpenAI API key as its value.
   Until one is saved, every launch's setup says so.
3. Start a conversation and ask.

### `dr-app` and `dr` in a terminal

Setup links two commands into `~/.deep-reasoning/bin`, and does not touch your `PATH` or
your shell's files. To call them by name, add the folder to your `PATH` (here for zsh,
macOS's shell; for bash, use `~/.bashrc`):

```sh
echo 'export PATH="$HOME/.deep-reasoning/bin:$PATH"' >> ~/.zshrc
```

- `dr-app export DIR [--namespace NAME]` writes your Library to `DIR/main.yaml`, a config
  that deep_reasoner's `dr` runs unchanged. It works while the app runs.
- `dr-app home` prints where your data lives (on Linux, with its filesystem type).
  `dr-app home DIR` keeps it in `DIR` from the next launch. `DIR` must be an absolute path to
  a folder on this computer that you own, of at most 55 bytes on Linux and 51 on macOS:
  deep_reasoner's Claude runs serve sockets under it, and a longer path is refused. Nothing
  is moved: copy `library.sqlite`, `runs/`, `sessions/` and `spend/` yourself, or export the
  Library and import it there.
- `dr` is deep_reasoner's own command line, from the same install.

Both exist once the first launch has installed them.

### Where your data lives

| Path | What |
|---|---|
| `~/.deep-reasoning/` | everything the app writes, readable only by you |
| `~/.deep-reasoning/canvas/` | Canvas's settings, secrets (encrypted), agent profiles and Apps; `agent-canvas/` in it holds your conversations |
| `~/.deep-reasoning/runtime/`, `bin/` | the installed deep-reasoning and deep_reasoner, and the two commands |
| `~/.deep-reasoning/canvas-app/` | the Library App as setup staged it for this computer: its manifest, panel and backend |
| `~/.deep-reasoning/setup.json`, `setup.lock` | what setup last did, and the folder `dr-app home` chose; a lock held while setup runs, so a launch and a terminal run never overlap |
| your data home | the Library (`library.sqlite`), `runs/`, `sessions/`, `prices.yaml`, and the spend ledgers (`spend/`) |

Your data home is `~/.deep-reasoning` itself, unless you chose another folder with
`dr-app home DIR`. On Linux, when your home folder is on a network filesystem (NFS and the
like, where the Library's database is unsafe), it is `/var/tmp/deep-reasoning-<uid>`, where
the system may delete files unused for 30 days: export your Library now and then, or choose
another folder. A `dr-acp` or `dr-library` run in a terminal without `--home` uses
`~/.deep-reasoning`, so on a local home it shares the app's Library.

### Uninstall

1. To keep your Library, export it first: `~/.deep-reasoning/bin/dr-app export ~/library-export`.
2. Delete the app: on macOS, drag Deep Reasoning from Applications to the Trash; a `.deb`,
   `sudo apt remove deep-reasoning`; an `.AppImage`, delete the file.
3. Delete what it wrote: `rm -rf ~/.deep-reasoning`, and also
   `/var/tmp/deep-reasoning-<uid>` (`rm -rf /var/tmp/deep-reasoning-$(id -u)`) if it was
   your data home, and any folder you chose with `dr-app home`. Electron keeps its window
   state and caches in `~/Library/Application Support/Deep Reasoning` on macOS and
   `~/.config/Deep Reasoning` on Linux.

uv's cache and the Pythons it manages are shared with any other use of uv, and stay.

## What the app protects, and what it does not

Setup says this at the first install, and the Library panel says it the first time it opens:

> deep_reasoner runs as you. It can read and change any file you can, and code it writes can find your model keys on this computer if it tries. Spend through the key proxy stops at $5 per conversation.

**It protects against accidents** (a key that ends up in a log, a transcript or a printout;
a loop that spends without end): `dr-acp`'s worker gets a token instead of your provider
key, so the key is not in its environment, in a process it starts, in the transcript or in
the run log; spending through the proxy stops at the cap; the agent-server's own secrets are
kept from the worker; usage reports are off; nothing of deep_reasoner is in the download.

**It does not protect against code that sets out to get around it.** Code deep_reasoner
writes runs as you, so it can:

- read every key you saved in Canvas: its secrets are encrypted with a key file you can
  read, and the agent-server's session key, also in a file, unlocks them all; on Linux it
  can also read the environments of `dr-acp` and the agent-server, which hold the keys;
- get past the cap: edit its ledger, raise the cap in the profile, or call the provider with
  a key it found;
- read and change any file you can, and reach anything your computer can on the network;
  the conversation's folder is not a boundary.

And, by design:

- Your Canvas secrets that are not provider keys (a `GITHUB_TOKEN` for a tool, say) reach
  the agent, because its tools need them. Tools and MCP servers run as you; a stdio MCP
  server gets whatever its settings give it, a provider key included.
- A key code prints after reading it from disk lands in the run log (the transcript masks
  it; the run log does not).
- On macOS, the Library's backend is HTTP on 127.0.0.1 with no sign-in, which any user of
  the same Mac could reach.
- deep_reasoner's Claude Code backbone, when it runs on your machine's own `claude` sign-in,
  calls Anthropic directly, past the proxy and the cap.
- The app is unsigned: on macOS you clear the quarantine flag yourself, so you trust what you
  downloaded. deep-reasoning and its releases are public; deep_reasoner_beta is private, is
  in no package, and is installed on your computer with your own git credentials.

The cap is `$5` per conversation, set by the **deep_reasoner** agent profile's arguments
(`--spend-cap-usd 5`); change it there, and setup keeps your change.
