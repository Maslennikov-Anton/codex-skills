#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
APPROX_TOKEN_DIVISOR = 4

CONSTRAINT_RE = re.compile(
    r"\b(do not|don't|must not|never|without|avoid|only|strictly|limit to|"
    r"at most|at least|no more than|required?|restrict|exclude|ensure|must|"
    r"shall|нельзя|без|только|строго|огранич|исключ|обязательно|должен)\b",
    re.IGNORECASE,
)
SPEC_RE = re.compile(
    r"\b(spec|requirements?|acceptance criteria|design|plan|rfc|scope|"
    r"constraints?|verification|критерии|требован|план|огранич|провер|"
    r"ожидаем)\b",
    re.IGNORECASE,
)
IMPLEMENTATION_RE = re.compile(
    r"\b(implement|fix|refactor|add|create|write|update|change|debug|"
    r"сделай|почини|добавь|создай|напиши|обнови|измени|отладь|разбер)\b",
    re.IGNORECASE,
)
FILLER_RE = re.compile(
    r"\b(please|kindly|thanks|basically|essentially|definitely|absolutely|"
    r"simply|very|quite|somewhat|certainly|пожалуйста|просто|вообще|"
    r"короче|как бы)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-zА-Яа-я0-9_]+")
SYNTHETIC_USER_PREFIXES = (
    "<environment_context>",
    "<turn_aborted>",
    "turn_aborted",
)


@dataclass
class Session:
    path: Path
    session_id: str
    started_at: datetime | None = None
    cwd: str = ""
    model: str = ""
    effort: str = ""
    user_messages: list[str] = field(default_factory=list)
    assistant_messages: list[str] = field(default_factory=list)
    tool_calls: list[str] = field(default_factory=list)
    compactions: int = 0
    token_events: int = 0
    fallback_user_messages: list[str] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.user_messages) + len(self.assistant_messages)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    title: str
    severity: str
    count: int
    detail: str
    action: str
    examples: tuple[str, ...] = ()


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if "text" in item:
            parts.append(str(item["text"]))
        elif "input_text" in item:
            parts.append(str(item["input_text"]))
        elif "output_text" in item:
            parts.append(str(item["output_text"]))
    return "\n".join(part for part in parts if part)


def is_synthetic_user_text(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith(SYNTHETIC_USER_PREFIXES)


def normalize_prompt(text: str) -> str:
    return " ".join(WORD_RE.findall(text.lower()))


def approx_tokens(text: str) -> int:
    return max(1, len(text) // APPROX_TOKEN_DIVISOR) if text else 0


def is_structured(text: str) -> bool:
    return bool(
        re.search(r"(?m)^[-*]\s+", text)
        or re.search(r"(?m)^\d+[.)]\s+", text)
        or re.search(r"(?m)^#{1,4}\s+", text)
        or SPEC_RE.search(text)
    )


def classify_work_type(text: str) -> str:
    lowered = text.lower()
    buckets = (
        ("review", ("review", "ревью", "посмотри", "глянь")),
        ("debug", ("debug", "fix", "error", "fail", "почини", "ошиб", "падает")),
        ("test", ("test", "pytest", "coverage", "тест")),
        ("docs", ("doc", "readme", "report", "док", "отчет")),
        ("git", ("commit", "push", "pr", "merge", "git", "пуш")),
        ("implementation", ("implement", "add", "create", "refactor", "сделай", "добавь")),
    )
    for name, markers in buckets:
        if any(marker in lowered for marker in markers):
            return name
    return "other"


def iter_session_files(root: Path, days: int | None) -> list[Path]:
    files = sorted(root.glob("**/*.jsonl"))
    if days is None:
        return files
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [
        path
        for path in files
        if datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc) >= cutoff
    ]


def parse_session(path: Path) -> Session:
    session = Session(path=path, session_id=path.stem)
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid json: {exc}") from exc

        event_type = event.get("type")
        payload = event.get("payload") or {}
        if event_type == "session_meta":
            session.session_id = str(payload.get("id") or session.session_id)
            session.started_at = parse_ts(payload.get("timestamp")) or parse_ts(event.get("timestamp"))
            session.cwd = str(payload.get("cwd") or session.cwd)
            session.model = str(payload.get("model") or session.model)
        elif event_type == "turn_context":
            session.cwd = str(payload.get("cwd") or session.cwd)
            session.model = str(payload.get("model") or session.model)
            session.effort = str(payload.get("effort") or session.effort)
        elif event_type == "event_msg":
            payload_type = payload.get("type")
            if payload_type == "user_message":
                text = str(payload.get("message") or "").strip()
                if text and not is_synthetic_user_text(text):
                    session.fallback_user_messages.append(text)
            elif payload_type == "token_count":
                session.token_events += 1
            elif payload_type in {"agent_reasoning_section_break", "compact_begin", "compact_end"}:
                session.compactions += 1
        elif event_type == "response_item":
            item_type = payload.get("type")
            if item_type == "message":
                role = payload.get("role")
                text = extract_text(payload.get("content")).strip()
                if not text:
                    continue
                if role == "user":
                    if not is_synthetic_user_text(text):
                        session.user_messages.append(text)
                elif role == "assistant":
                    session.assistant_messages.append(text)
            elif item_type == "function_call":
                session.tool_calls.append(str(payload.get("name") or "unknown"))
            elif item_type == "web_search_call":
                session.tool_calls.append("web_search")

    if not session.user_messages and session.fallback_user_messages:
        session.user_messages = session.fallback_user_messages
    return session


def format_pct(count: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{count / total:.0%}"


def example(text: str, limit: int = 96) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3] + "..."


def audit_sessions(sessions: list[Session]) -> list[Finding]:
    findings: list[Finding] = []
    all_prompts = [message for session in sessions for message in session.user_messages]
    total_prompts = len(all_prompts)
    total_sessions = len(sessions)

    mega = [s for s in sessions if s.message_count > 50]
    if mega:
        findings.append(
            Finding(
                "mega-sessions",
                "Mega sessions",
                "high",
                len(mega),
                f"{len(mega)} of {total_sessions} sessions have more than 50 messages.",
                "Start a fresh thread at natural task boundaries and leave a short handoff when context grows.",
                tuple(f"{s.cwd or 'unknown'}: {s.message_count} messages" for s in mega[:5]),
            )
        )

    drifting = []
    for session in sessions:
        work_types = {classify_work_type(message) for message in session.user_messages}
        work_types.discard("other")
        if len(work_types) >= 4 and len(session.user_messages) >= 5:
            drifting.append((session, sorted(work_types)))
    if drifting:
        findings.append(
            Finding(
                "session-drift",
                "Session drift",
                "medium",
                len(drifting),
                f"{len(drifting)} sessions mix four or more task types.",
                "Split bugfix, docs, test, git, and implementation work into focused sessions.",
                tuple(f"{s.cwd or 'unknown'}: {', '.join(types)}" for s, types in drifting[:5]),
            )
        )

    runaway = [s for s in sessions if len(s.tool_calls) >= 25 and len(s.user_messages) <= 3]
    if runaway:
        findings.append(
            Finding(
                "runaway-agent-loops",
                "Runaway agent loops",
                "high",
                len(runaway),
                f"{len(runaway)} short sessions used 25+ tool calls.",
                "When the agent keeps searching or retrying, stop and restate the target, "
                "evidence, and stop condition.",
                tuple(f"{s.cwd or 'unknown'}: {len(s.tool_calls)} tool calls" for s in runaway[:5]),
            )
        )

    normalized_counts = Counter(
        normalize_prompt(prompt)
        for prompt in all_prompts
        if len(normalize_prompt(prompt)) >= 12
    )
    repeated = [(prompt, count) for prompt, count in normalized_counts.items() if count >= 3]
    if repeated:
        repeated.sort(key=lambda item: item[1], reverse=True)
        findings.append(
            Finding(
                "repeated-prompts",
                "Repeated prompts",
                "medium",
                sum(count for _, count in repeated),
                f"{len(repeated)} prompt patterns were repeated 3+ times.",
                "Turn repeated requests into a skill, hook, runbook, or a sharper prompt template.",
                tuple(f"{count}x: {example(prompt)}" for prompt, count in repeated[:5]),
            )
        )

    short_prompts = [p for p in all_prompts if len(p.strip()) < 30]
    if total_prompts >= 10 and len(short_prompts) / total_prompts > 0.3:
        findings.append(
            Finding(
                "lazy-prompting",
                "Short low-context prompts",
                "medium",
                len(short_prompts),
                f"{format_pct(len(short_prompts), total_prompts)} of prompts are under 30 characters.",
                "Add intent, files, constraints, and expected output for implementation or debugging tasks.",
                tuple(example(p) for p in short_prompts[:5]),
            )
        )

    substantial = [p for p in all_prompts if len(p.strip()) >= 40]
    constrained = [p for p in substantial if CONSTRAINT_RE.search(p)]
    if len(substantial) >= 30 and len(constrained) / len(substantial) < 0.08:
        findings.append(
            Finding(
                "low-constraint-usage",
                "Low constraint usage",
                "medium",
                len(substantial) - len(constrained),
                "Only "
                f"{format_pct(len(constrained), len(substantial))} of substantial prompts "
                "include explicit constraints.",
                "State boundaries like only/avoid/without/must, expected verification, and non-goals.",
            )
        )

    unstructured_starts = []
    for session in sessions:
        if not session.user_messages:
            continue
        first = session.user_messages[0]
        if IMPLEMENTATION_RE.search(first) and not is_structured(first):
            unstructured_starts.append(session)
    if total_sessions >= 5 and len(unstructured_starts) / total_sessions > 0.3:
        findings.append(
            Finding(
                "no-spec-structure",
                "Unstructured task starts",
                "medium",
                len(unstructured_starts),
                f"{format_pct(len(unstructured_starts), total_sessions)} of sessions start "
                "implementation-style work without structure.",
                "Start larger tasks with scope, acceptance criteria, constraints, and verification commands.",
                tuple(example(s.user_messages[0]) for s in unstructured_starts[:5]),
            )
        )

    spec_driven = []
    implementation_sessions = []
    for session in sessions:
        joined_start = "\n".join(session.user_messages[:2])
        if any(IMPLEMENTATION_RE.search(message) for message in session.user_messages):
            implementation_sessions.append(session)
            if is_structured(joined_start):
                spec_driven.append(session)
    if len(implementation_sessions) >= 5 and len(spec_driven) / len(implementation_sessions) < 0.2:
        findings.append(
            Finding(
                "no-spec-driven-development",
                "Low spec-first rate",
                "medium",
                len(implementation_sessions) - len(spec_driven),
                "Only "
                f"{format_pct(len(spec_driven), len(implementation_sessions))} of implementation "
                "sessions start with a spec-like prompt.",
                "For non-trivial changes, ask for or provide a short plan before edits begin.",
            )
        )

    verbose_outputs = []
    for session in sessions:
        for prompt, output in zip(session.user_messages, session.assistant_messages):
            if len(prompt) <= 200 and approx_tokens(output) > 5000:
                verbose_outputs.append((prompt, approx_tokens(output)))
    if total_prompts >= 10 and verbose_outputs:
        findings.append(
            Finding(
                "verbose-output",
                "Verbose output from short prompts",
                "medium",
                len(verbose_outputs),
                f"{len(verbose_outputs)} short prompts produced responses over about 5K tokens.",
                "Ask for concise output, a specific format, or a maximum number of bullets "
                "when you only need a summary.",
                tuple(f"{tokens} tokens approx: {example(prompt)}" for prompt, tokens in verbose_outputs[:5]),
            )
        )

    verbose_prompts = [
        p for p in all_prompts if len(p) >= 800 and len(FILLER_RE.findall(p)) >= 2
    ]
    if total_prompts >= 15 and len(verbose_prompts) / total_prompts > 0.2:
        findings.append(
            Finding(
                "verbose-prompt-no-compression",
                "Verbose prompts",
                "low",
                len(verbose_prompts),
                f"{format_pct(len(verbose_prompts), total_prompts)} of prompts are long and contain filler words.",
                "Use compact bullets and remove politeness/filler text from technical prompts.",
                tuple(example(p) for p in verbose_prompts[:5]),
            )
        )

    tool_bloat = [s for s in sessions if len(set(s.tool_calls)) > 40]
    if tool_bloat:
        findings.append(
            Finding(
                "mcp-tool-bloat",
                "Large active tool surface",
                "medium",
                len(tool_bloat),
                f"{len(tool_bloat)} sessions used more than 40 distinct tool names.",
                "Scope MCP/tool availability per workflow and disable rarely used servers for normal coding sessions.",
                tuple(f"{s.cwd or 'unknown'}: {len(set(s.tool_calls))} tools" for s in tool_bloat[:5]),
            )
        )

    compactions = [s for s in sessions if s.compactions > 0]
    if compactions:
        findings.append(
            Finding(
                "context-compactions",
                "Context compactions",
                "medium",
                sum(s.compactions for s in compactions),
                f"{len(compactions)} sessions recorded compaction events.",
                "Create a handoff and start a fresh session before automatic compaction if the task is still active.",
                tuple(f"{s.cwd or 'unknown'}: {s.compactions} compactions" for s in compactions[:5]),
            )
        )

    high_tool_sessions = [s for s in sessions if len(s.tool_calls) >= 80]
    if high_tool_sessions:
        findings.append(
            Finding(
                "tool-heavy-sessions",
                "Tool-heavy sessions",
                "medium",
                len(high_tool_sessions),
                f"{len(high_tool_sessions)} sessions used 80+ tool calls.",
                "Review whether the workflow needs a script, fixture, or project-context update.",
                tuple(f"{s.cwd or 'unknown'}: {len(s.tool_calls)} tool calls" for s in high_tool_sessions[:5]),
            )
        )

    return sorted(findings, key=lambda f: ({"high": 0, "medium": 1, "low": 2}.get(f.severity, 9), f.rule_id))


def workspace_counts(sessions: list[Session]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for session in sessions:
        counts[session.cwd or "unknown"] += len(session.user_messages)
    return counts


def render_markdown(sessions: list[Session], findings: list[Finding], days: int | None) -> str:
    total_prompts = sum(len(session.user_messages) for session in sessions)
    total_tools = sum(len(session.tool_calls) for session in sessions)
    period = "all available sessions" if days is None else f"last {days} days"
    lines = [
        "# Codex Session Audit",
        "",
        f"- Period: {period}",
        f"- Sessions: {len(sessions)}",
        f"- User prompts: {total_prompts}",
        f"- Tool calls: {total_tools}",
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("No findings triggered for the selected session set.")
    for finding in findings:
        lines.extend(
            [
                f"### {finding.severity.upper()} - {finding.title}",
                "",
                f"- Rule: `{finding.rule_id}`",
                f"- Count: {finding.count}",
                f"- Detail: {finding.detail}",
                f"- Action: {finding.action}",
            ]
        )
        if finding.examples:
            lines.append("- Examples:")
            lines.extend(f"  - {item}" for item in finding.examples)
        lines.append("")

    lines.extend(["## Top Workspaces", ""])
    for workspace, count in workspace_counts(sessions).most_common(10):
        lines.append(f"- `{workspace}`: {count} prompts")
    lines.append("")
    lines.extend(["## Adopted Rule Ideas", ""])
    lines.extend(
        [
            "- From AI Engineering Coach: mega-sessions, session-drift, runaway-agent-loops, repeated-prompts.",
            "- From AI Engineering Coach: lazy-prompting, low-constraint-usage, "
            "no-spec-structure, no-spec-driven-development.",
            "- From AI Engineering Coach: verbose-output, verbose-prompt-no-compression, mcp-tool-bloat.",
            "- Codex-specific additions: context-compactions and tool-heavy-sessions.",
            "- Skipped for now: IDE-only auto-accept/devcontainer rules, personal schedule "
            "rules, and model-cost rules without reliable fields.",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def render_text(sessions: list[Session], findings: list[Finding], days: int | None) -> str:
    markdown = render_markdown(sessions, findings, days)
    return re.sub(r"^#+\s*", "", markdown, flags=re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit local Codex jsonl sessions for agentic workflow anti-patterns."
    )
    parser.add_argument("--sessions-root", type=Path, default=DEFAULT_SESSIONS_ROOT)
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="lookback window by file mtime; use 0 for all sessions",
    )
    parser.add_argument("--workspace", help="substring filter for session cwd")
    parser.add_argument("--format", choices=("text", "markdown"), default="text")
    parser.add_argument("--output", type=Path, help="write report to this file")
    args = parser.parse_args()

    days = None if args.days == 0 else args.days
    if not args.sessions_root.exists():
        print(f"sessions root not found: {args.sessions_root}", file=sys.stderr)
        return 2

    sessions = [parse_session(path) for path in iter_session_files(args.sessions_root, days)]
    if args.workspace:
        sessions = [session for session in sessions if args.workspace in session.cwd]

    findings = audit_sessions(sessions)
    if args.format == "markdown":
        report = render_markdown(sessions, findings, days)
    else:
        report = render_text(sessions, findings, days)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
