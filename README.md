# Github CI Status for xbar

Displays an icon in your macOS menu bar with a dropdown showing the CI check statuses of your open GitHub Pull Requests.

A rewrite of [jordanandree/bitbar-github-ci](https://github.com/jordanandree/bitbar-github-ci) in Python, using the [GitHub CLI (`gh`)](https://cli.github.com/) for authentication instead of a personal access token.

## Features

- Shows CI status for all your open PRs across configured repos
- Supports both GitHub Actions (check runs) and legacy commit statuses
- Sends macOS notifications when CI status changes (e.g. pending -> passed/failed)
- Clickable links to PRs and individual check runs
- GitHub Enterprise support

## Prerequisites

- [xbar](https://xbarapp.com/) (v2.x)
- Python 3
- [GitHub CLI (`gh`)](https://cli.github.com/), authenticated:

```sh
brew install gh
gh auth login
```

## Installation

1. Copy `github-ci.1m.py` to your xbar plugins directory:

```sh
cp github-ci.1m.py ~/Library/Application\ Support/xbar/plugins/
chmod +x ~/Library/Application\ Support/xbar/plugins/github-ci.1m.py
```

2. Configure the plugin variables in xbar (Preferences > Plugins > Github CI Status):

| Variable | Description | Example |
|---|---|---|
| `VAR_GITHUB_USERNAME` | Your GitHub username | `joloppo` |
| `VAR_GITHUB_REPOS` | Comma-separated list of repos to monitor | `owner/repo1,owner/repo2` |
| `VAR_GITHUB_HOSTNAME` | GitHub hostname (default: `github.com`) | `github.example.com` |

3. Refresh xbar or wait for the next poll interval (default: 1 minute).

## Refresh interval

The refresh interval is encoded in the filename. Rename the file to change it:

- `github-ci.1m.py` - every minute
- `github-ci.5m.py` - every 5 minutes
- `github-ci.30s.py` - every 30 seconds

## Notifications

The plugin tracks CI state between runs and sends native macOS notifications when a PR's CI status changes (e.g. from pending to passed or failed). State is stored in a `.state.json` sidecar file alongside the plugin.

## Credits

Originally created by [Jordan Andree](https://github.com/jordanandree) as a PHP/BitBar plugin. Rewritten in Python for xbar with `gh` CLI authentication by [Joscha Gutjahr](https://github.com/joloppo).
