#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
import statistics
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from pathlib import Path

from scipy import stats
from scipy.stats import rankdata

BASE = Path(__file__).resolve().parent
RATINGS = BASE / "anonymized_ratings.csv"
META = BASE / "participant_metadata.csv"

APPROACHES = [
    "Multi-Agent-Prototyp",
    "Zentralisierter Einzelagent",
    "Regelbasierter Ansatz",
]
SCENARIOS = [
    "Onboarding-Lernpfad",
    "Kursanpassung nach Testergebnissen",
    "Compliance-Pflichtschulung",
]


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def linear_quantile(values, q):
    xs = sorted(values)
    if not xs:
        return math.nan
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def fmt2(value):
    return f"{Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def fmt_p(value):
    return f"{value:.3f}" if value >= 0.1 else f"{value:.4f}"


def holm_adjust(pvalues):
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        candidate = min(1.0, (m - rank) * pvalues[idx])
        running = max(running, candidate)
        adjusted[idx] = running
    return adjusted


def rank_biserial(a, b):
    diffs = [x - y for x, y in zip(a, b)]
    nonzero = [d for d in diffs if abs(d) > 1e-12]
    ranks = rankdata([abs(d) for d in nonzero], method="average")
    w_plus = sum(r for r, d in zip(ranks, nonzero) if d > 0)
    w_minus = sum(r for r, d in zip(ranks, nonzero) if d < 0)
    return (w_plus - w_minus) / (w_plus + w_minus)


def main():
    ratings = read_csv(RATINGS)
    meta = read_csv(META)

    main_ids = {
        row["participant_id"]
        for row in meta
        if row["included_main_analysis"].lower() == "true"
    }
    main_rows = [r for r in ratings if r["participant_id"] in main_ids]

    possible = len(main_ids) * 3 * 3 * 6
    present = sum(1 for r in main_rows if r["score"] != "")
    missing = possible - present

    understandable = defaultdict(int)
    for row in meta:
        if row["participant_id"] in main_ids:
            understandable[row["criteria_understandable"]] += 1

    durations = {
        row["participant_id"]: float(row["duration_minutes"])
        for row in meta
        if row["participant_id"] in main_ids
    }
    under3 = sum(1 for d in durations.values() if d < 3.0)
    sensitivity_ids = {pid for pid, d in durations.items() if d >= 3.0}

    # Table 24: pooled valid individual ratings, scaled from 0–2 to 0–12.
    table24 = {}
    for scenario in SCENARIOS:
        table24[scenario] = {}
        for approach in APPROACHES:
            xs = [
                float(r["score"])
                for r in main_rows
                if r["scenario"] == scenario
                and r["approach"] == approach
                and r["score"] != ""
            ]
            table24[scenario][approach] = statistics.fmean(xs) * 6

    table24_total = {}
    for approach in APPROACHES:
        xs = [
            float(r["score"])
            for r in main_rows
            if r["approach"] == approach and r["score"] != ""
        ]
        table24_total[approach] = statistics.fmean(xs) * 6

    # Participant-level scenario scores: mean of available criteria * 6.
    grouped = defaultdict(list)
    for r in main_rows:
        if r["score"] == "":
            continue
        key = (r["participant_id"], r["scenario"], r["approach"])
        grouped[key].append(float(r["score"]))

    scenario_score = {
        key: statistics.fmean(xs) * 6
        for key, xs in grouped.items()
    }

    participant_total = defaultdict(dict)
    for pid in sorted(main_ids):
        for approach in APPROACHES:
            xs = [
                scenario_score[(pid, scenario, approach)]
                for scenario in SCENARIOS
            ]
            participant_total[pid][approach] = statistics.fmean(xs)

    values_by_approach = {
        approach: [participant_total[pid][approach] for pid in sorted(main_ids)]
        for approach in APPROACHES
    }

    table25 = {}
    for approach, xs in values_by_approach.items():
        table25[approach] = {
            "median": statistics.median(xs),
            "q1": linear_quantile(xs, 0.25),
            "q3": linear_quantile(xs, 0.75),
            "mean": statistics.fmean(xs),
        }

    # Friedman + Kendall W
    multi = values_by_approach[APPROACHES[0]]
    single = values_by_approach[APPROACHES[1]]
    rule = values_by_approach[APPROACHES[2]]
    friedman = stats.friedmanchisquare(multi, single, rule)
    kendall_w = friedman.statistic / (len(main_ids) * (len(APPROACHES) - 1))

    # Pairwise Wilcoxon. method="approx" reproduces the thesis analysis with zero differences present.
    pairs = [
        ("Multi-Agent gegen Einzelagent", multi, single),
        ("Multi-Agent gegen regelbasiert", multi, rule),
        ("Einzelagent gegen regelbasiert", single, rule),
    ]
    raw_p = []
    pair_stats = []
    for label, a, b in pairs:
        result = stats.wilcoxon(
            a,
            b,
            zero_method="wilcox",
            correction=False,
            alternative="two-sided",
            method="approx",
        )
        raw_p.append(float(result.pvalue))
        pair_stats.append(
            {
                "label": label,
                "wsr": float(result.statistic),
                "rrb": float(rank_biserial(a, b)),
            }
        )
    adjusted = holm_adjust(raw_p)
    for row, p_raw, p_adj in zip(pair_stats, raw_p, adjusted):
        row["p_raw"] = p_raw
        row["p_holm"] = p_adj

    # Sensitivity: pooled valid Multi-Agent ratings among participants with >= 3 minutes.
    sensitivity = {}
    for scenario in SCENARIOS:
        xs = [
            float(r["score"])
            for r in main_rows
            if r["participant_id"] in sensitivity_ids
            and r["scenario"] == scenario
            and r["approach"] == APPROACHES[0]
            and r["score"] != ""
        ]
        sensitivity[scenario] = statistics.fmean(xs) * 6

    print("DATENQUALITÄT")
    print(f"Rückläufe insgesamt: {len(meta)}")
    print(f"Hauptanalyse n: {len(main_ids)}")
    print(f"Mögliche Einzelratings: {possible}")
    print(f"Vorhandene Einzelratings: {present}")
    print(f"Fehlende Einzelratings: {missing} ({missing/possible*100:.2f} %)")
    print(f"Kriterien verständlich: Ja={understandable['Ja']}, Teilweise={understandable['Teilweise']}")
    print(f"Antworten unter 3 Minuten: {under3}")
    print(f"Sensitivitätsstichprobe >= 3 Minuten: {len(sensitivity_ids)}")
    print()

    print("TABELLE 24 – MITTELWERTE 0–12")
    for scenario in SCENARIOS:
        print(
            f"{scenario}: "
            f"Multi-Agent={fmt2(table24[scenario][APPROACHES[0]])}; "
            f"Einzelagent={fmt2(table24[scenario][APPROACHES[1]])}; "
            f"Regelbasiert={fmt2(table24[scenario][APPROACHES[2]])}"
        )
    print(
        "Gesamt: "
        f"Multi-Agent={fmt2(table24_total[APPROACHES[0]])}; "
        f"Einzelagent={fmt2(table24_total[APPROACHES[1]])}; "
        f"Regelbasiert={fmt2(table24_total[APPROACHES[2]])}"
    )
    print()

    print("TABELLE 25 – TEILNEHMERBEZOGENE GESAMTWERTE")
    for approach in APPROACHES:
        x = table25[approach]
        print(
            f"{approach}: Median={fmt2(x['median'])}; "
            f"Q1–Q3={fmt2(x['q1'])}–{fmt2(x['q3'])}; Mittelwert={fmt2(x['mean'])}"
        )
    print()

    print("INFERENZSTATISTIK")
    print(f"Friedman χ²(2)={fmt2(friedman.statistic)}; p={friedman.pvalue:.4f}")
    print(f"Kendall W={kendall_w:.3f}")
    for row in pair_stats:
        print(
            f"{row['label']}: WSR={row['wsr']:.1f}; "
            f"Holm-p={fmt_p(row['p_holm'])}; r_rb={row['rrb']:.3f}"
        )
    print()

    print("SENSITIVITÄTSANALYSE (>= 3 Minuten, Multi-Agent)")
    for scenario in SCENARIOS:
        print(f"{scenario}: {fmt2(sensitivity[scenario])}")


if __name__ == "__main__":
    main()
