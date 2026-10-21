#!/usr/bin/env python3
"""Conservative wall-time smoke comparison; never proves functional correctness."""

import argparse
import json
import math
from pathlib import Path
import statistics
import sys


def validate(record):
    if not isinstance(record, dict) or not isinstance(record.get("revision"), str) or not record["revision"]:
        raise ValueError("missing revision")
    for key in ("environment", "workload", "protocol"):
        if not isinstance(record.get(key), dict) or not record[key]:
            raise ValueError(f"missing {key}")
    for group, keys in (("environment", ("cpu", "kernel", "python", "dependencies")),
                        ("workload", ("id", "input_sha256")), ("protocol", ("method",))):
        for key in keys:
            value = record[group].get(key)
            if not isinstance(value, str) or value.strip().lower() in ("", "unknown", "n/a", "unavailable"):
                raise ValueError(f"missing {group}.{key}")
    protocol = record["protocol"]
    if protocol.get("unit") != "seconds":
        raise ValueError("unit must be seconds")
    if type(protocol.get("warmups")) is not int or protocol["warmups"] < 0:
        raise ValueError("invalid warmups")
    samples = record.get("samples_seconds")
    if not isinstance(samples, list) or not samples:
        raise ValueError("missing samples")
    if type(protocol.get("repeats")) is not int or protocol["repeats"] != len(samples):
        raise ValueError("repeats mismatch")
    if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in samples):
        raise ValueError("samples must be finite and positive")
    return samples


def compare(before, after, min_win=0.05, max_cv=0.05):
    if not all(math.isfinite(x) and 0 <= x < 1 for x in (min_win, max_cv)):
        raise ValueError("thresholds must be finite fractions in [0, 1)")
    old, new = validate(before), validate(after)
    reasons = [f"different {key}" for key in ("environment", "workload", "protocol")
               if before[key] != after[key]]
    if min(len(old), len(new)) < 5:
        reasons.append("at least five measured samples per variant required")
    old_cv = statistics.stdev(old) / statistics.mean(old) if len(old) > 1 else 0
    new_cv = statistics.stdev(new) / statistics.mean(new) if len(new) > 1 else 0
    if max(old_cv, new_cv) > max_cv:
        reasons.append("noise exceeds max_cv")
    gain = 1 - statistics.median(new) / statistics.median(old)
    if not all(math.isfinite(x) for x in (gain, old_cv, new_cv)):
        raise ValueError("non-finite comparison metrics")
    if reasons:
        verdict, code = "inconclusive", 2
    elif gain >= min_win and max(new) < min(old):
        verdict, code = "measurement-win", 0
    else:
        verdict, code = "no-win", 1
        reasons.append("gain below threshold or sample ranges overlap")
    return {"verdict": verdict, "reasons": reasons,
            "median_before_seconds": statistics.median(old),
            "median_after_seconds": statistics.median(new), "median_gain_fraction": gain,
            "cv_before": old_cv, "cv_after": new_cv,
            "samples_before": len(old), "samples_after": len(new),
            "limits": "Wall-time smoke only; no functional, memory, scaling or statistical-confidence proof."}, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--min-win", type=float, default=0.05)
    parser.add_argument("--max-cv", type=float, default=0.05)
    args = parser.parse_args()
    try:
        result, code = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()),
                               args.min_win, args.max_cv)
    except (ValueError, OSError, TypeError) as error:
        print(json.dumps({"verdict": "error", "reason": str(error)}))
        return 3
    print(json.dumps(result, indent=2, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
