"""Give every product photo a white background.

73 of the 102 photos in data/products/ were saved from transparent PNGs onto
black, so garments float on black squares. This script finds that black
background (dark pixels connected to the photo's edges, plus large pure-black
gaps such as between an arm and the body), turns it white, and lightens the
dark fringe left around each garment's outline.

Results go to data/products_white/ (same file names); photos that already have
a white background are copied unchanged (one also loses a thin black frame line). The originals are never modified, and
backend/main.py serves data/products_white/ when it exists.

Run from HW4/:  python scripts/whiten_backgrounds.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "products"
TARGET = ROOT / "data" / "products_white"

DARK = 4  # background is exact black (0); keep this tiny so very dark navy garments survive
PURE_BLACK = 2  # enclosed gaps this dark are background too, even if they don't touch an edge
MIN_GAP_AREA = 400  # ...as long as they're big enough not to be a shadow or a printed detail
FRINGE_PX = 3  # width of the anti-aliased outline to lighten
JPEG_QUALITY = 92


def has_black_background(image: np.ndarray) -> bool:
    """True when the four corners are black (garments sometimes touch an edge, corners never do)."""
    h, w = image.shape[:2]
    k = max(4, min(h, w) // 50)
    corners = [image[:k, :k], image[:k, -k:], image[-k:, :k], image[-k:, -k:]]
    return float(np.mean([c.mean() for c in corners])) < 20


def background_mask(brightest: np.ndarray) -> np.ndarray:
    """Black pixels connected to the border, plus large pure-black enclosed gaps."""
    dark = (brightest <= DARK).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    h, w = brightest.shape
    keep = np.zeros(count, dtype=bool)
    for label in range(1, count):
        x, y, bw, bh, area = stats[label]
        touches_edge = x == 0 or y == 0 or x + bw == w or y + bh == h
        if touches_edge:
            keep[label] = True
        elif area >= MIN_GAP_AREA and brightest[labels == label].mean() <= PURE_BLACK:
            keep[label] = True
    return keep[labels]


def clear_dark_frame(image: np.ndarray, max_px: int = 4) -> tuple[np.ndarray, bool]:
    """Whiten thin black frame lines along the edges (one white-background photo has a 1px black border)."""
    out = image.copy()
    dark = image.max(axis=2) <= DARK * 2
    h, w = dark.shape
    changed = False
    for d in range(max_px):
        for line, index in ((dark[d], (d, slice(None))), (dark[h - 1 - d], (h - 1 - d, slice(None))),
                            (dark[:, d], (slice(None), d)), (dark[:, w - 1 - d], (slice(None), w - 1 - d))):
            if line.mean() > 0.9:
                out[index] = 255
                changed = True
    return out, changed


def whiten(image: np.ndarray) -> np.ndarray:
    brightest = image.max(axis=2)
    bg = background_mask(brightest)

    # The garment's outline was blended with black: pixel = alpha * colour. Estimate alpha from the
    # brightest nearby garment pixel and re-blend with white instead: pixel + (1 - alpha) * 255.
    kernel = np.ones((3, 3), np.uint8)
    fringe = cv2.dilate(bg.astype(np.uint8), kernel, iterations=FRINGE_PX).astype(bool) & ~bg
    interior = ~(bg | fringe)
    reference = cv2.dilate(np.where(interior, brightest, 0).astype(np.uint8), np.ones((9, 9), np.uint8))
    alpha = np.clip(brightest / np.maximum(reference, 1), 0.0, 1.0)
    alpha = np.where(reference == 0, brightest / 255.0, alpha)

    out = image.astype(np.float32)
    lift = ((1.0 - alpha) * 255.0)[..., None]
    out = np.where(fringe[..., None], np.clip(out + lift, 0, 255), out)
    out[bg] = 255
    return out.astype(np.uint8)


def main() -> None:
    TARGET.mkdir(exist_ok=True)
    whitened = frames = copied = 0
    for path in sorted(SOURCE.glob("*.jpg")):
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            print(f"skipped (unreadable): {path.name}")
            continue
        if has_black_background(image):
            cv2.imwrite(str(TARGET / path.name), whiten(image), [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            whitened += 1
            continue
        framed, changed = clear_dark_frame(image)
        if changed:
            cv2.imwrite(str(TARGET / path.name), framed, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            frames += 1
        else:
            shutil.copy2(path, TARGET / path.name)
            copied += 1
    print(f"{whitened} black backgrounds whitened, {frames} black frame lines removed, "
          f"{copied} already white (copied) -> {TARGET}")


if __name__ == "__main__":
    main()
