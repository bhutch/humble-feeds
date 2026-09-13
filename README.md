# humble-feeds

Auto-generated RSS feeds of the current [Humble Bundle](https://www.humblebundle.com)
bundles, one item per live bundle, refreshed every 12 hours by a GitHub Action.

## Feeds

Once GitHub Pages is enabled for this repo, subscribe in any RSS reader:

- Books: `https://bhutch.github.io/humble-feeds/books.xml`
- Games: `https://bhutch.github.io/humble-feeds/games.xml`
- Software: `https://bhutch.github.io/humble-feeds/software.xml`

## How it works

`humble_feed.py` fetches Humble's `/books`, `/games`, and `/software` landing pages,
reads the bundle list from the `landingPage-json-data` JSON embedded in each page, and
writes one RSS file per category. The Action (`.github/workflows/feeds.yml`) runs it on a
schedule and commits the refreshed `.xml` files back; Pages serves them.

## Credits

Approach adapted from [Bloodeyesx/Bloodeyesx.github.io](https://github.com/Bloodeyesx/Bloodeyesx.github.io)
(MIT), reviving the idea of the now-offline
[shimst3r/go-humble](https://github.com/shimst3r/go-humble). Not affiliated with Humble
Bundle, Inc. Feed content is Humble's public bundle listings.

## License

MIT — see [LICENSE](LICENSE).
