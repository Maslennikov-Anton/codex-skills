#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


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
MODBUS_REGISTER_ROW_RE = re.compile(
    r"^\| `(?:QX0-QX65535|IX0-IX65535|IW0-IW65535|MW0-MW29999|MD0-MD9999|ML0-ML3750)`"
)
RESOURCE_RE = re.compile(
    r"(?:^|[\s(])`?((?:references|scripts|assets)/[A-Za-z0-9_./-]+(?:\.[A-Za-z0-9]+|/))`?"
)
EXAMPLE_LINE_RE = re.compile(
    r"\b(?:example|examples|e\.g\.|пример|например|would be helpful)\b",
    re.IGNORECASE,
)


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


def mentioned_resources(skill: Skill) -> set[str]:
    resources: set[str] = set()
    in_fence = False
    for line in skill.body.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for resource in RESOURCE_RE.findall(line):
            resource = resource.rstrip(".,);")
            if not (skill.path / resource).exists() and EXAMPLE_LINE_RE.search(line):
                continue
            resources.add(resource)
    return resources


def audit_agent_metadata(skill: Skill) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    metadata_path = skill.path / "agents" / "openai.yaml"
    if not metadata_path.exists():
        return ["missing agents/openai.yaml"], warnings

    try:
        payload = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        return [f"invalid agents/openai.yaml: {error}"], warnings

    interface = payload.get("interface")
    if not isinstance(interface, dict):
        return ["agents/openai.yaml: missing interface mapping"], warnings

    for field in ("display_name", "short_description", "default_prompt"):
        value = interface.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"agents/openai.yaml: missing non-empty interface.{field}")

    short_description = interface.get("short_description")
    if isinstance(short_description, str) and not 25 <= len(short_description) <= 64:
        warnings.append(
            "agents/openai.yaml: interface.short_description is "
            f"{len(short_description)} chars; expected 25-64"
        )

    default_prompt = interface.get("default_prompt")
    if isinstance(default_prompt, str) and f"${skill.name}" not in default_prompt:
        errors.append(
            f"agents/openai.yaml: interface.default_prompt must mention ${skill.name}"
        )

    return errors, warnings


def audit_skill(skill: Skill, root: Path, max_description_chars: int, max_skill_lines: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if skill.name != skill.path.name:
        errors.append(
            f"frontmatter name {skill.name!r} does not match folder {skill.path.name!r}"
        )

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

    mentioned = mentioned_resources(skill)
    for resource in sorted(mentioned):
        if not (skill.path / resource).exists() and not (root / resource).exists():
            errors.append(f"missing referenced resource: {resource}")

    references_dir = skill.path / "references"
    if references_dir.exists():
        existing_refs = sorted(path.relative_to(skill.path).as_posix() for path in references_dir.glob("*.md"))
        unmentioned_refs = [reference for reference in existing_refs if reference not in mentioned]
        if unmentioned_refs:
            warnings.append(
                "references not mentioned from SKILL.md: " + ", ".join(unmentioned_refs[:8])
            )

    metadata_errors, metadata_warnings = audit_agent_metadata(skill)
    if skill.path.parent == root / ".system":
        warnings.extend(metadata_errors)
    else:
        errors.extend(metadata_errors)
    warnings.extend(metadata_warnings)

    return errors, warnings


def run_smoke_cases(
    root: Path,
    skills: list[Skill],
    cases_path: Path | None,
    required_skill_names: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    if cases_path is None:
        cases_path = root / "scripts" / "skill_trigger_smoke_cases.json"
    if not cases_path.exists():
        return [], [f"smoke cases file not found: {cases_path}"]

    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        return [f"cannot read smoke cases: {error}"], []
    if not isinstance(cases, list):
        return ["smoke cases root must be a JSON list"], []

    errors: list[str] = []
    warnings: list[str] = []
    skill_vectors = {
        skill.name: (
            tokens(f"{skill.name} {skill.path.name}"),
            tokens(skill.description),
        )
        for skill in skills
    }

    known_skill_names = set(skill_vectors)
    covered_skill_names: set[str] = set()
    seen_prompts: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or not isinstance(case.get("prompt"), str) or not isinstance(case.get("expected"), str):
            errors.append(f"case {index}: expected string prompt and expected fields")
            continue
        prompt = case["prompt"].strip()
        expected = case["expected"].strip()
        if not prompt or not expected:
            errors.append(f"case {index}: prompt and expected must be non-empty")
            continue
        if prompt in seen_prompts:
            errors.append(f"case {index}: duplicate prompt {prompt!r}")
            continue
        seen_prompts.add(prompt)
        if expected not in known_skill_names:
            errors.append(f"case {index}: unknown expected skill {expected!r}")
            continue
        covered_skill_names.add(expected)
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

    if required_skill_names:
        missing = sorted(required_skill_names - covered_skill_names)
        if missing:
            errors.append("skills without trigger smoke coverage: " + ", ".join(missing))
    return errors, warnings


def run_repository_contract_checks(root: Path) -> list[str]:
    errors: list[str] = []

    contract_paths = (
        root / "vcont" / "references" / "studio-vcont-contract.md",
        root / "vcstudio" / "references" / "studio-vcont-contract.md",
    )
    if all(path.exists() for path in contract_paths):
        if contract_paths[0].read_bytes() != contract_paths[1].read_bytes():
            errors.append(
                "reference-parity: vcont and vcstudio studio-vcont-contract.md differ"
            )

    modbus_paths = (
        root / "vcont" / "references" / "vc024sa-runtime-contract.md",
        root / "vcstudio" / "references" / "communications.md",
        root / "vcstudio" / "references" / "vc024sa-key-facts.md",
    )
    if all(path.exists() for path in modbus_paths):
        row_sets: list[tuple[str, ...]] = []
        for path in modbus_paths:
            rows = tuple(
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if MODBUS_REGISTER_ROW_RE.match(line)
            )
            if len(rows) != 6:
                errors.append(
                    f"reference-parity: expected 6 Modbus memory rows in {path.relative_to(root)}, got {len(rows)}"
                )
            row_sets.append(rows)
        if len(set(row_sets)) != 1:
            errors.append("reference-parity: Modbus server memory maps differ")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local Codex skills for trigger quality and structure.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="codex-skills repository root")
    parser.add_argument("--include-system", action="store_true", help="also audit .system skills")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument(
        "--require-smoke-coverage",
        action="store_true",
        help="require at least one smoke case for every audited skill",
    )
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

    required_skill_names = {skill.name for skill in skills} if args.require_smoke_coverage else None
    smoke_errors, smoke_warnings = run_smoke_cases(
        root,
        smoke_skills,
        args.smoke_cases,
        required_skill_names=required_skill_names,
    )
    errors.extend(f"trigger-smoke: {message}" for message in smoke_errors)
    warnings.extend(f"trigger-smoke: {message}" for message in smoke_warnings)
    errors.extend(run_repository_contract_checks(root))

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
