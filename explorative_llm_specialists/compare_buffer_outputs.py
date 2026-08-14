"""Vergleicht zwei JSON-Ausgaben des experimentellen Multi-Agent-Puffers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def raw_actions(data):
    return sum(len(r.get("proposed_actions", [])) for r in data.get("specialist_results", []))


def final_actions(data):
    return len(data.get("plan", {}).get("actions", []))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--label-a", default="A")
    p.add_argument("--label-b", default="B")
    args = p.parse_args()
    a, b = load(args.a), load(args.b)
    print("Vergleich Multi-Agent-Puffer")
    print("=" * 52)
    for label, data in ((args.label_a, a), (args.label_b, b)):
        print(f"{label} Roh-Aktionen:       {raw_actions(data)}")
        print(f"{label} Final-Aktionen:     {final_actions(data)}")
        c = data.get("consolidation", {})
        if c:
            if "ownership_rejected_count" in c:
                print(f"{label} Ownership-Rejects:  {c.get('ownership_rejected_count')}")
            if "grounding_rejected_count" in c:
                print(f"{label} Grounding-Rejects:  {c.get('grounding_rejected_count')}")
            if "passed_ownership_and_grounding_count" in c:
                print(f"{label} Beide Filter ok:    {c.get('passed_ownership_and_grounding_count')}")
            print(f"{label} Konsolidiert final: {c.get('final_consolidated_action_count')}")
        print("-" * 52)


if __name__ == "__main__":
    main()
