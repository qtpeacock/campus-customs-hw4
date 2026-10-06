"""Copy "worn on campus" photos from last homework into data/worn/.

HW3's identify agent checked four photos of people and matched two of them to
catalogue products (output/identify_product.json). For every confident match
whose product exists in this catalogue, this script saves the photo as
data/worn/<product_id>.jpg (resized to at most 1000px). The website then shows
it when you hover over that product's card and as a second photo on its page.

data/ is not committed (these are photos of real people), so run this once
after unzipping data.zip.

Run from HW4/:  python scripts/import_worn_photos.py --hw3 ../HW3
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
WORN = ROOT / "data" / "worn"
MAX_SIDE = 1000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hw3", type=Path, default=ROOT.parent / "HW3", help="the HW3 folder (default: ../HW3)")
    args = parser.parse_args()

    results = json.loads((args.hw3 / "output" / "identify_product.json").read_text(encoding="utf-8"))
    with closing(sqlite3.connect(DB_PATH)) as conn:
        known = {row[0] for row in conn.execute("SELECT product_id FROM catalogue")}

    WORN.mkdir(parents=True, exist_ok=True)
    for result in results:
        match = result.get("best_match") or {}
        product_id = match.get("product_id")
        if not (result.get("product_present") and match.get("confidence") == "high" and product_id in known):
            print(f"skip   {result['image_path']} (no confident match in this catalogue)")
            continue
        image = cv2.imread(str(args.hw3 / result["image_path"]))
        height, width = image.shape[:2]
        scale = min(1.0, MAX_SIDE / max(height, width))
        if scale < 1:
            image = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
        target = WORN / f"{product_id}.jpg"
        cv2.imwrite(str(target), image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"saved  {result['image_path']} -> data/worn/{target.name}")


if __name__ == "__main__":
    main()
