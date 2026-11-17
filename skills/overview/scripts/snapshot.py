#!/usr/bin/env python3
"""Snapshot an umbrella folder: its workspaces, their Claude sessions, PRs and issues.

  snapshot.py [--umbrella DIR]            print the snapshot as JSON
  snapshot.py [--umbrella DIR] --watch    print one line per meaningful change, forever
  snapshot.py [--umbrella DIR] --discover print a proposed .overview/config.json
  snapshot.py [--umbrella DIR] --board    print the board as text; with --watch, redraw it live

Standard library only and Python 3.9 compatible, so /usr/bin/python3 runs it whatever the
umbrella's mise pins.
"""

import argparse
import calendar
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

LOCAL_INTERVAL = 5
REMOTE_TTL = 90
WAITING_LONG = 5 * 60
STALLED = 20 * 60
RECENT_CLOSED = 12 * 3600
TITLE_WIDTH = 40
REGISTRY = os.path.expanduser("~/.claude/sessions")
PROJECTS = os.path.expanduser("~/.claude/projects")
REGISTRY_FIELDS = ("pid", "sessionId", "cwd", "name", "status", "statusUpdatedAt")
TRACKER_ID = re.compile(r"(?<![\w/])(#\d+|[A-Z][A-Z0-9]+-\d+)\b")
# /skills:pr names Linear-tracked bookmarks like max/dev-35-set-custom-domains.
BOOKMARK_ID = re.compile(r"^[^/]+/([a-z][a-z0-9]*-\d+)-")
SEP = "\x1f"


def run(cmd, cwd=None, timeout=20):
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout if out.returncode == 0 else None


def jj(path, *args):
    # --ignore-working-copy: never snapshot a working copy that belongs to another session.
    return run(["jj", "--ignore-working-copy", "--no-pager", "--color=never", "-R", path] + list(args))


def tracker_ids(text):
    return TRACKER_ID.findall(text or "")


# --- discovery ---------------------------------------------------------------------------


def github_slug(url):
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url or "")
    return m.group(1) if m else None


def jj_store(path):
    # The workspace that created the repo holds the store in .jj/repo; every other workspace
    # has a file there pointing at it. (`jj workspace list` can't group them: workspaces made
    # by older jj versions have no recorded root.)
    store = os.path.join(path, ".jj", "repo")
    if os.path.isfile(store):
        with open(store) as f:
            store = os.path.join(path, ".jj", f.read().strip())
    return os.path.realpath(store)


def discover(umbrella):
    groups = {}
    nested = {}
    for entry in sorted(os.listdir(umbrella)):
        path = os.path.join(umbrella, entry)
        if entry.startswith(".") or not os.path.isdir(path):
            continue
        if os.path.isdir(os.path.join(path, ".jj")):
            groups.setdefault(jj_store(path), []).append(entry)
        elif os.path.exists(os.path.join(path, ".git")):
            groups[path] = [entry]
        else:
            inner = sorted(e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e, ".jj"))
                           or os.path.exists(os.path.join(path, e, ".git")))
            if inner:
                nested[entry] = inner
    repos = {}
    for store, members in groups.items():
        path = os.path.join(umbrella, members[0])
        if store.endswith(os.path.join(".jj", "repo")):
            name = os.path.basename(os.path.dirname(os.path.dirname(store)))
            remotes = jj(path, "git", "remote", "list") or ""
            origin = next((l.split(None, 1)[1] for l in remotes.splitlines() if l.startswith("origin ")), None)
        else:
            name = members[0]
            origin = (run(["git", "-C", path, "remote", "get-url", "origin"]) or "").strip()
        github = github_slug(origin)
        repos[name] = {
            "github": github,
            "tracker": "github" if github else None,
            "workspaces": members,
            "watch": github is not None,
        }
    # Not part of the config: folders that hold repos a level down, for init to ask about.
    return {"repos": repos, "nested": nested}


# --- sessions ----------------------------------------------------------------------------


def alive(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError, TypeError):
        return True
    return True


def transcript(cwd, session_id):
    path = os.path.join(PROJECTS, re.sub(r"[^A-Za-z0-9-]", "-", cwd), session_id + ".jsonl")
    if os.path.exists(path):
        return path
    found = glob.glob(os.path.join(PROJECTS, "*", session_id + ".jsonl"))
    return found[0] if found else None


_prompts = {}


def prompts(path):
    """The last thing a human typed, cut to 80 characters; the tracker IDs of the latest prompt
    that names any; and whether the session's last words since then were a question.
    A task starts with `/skills:task implement #57` and the prompts after it rarely repeat the
    number, so the IDs have to outlive the prompt that carried them, often by megabytes of
    transcript. The file is read once, then only what was appended since."""
    offset, head, ids, asked = _prompts.get(path, (0, None, [], False))
    if os.path.getsize(path) < offset:
        offset, head, ids, asked = 0, None, [], False
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read()
    complete = data[:data.rfind(b"\n") + 1]
    for kind, text in turns(complete.decode("utf-8", "replace").splitlines()):
        if kind == "prompt":
            head, asked = text[:80], False
            ids = tracker_ids(text) or ids
        else:
            asked = asks(text)
    _prompts[path] = (offset + len(complete), head, ids, asked)
    return head, ids, asked


def asks(text):
    # A turn that ends on a question leaves the session idle, not waiting, though it is the
    # user's move: "Shall I commit?" in an otherwise empty workspace is not a free workspace.
    # Sessions often add a closing line after the question, so look at the last two lines of
    # prose, leaving out code, where a "?" means nothing.
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    lines = [re.sub(r"`[^`]*`", "", l) for l in prose.splitlines() if l.strip()]
    return any(re.search(r"\?(\s|$|\*)", l) for l in lines[-2:])


def turns(lines):
    """("prompt", text) for each prompt the user typed and ("said", text) for each message the
    session wrote, oldest first."""
    for line in lines:
        if '"user"' not in line and '"assistant"' not in line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("isMeta") or row.get("isSidechain"):
            continue
        if row.get("type") == "assistant":
            content = row.get("message", {}).get("content")
            texts = [c.get("text", "") for c in content if c.get("type") == "text"] if isinstance(content, list) else []
            if texts:
                yield "said", texts[-1]
            continue
        if row.get("type") != "user":
            continue
        content = row.get("message", {}).get("content")
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if c.get("type") == "text"]
            if not texts:
                continue  # a tool result, not a prompt
            content = texts[0]
        if not isinstance(content, str) or content.startswith(("<task-notification>", "<system-reminder>", "<local-command")):
            continue
        cmd = re.search(r"<command-name>(.*?)</command-name>", content)
        if cmd:
            args = re.search(r"<command-args>(.*?)</command-args>", content, re.S)
            content = cmd.group(1) + (" " + args.group(1) if args else "")
        yield "prompt", " ".join(content.split())


def sessions(umbrella, now, warnings):
    found = []
    for path in glob.glob(os.path.join(REGISTRY, "*.json")):
        try:
            with open(path) as f:
                entry = json.load(f)
        except (OSError, ValueError):
            continue
        missing = [k for k in REGISTRY_FIELDS if k not in entry]
        if missing:
            warnings.append("session registry format changed: %s lacks %s" % (os.path.basename(path), ", ".join(missing)))
            continue
        cwd = entry["cwd"]
        if not (cwd == umbrella or cwd.startswith(umbrella + os.sep)) or not alive(entry["pid"]):
            continue
        since = entry["statusUpdatedAt"] / 1000.0
        log = transcript(cwd, entry["sessionId"])
        activity = max(since, os.path.getmtime(log) if log else 0)
        status = entry["status"]
        head, ids, asked = prompts(log) if log else (None, [], False)
        found.append({
            "name": entry["name"],
            "session_id": entry["sessionId"],
            "cwd": cwd,
            "status": status,
            "waiting_for": entry.get("waitingFor"),
            "status_age_s": int(now - since),
            "idle_age_s": int(now - activity),
            "waiting_long": status == "waiting" and now - since > WAITING_LONG,
            "stalled": status == "busy" and now - activity > STALLED,
            "prompt_head": head,
            "asked": status == "idle" and asked,
            "prompt_ids": ids,
        })
    return found


# --- workspaces --------------------------------------------------------------------------


def todo_ids(path):
    ids = []
    for root, dirs, files in os.walk(path):
        depth = os.path.relpath(root, path).count(os.sep)
        dirs[:] = [] if depth >= 1 else [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "target", "_build", "deps", "vendor")]
        if "TODO.md" in files:
            with open(os.path.join(root, "TODO.md"), errors="replace") as f:
                ids += [i for line in f if line.startswith("## ") for i in tracker_ids(line)]
    return ids


def jj_workspace(path):
    template = SEP.join([
        "change_id.short()", "commit_id.short()", "if(empty, \"empty\", \"\")",
        "local_bookmarks.map(|b| b.name()).join(\",\")", "description.first_line()",
    ]) + ' ++ "\\n"'
    template = template.replace(SEP, ' ++ "\\x1f" ++ ')
    out = jj(path, "log", "-r", "trunk()..@ | @", "--no-graph", "-T", template)
    if out is None:
        return None
    stack = []
    for line in out.splitlines():
        change, commit, empty, bookmarks, title = (line.split(SEP) + [""] * 5)[:5]
        stack.append({
            "change": change, "commit": commit, "empty": empty == "empty",
            "bookmarks": [b for b in bookmarks.split(",") if b], "title": title,
        })
    return stack


def git_workspace(path):
    out = run(["git", "-C", path, "log", "--format=%h%x1f%D%x1f%s", "@{upstream}..HEAD"])
    if out is None:
        out = run(["git", "-C", path, "log", "-1", "--format=%h%x1f%D%x1f%s"]) or ""
    dirty = bool((run(["git", "-C", path, "status", "--porcelain"]) or "").strip())
    stack = []
    for line in out.splitlines():
        commit, refs, title = (line.split(SEP) + ["", ""])[:3]
        branches = [r.strip().replace("HEAD -> ", "") for r in refs.split(",") if r.strip() and "/" not in r]
        stack.append({"change": commit, "commit": commit, "empty": False, "bookmarks": branches, "title": title})
    return {"stack": stack, "dirty": dirty}


def workspace(umbrella, name):
    path = os.path.join(umbrella, name)
    if os.path.isdir(os.path.join(path, ".jj")):
        stack = jj_workspace(path)
        ws = {"vcs": "jj", "stack": stack if stack is not None else [], "error": stack is None}
        at = ws["stack"][0] if ws["stack"] else None
        ws["free"] = bool(at and at["empty"] and len(ws["stack"]) == 1 and not at["bookmarks"])
    else:
        ws = dict(git_workspace(path), vcs="git")
        ws["free"] = not ws["dirty"] and not any(c["bookmarks"] for c in ws["stack"][1:])
    ids = []
    for change in ws["stack"]:
        ids += tracker_ids(change["title"])
        for b in change["bookmarks"]:
            m = BOOKMARK_ID.match(b)
            if m:
                ids.append(m.group(1).upper())
    ws["stack_ids"] = sorted(set(ids))
    ws["todo_ids"] = sorted(set(todo_ids(path)))
    return ws


# --- GitHub (cached) ---------------------------------------------------------------------


def checks(rollup):
    if not rollup:
        return None
    states = []
    for c in rollup:
        if c.get("__typename") == "StatusContext":
            states.append(c.get("state"))
        else:
            states.append(c.get("conclusion") if c.get("status") == "COMPLETED" else "PENDING")
    if any(s in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "STARTUP_FAILURE") for s in states):
        return "fail"
    if any(s in ("PENDING", "EXPECTED", None, "") for s in states):
        return "pending"
    return "pass"


def fetch_prs(slug, everyone, now):
    fields = ("number,title,url,author,headRefName,state,isDraft,mergedAt,closedAt,reviewDecision,"
              "statusCheckRollup,closingIssuesReferences")
    cmd = ["gh", "pr", "list", "-R", slug, "--state", "all", "--limit", "30", "--json", fields]
    out = run(cmd if everyone else cmd + ["--author", "@me"])
    if out is None:
        return None
    prs = []
    for pr in json.loads(out):
        ended = pr.get("mergedAt") or pr.get("closedAt")
        if pr["state"] != "OPEN" and ended and now - iso_epoch(ended) > RECENT_CLOSED:
            continue
        prs.append({
            "number": pr["number"], "title": pr["title"], "url": pr["url"],
            "author": (pr.get("author") or {}).get("login"),
            "head": pr["headRefName"], "state": pr["state"], "draft": pr["isDraft"],
            "merged_at": pr.get("mergedAt"), "review": pr.get("reviewDecision") or None,
            "checks": checks(pr.get("statusCheckRollup")),
            "closes": ["#%d" % i["number"] for i in pr.get("closingIssuesReferences") or []],
        })
    return prs


def fetch_trunk(slug, branch):
    """The current result of each workflow on the default branch. A cancelled or skipped run says
    nothing about the code (usually a newer push superseded it), so the result per workflow is
    its newest run that finished otherwise, or is still going."""
    out = run(["gh", "run", "list", "-R", slug, "--branch", branch, "--limit", "30",
               "--json", "workflowName,status,conclusion,headSha,url,createdAt"])
    if out is None:
        return None
    workflows = {}
    for r in json.loads(out):
        if r["workflowName"] in workflows or r.get("conclusion") in ("cancelled", "skipped", "neutral", "stale"):
            continue
        if r["status"] != "completed":
            result = "pending"
        elif r["conclusion"] == "success":
            result = "pass"
        else:
            result = "fail"
        workflows[r["workflowName"]] = {"result": result, "sha": r["headSha"][:8], "url": r["url"], "created_at": r["createdAt"]}
    return workflows


def github(umbrella, repo, spec, issue_ids, now, warnings):
    slug = spec["github"]
    cache_path = os.path.join(umbrella, ".overview", "cache", "gh-%s.json" % repo)
    try:
        with open(cache_path) as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    stale = now - cache.get("fetched_at", 0) > REMOTE_TTL or "trunk" not in cache \
        or any("pr" not in v for v in cache.get("issues", {}).values())
    if stale:
        # Record the attempt even when it fails, so a broken gh is retried every REMOTE_TTL,
        # not every tick.
        errors = []
        branch = cache.get("default_branch") or (run(["gh", "repo", "view", slug, "--json", "defaultBranchRef",
                                                       "--jq", ".defaultBranchRef.name"]) or "").strip()
        prs = fetch_prs(slug, spec.get("prs") == "all", now)
        trunk = fetch_trunk(slug, branch) if branch else None
        if prs is None:
            errors.append("gh pr list failed for %s; PR data is older" % slug)
        if trunk is None:
            errors.append("gh run list failed for %s; trunk CI data is older" % slug)
        cache = {
            "fetched_at": now, "default_branch": branch or None, "errors": errors,
            "prs": cache.get("prs", []) if prs is None else prs,
            "trunk": cache.get("trunk", {}) if trunk is None else trunk,
            "issues": {},
        }
    warnings.extend(cache["errors"])
    for issue in issue_ids:
        if issue in cache["issues"]:
            continue
        out = run(["gh", "issue", "view", issue.lstrip("#"), "-R", slug, "--json", "number,title,state,stateReason,url"])
        if out is not None:
            data = json.loads(out)
            # gh answers for PR numbers too, and prompts name PRs as often as issues.
            data["pr"] = "/pull/" in data.pop("url", "")
            cache["issues"][issue] = data
    # The board pane and the guide's watcher share this cache; never let one read a half-written file.
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path + ".tmp%d" % os.getpid(), "w") as f:
        json.dump(cache, f)
    os.replace(f.name, cache_path)
    return {
        "prs": cache["prs"],
        "trunk": {"branch": cache["default_branch"], "workflows": cache["trunk"]},
        "issues": {k: v for k, v in cache["issues"].items() if k in issue_ids},
    }


def iso_epoch(stamp):
    return calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))


# --- snapshot ----------------------------------------------------------------------------


def owns_merge(ws, pr):
    """Whether the workspace's one session still owns the merged PR, so a wrapup sent to it
    lands on that work. A session that moved on to another issue in the same workspace, or a
    stack carrying other work above the PR, would get a wrapup it can only decline."""
    if len(ws["sessions"]) != 1 or ws["sessions"][0]["status"] != "idle":
        return False
    head = next(i for i, c in enumerate(ws["stack"]) if pr["head"] in c["bookmarks"])
    above, below = ws["stack"][:head], ws["stack"][head:]
    if any(not c["empty"] or c["bookmarks"] for c in above):
        return False
    if any(b != pr["head"] for c in below for b in c["bookmarks"]):
        return False
    named = ws["sessions"][0]["prompt_ids"]
    return not named or bool(set(named) & {"#%d" % pr["number"], *pr["closes"], *ws["stack_ids"]})


def snapshot(umbrella, config):
    now = time.time()
    warnings = []
    live = sessions(umbrella, now, warnings)
    out = {"umbrella": umbrella, "generated_at": int(now), "warnings": warnings, "repos": {}, "guide": [], "elsewhere": []}
    claimed = set()
    for repo, spec in config["repos"].items():
        if not spec.get("watch", True):
            continue
        entry = {"tracker": spec.get("tracker"), "github": spec.get("github"), "everyone": spec.get("prs") == "all", "workspaces": {}}
        ids = set()
        overrides = load_notes(umbrella).get("overrides", {})
        for name in spec["workspaces"]:
            ws = workspace(umbrella, name)
            root = os.path.join(umbrella, name)
            ws["sessions"] = [s for s in live if s["cwd"] == root or s["cwd"].startswith(root + os.sep)]
            claimed.update(s["session_id"] for s in ws["sessions"])
            ws["prompt_ids"] = sorted({i for s in ws["sessions"] for i in s["prompt_ids"]})
            ids.update(ws["stack_ids"] + ws["todo_ids"] + ws["prompt_ids"])
            if overrides.get(name):
                ids.add(overrides[name])
            entry["workspaces"][name] = ws
        if spec.get("github"):
            issue_ids = sorted(i for i in ids if i.startswith("#")) if spec.get("tracker") == "github" else []
            entry.update(github(umbrella, repo, spec, issue_ids, now, warnings))
        prs = sorted(entry.get("prs", []), key=lambda p: p["state"] != "OPEN")
        for ws in entry["workspaces"].values():
            bookmarks = [b for c in ws["stack"] for b in c["bookmarks"]]
            pr = next((p for p in prs if p["head"] in bookmarks), None)
            ws["pr"] = pr["number"] if pr else None
            # The moment auto_wrapup waits for: busy -> idle does not wake the guide by itself.
            ws["wrapup_ready"] = bool(pr and pr["state"] == "MERGED" and owns_merge(ws, pr))
        out["repos"][repo] = entry
    for s in live:
        if s["session_id"] not in claimed:
            out["guide" if s["cwd"] == umbrella else "elsewhere"].append(s)
    return out


def signal(snap):
    """The fields whose change is worth waking the guide for, flattened. Each wake re-reads the
    guide's whole context, so this holds only what can need the user or change what the guide
    offers. The board pane shows everything else: ages, busy/idle, sessions coming and going,
    issue IDs shifting as a stack is reworked, bookmarks, and checks turning green."""
    flat = {"warnings": "; ".join(snap["warnings"]) or None}
    for repo, entry in snap["repos"].items():
        for name, ws in entry["workspaces"].items():
            flat["%s free" % name] = ws["free"]
            flat["%s wrapup ready" % name] = ws.get("wrapup_ready") or None
            for s in ws["sessions"]:
                key = "%s session %s" % (name, s["name"])
                flat[key + " waiting 5m+"] = s["waiting_long"] or None
                flat[key + " silent 20m+"] = s["stalled"] or None
        for pr in entry.get("prs", []):
            key = "%s PR #%d" % (repo, pr["number"])
            flat[key] = "MERGED" if pr["state"] == "MERGED" else ("DRAFT" if pr["draft"] else pr["state"])
            flat[key + " checks failing"] = (pr["state"] == "OPEN" and pr["checks"] == "fail") or None
            flat[key + " changes requested"] = (pr["state"] == "OPEN" and pr["review"] == "CHANGES_REQUESTED") or None
        trunk = entry.get("trunk") or {}
        for workflow, run_ in (trunk.get("workflows") or {}).items():
            flat["%s %s %s" % (repo, trunk["branch"], workflow)] = "fail" if run_["result"] == "fail" else None
        for issue, data in entry.get("issues", {}).items():
            flat["%s issue %s" % (repo, issue)] = data.get("state")
    for s in snap["elsewhere"]:
        flat["unmapped session %s" % s["name"]] = s["cwd"]
    return flat


def shown(value):
    return "-" if value is None else str(value)


def watch(umbrella, config):
    before = signal(snapshot(umbrella, config))
    last_error = None
    while True:
        time.sleep(LOCAL_INTERVAL)
        try:
            after = signal(snapshot(umbrella, config))
        except Exception as e:  # a watcher that dies silently looks exactly like "no change"
            if str(e) != last_error:
                print("snapshot error: %s" % e, flush=True)
                last_error = str(e)
            continue
        last_error = None
        changes = []
        for key in sorted(set(before) | set(after)):
            # PRs and issues age out of the window, and an issue's first sighting is already
            # reported by its workspace's "issues" line; neither is news.
            if after.get(key) is None and (" PR #" in key or " issue " in key):
                continue
            if before.get(key) is None and " issue " in key:
                continue
            if before.get(key) != after.get(key):
                changes.append("%s: %s -> %s" % (key, shown(before.get(key)), shown(after.get(key))))
        if changes:
            print("\n".join(changes), flush=True)
        before = after


# --- board -------------------------------------------------------------------------------


def age(seconds):
    if seconds < 3600:
        return "%dm" % (seconds // 60)
    if seconds < 86400:
        return "%dh" % (seconds // 3600)
    return "%dd" % (seconds // 86400)


class Paint:
    def __init__(self, on):
        self.on = on

    def __call__(self, code, text):
        return "\033[%sm%s\033[0m" % (code, text) if self.on and text else text

    def red(self, t):
        return self("31", t)

    def green(self, t):
        return self("32", t)

    def dim(self, t):
        return self("2", t)


def pr_text(pr, paint):
    mark = "" if pr["state"] != "OPEN" else {"pass": paint.green("✓"), "fail": paint.red("✗"), "pending": "…"}.get(pr["checks"], "")
    review = {"APPROVED": paint.green("approved"), "CHANGES_REQUESTED": paint.red("changes requested")}.get(pr["review"], "")
    state = {"MERGED": "merged", "CLOSED": "closed"}.get(pr["state"], "draft" if pr["draft"] else "")
    return " ".join(x for x in ("PR #%d" % pr["number"], state, mark, review) if x)


def session_text(s, now, paint):
    if s["status"] == "waiting":
        text = "waiting %s" % age(s["status_age_s"])
        return paint.red("⚠ " + text) if s["waiting_long"] else text
    if s["status"] == "busy":
        return paint.red("⚠ silent %s" % age(s["idle_age_s"])) if s["stalled"] else "busy"
    if s.get("asked"):
        return "asked you %s ago" % age(s["idle_age_s"])
    return paint.dim("idle %s" % age(s["idle_age_s"]))


def board(snap, notes, paint):
    """The board as text lines. The snapshot gives the facts; notes.json gives what only the
    guide can judge: overrides, next-up hints, short notes and open offers."""
    now = snap["generated_at"]
    overrides = notes.get("overrides", {})
    hints = notes.get("workspaces", {})
    titles = notes.get("titles", {})
    rows, ci, stray = [], [], []
    for repo, entry in snap["repos"].items():
        prs = entry.get("prs", [])
        claimed = set()
        for name, ws in entry["workspaces"].items():
            pr = next((p for p in prs if p["number"] == ws.get("pr")), None)
            if pr:
                claimed.add(pr["number"])
            # In a Linear repo a #N is a PR or a GitHub issue nobody tracks, never the work item.
            linear = (entry.get("tracker") or "").startswith("linear")
            known = entry.get("issues") or {}
            ids = [i for i in ws["stack_ids"] + ws["todo_ids"] + ws["prompt_ids"]
                   if not (linear and i.startswith("#")) and not (known.get(i) or {}).get("pr")]
            issue = overrides.get(name) or next(iter(ids), "")
            if pr and pr["state"] == "OPEN":
                state = "in review"
            elif pr and pr["state"] == "MERGED":
                state = "merged"
            elif ws["free"] and not issue and any(x["asked"] for x in ws["sessions"]):
                state = "your turn"  # idle, but its last words were a question to the user
            elif ws["free"] and not issue:
                state = "free"
            elif not ws["sessions"]:
                state = "parked"  # work left behind that nobody is on
            else:
                state = "working"
            if state == "working" and not issue:
                issue = "?"
            people = ", ".join(session_text(s, now, paint) for s in ws["sessions"]) or paint.dim("no session")
            hint = hints.get(name, {})
            extra = [pr_text(pr, paint)] if pr else []
            if state == "free" and hint.get("next"):
                extra.append("next up: " + hint["next"])
            if hint.get("note"):
                extra.append(hint["note"])
            # GitHub titles come from gh; Linear ones only the guide can fetch, into notes.json.
            title = ((entry.get("issues") or {}).get(issue) or {}).get("title") or titles.get(issue) \
                or (pr and re.sub(r"^\s*(#\d+|[A-Z][A-Z0-9]+-\d+)\s*[/:\-–—]?\s*", "", pr["title"])) or ""
            commits = [c for c in ws["stack"] if not c["empty"]]
            if state == "parked" and not title and commits:
                described = next((c["title"] for c in commits if c["title"]), "no description")
                title = "%d local commit%s: %s" % (len(commits), "" if len(commits) == 1 else "s", described)
            if len(title) > TITLE_WIDTH:
                title = title[:TITLE_WIDTH - 1] + "…"
            rows.append((name, issue, title, state, people, " · ".join(extra)))
        for p in prs:
            if p["state"] == "OPEN" and p["number"] not in claimed:
                who = " by " + p["author"] if entry.get("everyone") and p.get("author") else ""
                stray.append("%s %s%s: %s" % (repo, pr_text(p, paint), who, p["title"]))
        trunk = entry.get("trunk") or {}
        for workflow, r in sorted((trunk.get("workflows") or {}).items()):
            if r["result"] == "fail":
                since = now - iso_epoch(r["created_at"])
                line = "✗ %s %s: %s (%s ago)" % (repo, trunk["branch"], workflow, age(since))
                # A workflow red for a week is a known state, not something that just broke.
                ci.append(paint.dim(line) if since > 7 * 86400 else paint.red(line))

    lines = ["%s · %s" % (os.path.basename(snap["umbrella"]), time.strftime("%H:%M", time.localtime(now)))]
    lines += [paint.red("⚠ " + w) for w in snap["warnings"]]
    lines.append("")
    widths = [max([len(r[i]) for r in rows] + [0]) for i in range(4)]
    for name, issue, title, state, people, extra in rows:
        line = "%-*s  %-*s  %-*s  %-*s  %s" % (widths[0], name, widths[1], issue, widths[2], title,
                                               widths[3], state, people)
        lines.append((paint.dim(line) if state == "free" and not extra else line) + ("  " + extra if extra else ""))
    for title, items in (("CI on trunk", ci), ("Other open PRs", stray),
                         ("Offers", notes.get("offers", [])), ("Notes", notes.get("notes", []))):
        if items:
            lines += ["", title] + ["  " + i for i in items]
    return lines


def load_notes(umbrella):
    try:
        with open(os.path.join(umbrella, ".overview", "notes.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def board_watch(umbrella, config):
    paint = Paint(sys.stdout.isatty() and "NO_COLOR" not in os.environ)
    while True:
        try:
            lines = board(snapshot(umbrella, config), load_notes(umbrella), paint)
        except Exception as e:  # keep the pane alive; the next tick may succeed
            lines = ["board error: %s" % e]
        width = shutil.get_terminal_size().columns
        sys.stdout.write("\033[H\033[2J" + "\n".join(l if "\033" in l else l[:width] for l in lines) + "\n")
        sys.stdout.flush()
        time.sleep(LOCAL_INTERVAL)


def find_umbrella(start):
    # The guide's shell drifts into .overview/ or a workspace; the umbrella is still above it.
    path = os.path.realpath(start)
    while True:
        if os.path.isfile(os.path.join(path, ".overview", "config.json")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return start
        path = parent


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--umbrella", help="default: the nearest folder up from the cwd that has .overview/config.json")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--watch", action="store_true")
    mode.add_argument("--discover", action="store_true")
    parser.add_argument("--board", action="store_true")
    parser.add_argument("--workspace", metavar="NAME", help="limit the JSON snapshot to one workspace and its repo")
    args = parser.parse_args()
    umbrella = os.path.realpath(args.umbrella or find_umbrella(os.getcwd()))

    if args.discover:
        json.dump(discover(umbrella), sys.stdout, indent=2)
        print()
        return
    try:
        with open(os.path.join(umbrella, ".overview", "config.json")) as f:
            config = json.load(f)
    except OSError:
        sys.exit("no .overview/config.json in %s; run /skills:overview init there first" % umbrella)
    if args.board and args.watch:
        board_watch(umbrella, config)
    elif args.board:
        paint = Paint(sys.stdout.isatty() and "NO_COLOR" not in os.environ)
        print("\n".join(board(snapshot(umbrella, config), load_notes(umbrella), paint)))
    elif args.watch:
        watch(umbrella, config)
    else:
        snap = snapshot(umbrella, config)
        snap["signal_hash"] = hashlib.sha1(json.dumps(signal(snap), sort_keys=True).encode()).hexdigest()[:12]
        if args.workspace:
            for repo, entry in list(snap["repos"].items()):
                ws = entry["workspaces"].get(args.workspace)
                if ws is None:
                    del snap["repos"][repo]
                    continue
                entry["workspaces"] = {args.workspace: ws}
                entry["prs"] = [p for p in entry.get("prs", []) if p["number"] == ws.get("pr")]
            if not snap["repos"]:
                sys.exit("no workspace %s in this umbrella" % args.workspace)
        json.dump(snap, sys.stdout, separators=(",", ":"))  # read by a model on every wake
        print()


if __name__ == "__main__":
    main()
