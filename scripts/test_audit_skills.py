from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.audit_skills import (
    Skill,
    audit_agent_metadata,
    audit_skill,
    mentioned_resources,
    run_repository_contract_checks,
)


class AuditSkillsTest(unittest.TestCase):
    def make_skill(self, root: Path, name: str = "sample-skill") -> Skill:
        skill_path = root / name
        skill_path.mkdir()
        agents_path = skill_path / "agents"
        agents_path.mkdir()
        (agents_path / "openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Sample Skill"\n'
            '  short_description: "Short sample skill description."\n'
            f'  default_prompt: "Use ${name} to do the task."\n',
            encoding="utf-8",
        )
        return Skill(
            path=skill_path,
            name=name,
            description="Inspect sample artifacts for a concrete task.",
            body="# Sample\n",
        )

    def test_missing_example_resource_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = self.make_skill(Path(directory))
            skill = Skill(
                path=skill.path,
                name=skill.name,
                description=skill.description,
                body="- Example: `references/example.md` for illustration.\n",
            )
            self.assertEqual(mentioned_resources(skill), set())

    def test_missing_real_resource_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = self.make_skill(root)
            skill = Skill(
                path=skill.path,
                name=skill.name,
                description=skill.description,
                body="Read `references/missing.md` before acting.\n",
            )
            errors, _ = audit_skill(skill, root, 220, 500)
            self.assertIn("missing referenced resource: references/missing.md", errors)

    def test_default_prompt_must_name_skill(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skill = self.make_skill(Path(directory))
            metadata_path = skill.path / "agents" / "openai.yaml"
            metadata_path.write_text(
                "interface:\n"
                '  display_name: "Sample Skill"\n'
                '  short_description: "Short sample skill description."\n'
                '  default_prompt: "Use the skill for this task."\n',
                encoding="utf-8",
            )
            errors, _ = audit_agent_metadata(skill)
            self.assertIn(
                "agents/openai.yaml: interface.default_prompt must mention $sample-skill",
                errors,
            )

    def test_repository_contract_check_detects_copy_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left = root / "vcont" / "references" / "studio-vcont-contract.md"
            right = root / "vcstudio" / "references" / "studio-vcont-contract.md"
            left.parent.mkdir(parents=True)
            right.parent.mkdir(parents=True)
            left.write_text("left\n", encoding="utf-8")
            right.write_text("right\n", encoding="utf-8")
            self.assertIn(
                "reference-parity: vcont and vcstudio studio-vcont-contract.md differ",
                run_repository_contract_checks(root),
            )


if __name__ == "__main__":
    unittest.main()
