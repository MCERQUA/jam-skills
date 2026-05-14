#!/usr/bin/env python3
"""Stage 1 of the contact-enrichment cascade.

Classifies a raw name string as `person`, `company`, or `ambiguous`.
Heuristic — no external libs, no API calls. Outputs JSON.

Spec + cascade context: /home/mike/MIKE-AI/docs/jambot/contact-enrichment-skill.md
"""

import argparse
import json
import re
import sys

BUSINESS_SUFFIXES = {
    "llc", "l.l.c.", "l.l.c",
    "llp", "l.l.p.", "l.l.p",
    "inc", "inc.", "incorporated",
    "corp", "corp.", "corporation",
    "ltd", "ltd.", "limited",
    "co", "co.", "company",
    "lp", "l.p.", "l.p",
    "plc", "p.l.c.", "p.l.c",
    "pc", "p.c.", "p.c",
    "pa", "p.a.", "p.a",
    "lc", "l.c.", "l.c",
    "pllc", "p.l.l.c.", "p.l.l.c",
    "gmbh", "ag", "sa", "bv", "nv", "spa", "srl", "kg", "ohg",
}

INDUSTRY_KEYWORDS = {
    "insulation", "insulate", "insulated", "insulating",
    "foam", "foams", "spray", "sprayed", "spraying", "sprayfoam",
    "contractor", "contractors", "contracting",
    "builder", "builders", "building", "construction", "constructions",
    "restoration", "restorations", "remodel", "remodeling",
    "roofing", "roofer", "roofers",
    "painting", "painter", "painters",
    "plumbing", "plumber", "plumbers",
    "electric", "electrical", "electrician", "electricians",
    "hvac", "heating", "cooling", "mechanical",
    "energy", "energies",
    "services", "service",
    "solutions", "solution",
    "systems", "system",
    "group", "holdings",
    "enterprises", "enterprise",
    "supply", "supplies",
    "products", "product",
    "industries", "industry", "industrial",
    "partners", "partnership",
    "associates",
    "consultants", "consulting",
    "management",
    "properties", "property",
    "realty",
    "design", "designs", "designer",
    "remediation",
    "exteriors", "interiors",
    "siding", "windows", "doors",
    "concrete", "masonry",
    "landscaping", "landscapers",
    # Family-business markers — treated as company signals
    "brothers", "bros", "sisters", "sons", "daughters", "family",
}

PARTICLES = {"van", "der", "de", "la", "le", "da", "di", "von", "el", "del", "du"}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'\-\.]*")
WS_RE = re.compile(r"\s+")


def _tokens(s: str) -> list:
    return TOKEN_RE.findall(s)


def _norm(s: str) -> str:
    return WS_RE.sub(" ", s).strip()


def classify(name: str) -> dict:
    raw = name if isinstance(name, str) else str(name)
    normalized = _norm(raw)
    tokens = _tokens(normalized)
    lower_tokens = [t.lower().rstrip(".") for t in tokens]
    signals = []

    if not tokens:
        return {
            "input": raw,
            "type": "ambiguous",
            "confidence": "low",
            "normalized": normalized,
            "tokens": [],
            "signals": ["empty"],
        }

    found_suffixes = [t for t in lower_tokens if t in BUSINESS_SUFFIXES]
    if found_suffixes:
        signals.append(f"suffix:{found_suffixes[0]}")

    found_keywords = [t for t in lower_tokens if t in INDUSTRY_KEYWORDS]
    if found_keywords:
        signals.append(f"keyword:{found_keywords[0]}")

    if re.search(r"'s\b", normalized) or re.search(r"’s\b", normalized):
        signals.append("possessive")

    if "&" in normalized or re.search(r"\band\b", normalized.lower()):
        signals.append("conjunction")

    # HIGH-CONFIDENCE COMPANY: explicit corporate suffix
    if found_suffixes:
        return {
            "input": raw,
            "type": "company",
            "confidence": "high",
            "normalized": normalized,
            "tokens": tokens,
            "signals": signals,
        }

    # "Last, First" person format — only when there's a single comma and no company signals
    if "," in normalized and not found_keywords and "conjunction" not in signals:
        parts = [p.strip() for p in normalized.split(",", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            left_tokens = _tokens(parts[0])
            right_tokens = _tokens(parts[1])
            if 1 <= len(left_tokens) <= 3 and 1 <= len(right_tokens) <= 3:
                signals.append("last-first-format")
                return {
                    "input": raw,
                    "type": "person",
                    "confidence": "high",
                    "first": right_tokens[0],
                    "last": " ".join(left_tokens),
                    "normalized": normalized,
                    "tokens": tokens,
                    "signals": signals,
                }

    # MEDIUM-CONFIDENCE COMPANY: industry keyword / possessive / conjunction
    if found_keywords or "possessive" in signals or "conjunction" in signals:
        return {
            "input": raw,
            "type": "company",
            "confidence": "medium",
            "normalized": normalized,
            "tokens": tokens,
            "signals": signals,
        }

    # Person heuristic: 2-4 capitalized tokens, no signals.
    # Particle words (van/der/de/...) are expected to be lowercase — don't fail capitalization on them.
    all_cap = all(
        t[0].isupper()
        for t in tokens
        if t and t[0].isalpha() and t.lower() not in PARTICLES
    )
    if 2 <= len(tokens) <= 4 and all_cap:
        non_particle = [t for t in tokens if t.lower() not in PARTICLES]
        if len(non_particle) >= 2:
            first = non_particle[0]
            try:
                first_idx = tokens.index(first)
            except ValueError:
                first_idx = 0
            last = " ".join(tokens[first_idx + 1 :])
            signals.append("name-pattern")
            confidence = "high" if len(tokens) <= 3 else "medium"
            return {
                "input": raw,
                "type": "person",
                "confidence": confidence,
                "first": first,
                "last": last or non_particle[-1],
                "normalized": normalized,
                "tokens": tokens,
                "signals": signals,
            }

    if len(tokens) == 1:
        signals.append("single-token")
    else:
        signals.append("no-signals")

    return {
        "input": raw,
        "type": "ambiguous",
        "confidence": "low",
        "normalized": normalized,
        "tokens": tokens,
        "signals": signals,
    }


TEST_CASES = [
    # (input, expected_type, expected_confidence)
    ("ACME Insulation LLC", "company", "high"),
    ("Smith & Sons Inc", "company", "high"),
    ("ABC Corp.", "company", "high"),
    ("Insulate Pro", "company", "medium"),
    ("Bob's Spray Foam", "company", "medium"),
    ("Foam Industries", "company", "medium"),
    ("Williams Insulation", "company", "medium"),
    ("Smith and Associates", "company", "medium"),
    ("John Smith", "person", "high"),
    ("Mike Cerqua", "person", "high"),
    ("J.K. Rowling", "person", "high"),
    ("Bob O'Brien", "person", "high"),
    ("Smith-Jones, Mary", "person", "high"),
    ("Mary van der Berg", "person", None),  # accepts high or medium
    ("Joe", "ambiguous", "low"),
    ("Acme", "ambiguous", "low"),
    ("Smith Brothers", "company", "medium"),  # family-business pattern
    ("", "ambiguous", "low"),
]


def _run_tests() -> int:
    fails = 0
    for inp, want_type, want_conf in TEST_CASES:
        got = classify(inp)
        type_ok = got["type"] == want_type
        conf_ok = (want_conf is None) or (got["confidence"] == want_conf)
        status = "OK  " if type_ok and conf_ok else "FAIL"
        if not (type_ok and conf_ok):
            fails += 1
        print(
            f"  [{status}] {inp!r:42} -> type={got['type']:9} conf={got['confidence']:6} "
            f"want=({want_type},{want_conf})  signals={got.get('signals')}"
        )
    print(f"\n{len(TEST_CASES) - fails}/{len(TEST_CASES)} passed.")
    return 0 if fails == 0 else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Classify a name as person/company/ambiguous.")
    p.add_argument("name", nargs="?", help="Name to classify (omit if using --batch or --test)")
    p.add_argument("--batch", metavar="FILE", help="Read names from FILE (one per line). Use '-' for stdin.")
    p.add_argument("--test", action="store_true", help="Run built-in test suite.")
    args = p.parse_args()

    if args.test:
        return _run_tests()

    if args.batch:
        stream = sys.stdin if args.batch == "-" else open(args.batch, "r", encoding="utf-8")
        try:
            for line in stream:
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                print(json.dumps(classify(line), ensure_ascii=False))
        finally:
            if stream is not sys.stdin:
                stream.close()
        return 0

    if not args.name:
        p.print_help(sys.stderr)
        return 2

    print(json.dumps(classify(args.name), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
