#!/usr/bin/env python3
"""Release the OpenPlatform train in dependency order.

The reusable java-release workflow publishes one repository. This script is
the train: it reads every repository POM, groups repositories that do not
depend on each other, and only tags the next group after the current group
has published to GitHub Packages.

  python3 scripts/openplatform_release.py plan
  python3 scripts/openplatform_release.py release --version 26.10.4 --dry-run
  python3 scripts/openplatform_release.py release --version 26.10.4

install-upstreams is used by java-release.yml. It installs sibling reactors
from source with the same dependency rules, because GITHUB_TOKEN cannot read
another repository's GitHub Packages.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ORG = "fireflysoftwaresolutions"
SKIP_ARTIFACTS = {"firefly-parent", "firefly-bom"}
SUFFIXES = ("-sdk", "-interfaces", "-models", "-infra", "-core", "-web")
ALIASES = {
    "core-lending-mortgages": "core-lending-mortgage",
    "domain-core-security-center-session": "domain-core-security-center",
}
WAVE_TIMEOUT_SECONDS = int(os.environ.get("WAVE_TIMEOUT_SECONDS", "3600"))
POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "20"))


def repo_for(artifact: str) -> str:
    base = artifact
    for suffix in SUFFIXES:
        if artifact.endswith(suffix) and len(artifact) > len(suffix):
            base = artifact[: -len(suffix)]
            break
    return ALIASES.get(base, base)


def platform_version(pom: str) -> str:
    """Version of this reactor: its own version, otherwise its parent version."""
    parent = re.search(r"<parent>(.*?)</parent>", pom, flags=re.S)
    body = re.sub(r"<parent>.*?</parent>", "", pom, count=1, flags=re.S)
    head = re.split(
        r"<modules>|<properties>|<dependencies>|<dependencyManagement>|<build>|<name>",
        body,
        maxsplit=1,
    )[0]
    own = re.search(r"<version>\s*([^<]+)\s*</version>", head)
    if own and not own.group(1).strip().startswith("${"):
        return own.group(1).strip()
    if parent:
        inherited = re.search(r"<version>\s*([^<]+)\s*</version>", parent.group(1))
        if inherited:
            return inherited.group(1).strip()
    raise ValueError("pom has no platform version")


def artifact_deps(poms: list[str], repo: str) -> set[str]:
    found: set[str] = set()
    for text in poms:
        text = re.sub(r"<dependencyManagement>.*?</dependencyManagement>", "", text, flags=re.S)
        for artifact in re.findall(
            r"<groupId>\s*io\.fireflysoftware\s*</groupId>\s*<artifactId>\s*([^<\s]+)\s*</artifactId>",
            text,
        ):
            if artifact in SKIP_ARTIFACTS or repo_for(artifact) == repo:
                continue
            found.add(artifact)
    return found


def poms_on_disk(repo_dir: Path) -> list[str]:
    files = []
    for pom in repo_dir.rglob("pom.xml"):
        relative = pom.relative_to(repo_dir)
        if "target" in relative.parts or ".ci" in relative.parts:
            continue
        files.append(relative)
    files.sort(key=lambda path: (len(path.parts), str(path)))
    return [(repo_dir / path).read_text(encoding="utf-8", errors="replace") for path in files]


def release_repos_on_disk(root: Path) -> list[str]:
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and (path / ".github" / "workflows" / "release.yml").is_file()
    )


def local_root() -> Path | None:
    override = os.environ.get("OPENPLATFORM_ROOT")
    if override:
        root = Path(override)
        return root if (root / "firefly-bom" / "pom.xml").is_file() else None
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "firefly-bom" / "pom.xml").is_file():
        return candidate
    return None


def gh(args: list[str], payload: dict | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["gh", *args]
    last: subprocess.CompletedProcess[str] | None = None
    for attempt in range(4):
        last = subprocess.run(
            command,
            input=None if payload is None else json.dumps(payload),
            capture_output=True,
            text=True,
        )
        retriable = last.returncode != 0 and (
            "HTTP 5" in last.stderr or "Resource temporarily unavailable" in last.stderr
        )
        if last.returncode == 0 or not retriable or attempt == 3:
            break
        time.sleep(2 + attempt)
    if check and last and last.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{last.stderr.strip()}")
    return last


def gh_json(path: str):
    result = gh(["api", path])
    return json.loads(result.stdout)


def release_repos_via_api() -> list[str]:
    names = gh(
        [
            "api",
            "--paginate",
            f"orgs/{ORG}/repos",
            "--jq",
            '.[] | select(.archived == false and .disabled == false) | .name',
        ]
    ).stdout.split()
    selected = []
    for name in names:
        probe = gh(
            ["api", f"repos/{ORG}/{name}/contents/.github/workflows/release.yml?ref=main"],
            check=False,
        )
        if probe.returncode == 0:
            selected.append(name)
    return sorted(selected)


def poms_via_api(repo: str) -> list[str]:
    tree = gh_json(f"repos/{ORG}/{repo}/git/trees/main?recursive=1")
    if tree.get("truncated"):
        raise SystemExit(f"{repo}: Git tree is truncated; cannot read every pom.xml")
    paths = sorted(
        (
            item["path"]
            for item in tree.get("tree", [])
            if item["path"].endswith("pom.xml") and "/target/" not in item["path"] and "/.ci/" not in item["path"]
        ),
        key=lambda path: (path.count("/"), path),
    )
    texts = []
    for path in paths:
        item = gh_json(f"repos/{ORG}/{repo}/contents/{path}?ref=main")
        texts.append(base64.b64decode(item["content"]).decode("utf-8", errors="replace"))
    return texts


def load_repositories() -> dict[str, list[str]]:
    root = local_root()
    if root is not None:
        return {name: poms_on_disk(root / name) for name in release_repos_on_disk(root)}
    return {name: poms_via_api(name) for name in release_repos_via_api()}


def build_waves(repositories: dict[str, list[str]]) -> list[list[str]]:
    graph: dict[str, set[str]] = {}
    unknown: list[str] = []
    for repo, poms in repositories.items():
        deps: set[str] = set()
        for artifact in artifact_deps(poms, repo):
            dest = repo_for(artifact)
            if dest not in repositories:
                unknown.append(f"{repo} depends on {artifact}, which is not a release repository ({dest})")
                continue
            deps.add(dest)
        graph[repo] = deps
    if unknown:
        raise SystemExit("Unmapped dependencies:\n" + "\n".join(sorted(unknown)))
    for required in ("firefly-bom", "firefly-parent"):
        if required not in graph:
            raise SystemExit(f"{required} has no release workflow")

    pending = {
        repo: set(deps) - {"firefly-bom", "firefly-parent"}
        for repo, deps in graph.items()
        if repo not in {"firefly-bom", "firefly-parent"}
    }
    waves = [["firefly-bom"], ["firefly-parent"]]
    while pending:
        ready = sorted(repo for repo, deps in pending.items() if not deps)
        if not ready:
            raise SystemExit(f"dependency cycle among {sorted(pending)}")
        waves.append(ready)
        for repo in ready:
            del pending[repo]
        for deps in pending.values():
            deps.difference_update(ready)
    return waves


def verify_version(repositories: dict[str, list[str]], version: str) -> None:
    mismatches = []
    for repo, poms in sorted(repositories.items()):
        if not poms:
            mismatches.append(f"{repo}: no pom.xml")
            continue
        try:
            found = platform_version(poms[0])
        except ValueError as exc:
            mismatches.append(f"{repo}: {exc}")
            continue
        if found != version:
            mismatches.append(f"{repo}: pom is {found}, expected {version}")
    if mismatches:
        raise SystemExit("Refusing to tag. Main is not at the requested version:\n" + "\n".join(mismatches))


def print_waves(waves: list[list[str]]) -> None:
    print(f"waves {len(waves)} repositories {sum(len(wave) for wave in waves)}")
    for index, wave in enumerate(waves):
        print(f"wave {index} ({len(wave)})")
        for repo in wave:
            print(f"  {repo}")


def cmd_plan(_args: argparse.Namespace) -> None:
    print_waves(build_waves(load_repositories()))


def install_upstreams() -> None:
    current = os.environ["GITHUB_REPOSITORY"].split("/", 1)[1]
    queue = sorted(artifact_deps(poms_on_disk(Path(".")), current))
    seen: set[str] = set()
    graph: dict[str, set[str]] = {}
    while queue:
        artifact = queue.pop(0)
        repo = repo_for(artifact)
        if repo in seen or repo == current:
            continue
        seen.add(repo)
        dest = Path(".ci/upstream") / repo
        print(f"::group::checkout {repo}", flush=True)
        subprocess.check_call(
            ["gh", "repo", "clone", f"{ORG}/{repo}", str(dest), "--", "--depth", "1", "--branch", "main"]
        )
        print("::endgroup::", flush=True)
        upstream = artifact_deps(poms_on_disk(dest), repo)
        graph[repo] = {repo_for(item) for item in upstream}
        graph[repo].discard(current)
        queue.extend(sorted(upstream))

    pending = {repo: {dep for dep in deps if dep in seen} for repo, deps in graph.items()}
    order: list[str] = []
    while pending:
        ready = sorted(repo for repo, deps in pending.items() if not deps)
        if not ready:
            raise SystemExit(f"dependency cycle among {sorted(pending)}")
        for repo in ready:
            order.append(repo)
            del pending[repo]
        for deps in pending.values():
            deps.difference_update(ready)

    for repo in order:
        print(f"::group::install {repo}", flush=True)
        subprocess.check_call(
            [
                "mvn",
                "-B",
                "-ntp",
                "-f",
                f".ci/upstream/{repo}/pom.xml",
                "install",
                "-Dmaven.test.skip=true",
                "-DskipOpenApiGen",
            ]
        )
        print("::endgroup::", flush=True)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def tag_exists(repo: str, tag: str) -> bool:
    result = gh(["api", f"repos/{ORG}/{repo}/git/ref/tags/{tag}"], check=False)
    return result.returncode == 0


def main_sha(repo: str) -> str:
    return gh_json(f"repos/{ORG}/{repo}/commits/main")["sha"]


def create_annotated_tag(repo: str, tag: str, version: str, sha: str) -> None:
    created = gh(
        ["api", "--method", "POST", f"repos/{ORG}/{repo}/git/tags", "--input", "-"],
        payload={
            "tag": tag,
            "message": f"OpenPlatform {version}\n",
            "object": sha,
            "type": "commit",
            "tagger": {
                "name": "Firefly Software Foundation",
                "email": "dev@fireflysoftware.io",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        },
    )
    tag_sha = json.loads(created.stdout)["sha"]
    gh(
        ["api", "--method", "POST", f"repos/{ORG}/{repo}/git/refs", "--input", "-"],
        payload={"ref": f"refs/tags/{tag}", "sha": tag_sha},
    )


def dispatch_release(repo: str, tag: str) -> None:
    gh(
        [
            "api",
            "--method",
            "POST",
            f"repos/{ORG}/{repo}/actions/workflows/release.yml/dispatches",
            "-f",
            f"ref=refs/tags/{tag}",
        ]
    )


def latest_run(repo: str, tag: str, not_before: datetime | None) -> dict | None:
    data = gh_json(f"repos/{ORG}/{repo}/actions/workflows/release.yml/runs?per_page=20&branch={tag}")
    for run in data.get("workflow_runs", []):
        if run.get("head_branch") != tag:
            continue
        if not_before is not None and parse_time(run["created_at"]) < not_before:
            continue
        return run
    return None


def wait_for(tag: str, pending: dict[str, datetime]) -> None:
    deadline = time.time() + WAVE_TIMEOUT_SECONDS
    while pending:
        if time.time() > deadline:
            raise SystemExit(f"timed out waiting for {', '.join(sorted(pending))}")
        still: dict[str, datetime] = {}
        for repo, not_before in pending.items():
            run = latest_run(repo, tag, not_before)
            if run is None or run.get("status") != "completed":
                still[repo] = not_before
                continue
            if run.get("conclusion") != "success":
                raise SystemExit(f"{repo} release failed: {run.get('html_url')}")
            print(f"published {repo}", flush=True)
        pending = still
        if pending:
            names = ", ".join(sorted(pending)[:6])
            print(f"waiting {len(pending)}: {names}", flush=True)
            time.sleep(POLL_SECONDS)


def release_wave(wave: list[str], version: str, dry_run: bool) -> None:
    tag = f"v{version}"
    waiting: dict[str, datetime] = {}
    for repo in wave:
        if tag_exists(repo, tag):
            run = latest_run(repo, tag, None)
            if run and run.get("status") == "completed" and run.get("conclusion") == "success":
                print(f"already published {repo}", flush=True)
                continue
            if run and run.get("status") != "completed":
                print(f"already running {repo}", flush=True)
                waiting[repo] = parse_time(run["created_at"])
                continue
            print(f"retry {repo}", flush=True)
            if not dry_run:
                dispatch_release(repo, tag)
                waiting[repo] = parse_time(run["created_at"]) + timedelta(seconds=1) if run else datetime.min.replace(tzinfo=timezone.utc)
            continue
        sha = main_sha(repo)
        print(f"tag {repo} {tag} {sha[:12]}", flush=True)
        if dry_run:
            continue
        create_annotated_tag(repo, tag, version, sha)
        waiting[repo] = datetime.min.replace(tzinfo=timezone.utc)
    if waiting and not dry_run:
        wait_for(tag, waiting)


def cmd_release(args: argparse.Namespace) -> None:
    if not re.fullmatch(r"\d{2}\.\d{1,2}\.\d+", args.version):
        raise SystemExit(f"version must look like 26.10.4, got {args.version}")
    repositories = load_repositories()
    verify_version(repositories, args.version)
    waves = build_waves(repositories)
    print_waves(waves)
    for index, wave in enumerate(waves):
        print(f"=== wave {index} ===", flush=True)
        release_wave(wave, args.version, args.dry_run)
        print(f"=== wave {index} complete ===", flush=True)
    if args.dry_run:
        print("dry run: no tags were created")


def main() -> None:
    parser = argparse.ArgumentParser(description="Release OpenPlatform in dependency order")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="Print the dependency waves")
    commands.add_parser("install-upstreams", help="Install sibling reactors from source")
    release = commands.add_parser("release", help="Tag and publish each wave")
    release.add_argument("--version", required=True)
    release.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "plan":
        cmd_plan(args)
    elif args.command == "install-upstreams":
        install_upstreams()
    else:
        cmd_release(args)


if __name__ == "__main__":
    main()
