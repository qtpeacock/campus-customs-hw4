"""Replace the three placeholder catalogue rows with descriptions written from their photos.

As delivered, these products had "Vision blocked; filename-based stub" as their
description, no colors, and search tags made only from the file name. The text
below was written from each product photo and approved by Quinn on 2026-10-05.

The database isn't committed to the repo, so run this once after unzipping a
fresh data.zip. Running it again just rewrites the same values.

Run from HW4/:  python scripts/fix_catalogue.py
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "campus_customs.db"

# Colors list the garment's own color first, then the print, like the rest of the catalogue.
FIXES = {
    "benjamin-franklin-t-shirt": {
        "garment_type": "short-sleeve t-shirt",
        "description": (
            "Heather gray short-sleeve crew-neck T-shirt featuring the Benjamin Franklin College shield crest "
            "centered on the chest, quartered in blue and red with white diagonal bolts and white fleurs-de-lis, "
            "above the words BENJAMIN FRANKLIN COLLEGE."
        ),
        "colors": ["heather gray", "blue", "red", "white", "black"],
        "search_tags": [
            "Yale", "Benjamin Franklin College", "Franklin", "college shirt", "crest shirt",
            "logo t-shirt", "gray t-shirt", "short sleeve", "crew neck",
        ],
    },
    "berkeley-sweater-fleece-jacket": {
        "garment_type": "fleece jacket",
        "description": (
            "Light heather gray full-zip sweater fleece jacket with a stand collar, charcoal gray zipper and "
            "pocket trim, and an embroidered red-and-white Berkeley College crest with BERKELEY lettering on "
            "the left chest."
        ),
        "colors": ["light heather gray", "charcoal gray", "red", "white"],
        "search_tags": [
            "Yale", "Berkeley", "Berkeley College", "fleece jacket", "sweater fleece", "full zip",
            "gray jacket", "college crest", "embroidered logo", "outerwear",
        ],
    },
    "timothy-dwight-college-crewneck": {
        "garment_type": "crewneck sweatshirt",
        "description": (
            "Heather gray long-sleeve crewneck sweatshirt with ribbed collar, cuffs, and waistband. Features a "
            "small Timothy Dwight College crest, a red lion on a white shield under a red band with a white "
            "crescent, and TIMOTHY DWIGHT text on the left chest."
        ),
        "colors": ["heather gray", "red", "white", "black"],
        "search_tags": [
            "Timothy Dwight College", "TD", "Yale", "crewneck", "sweatshirt", "gray sweatshirt",
            "college merch", "crest", "left chest logo", "long sleeve",
        ],
    },
}


def main() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        for product_id, fix in FIXES.items():
            cursor = conn.execute(
                "UPDATE catalogue SET garment_type = ?, description = ?, colors = ?, search_tags = ? "
                "WHERE product_id = ?",
                (
                    fix["garment_type"],
                    fix["description"],
                    json.dumps(fix["colors"]),
                    json.dumps(fix["search_tags"]),
                    product_id,
                ),
            )
            print(f"{'updated' if cursor.rowcount else 'NOT FOUND'}: {product_id}")


if __name__ == "__main__":
    main()
