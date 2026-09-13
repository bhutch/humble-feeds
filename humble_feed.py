#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests", "beautifulsoup4"]
# ///
# Self-contained: `uv run --script humble_feed.py`. Plain `python3 humble_feed.py`
# (and the bare `humble-feed` bin link) works once requests + beautifulsoup4 are in
# the env (both already in install/lib-deps.yaml, core/web profiles).
#
# Approach adapted from Bloodeyesx/Bloodeyesx.github.io (MIT): current Humble pages
# embed the bundle list as JSON in <script id="landingPage-json-data">. The original
# shimst3r/go-humble feeds went offline when their domain lapsed; this regenerates
# them locally. RSS is hand-rolled (stdlib) so the only deps are the fetch + parse.
"""Generate RSS feeds of current Humble Bundle bundles (books, games, software),
one <item> per live bundle. Feeds are written as <out>/<category>.xml; point an RSS
reader at the files (or serve the directory).

  humble-feed                        # all three, into ~/humble-feeds/
  humble-feed --categories books     # just books
  humble-feed --out ~/feeds          # choose the output directory
"""

import argparse
import json
import sys
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from bs4 import BeautifulSoup

BASE = "https://www.humblebundle.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
CATEGORIES = ["books", "games", "software"]  # books first: the one that matters most here


def fetch_products(category):
    """Return the list of bundle products on a Humble category landing page."""
    r = requests.get(f"{BASE}/{category}", headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    tag = BeautifulSoup(r.text, "html.parser").find("script", id="landingPage-json-data")
    if tag is None:
        raise RuntimeError(f"no landingPage-json-data on /{category} (page layout changed?)")
    data = json.loads(tag.string)
    mosaic = data["data"][category]["mosaic"]
    seen, products = set(), []
    for section in mosaic:
        for p in section.get("products", []):
            mn = p.get("machine_name")
            if p.get("product_url") and mn and mn not in seen:
                seen.add(mn)
                products.append(p)
    return products


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def item_xml(p, now):
    title = p.get("tile_short_name") or p.get("tile_name") or p["machine_name"]
    link = BASE + p["product_url"]
    blurb = p.get("short_marketing_blurb") or p.get("marketing_blurb") or ""
    img = p.get("high_res_tile_image") or p.get("tile_image") or ""
    start = parse_dt(p.get("start_date|datetime"))
    end = parse_dt(p.get("end_date|datetime"))
    desc = ""
    if img:
        desc += f'<img src="{escape(img)}"><br>'
    if blurb:
        desc += escape(blurb)
    if end:
        desc += f"<br>Ends: {end:%Y-%m-%d}"
    return f"""    <item>
      <title>{escape(title)}</title>
      <link>{escape(link)}</link>
      <guid isPermaLink="false">{escape(p['machine_name'])}</guid>
      <pubDate>{format_datetime(start or now)}</pubDate>
      <description>{escape(desc)}</description>
    </item>"""


def feed_xml(category, products, now):
    items = "\n".join(item_xml(p, now) for p in products)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Humble {category.capitalize()} Bundles</title>
    <link>{BASE}/{category}</link>
    <description>Current Humble Bundle {category} bundles</description>
    <lastBuildDate>{format_datetime(now)}</lastBuildDate>
    <generator>humble-feed (~/tools/media)</generator>
{items}
  </channel>
</rss>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--categories", default=",".join(CATEGORIES),
                    help=f"comma-separated subset of {CATEGORIES}")
    ap.add_argument("--out", type=Path, default=Path.home() / "humble-feeds",
                    help="output directory (default: ~/humble-feeds)")
    args = ap.parse_args()

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    bad = [c for c in cats if c not in CATEGORIES]
    if bad:
        sys.exit(f"unknown categories {bad}; choose from {CATEGORIES}")
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    for c in cats:
        try:
            products = fetch_products(c)
        except Exception as e:
            print(f"{c}: FAILED — {e}", file=sys.stderr)
            continue
        path = out / f"{c}.xml"
        path.write_text(feed_xml(c, products, now), encoding="utf-8")
        print(f"{c}: {len(products)} bundles -> {path.as_uri()}")


if __name__ == "__main__":
    main()
