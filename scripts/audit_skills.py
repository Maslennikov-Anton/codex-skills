#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MAX_DESCRIPTION_CHARS = 220
DEFAULT_MAX_SKILL_LINES = 500
GENERIC_DESCRIPTION_PATTERNS = (
    re.compile(r"\bhelp(s|ing)?\b", re.IGNORECASE),
    re.compile(r"\bwork(s|ing)? with\b", re.IGNORECASE),
    re.compile(r"\bvarious\b", re.IGNORECASE),
    re.compile(r"\bthings\b", re.IGNORECASE),
    re.compile(r"\bbetter\b", re.IGNORECASE),
    re.compile(r"\bпомог", re.IGNORECASE),
    re.compile(r"\bразн", re.IGNORECASE),
)
WORD_RE = re.compile(r"[A-Za-zА-Яа-я0-9_]{3,}")
REFERENCE_RE = re.compile(r"(?:^|[\s(])`?(references/[A-Za-z0-9_./-]+)`?")
FENCED_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)


@dataclass(frozen=True)
class Skill:
    path: Path
    name: str
    description: str
    body: str


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated YAML frontmatter")

    raw_frontmatter = text[4:end]
    body = text[end + len("\n---") :].lstrip("\n")
    frontmatter: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key is not None:
            frontmatter[current_key] = " ".join(line.strip() for line in current_lines).strip().strip("\"'")
        current_key = None
        current_lines = []

    for line in raw_frontmatter.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" ") and ":" in line:
            flush()
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = value.strip()
            if value in {">", "|"}:
                current_lines = []
            else:
                current_lines = [value]
        elif current_key is not None:
            current_lines.append(line)
    flush()
    return frontmatter, body


def discover_skills(root: Path, include_system: bool) -> list[Skill]:
    skills: list[Skill] = []
    candidates = sorted(root.glob("*/SKILL.md"))
    if include_system:
        candidates.extend(sorted((root / ".system").glob("*/SKILL.md")))
    for skill_file in candidates:
        text = skill_file.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text, skill_file)
        name = frontmatter.get("name") or skill_file.parent.name
        description = frontmatter.get("description", "")
        skills.append(Skill(path=skill_file.parent, name=name, description=description, body=body))
    return skills


def tokens(text: str) -> set[str]:
    text = re.sub(r"[./-]", " ", text)
    return {token.lower() for token in WORD_RE.findall(text)}


def audit_skill(skill: Skill, root: Path, max_description_chars: int, max_skill_lines: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not skill.description:
        errors.append("missing description")
    if len(skill.description) > max_description_chars:
        warnings.append(
            f"description is {len(skill.description)} chars; preferred max is {max_description_chars}"
        )
    if any(pattern.search(skill.description) for pattern in GENERIC_DESCRIPTION_PATTERNS):
        warnings.append("description may be generic; put the concrete trigger first")

    body_lines = skill.body.splitlines()
    if len(body_lines) > max_skill_lines:
        warnings.append(f"SKILL.md body has {len(body_lines)} lines; preferred max is {max_skill_lines}")

    references_dir = skill.path / "references"
    body_without_code_blocks = FENCED_BLOCK_RE.sub("", skill.body)
    mentioned_refs = sorted(set(REFERENCE_RE.findall(body_without_code_blocks)))
    for reference in mentioned_refs:
        reference = reference.rstrip(".,);")
        reference_path = skill.path / reference
        if not reference_path.exists():
            errors.append(f"missing referenced file: {reference}")

    if references_dir.exists():
        existing_refs = sorted(path.relative_to(skill.path).as_posix() for path in references_dir.glob("*.md"))
        unmentioned_refs = [reference for reference in existing_refs if reference not in mentioned_refs]
        if unmentioned_refs:
            warnings.append(
                "references not mentioned from SKILL.md: " + ", ".join(unmentioned_refs[:8])
            )

    return errors, warnings


def run_smoke_cases(root: Path, skills: list[Skill], cases_path: Path | None) -> tuple[list[str], list[str]]:
    if cases_path is None:
        cases_path = root / "scripts" / "skill_trigger_smoke_cases.json"
    if not cases_path.exists():
        return [], [f"smoke cases file not found: {cases_path}"]

    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []
    skill_vectors = {
        skill.name: (
            tokens(f"{skill.name} {skill.path.name}"),
            tokens(skill.description),
        )
        for skill in skills
    }

    for case in cases:
        prompt = str(case["prompt"])
        expected = str(case["expected"])
        prompt_tokens = tokens(prompt)
        ranked = sorted(
            (
                (len(prompt_tokens & name_tokens) * 3 + len(prompt_tokens & description_tokens), skill_name)
                for skill_name, (name_tokens, description_tokens) in skill_vectors.items()
            ),
            reverse=True,
        )
        top = [skill_name for score, skill_name in ranked[:3] if score > 0]
        if expected not in top:
            errors.append(f"smoke mismatch for {prompt!r}: expected {expected}, top={top}")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local Codex skills for trigger quality and structure.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="codex-skills repository root")
    parser.add_argument("--include-system", action="store_true", help="also audit .system skills")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--smoke-cases", type=Path, default=None, help="optional smoke cases JSON path")
    parser.add_argument("--max-description-chars", type=int, default=DEFAULT_MAX_DESCRIPTION_CHARS)
    parser.add_argument("--max-skill-lines", type=int, default=DEFAULT_MAX_SKILL_LINES)
    args = parser.parse_args()

    root = args.root.resolve()
    skills = discover_skills(root, include_system=args.include_system)
    smoke_skills = discover_skills(root, include_system=True)
    errors: list[str] = []
    warnings: list[str] = []

    for skill in skills:
        skill_errors, skill_warnings = audit_skill(
            skill,
            root=root,
            max_description_chars=args.max_description_chars,
            max_skill_lines=args.max_skill_lines,
        )
        errors.extend(f"{skill.path.relative_to(root)}: {message}" for message in skill_errors)
        warnings.extend(f"{skill.path.relative_to(root)}: {message}" for message in skill_warnings)

    smoke_errors, smoke_warnings = run_smoke_cases(root, smoke_skills, args.smoke_cases)
    errors.extend(f"trigger-smoke: {message}" for message in smoke_errors)
    warnings.extend(f"trigger-smoke: {message}" for message in smoke_warnings)

    print(f"Audited {len(skills)} skills")
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"ERROR: {message}")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
