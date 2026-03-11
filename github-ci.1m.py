#!/usr/bin/env python3

# <xbar.title>Github CI Status</xbar.title>
# <xbar.version>v2.2</xbar.version>
# <xbar.author>Joscha Gutjahr</xbar.author>
# <xbar.author.github>joloppo</xbar.author.github>
# <xbar.desc>Displays Github Pull Request CI Check statuses using the gh CLI</xbar.desc>
# <xbar.dependencies>python3,gh</xbar.dependencies>
# <xbar.abouturl>https://github.com/joloppo/xbar-github-ci</xbar.abouturl>
#
# <xbar.var>string(VAR_GITHUB_USERNAME=""): Your GitHub username.</xbar.var>
# <xbar.var>string(VAR_GITHUB_REPOS=""): Comma-separated list of repos (e.g. owner/repo1,owner/repo2).</xbar.var>
# <xbar.var>string(VAR_GITHUB_HOSTNAME="github.com"): GitHub hostname (change for GitHub Enterprise).</xbar.var>
#
# Icon sourced from feather icons: https://feathericons.com/
#
# Requires the GitHub CLI (gh) to be installed and authenticated:
#   brew install gh
#   gh auth login

import json
import os
import shutil
import subprocess
import sys

# --- Ensure gh is discoverable ---
# xbar runs plugins with a minimal PATH that typically excludes Homebrew and
# other common install locations. Prepend them so subprocess can find `gh`.
EXTRA_PATHS = [
    "/opt/homebrew/bin",  # Homebrew on Apple Silicon
    "/usr/local/bin",  # Homebrew on Intel / manual installs
    "/run/current-system/sw/bin",  # NixOS / nix-darwin
    os.path.expanduser("~/.nix-profile/bin"),  # Nix per-user
    os.path.expanduser("~/go/bin"),  # go install
    os.path.expanduser("~/bin"),
]
os.environ["PATH"] = (
    os.pathsep.join(EXTRA_PATHS) + os.pathsep + os.environ.get("PATH", "")
)

# --- Configuration via xbar variables (environment) ---

USERNAME = os.environ.get("VAR_GITHUB_USERNAME", "").strip()
REPOS = [
    r.strip() for r in os.environ.get("VAR_GITHUB_REPOS", "").split(",") if r.strip()
]
HOSTNAME = os.environ.get("VAR_GITHUB_HOSTNAME", "github.com").strip()

ICON = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAAlwSFlzAAAW"
    "JQAAFiUBSVIk8AAABDtpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6"
    "eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDUuNC4wIj4KICAgPHJkZjpSREYg"
    "eG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4K"
    "ICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6eG1w"
    "PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIgogICAgICAgICAgICB4bWxuczp4bXBNTT0i"
    "aHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgICAgICAgICAgeG1sbnM6c3RSZWY9"
    "Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiCiAgICAgICAg"
    "ICAgIHhtbG5zOnRpZmY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vdGlmZi8xLjAvIj4KICAgICAgICAg"
    "PHhtcDpDcmVhdG9yVG9vbD5BZG9iZSBQaG90b3Nob3AgQ0MgMjAxNyAoTWFjaW50b3NoKTwveG1w"
    "OkNyZWF0b3JUb29sPgogICAgICAgICA8eG1wTU06RG9jdW1lbnRJRD54bXAuZGlkOjVEMzE5OTBG"
    "REQzRTExRTdCNjU1Q0M4MUYwMENBMTNDPC94bXBNTTpEb2N1bWVudElEPgogICAgICAgICA8eG1w"
    "TU06RGVyaXZlZEZyb20gcmRmOnBhcnNlVHlwZT0iUmVzb3VyY2UiPgogICAgICAgICAgICA8c3RS"
    "ZWY6aW5zdGFuY2VJRD5hZG9iZTpkb2NpZDpwaG90b3Nob3A6ODMzYTI0NjgtMjVhOC0xMTdiLTkx"
    "NzEtZjU1MDA2YWFhMDcyPC9zdFJlZjppbnN0YW5jZUlEPgogICAgICAgICAgICA8c3RSZWY6ZG9j"
    "dW1lbnRJRD5hZG9iZTpkb2NpZDpwaG90b3Nob3A6ODMzYTI0NjgtMjVhOC0xMTdiLTkxNzEtZjU1"
    "MDA2YWFhMDcyPC9zdFJlZjpkb2N1bWVudElEPgogICAgICAgICA8L3htcE1NOkRlcml2ZWRGcm9t"
    "PgogICAgICAgICA8eG1wTU06SW5zdGFuY2VJRD54bXAuaWlkOjVEMzE5OTBFREQzRTExRTdCNjU1"
    "Q0M4MUYwMENBMTNDPC94bXBNTTpJbnN0YW5jZUlEPgogICAgICAgICA8dGlmZjpPcmllbnRhdGlv"
    "bj4xPC90aWZmOk9yaWVudGF0aW9uPgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6"
    "UkRGPgo8L3g6eG1wbWV0YT4K4XbDnwAAAxFJREFUWAnNl1uITlEUxweTonG/y2UYIsUUUSIP84zw"
    "IELNk9LwwpsXmhEvk8sTKZq8eBJJXqQUuV+SUJPmySXjEpM7g9//m73OrDnO/r75Lg9W/WatvfZa"
    "6+y9z977fFNVlS0NuD/BH+iAw1AHxUgNwdvhBnSDarVCHxnQp9XbOI+5qreZs1TgOLTBfJgNI2EU"
    "fIH38BwegAZ7AMaAlx80xsNH78yyVVAP7AJbCbVL4Td5r1zuSuxEBiZWrzEWc0hoXkRPhF3wIfj6"
    "qzTYNpgDO8BkqhnS1b4RbD8oFdEKHIRTsBO05Frmh9AJGthQGA1zYVGwT6BvgWRBj8r9jb32JEQ"
    "B9graE295Rgvp9vr67C0/W3vEYozBoTHDnGVqbViTpWbE9BU6bLTNsaAi/ZrU91BXJ2FaLL8+BG"
    "kAes+DYoEl+HeTYxPbH8v3QY2xoBL9I8jT7DWI+7EaJ0OAgqbHgsrw3w71P1uN9CbUUTIpeFtZY"
    "BHa7hId25ykB6BbyyR9jZq/HO0nmKuTHsBLV32Ssytl2u5/bQXTA3hiHegVzq6EqbtgXCj01AqmB"
    "3DZOtBrnF0Jc60r4p/j3D3mdZSd1/X/9JbmmEDam1D3F7oWotJAjw1A34TV0cj+deg43wGreaw/a"
    "YdcghIvgL7jyfHBzie6QXX96ivqf09ojw2DgqK9cQRs1KZ1k90FzWIyeFHOXrgGXWA5pnW1T4FM2"
    "YxXH4t7sNxFrMNuByvitQboZRkN32+2BrMP7EeOz0ns01iWoFlqH5hoZlp+f00rdqMFBK1fUp1gd"
    "bQS22A4FJR5RFwFS36HPTOVtdD1a09kySacVqM1KyCfTxvnrCvwDHuWS9jg+rY6vzc1WxvAGd8Rs"
    "6tdRzf2FtDS1UMdPIZLoDMsn4leU5bofZtoQiWJrstHYDPJ0o15Klv8uTwxSZc2WFo02yWwB16kO"
    "yvdzhqAnvEVmkHnVue9Fpqg4uL3QKy4/quR6FquuMRWIOtBfoN5Ox37Mzi0igWlmJ3aQbUauAlHQ"
    "acmSxT3DVrgbVbAf+X7C2311IYwO5eYAAAAAElFTkSuQmCC"
)

STATUS_COLORS = {
    "success": "green",
    "failure": "red",
    "pending": "blue",
    "error": "red",
    "warning": "orange",
}

STATUS_ICONS = {
    "success": ":white_check_mark:",
    "failure": ":x:",
    "pending": ":hourglass:",
    "error": ":exclamation:",
    "warning": ":warning:",
}

# Map GitHub check run conclusions to a unified state
CHECK_RUN_STATE = {
    "success": "success",
    "failure": "failure",
    "neutral": "success",
    "cancelled": "failure",
    "timed_out": "failure",
    "action_required": "warning",
    "skipped": "success",
    "stale": "pending",
}

# Priority for computing the overall state (higher = worse)
STATE_PRIORITY = {
    "success": 0,
    "pending": 1,
    "warning": 2,
    "failure": 3,
    "error": 4,
}

# Human-readable labels for notification messages
STATE_LABELS = {
    "success": "passed",
    "failure": "failed",
    "error": "errored",
    "pending": "pending",
    "warning": "has warnings",
}

# --- State persistence ---
# State file lives alongside the plugin, e.g. github-ci.1m.py.state.json
STATE_FILE = os.path.realpath(__file__) + ".state.json"

# --- Hidden PRs ---
# Stores a list of PR keys (e.g. "owner/repo#123") the user has chosen to hide
HIDDEN_FILE = os.path.realpath(__file__) + ".hidden.json"
SELF_PATH = os.path.realpath(__file__)


def load_state():
    """Load the previous run's state from disk."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_state(state):
    """Persist current state to disk."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except OSError:
        pass  # Non-critical; notifications just won't work next run


def load_hidden():
    """Load the set of hidden PR keys from disk."""
    try:
        with open(HIDDEN_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return set()


def save_hidden(hidden):
    """Persist hidden PR keys to disk."""
    try:
        with open(HIDDEN_FILE, "w") as f:
            json.dump(sorted(hidden), f, indent=2)
    except OSError:
        pass


def handle_hide_unhide():
    """Handle --hide / --unhide CLI arguments and exit."""
    if len(sys.argv) < 3:
        return False
    action = sys.argv[1]
    pr_key = sys.argv[2]
    if action not in ("--hide", "--unhide"):
        return False
    hidden = load_hidden()
    if action == "--hide":
        hidden.add(pr_key)
    elif action == "--unhide":
        hidden.discard(pr_key)
    save_hidden(hidden)
    return True


NOTIFICATION_ICON = "https://github.githubassets.com/favicons/favicon.png"


def send_notification(title, message, url=None):
    """Send a macOS notification, preferring terminal-notifier for custom icons."""
    notifier = shutil.which("terminal-notifier")
    try:
        if notifier:
            cmd = [
                notifier,
                "-title",
                title,
                "-message",
                message,
                "-appIcon",
                NOTIFICATION_ICON,
            ]
            if url:
                cmd += ["-open", url]
            subprocess.run(cmd, capture_output=True, timeout=5)
        else:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5,
            )
    except (subprocess.TimeoutExpired, OSError):
        pass  # Non-critical


def check_and_notify(current_pr_states):
    """Compare current PR states against previous run and notify on changes."""
    previous = load_state()

    for pr_key, current in current_pr_states.items():
        prev = previous.get(pr_key)

        # Skip if this PR is new (first time seeing it) or state unchanged
        if prev is None:
            continue
        if prev.get("state") == current["state"]:
            continue
        # Skip transitions from one non-terminal state to another
        # (e.g. pending -> pending is already filtered above)
        prev_state = prev.get("state", "pending")
        curr_state = current["state"]

        # Only notify when all checks have settled (no pending/warning)
        # and the overall PR state actually changed.
        if curr_state in ("pending", "warning"):
            continue

        label = STATE_LABELS.get(curr_state, curr_state)
        title = current.get("title", pr_key)
        pr_url = current.get("url")
        send_notification("GitHub CI", f"{title} {label}", url=pr_url)

    save_state(current_pr_states)


def find_gh():
    """Locate the gh binary, raising a clear error if not found."""
    path = shutil.which("gh")
    if path is None:
        raise RuntimeError("gh CLI not found in PATH. Install it with: brew install gh")
    return path


GH_BIN = None


def gh_api(endpoint, params=None):
    """Call the GitHub API via the gh CLI."""
    global GH_BIN
    if GH_BIN is None:
        GH_BIN = find_gh()
    # Build the URL with query params inline. Using -f/--field would cause
    # gh to send a POST request, but we always want GET here.
    if params:
        from urllib.parse import urlencode

        endpoint = f"{endpoint}?{urlencode(params)}"
    cmd = [GH_BIN, "api", "--method", "GET"]
    if HOSTNAME != "github.com":
        cmd += ["--hostname", HOSTNAME]
    cmd.append(endpoint)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        raise RuntimeError("gh API request timed out")
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "auth login" in stderr or "not logged" in stderr.lower():
            raise RuntimeError("gh is not authenticated. Run: gh auth login")
        raise RuntimeError(f"gh API error: {stderr}")
    return json.loads(result.stdout)


def search_pull_requests():
    """Find open PRs authored by USERNAME in the configured repos."""
    q_parts = [f"state:open author:{USERNAME} type:pr"]
    for repo in REPOS:
        q_parts.append(f"repo:{repo}")
    q = " ".join(q_parts)
    data = gh_api("search/issues", {"q": q})
    return data.get("items", [])


def get_pull_request(repo, number):
    """Fetch a single pull request."""
    return gh_api(f"repos/{repo}/pulls/{number}")


def get_combined_status(repo, sha):
    """Fetch the combined commit status (legacy status API)."""
    return gh_api(f"repos/{repo}/commits/{sha}/status")


def get_check_runs(repo, sha):
    """Fetch check runs for a commit (checks API - used by GitHub Actions)."""
    return gh_api(f"repos/{repo}/commits/{sha}/check-runs")


def worst_state(a, b):
    """Return the more severe of two states."""
    if STATE_PRIORITY.get(b, 0) > STATE_PRIORITY.get(a, 0):
        return b
    return a


def format_line(state, text, url, indent=0):
    """Format a single xbar menu line."""
    prefix = "--" * indent
    icon = STATUS_ICONS.get(state, ":grey_question:")
    color = STATUS_COLORS.get(state, "gray")
    return f"{prefix}{icon} {text} | href={url} color={color}"


def main():
    # Handle hide/unhide actions triggered from the menu
    if handle_hide_unhide():
        return

    if not USERNAME:
        print(f":octocat: GH CI | templateImage={ICON}")
        print("---")
        print("VAR_GITHUB_USERNAME is not set | color=red")
        print("Configure it in xbar plugin settings | color=gray")
        return

    if not REPOS:
        print(f":octocat: GH CI | templateImage={ICON}")
        print("---")
        print("VAR_GITHUB_REPOS is not set | color=red")
        print("Configure it in xbar plugin settings | color=gray")
        return

    try:
        pull_requests = search_pull_requests()
    except RuntimeError as e:
        print(f":x: GH CI | templateImage={ICON}")
        print("---")
        print(f"Error: {e} | color=red")
        return

    if not pull_requests:
        print(f":white_check_mark: GH CI | templateImage={ICON}")
        print("---")
        print("No open Pull Requests | color=gray")
        save_state({})
        return

    overall_state = "success"
    lines = []
    current_pr_states = {}
    hidden = load_hidden()
    hidden_prs = []  # Track hidden PRs for the submenu

    for pr in pull_requests:
        repo = pr["repository_url"].replace("https://api.github.com/repos/", "")
        number = pr["number"]
        title = pr["title"]
        pr_url = pr["html_url"]

        try:
            pr_detail = get_pull_request(repo, number)
            head_sha = pr_detail["head"]["sha"]

            # Gather statuses from both the legacy status API and the checks API
            checks = []

            # Legacy commit statuses (e.g. external CI integrations)
            combined = get_combined_status(repo, head_sha)
            for status in combined.get("statuses", []):
                checks.append(
                    {
                        "state": status["state"],
                        "name": status["context"],
                        "url": status.get("target_url") or pr_url,
                    }
                )

            # Check runs (GitHub Actions, etc.)
            check_runs_data = get_check_runs(repo, head_sha)
            for run in check_runs_data.get("check_runs", []):
                if run["status"] == "completed":
                    conclusion = run.get("conclusion", "failure")
                    state = CHECK_RUN_STATE.get(conclusion, "failure")
                else:
                    state = "pending"
                checks.append(
                    {
                        "state": state,
                        "name": run["name"],
                        "url": run.get("html_url") or run.get("details_url") or pr_url,
                    }
                )

            # Derive PR state from the actual checks rather than trusting
            # the combined status API (which returns "pending" when there
            # are no legacy statuses, even if all check runs passed).
            if checks:
                pr_state = "success"
                for check in checks:
                    pr_state = worst_state(pr_state, check["state"])
            else:
                pr_state = "success"

        except RuntimeError:
            pr_state = "error"
            checks = []

        pr_key = f"{repo}#{number}"
        current_pr_states[pr_key] = {
            "state": pr_state,
            "title": f"{repo}#{number}: {title}",
            "url": pr_url,
        }

        if pr_key in hidden:
            hidden_prs.append((pr_key, pr_state, f"{repo}#{number}: {title}", pr_url))
            continue

        overall_state = worst_state(overall_state, pr_state)

        lines.append(format_line(pr_state, f"{repo}#{number}: {title}", pr_url))
        # Hide action as a submenu item under each PR
        lines.append(
            f"--Hide this PR | shell={SELF_PATH} param1=--hide param2={pr_key}"
            f" terminal=false refresh=true"
        )
        for check in checks:
            lines.append(
                format_line(check["state"], check["name"], check["url"], indent=1)
            )

    # Compare against previous run and send macOS notifications for changes
    check_and_notify(current_pr_states)

    # Menu bar title
    bar_icon = STATUS_ICONS.get(overall_state, ":octocat:")
    print(f"{bar_icon} | templateImage={ICON}")
    print("---")
    if lines:
        print("\n".join(lines))
    else:
        print("All PRs are hidden | color=gray")

    # Hidden PRs submenu
    if hidden_prs:
        print("---")
        print(f"Hidden ({len(hidden_prs)})")
        for pr_key, pr_state, pr_title, pr_url in hidden_prs:
            icon = STATUS_ICONS.get(pr_state, ":grey_question:")
            color = STATUS_COLORS.get(pr_state, "gray")
            print(f"--{icon} {pr_title} | href={pr_url} color={color}")
            print(
                f"--Unhide this PR | shell={SELF_PATH} param1=--unhide"
                f" param2={pr_key} terminal=false refresh=true"
            )


if __name__ == "__main__":
    main()
