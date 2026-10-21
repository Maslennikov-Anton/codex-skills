#!/usr/bin/env python3
"""Detect drift in source fingerprints; matching bytes do not verify prose claims."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def check(manifest: dict, source_root: Path | None = None) -> list[dict]:
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("references"), list) or not manifest["references"]:
        raise ValueError("Expected schema_version 1 and nonempty references")
    root = source_root or Path(manifest["source_root"])
    result = []
    for group in manifest["references"]:
        if not isinstance(group.get("source_sha256"), dict) or not group["source_sha256"]:
            raise ValueError("Each reference needs nonempty source fingerprints")
        drift = []
        for name, expected in group["source_sha256"].items():
            if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
                raise ValueError("Expected a SHA256 source fingerprint")
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError("Fingerprint source path escapes source root")
            if not path.is_file():
                drift.append({"path": name, "state": "missing"})
            else:
                hasher = hashlib.sha256()
                with path.open("rb") as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        hasher.update(chunk)
                if hasher.hexdigest() != expected:
                    drift.append({"path": name, "state": "changed"})
        result.append({"reference": group["reference"], "fingerprints": "drift" if drift else "match",
                       "semantic_review": group["semantic_review"], "captured_at": manifest["captured_at"],
                       "captured_commit": manifest["captured_commit"], "drift": drift})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-root", type=Path, help="Relocate a checkout without rewriting the manifest")
    args = parser.parse_args()
    try:
        result = check(json.loads(args.manifest.read_text()), args.source_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(any(row["drift"] for row in result))
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f"Source fingerprint check failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
