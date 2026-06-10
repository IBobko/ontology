"""Publish Markdown drafts to the WordPress source-document archive."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import markdown
import yaml

try:
    from .wp_client import WordPressClient, WordPressSettings
except ImportError:
    from wp_client import WordPressClient, WordPressSettings


DEFAULT_REPO_ROOT = Path.cwd().resolve()
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class SyncConfig:
    repo_root: Path
    site_url: str
    project: str
    collection: str
    source_dir: Path
    post_type: str
    status: str
    default_language: str
    tracked_only: bool
    excludes: tuple[str, ...]


@dataclass(frozen=True)
class GitContext:
    repository: str
    branch: str
    commit: str


def load_config(path: Path, repo_root: Path) -> SyncConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    site = data.get("site") or {}
    source = data.get("source") or {}
    source_dir = source.get("source_dir", "draft")
    return SyncConfig(
        repo_root=repo_root,
        site_url=str(site.get("url", "https://deconreality.com")).rstrip("/"),
        project=str(source.get("project", "deconreality")),
        collection=str(source.get("collection", "drafts")),
        source_dir=repo_root / str(source_dir),
        post_type=str(source.get("post_type", "source_document")),
        status=str(source.get("status", "publish")),
        default_language=str(source.get("default_language", "ru")),
        tracked_only=bool(source.get("tracked_only", True)),
        excludes=tuple(str(item) for item in data.get("exclude", [])),
    )


def run_git(repo_root: Path, *args: str, default: str = "") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return default
    return result.stdout.strip() or default


def get_git_context(repo_root: Path) -> GitContext:
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not repository:
        remote = run_git(
            repo_root,
            "remote",
            "get-url",
            "origin",
            default=repo_root.name,
        )
        repository = re.sub(r"^(?:git@github\.com:|https://github\.com/)", "", remote)
        repository = re.sub(r"\.git$", "", repository)

    branch = os.environ.get("GITHUB_REF_NAME") or run_git(
        repo_root,
        "branch", "--show-current", default="main"
    )
    commit = os.environ.get("GITHUB_SHA") or run_git(
        repo_root,
        "rev-parse", "HEAD", default="unknown"
    )
    return GitContext(repository=repository, branch=branch, commit=commit)


def is_excluded(path: Path, repo_root: Path, patterns: Iterable[str]) -> bool:
    relative = path.relative_to(repo_root).as_posix()
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def iter_drafts(
    config: SyncConfig,
    selected_paths: Iterable[str] = (),
) -> Iterable[Path]:
    if not config.source_dir.exists():
        raise FileNotFoundError(f"Draft directory not found: {config.source_dir}")

    selected = tuple(selected_paths)
    tracked_paths = {
        relative
        for relative in run_git(config.repo_root, "ls-files", "*.md").splitlines()
        if relative
    }
    if selected:
        resolved_candidates: list[Path] = []
        for value in selected:
            candidate = (config.repo_root / value).resolve()
            try:
                relative = candidate.relative_to(config.repo_root).as_posix()
                candidate.relative_to(config.source_dir)
            except ValueError as error:
                raise ValueError(f"Path is outside the configured source: {value}") from error
            if config.tracked_only and relative not in tracked_paths:
                raise ValueError(f"Path is not tracked by Git: {value}")
            resolved_candidates.append(candidate)
        candidates = resolved_candidates
    elif config.tracked_only:
        candidates = (
            config.repo_root / relative
            for relative in tracked_paths
        )
    else:
        candidates = config.source_dir.rglob("*.md")

    for path in sorted(candidates):
        try:
            path.relative_to(config.source_dir)
        except ValueError:
            continue
        if path.is_file() and not is_excluded(path, config.repo_root, config.excludes):
            yield path


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        return {}, text
    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        raise ValueError("Frontmatter must contain a YAML mapping")
    return metadata, text[match.end():]


def clean_markdown_title(value: str) -> str:
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"[*_`~]+", "", value)
    return value.strip().strip('"').strip()


def is_metadata_heading(value: str) -> bool:
    return bool(re.match(r"^(?:original|share)\s+https?://", value, re.IGNORECASE))


def extract_title(body: str, path: Path, metadata: dict[str, Any]) -> tuple[str, str]:
    configured_title = metadata.get("title")
    match = None
    for candidate in HEADING_PATTERN.finditer(body):
        if not is_metadata_heading(clean_markdown_title(candidate.group(1))):
            match = candidate
            break
    title = clean_markdown_title(str(configured_title)) if configured_title else ""
    if not title and match:
        title = clean_markdown_title(match.group(1))
    if not title:
        title = path.stem.replace("_", " ").replace("-", " ").strip()

    if match:
        body = f"{body[:match.start()]}{body[match.end():]}".lstrip("\n")
    return title, body


def normalize_tags(value: Any, path: Path, source_dir: Path) -> list[str]:
    if value is None:
        tags: list[str] = []
    elif isinstance(value, list):
        tags = [str(item).strip() for item in value if str(item).strip()]
    else:
        tags = [str(value).strip()]

    relative_parent = path.relative_to(source_dir).parent
    if relative_parent != Path("."):
        folder_tag = relative_parent.parts[0]
        if folder_tag not in tags:
            tags.append(folder_tag)
    return tags


def build_topics(path: Path, source_dir: Path) -> list[str]:
    relative_parent = path.relative_to(source_dir).parent
    if relative_parent == Path("."):
        return ["Основное"]
    return list(relative_parent.parts)


def build_payload(
    path: Path,
    config: SyncConfig,
    git: GitContext,
) -> dict[str, Any]:
    raw_text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw_text)
    title, body = extract_title(body, path, metadata)
    source_path = path.relative_to(config.repo_root).as_posix()
    source_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    source_commit = run_git(
        config.repo_root,
        "log",
        "-1",
        "--format=%H",
        "--",
        source_path,
        default=git.commit,
    )
    html = markdown.markdown(
        body,
        extensions=["extra", "tables", "fenced_code"],
    )

    payload = {
        "post_type": config.post_type,
        "title": title,
        "content": html,
        "excerpt": str(metadata.get("excerpt", "")),
        "slug": str(metadata.get("slug", "")),
        "status": str(metadata.get("wp_status", config.status)),
        "lang": str(metadata.get("lang", config.default_language)),
        "tags": normalize_tags(metadata.get("tags"), path, config.source_dir),
        "topics": build_topics(path, config.source_dir),
        "project": config.project,
        "collection": config.collection,
        "source_repo": git.repository,
        "source_branch": git.branch,
        "source_path": source_path,
        "source_commit": source_commit,
        "source_hash": source_hash,
        "draft_status": str(metadata.get("draft_status", metadata.get("status", "draft"))),
        "canonical_article_id": metadata.get("canonical_article_id"),
        "last_synced_at": datetime.now(timezone.utc).isoformat(),
    }
    comparable_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"source_commit", "last_synced_at"}
    }
    payload["sync_hash"] = hashlib.sha256(
        json.dumps(
            comparable_payload,
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return payload


def sync_draft(
    client: WordPressClient,
    payload: dict[str, Any],
    dry_run: bool,
) -> None:
    source_path = payload["source_path"]
    if dry_run:
        print(f"[DRY RUN] {source_path} -> {payload['title']}")
        return
    response = client.post(
        "wp-json/deconreality-content-sync/v1/documents/upsert",
        json=payload,
    )
    result = response.json()
    print(f"[{result.get('action', 'OK').upper()}] {source_path} -> post {result.get('id')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize draft Markdown files to WordPress."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help="Root of the content repository. Defaults to the current directory.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Config path. Defaults to <repo-root>/.content-sync.yml.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and display drafts without sending them to WordPress.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Synchronize one repository-relative Markdown path. Repeatable.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config_path = (
        args.config.resolve()
        if args.config
        else repo_root / ".content-sync.yml"
    )
    config = load_config(config_path, repo_root)
    git = get_git_context(repo_root)
    settings = WordPressSettings.from_environment(default_url=config.site_url)
    client = WordPressClient(settings)

    count = 0
    for path in iter_drafts(config, args.path):
        sync_draft(client, build_payload(path, config, git), args.dry_run)
        count += 1
    print(f"Processed {count} draft files.")


if __name__ == "__main__":
    main()
