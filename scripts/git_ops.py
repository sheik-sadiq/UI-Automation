
"""
git_ops.py
==========
All git and GitHub CLI operations used by the auto-heal bot:

  push_and_open_pr(fix_summary)
      Creates a bot branch, stages pages/ only, commits, pushes,
      and opens a PR against main via the `gh` CLI.

  open_github_issue(title, body)
      Opens a GitHub Issue for graceful escalation when healing fails.
"""
import os
import subprocess
from datetime import date


def _run(cmd: list, **kwargs) -> subprocess.CompletedProcess:
    """Run a shell command, raise on non-zero exit."""
    return subprocess.run(cmd, check=True, **kwargs)


def push_and_open_pr(fix_summary: list) -> None:
    """
    Commit pages/ changes to a bot branch and open a PR against main.

    Branch name format: bot/auto-heal-<short-sha>-<YYYY-MM-DD>
    PR title format  : 🤖 auto-heal: fix N broken locator(s) [YYYY-MM-DD]
    """
    sha_short = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"]
    ).decode().strip()

    today  = date.today().isoformat()
    branch = f"bot/auto-heal-{sha_short}-{today}"
    repo   = os.environ["GITHUB_REPOSITORY"]

    _run(["git", "checkout", "-b", branch])
    _run(["git", "add", "pages/"])
    _run(["git", "commit", "-m",
          f"🤖 auto-heal: fix {len(fix_summary)} broken locator(s)"])
    _run(["git", "push", "origin", branch])

    body = (
        "## 🤖 Auto-Heal Bot\n\n"
        "The following locators were automatically diagnosed and fixed "
        f"on `{today}`:\n\n"
        + "\n".join(fix_summary)
        + "\n\n---\n"
        "_Opened automatically by the auto-heal GitHub Actions bot._\n"
        "_Please review the diff carefully before merging._"
    )

    _run([
        "gh", "pr", "create",
        "--repo",  repo,
        "--base",  "main",
        "--head",  branch,
        "--title", f"🤖 auto-heal: fix {len(fix_summary)} broken locator(s) [{today}]",
        "--body",  body,
    ])

    print(f"[GIT] PR opened: {branch} → main")


ISSUE_LABELS = ["auto-heal", "needs-human"]


def _ensure_labels(repo: str) -> None:
    """Create issue labels if they don't already exist in the repo."""
    label_defs = {
        "auto-heal":   ("Bot-generated heal attempt", "e11d48"),  # red-ish
        "needs-human": ("Requires human investigation", "f97316"), # orange
    }
    for name, (desc, colour) in label_defs.items():
        subprocess.run(
            ["gh", "label", "create", name,
             "--repo",        repo,
             "--description", desc,
             "--color",       colour,
             "--force"],       # --force = update if already exists, no error
            check=False,       # never crash if this fails
            capture_output=True,
        )


def open_github_issue(title: str, body: str) -> None:
    """
    Open a GitHub Issue to escalate when the heal bot cannot fix failures.
    Labels are created automatically if they don't exist yet.
    """
    repo = os.environ["GITHUB_REPOSITORY"]
    _ensure_labels(repo)
    _run([
        "gh", "issue", "create",
        "--repo",  repo,
        "--title", title,
        "--body",  body,
        "--label", ",".join(ISSUE_LABELS),
    ])
    print(f"[GIT] Issue opened: {title}")
