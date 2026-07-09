from __future__ import annotations

import argparse
from pathlib import Path

import requests

from app.core.config import PLAYER_IMAGE_DIR
from app.services.fc26_loader import load_fc26_players
from app.services.fc26_scoring import rank_players


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cache FC26 player images locally.")
    parser.add_argument("--limit", type=int, default=500, help="Maximum number of player images to cache.")
    parser.add_argument("--overwrite", action="store_true", help="Download images even when local files already exist.")
    parser.add_argument("--preset", default="balanced", help="Ranking preset used to choose which players to cache first.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    PLAYER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    df = rank_players(load_fc26_players(), preset=args.preset)
    rows = df[["player_id", "short_name", "player_face_url"]].dropna(subset=["player_face_url"]).head(args.limit)

    downloaded = 0
    skipped = 0
    failed = 0
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }

    for index, row in enumerate(rows.to_dict("records"), start=1):
        player_id = str(int(float(row["player_id"])))
        image_url = str(row.get("player_face_url") or "").strip()
        target = PLAYER_IMAGE_DIR / f"{player_id}.png"

        if not image_url:
            skipped += 1
            continue
        if target.exists() and not args.overwrite:
            skipped += 1
            continue

        try:
            response = requests.get(image_url, headers=headers, timeout=(5, 8))
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type:
                raise ValueError(f"Unexpected content type: {content_type}")
            target.write_bytes(response.content)
            downloaded += 1
            if downloaded % 25 == 0:
                print(f"downloaded {downloaded} images ({index}/{len(rows)})")
        except Exception as exc:
            failed += 1
            print(f"failed: {player_id} {row.get('short_name', '')} {exc}")

    print(f"cached={downloaded} skipped={skipped} failed={failed} dir={PLAYER_IMAGE_DIR}")


if __name__ == "__main__":
    main()
