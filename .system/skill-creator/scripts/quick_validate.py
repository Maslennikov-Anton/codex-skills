#!/usr/bin/env python3
"""Quick validation script for skills."""

import re
import sys
from pathlib import Path

import yaml

MAX_SKILL_NAME_LENGTH = 64
RESOURCE_LINK_RE = re.compile(
    r"\b(?P<path>(?:references|scripts|assets)/[^)\s`\]]+)"
)


def _extract_frontmatter(content: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise ValueError("Invalid frontmatter format")

    frontmatter_text = match.group(1)
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in frontmatter: {exc}") from exc

    if not isinstance(frontmatter, dict):
        raise ValueError("Frontmatter must be a YAML dictionary")

    return frontmatter


def _validate_frontmatter(frontmatter: dict) -> list[str]:
    errors: list[str] = []

    allowed_properties = {"name", "description", "license", "allowed-tools", "metadata"}
    unexpected_keys = set(frontmatter.keys()) - allowed_properties
    if unexpected_keys:
        allowed = ", ".join(sorted(allowed_properties))
        unexpected = ", ".join(sorted(unexpected_keys))
        errors.append(
            f"Unexpected key(s) in SKILL.md frontmatter: {unexpected}. "
            f"Allowed properties are: {allowed}"
        )

    if "name" not in frontmatter:
        errors.append("Missing 'name' in frontmatter")
    if "description" not in frontmatter:
        errors.append("Missing 'description' in frontmatter")

    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        errors.append(f"Name must be a string, got {type(name).__name__}")
    else:
        name = name.strip()
        if name:
            if not re.match(r"^[a-z0-9-]+$", name):
                errors.append(
                    f"Name '{name}' should be hyphen-case "
                    "(lowercase letters, digits, and hyphens only)"
                )
            if name.startswith("-") or name.endswith("-") or "--" in name:
                errors.append(
                    f"Name '{name}' cannot start/end with hyphen "
                    "or contain consecutive hyphens"
                )
            if len(name) > MAX_SKILL_NAME_LENGTH:
                errors.append(
                    f"Name is too long ({len(name)} characters). "
                    f"Maximum is {MAX_SKILL_NAME_LENGTH} characters."
                )

    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        errors.append(
            f"Description must be a string, got {type(description).__name__}"
        )
    else:
        description = description.strip()
        if description:
            if "<" in description or ">" in description:
                errors.append("Description cannot contain angle brackets (< or >)")
            if len(description) > 1024:
                errors.append(
                    f"Description is too long ({len(description)} characters). "
                    "Maximum is 1024 characters."
                )

    return errors


def _validate_referenced_resources(skill_path: Path, content: str) -> list[str]:
    errors: list[str] = []
    referenced_paths = sorted(
        {match.group("path").rstrip(".,:;") for match in RESOURCE_LINK_RE.finditer(content)}
    )

    for relative_path in referenced_paths:
        if not (skill_path / relative_path).exists():
            errors.append(f"Referenced path does not exist: {relative_path}")

    return errors


def _validate_openai_yaml(skill_path: Path) -> list[str]:
    errors: list[str] = []
    openai_yaml = skill_path / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        return errors

    try:
        parsed = yaml.safe_load(openai_yaml.read_text())
    except yaml.YAMLError as exc:
        return [f"Invalid YAML in agents/openai.yaml: {exc}"]

    if parsed is None:
        return ["agents/openai.yaml is empty"]
    if not isinstance(parsed, dict):
        return ["agents/openai.yaml must be a YAML dictionary"]

    interface = parsed.get("interface")
    if not isinstance(interface, dict):
        errors.append("agents/openai.yaml must contain an 'interface' mapping")
        return errors

    display_name = interface.get("display_name")
    short_description = interface.get("short_description")
    default_prompt = interface.get("default_prompt")

    if not isinstance(display_name, str) or not display_name.strip():
        errors.append("agents/openai.yaml interface.display_name must be a non-empty string")
    if not isinstance(short_description, str) or not short_description.strip():
        errors.append(
            "agents/openai.yaml interface.short_description must be a non-empty string"
        )
    if not isinstance(default_prompt, str) or not default_prompt.strip():
        errors.append("agents/openai.yaml interface.default_prompt must be a non-empty string")

    return errors


def validate_skill(skill_path):
    """Validate a skill folder and return an aggregate result."""
    skill_path = Path(skill_path)

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    try:
        frontmatter = _extract_frontmatter(content)
    except ValueError as exc:
        return False, str(exc)

    errors = []
    errors.extend(_validate_frontmatter(frontmatter))
    errors.extend(_validate_referenced_resources(skill_path, content))
    errors.extend(_validate_openai_yaml(skill_path))

    if errors:
        return False, "\n".join(errors)

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)
