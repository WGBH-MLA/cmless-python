# CMLess
Python parsers for CMLess

## Command line

Installing the package provides a `cmless` command (or run it with `uvx cmless`). Every command except `html` prints JSON to stdout, or to a file with `-o/--output`; add `--compact` for single-line output. Parser warnings go to stderr, so stdout is always safe to pipe.

```sh
cmless parse app/views/special_collections/zoom.md            # raw sections
cmless parse app/views/special_collections/zoom.md -m collection  # validated against a model
cmless collections app/views/special_collections -o collections.json
cmless exhibits app/views/exhibits -o exhibits.json            # includes sub-pages as children
```

Section helpers read a Markdown snippet from a file or `-` for stdin, so they compose with `parse`:

```sh
cmless parse zoom.md | jq -r .Featured | cmless featured -
```

| Command      | Extracts                                         |
| ------------ | ------------------------------------------------ |
| `thumbnails` | Markdown images (title, URL)                     |
| `featured`   | Linked featured items (title, GUID, start time)  |
| `records`    | Record GUIDs from `/catalog/` links              |
| `authors`    | Authors (name, title, image) from HTML blocks    |
| `html`       | Renders Markdown to HTML (not JSON)              |

Run `cmless COMMAND --help` for details.

## Credits
Developed by [GBH Archives](https://wgbh.org/foundation/archives) for the [American Archive of Public Broadcasting](https://americanarchive.org/)