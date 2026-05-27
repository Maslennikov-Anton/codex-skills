#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_codex_sessions import audit_sessions, parse_session


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")


class AuditCodexSessionsTest(unittest.TestCase):
    def test_parse_session_extracts_messages_and_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(
                path,
                [
                    {"type": "session_meta", "payload": {"id": "s1", "cwd": "/repo"}},
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "fix failing tests"}],
                        },
                    },
                    {
                        "type": "response_item",
                        "payload": {"type": "function_call", "name": "exec_command"},
                    },
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "done"}],
                        },
                    },
                ],
            )

            session = parse_session(path)

        self.assertEqual(session.session_id, "s1")
        self.assertEqual(session.cwd, "/repo")
        self.assertEqual(session.user_messages, ["fix failing tests"])
        self.assertEqual(session.assistant_messages, ["done"])
        self.assertEqual(session.tool_calls, ["exec_command"])

    def test_parse_session_ignores_synthetic_environment_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(
                path,
                [
                    {"type": "session_meta", "payload": {"id": "s1", "cwd": "/repo"}},
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": "<environment_context>\n...</environment_context>",
                                }
                            ],
                        },
                    },
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "real task"}],
                        },
                    },
                ],
            )

            session = parse_session(path)

        self.assertEqual(session.user_messages, ["real task"])

    def test_audit_detects_repeated_prompts_and_mega_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            events = [{"type": "session_meta", "payload": {"id": "s1", "cwd": "/repo"}}]
            for _ in range(26):
                events.append(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "please fix the failing pytest suite"}],
                        },
                    }
                )
                events.append(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "ok"}],
                        },
                    }
                )
            write_jsonl(path, events)
            session = parse_session(path)

        rule_ids = {finding.rule_id for finding in audit_sessions([session])}
        self.assertIn("mega-sessions", rule_ids)
        self.assertIn("repeated-prompts", rule_ids)


if __name__ == "__main__":
    unittest.main()
