"""Export a local codebase to a reviewable text file for sharing.

The default mode is intentionally conservative: ignored/generated folders,
data/document folders, and likely secret-bearing files are omitted and
recorded in a manifest. Opt in to additional content only after reviewing it.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse


TEXT_EXTENSIONS = {
    ".bat",
    ".c",
    ".cfg",
    ".conf",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".dockerfile",
    ".go",
    ".graphql",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".php",
    ".properties",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {
    ".editorconfig",
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "dockerfile",
    "license",
    "makefile",
    "procfile",
    "readme",
}
ALWAYS_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".idea",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "htmlcov",
    "node_modules",
    "site-packages",
    "target",
    "venv",
}
DATA_DIRS = {
    "data",
    "dataset",
    "datasets",
    "documents",
    "storage",
    "uploads",
}
SENSITIVE_FILENAMES = {
    ".env",
    ".netrc",
    "credentials.json",
    "id_dsa",
    "id_rsa",
    "secrets.json",
    "secrets.toml",
}
SENSITIVE_EXTENSIONS = {".key", ".p12", ".pem", ".pfx"}
PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "example",
    "mock",
    "none",
    "placeholder",
    "replace_me",
    "test",
}
CREDENTIAL_VALUE_PATTERN = re.compile(
    r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY)"
    r"[A-Z0-9_]*\s*[:=]\s*[\"']?([^\s\"'#]+)"
)


@dataclass
class SkippedFile:
    path: str
    reason: str


def parse_project_path(value: str) -> Path:
    """Convert a filesystem path or local file URL into an absolute directory."""
    if re.match(r"^[A-Za-z]:[\\/]", value):
        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Project directory does not exist: {path}")
        return path
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme.lower() != "file":
        raise ValueError(
            "Only local paths or file:// URLs are accepted. Clone/download a remote "
            "repository first, then export its local directory."
        )
    if parsed.scheme.lower() == "file":
        raw_path = unquote(parsed.path)
        if os.name == "nt" and raw_path.startswith("/") and len(raw_path) > 2:
            raw_path = raw_path[1:]
        path = Path(raw_path)
    else:
        path = Path(value).expanduser()
    path = path.resolve()
    if not path.is_dir():
        raise ValueError(f"Project directory does not exist: {path}")
    return path


def resolve_output_path(value: str | None, project_path: Path) -> Path:
    default_name = f"{project_path.name}_codebase.txt"
    if not value:
        return (Path.cwd() / default_name).resolve()

    raw = Path(value).expanduser()
    if raw.exists() and raw.is_dir():
        return (raw / default_name).resolve()
    if str(value).endswith(("/", "\\")) or raw.suffix.lower() != ".txt":
        return (raw / default_name).resolve()
    return raw.resolve()


def git_file_list(project_path: Path) -> list[Path] | None:
    """Return tracked and non-ignored untracked files when inside a Git worktree."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(project_path),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            capture_output=True,
            check=False,
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return [
        project_path / os.fsdecode(relative_path)
        for relative_path in result.stdout.split(b"\0")
        if relative_path
    ]


def filesystem_file_list(project_path: Path) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = sorted(
            directory
            for directory in dirs
            if directory.casefold() not in ALWAYS_EXCLUDED_DIRS
        )
        files.extend(Path(root) / filename for filename in sorted(filenames))
    return files


def has_part(path: Path, names: set[str]) -> bool:
    return bool({part.casefold() for part in path.parts} & names)


def likely_sensitive_name(relative_path: Path) -> bool:
    name = relative_path.name.casefold()
    if name == ".env.example":
        return False
    return (
        name in SENSITIVE_FILENAMES
        or name.startswith(".env.")
        or relative_path.suffix.casefold() in SENSITIVE_EXTENSIONS
        or "credential" in name
        or "secret" in name
    )


def is_generated_export(relative_path: Path) -> bool:
    name = relative_path.name.casefold()
    return name.endswith("_codebase.txt") or name.endswith("_manifest.txt")


def is_text_file(path: Path) -> bool:
    name = path.name.casefold()
    return (
        path.suffix.casefold() in TEXT_EXTENSIONS
        or name in TEXT_FILENAMES
        or name.startswith("license.")
        or name.startswith("readme.")
    )


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


def contains_apparent_secret(text: str) -> bool:
    for match in CREDENTIAL_VALUE_PATTERN.finditer(text):
        value = match.group(1).strip().casefold()
        if (
            value in PLACEHOLDER_VALUES
            or value.startswith("your_")
            or value.startswith("example_")
            or "replace" in value
        ):
            continue
        if len(value) >= 8:
            return True
    return False


def export_codebase(
    project_path: Path,
    output_file: Path,
    *,
    include_data: bool = False,
    include_sensitive: bool = False,
    max_file_size: int = 1_000_000,
) -> tuple[list[str], list[SkippedFile], Path, bool]:
    manifest_file = output_file.with_name(f"{output_file.stem}_manifest.txt")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_resolved = output_file.resolve()
    manifest_resolved = manifest_file.resolve()
    candidate_files = git_file_list(project_path)
    used_git = candidate_files is not None
    if candidate_files is None:
        candidate_files = filesystem_file_list(project_path)
    nested_output_dir: Path | None = None
    if output_file.parent != project_path and output_file.parent.is_relative_to(project_path):
        nested_output_dir = output_file.parent

    included: list[tuple[str, str]] = []
    skipped: list[SkippedFile] = []
    for path in sorted(candidate_files, key=lambda item: str(item).casefold()):
        if not path.is_file():
            continue
        relative_path = path.relative_to(project_path)
        display_path = relative_path.as_posix()
        lowered_parts = {part.casefold() for part in relative_path.parts[:-1]}
        if nested_output_dir is not None and path.is_relative_to(nested_output_dir):
            skipped.append(SkippedFile(display_path, "destination export directory"))
        elif path.resolve() in {output_resolved, manifest_resolved}:
            skipped.append(SkippedFile(display_path, "generated export file"))
        elif is_generated_export(relative_path):
            skipped.append(SkippedFile(display_path, "previous generated export file"))
        elif lowered_parts & ALWAYS_EXCLUDED_DIRS:
            skipped.append(SkippedFile(display_path, "generated or tooling directory"))
        elif lowered_parts & DATA_DIRS and not include_data:
            skipped.append(SkippedFile(display_path, "data/document directory; use --include-data"))
        elif likely_sensitive_name(relative_path) and not include_sensitive:
            skipped.append(SkippedFile(display_path, "sensitive filename; use --include-sensitive"))
        elif not is_text_file(path):
            skipped.append(SkippedFile(display_path, "not a supported text/source file"))
        elif path.stat().st_size > max_file_size:
            skipped.append(SkippedFile(display_path, f"larger than {max_file_size:,} bytes"))
        else:
            text = read_text(path)
            if text is None:
                skipped.append(SkippedFile(display_path, "not valid UTF-8 text or unreadable"))
            elif contains_apparent_secret(text) and not include_sensitive:
                skipped.append(
                    SkippedFile(display_path, "possible secret assignment; use --include-sensitive")
                )
            else:
                included.append((display_path, text))

    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with output_file.open("w", encoding="utf-8", newline="\n") as outfile:
        outfile.write("# Codebase Text Export\n")
        outfile.write(f"# Project: {project_path}\n")
        outfile.write(f"# Generated (UTC): {timestamp}\n")
        outfile.write(f"# Included files: {len(included)}\n")
        outfile.write(f"# Skipped files: {len(skipped)} (see {manifest_file.name})\n")
        for relative_path, text in included:
            outfile.write(f"\n{'=' * 24} FILE: {relative_path} {'=' * 24}\n")
            outfile.write(text)
            if not text.endswith("\n"):
                outfile.write("\n")

    with manifest_file.open("w", encoding="utf-8", newline="\n") as manifest:
        manifest.write("Codebase export manifest\n")
        manifest.write(f"Project: {project_path}\n")
        manifest.write(f"Output: {output_file}\n")
        manifest.write(f"Generated (UTC): {timestamp}\n")
        manifest.write(f"Discovery: {'git-aware' if used_git else 'filesystem walk'}\n")
        manifest.write(f"Included: {len(included)}\n")
        manifest.write(f"Skipped: {len(skipped)}\n\n")
        manifest.write("Included files:\n")
        for relative_path, _ in included:
            manifest.write(f"  {relative_path}\n")
        manifest.write("\nSkipped files:\n")
        for item in skipped:
            manifest.write(f"  {item.path} - {item.reason}\n")
        manifest.write(
            "\nReview the exported text before sharing; automated checks cannot "
            "identify every private or proprietary value.\n"
        )

    return [relative_path for relative_path, _ in included], skipped, manifest_file, used_git


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export a local codebase into a single reviewable text file."
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Local project directory path or file:// URL. Prompted when omitted.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output .txt file or destination directory. Prompted when omitted.",
    )
    parser.add_argument(
        "--include-data",
        action="store_true",
        help="Include text files under data/document/upload directories.",
    )
    parser.add_argument(
        "--include-sensitive",
        action="store_true",
        help="Include likely credential files or files containing possible secrets.",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=1_000_000,
        metavar="BYTES",
        help="Maximum size for any individual included file (default: 1000000).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_value = args.project or input("Project directory path or file:// URL: ").strip()
    output_value = args.output
    if output_value is None:
        output_value = input(
            "Destination directory or .txt filename [current directory]: "
        ).strip() or None
    try:
        project_path = parse_project_path(project_value)
        output_file = resolve_output_path(output_value, project_path)
        included, skipped, manifest_file, used_git = export_codebase(
            project_path,
            output_file,
            include_data=args.include_data,
            include_sensitive=args.include_sensitive,
            max_file_size=args.max_file_size,
        )
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Export written to: {output_file}")
    print(f"Manifest written to: {manifest_file}")
    print(f"Discovery mode: {'git-aware' if used_git else 'filesystem walk'}")
    print(f"Included files: {len(included)}")
    print(f"Skipped files: {len(skipped)}")
    print("Review the output and manifest before sharing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
