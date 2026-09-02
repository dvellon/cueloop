#!/usr/bin/env python3
"""Evaluate pinned YAMNet against a provenance-complete local WAV manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from cueloop.evaluation import DatasetValidationError, evaluate, load_evaluation_manifest
from cueloop.yamnet import DEFAULT_YAMNET_SHA256, ModelConfigurationError, YamnetClassifier


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--model-sha256", default=DEFAULT_YAMNET_SHA256)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument(
        "--split", choices=("calibration", "validation", "test"), required=True
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        dataset_id, records = load_evaluation_manifest(args.manifest, split=args.split)
        classifier = YamnetClassifier(
            args.model,
            args.mapping,
            expected_sha256=args.model_sha256,
            num_threads=args.threads,
            evidence_tier="development-computer",
        )
        result = evaluate(classifier, records, dataset_id=dataset_id)
    except (DatasetValidationError, ModelConfigurationError, OSError) as error:
        print(f"evaluation failed: {error}", file=sys.stderr)
        return 2
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

