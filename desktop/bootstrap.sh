# The setup command (C3 §4.2): explain the two failures that happen before dr-app exists, then run it.
set -u
export GIT_TERMINAL_PROMPT=0
: "${GIT_SSH_COMMAND:=ssh -o BatchMode=yes}"
export GIT_SSH_COMMAND
case "$(uname -s)" in Darwin) PATH="$PATH:/opt/homebrew/bin:/usr/local/bin" ;; esac
if ! git --version >/dev/null 2>&1; then
  echo "✗ deep_reasoner is fetched with git, which was not found. On macOS run xcode-select --install; on Linux install git."
  exit 10
fi
uvx --from "$1" dr-app setup --repo "$2" --commit "$3"
status=$?
if [ "$status" -ne 0 ] && { [ "$status" -lt 10 ] || [ "$status" -gt 19 ]; } && ! git ls-remote "$2" HEAD >/dev/null 2>&1; then
  echo "✗ Could not fetch ${2#https://}: check that this computer is online, and that your git credentials can read it. It is private: ask Michael for read access, then sign git in for https (gh auth login, or an SSH key and git config --global url.\"git@github.com:\".insteadOf \"https://github.com/\") and restart. Nothing was installed."
fi
exit "$status"
