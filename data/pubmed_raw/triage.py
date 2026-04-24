#!/usr/bin/env python3
"""Mechanical first-pass triage of PubMed hits for plant-NLR ground-truth curation."""
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("/Users/macleand/Desktop/sni_paper/sni_ml/data/pubmed_raw")
OUT_CSV = Path("/Users/macleand/Desktop/sni_paper/sni_ml/data/known_oligomer_states_audit.csv")
OUT_ABSTRACTS = ROOT / "abstracts.json"

STRUCTURAL_TERMS = [
    "cryo-em", "cryo em", "cryoelectron",
    "crystal structure", "x-ray structure", "x ray structure",
    "structure of", "structural basis", "structural characteri",
    "pentamer", "hexamer", "tetramer", "heptamer", "trimer", "dimer", "octamer",
    "oligomer", "stoichiometr",
    "resistosome", "pre-resistosome", "apoptosome", "inflammasome",
    "wheel-like", "ring-like", "funnel", "pore-forming", "filament",
    "assembly", "complex",
]

REVIEW_PUBTYPES = {"Review", "Systematic Review"}


def load_unique_pmids():
    with open(ROOT / "unique_pmids.json") as f:
        return json.load(f)


def load_esummary_meta():
    """Return dict pmid -> {year, journal, pubtypes (from esummary), title (esummary)}."""
    out = {}
    for i in range(6):
        with open(ROOT / f"esummary_{i}.json") as f:
            d = json.load(f)
        result = d.get("result", {})
        for uid in result.get("uids", []):
            entry = result.get(uid, {})
            pubdate = entry.get("pubdate", "") or ""
            year = pubdate.split(" ")[0] if pubdate else ""
            # Sometimes year is at start; pubdate like "2024 Jan 5"
            # take first 4-digit token
            year_tok = ""
            for tok in pubdate.split():
                if len(tok) == 4 and tok.isdigit():
                    year_tok = tok
                    break
            if not year_tok and year[:4].isdigit():
                year_tok = year[:4]
            journal = entry.get("source", "") or ""
            pubtypes = entry.get("pubtype", []) or []
            title = entry.get("title", "") or ""
            out[uid] = {
                "year": year_tok,
                "journal": journal,
                "pubtypes_summary": pubtypes,
                "title_summary": title,
            }
    return out


def parse_efetch_xml():
    """Return dict pmid -> {title, abstract, pubtypes}."""
    out = {}
    for i in range(6):
        path = ROOT / f"efetch_{i}.xml"
        try:
            tree = ET.parse(path)
        except ET.ParseError as e:
            print(f"  PARSE ERROR efetch_{i}.xml: {e}")
            continue
        root = tree.getroot()
        # PubmedArticle entries
        for art in root.findall(".//PubmedArticle"):
            pmid_el = art.find(".//MedlineCitation/PMID")
            if pmid_el is None or not pmid_el.text:
                continue
            pmid = pmid_el.text.strip()
            title_el = art.find(".//Article/ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else ""
            abs_parts = []
            for at in art.findall(".//Article/Abstract/AbstractText"):
                txt = "".join(at.itertext())
                label = at.get("Label")
                if label:
                    abs_parts.append(f"{label}: {txt}")
                else:
                    abs_parts.append(txt)
            abstract = " ".join(p.strip() for p in abs_parts if p).strip()
            pubtypes = []
            for pt in art.findall(".//Article/PublicationTypeList/PublicationType"):
                if pt.text:
                    pubtypes.append(pt.text.strip())
            out[pmid] = {
                "title": title,
                "abstract": abstract,
                "pubtypes": pubtypes,
            }
        # Also handle PubmedBookArticle
        for art in root.findall(".//PubmedBookArticle"):
            pmid_el = art.find(".//PMID")
            if pmid_el is None or not pmid_el.text:
                continue
            pmid = pmid_el.text.strip()
            if pmid in out:
                continue
            title_el = art.find(".//BookDocument/Book/BookTitle")
            if title_el is None:
                title_el = art.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else ""
            abs_parts = []
            for at in art.findall(".//Abstract/AbstractText"):
                txt = "".join(at.itertext())
                label = at.get("Label")
                if label:
                    abs_parts.append(f"{label}: {txt}")
                else:
                    abs_parts.append(txt)
            abstract = " ".join(p.strip() for p in abs_parts if p).strip()
            pubtypes = []
            for pt in art.findall(".//PublicationTypeList/PublicationType"):
                if pt.text:
                    pubtypes.append(pt.text.strip())
            out[pmid] = {
                "title": title,
                "abstract": abstract,
                "pubtypes": pubtypes,
            }
    return out


def apply_rules(title, abstract, pubtypes, abstract_available):
    """Return (disposition, rule_fired)."""
    pt_set = set(pubtypes)
    if pt_set & REVIEW_PUBTYPES:
        which = sorted(pt_set & REVIEW_PUBTYPES)[0]
        return "review", f"pubtype={which}"
    hay = (title + " \n " + abstract).lower()
    for term in STRUCTURAL_TERMS:
        if term in hay:
            # not no_structure -> ambiguous
            note = "survived all mechanical rules"
            if not abstract_available:
                note += "; abstract unavailable, title-only check"
            return "ambiguous", note
    note = "no structural vocabulary in title/abstract"
    if not abstract_available:
        note = "no structural vocabulary in title; abstract unavailable"
    return "no_structure", note


def main():
    print("Loading unique_pmids.json ...")
    unique_pmids = load_unique_pmids()
    print(f"  {len(unique_pmids)} unique PMIDs")

    print("Loading esummary metadata ...")
    summary_meta = load_esummary_meta()
    print(f"  {len(summary_meta)} summaries")

    print("Parsing efetch XML ...")
    fetch_meta = parse_efetch_xml()
    print(f"  {len(fetch_meta)} parsed records")

    # Build abstracts.json
    abstracts_out = {}
    for pmid in unique_pmids:
        s = summary_meta.get(pmid, {})
        f = fetch_meta.get(pmid, {})
        title = f.get("title") or s.get("title_summary", "")
        abstract = f.get("abstract", "")
        pubtypes = f.get("pubtypes") or s.get("pubtypes_summary", [])
        abstracts_out[pmid] = {
            "title": title,
            "abstract": abstract,
            "pubtypes": pubtypes,
            "year": s.get("year", ""),
            "journal": s.get("journal", ""),
        }

    with open(OUT_ABSTRACTS, "w") as f:
        json.dump(abstracts_out, f, indent=2, ensure_ascii=False)
    print(f"  wrote {OUT_ABSTRACTS}")

    # Apply rules and write CSV
    rows = []
    disp_counter = Counter()
    per_query_amb = defaultdict(int)
    missing_efetch = []
    missing_summary = []

    for pmid, queries in unique_pmids.items():
        a = abstracts_out[pmid]
        title = a["title"]
        abstract = a["abstract"]
        pubtypes = a["pubtypes"]
        year = a["year"]
        journal = a["journal"]
        abstract_available = bool(abstract)
        if pmid not in fetch_meta:
            missing_efetch.append(pmid)
        if pmid not in summary_meta:
            missing_summary.append(pmid)
        disposition, rule_fired = apply_rules(title, abstract, pubtypes, abstract_available)
        disp_counter[disposition] += 1
        if disposition == "ambiguous":
            for q in queries:
                per_query_amb[q] += 1
        snippet = abstract[:300].replace("\n", " ").replace("\r", " ")
        rows.append({
            "pmid": pmid,
            "queries_hit": "|".join(queries),
            "year": year,
            "journal": journal,
            "title": title.replace("\n", " ").replace("\r", " "),
            "pubtypes": "|".join(pubtypes),
            "disposition": disposition,
            "rule_fired": rule_fired,
            "abstract_snippet": snippet,
            "needs_human_review": "TRUE" if disposition == "ambiguous" else "FALSE",
        })

    cols = ["pmid", "queries_hit", "year", "journal", "title", "pubtypes",
            "disposition", "rule_fired", "abstract_snippet", "needs_human_review"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"  wrote {OUT_CSV}")

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Total: {sum(disp_counter.values())}")
    for k, v in sorted(disp_counter.items()):
        print(f"  {k}: {v}")
    print("\nPer-query ambiguous breakdown:")
    for q in ["P1", "P2", "P3", "M1", "M2"]:
        print(f"  {q}: {per_query_amb[q]}")
    print(f"\nMissing efetch records: {len(missing_efetch)}")
    if missing_efetch:
        print("  ", missing_efetch[:20])
    print(f"Missing esummary records: {len(missing_summary)}")
    if missing_summary:
        print("  ", missing_summary[:20])


if __name__ == "__main__":
    main()
