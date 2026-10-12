"""
Import the official CMS ICD-10-CM code titles (FY2027) for validator V4/V5.

Official source: CMS "2027 Code Descriptions in Tabular Order (ZIP)"
  https://www.cms.gov/files/zip/2027-code-descriptions-tabular-order.zip
  (CDC NCHS mirror: https://ftp.cdc.gov/pub/health_statistics/nchs/publications/ICD10CM/2027/)
Order file inside: Code Descriptions/icd10cm_order_2027.txt
Format per line: order(1-5) + code-without-dot(7-13) + billable-flag + long title + short title.

Usage:
    py -3.13 scripts/import_icd10_cm.py --input <icd10cm_order_2027.txt> [--fy 2027]

Output: configs/validation/icd10_cm_titles_FY2027.json
  {"_meta": {...provenance...}, "titles": {"J18.9": "Pneumonia, unspecified organism", ...}}

Content owner: Medical Expert (official terminology; never model-generated).
"""

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "configs" / "validation" / "icd10_cm_titles_FY2027.json"

SOURCE_URL = "https://www.cms.gov/files/zip/2027-code-descriptions-tabular-order.zip"
SOURCE_MIRROR = "https://ftp.cdc.gov/pub/health_statistics/nchs/publications/ICD10CM/2027/"


def dotted(code: str) -> str:
    """ICD-10-CM dotted form: category (3 chars) + '.' + remainder."""
    clean = code.strip().upper()
    if len(clean) > 3:
        return clean[:3] + "." + clean[3:]
    return clean


def parse_order_file(path: Path) -> dict:
    titles: dict = {}
    billable = 0
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if len(line) < 15:
                continue
            raw_code = line[6:13].strip()
            if not raw_code:
                continue
            flag = line[14:15]
            title = line[16:76].strip() if len(line) > 16 else ""
            if not title:
                continue
            titles[dotted(raw_code)] = title
            if flag == "1":
                billable += 1
    return titles, billable


def main() -> int:
    parser = argparse.ArgumentParser(description="Import official CMS ICD-10-CM titles")
    parser.add_argument("--input", type=str, required=True, help="Path to icd10cm_order_2027.txt")
    parser.add_argument("--fy", type=str, default="2027")
    args = parser.parse_args()

    titles, billable = parse_order_file(Path(args.input))
    payload = {
        "_meta": {
            "source": f"CMS ICD-10-CM FY{args.fy} Code Descriptions in Tabular Order",
            "source_url": SOURCE_URL,
            "source_mirror": SOURCE_MIRROR,
            "order_file": "Code Descriptions/icd10cm_order_2027.txt",
            "note": "Official public file; titles copied verbatim, never model-generated.",
            "total_codes": len(titles),
            "billable_codes": billable,
            "is_synthetic": False,
        },
        "titles": titles,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"Wrote {len(titles)} titles ({billable} billable) to {OUT_PATH}")
    print(f"Spot check J18.9: {titles.get('J18.9')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
