"""Genere la ColorMap de test 512x512 du jalon M0 — sans dependance externe.

Garantie anti-aliasing : chaque pixel est calcule par test entier et ecrit
dans un PNG sans perte (RGB 8 bits, non entrelace). Aucune primitive de
dessin n'est utilisee, donc aucun lissage n'est possible, par construction.

4 Provinces :
  1. #FF0000 bande ouest    (x < 171, hors ile)
  2. #00FF00 bande centrale (171 <= x < 342, hors ile)
  3. #0000FF bande est      (x >= 342, hors ile)
  4. #FFFF00 ile circulaire (centre 256,256 ; rayon 80)

Usage : python tools/generate_test_colormap.py [chemin_sortie]
        (defaut : provinces.png dans le dossier courant)
"""

import struct
import sys
import zlib

WIDTH = 512
HEIGHT = 512

P1_RED = (255, 0, 0)
P2_GREEN = (0, 255, 0)
P3_BLUE = (0, 0, 255)
P4_YELLOW = (255, 255, 0)

ISLAND_CX = 256
ISLAND_CY = 256
ISLAND_RADIUS = 80

BAND_1_END = 171
BAND_2_END = 342


def province_color(x: int, y: int) -> tuple:
    dx = x - ISLAND_CX
    dy = y - ISLAND_CY
    if dx * dx + dy * dy <= ISLAND_RADIUS * ISLAND_RADIUS:
        return P4_YELLOW
    if x < BAND_1_END:
        return P1_RED
    if x < BAND_2_END:
        return P2_GREEN
    return P3_BLUE


def build_raw_rows() -> bytes:
    """Lignes brutes au format PNG : 1 octet de filtre (0 = None) + WIDTH pixels RGB."""
    rows = bytearray()
    for y in range(HEIGHT):
        rows.append(0)
        for x in range(WIDTH):
            rows.extend(province_color(x, y))
    return bytes(rows)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload))
    )


def write_png(path: str, raw_rows: bytes) -> None:
    # IHDR : largeur, hauteur, 8 bits/canal, type 2 (RGB), compression/filtre/entrelacement 0
    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(raw_rows, 9))
        + png_chunk(b"IEND", b"")
    )
    with open(path, "wb") as handle:
        handle.write(data)


def count_unique_colors(raw_rows: bytes) -> set:
    colors = set()
    stride = 1 + WIDTH * 3
    for y in range(HEIGHT):
        row = raw_rows[y * stride + 1 : (y + 1) * stride]
        for x in range(WIDTH):
            colors.add(tuple(row[x * 3 : x * 3 + 3]))
    return colors


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "provinces.png"
    raw_rows = build_raw_rows()
    write_png(out_path, raw_rows)

    colors = count_unique_colors(raw_rows)
    hex_colors = sorted("#%02X%02X%02X" % c for c in colors)
    print(f"OK {out_path} : {WIDTH}x{HEIGHT}, {len(colors)} couleurs uniques : {hex_colors}")
    if len(colors) != 4:
        raise SystemExit("ERREUR : la ColorMap doit contenir exactement 4 couleurs")


if __name__ == "__main__":
    main()
