"""Command line interface for cmless."""

import contextlib
import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, Callable

import typer
from pydantic import BaseModel

from .models import Collection, Exhibit
from .parse import (
    markdownify,
    parse_cmless,
    parse_cmless_thumbnail,
    parse_collections,
    parse_exhibits,
    parse_featured_markdown,
    parse_records_markdown,
    pasre_authors_markdown,
)

app = typer.Typer(
    help="Parse CMLess Markdown documents into JSON.",
    no_args_is_help=True,
    add_completion=False,
)


class ModelName(StrEnum):
    raw = "raw"
    collection = "collection"
    exhibit = "exhibit"


OutputOption = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        dir_okay=False,
        writable=True,
        help="Write JSON to this file instead of stdout.",
    ),
]
CompactOption = Annotated[
    bool, typer.Option("--compact", help="Emit minimal JSON without indentation.")
]
SnippetArgument = Annotated[
    typer.FileText,
    typer.Argument(
        encoding="utf-8", metavar="FILE", help="Markdown file to read, or - for stdin."
    ),
]
DirectoryArgument = Annotated[
    Path, typer.Argument(exists=True, file_okay=False, readable=True)
]


def _encode(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(exclude_none=True, by_alias=True)
    raise TypeError(f"Cannot serialize {type(obj).__name__}")


def _emit(data: Any, output: Path | None, compact: bool) -> None:
    text = json.dumps(
        data,
        default=_encode,
        indent=None if compact else 2,
        separators=(",", ":") if compact else None,
    )
    if output:
        output.write_text(text + "\n", encoding="utf-8")
    else:
        typer.echo(text)


def _quiet[T](func: Callable[..., T], *args: Any) -> T:
    """Call a parser, sending its print() diagnostics to stderr to keep stdout clean."""
    with contextlib.redirect_stdout(sys.stderr):
        return func(*args)


@app.command()
def parse(
    file: Annotated[
        Path, typer.Argument(exists=True, dir_okay=False, readable=True)
    ],
    model: Annotated[
        ModelName,
        typer.Option(
            "--model",
            "-m",
            help="Validate against a model: unknown sections are an error and empty ones are dropped.",
        ),
    ] = ModelName.raw,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Parse a single CMLess file."""
    try:
        data: Any = parse_cmless(str(file))
        if model is ModelName.collection:
            data = Collection.model_validate(data)
        elif model is ModelName.exhibit:
            data = Exhibit.model_validate(data)
    except (AssertionError, ValueError) as error:
        typer.echo(f"Error parsing {file}: {error}", err=True)
        raise typer.Exit(1)
    _emit(data, output, compact)


@app.command()
def collections(
    directory: DirectoryArgument,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Parse every collection file in DIRECTORY. Files that fail are reported on stderr."""
    _emit(_quiet(parse_collections, str(directory)), output, compact)


@app.command()
def exhibits(
    directory: DirectoryArgument,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Parse every exhibit in DIRECTORY, including pages in same-named subdirectories."""
    _emit(_quiet(parse_exhibits, str(directory)), output, compact)


@app.command()
def thumbnails(
    source: SnippetArgument,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Extract Markdown images as title and URL pairs."""
    _emit(parse_cmless_thumbnail(source.read()), output, compact)


@app.command()
def featured(
    source: SnippetArgument,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Extract featured items (images that link to a record) from Markdown."""
    _emit(parse_featured_markdown(source.read()), output, compact)


@app.command()
def records(
    source: SnippetArgument,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Extract record GUIDs from a Markdown list of /catalog/ links."""
    _emit(parse_records_markdown(source.read()), output, compact)


@app.command()
def authors(
    source: SnippetArgument,
    output: OutputOption = None,
    compact: CompactOption = False,
) -> None:
    """Extract authors from a Markdown list of HTML author blocks."""
    _emit(_quiet(pasre_authors_markdown, source.read()), output, compact)


@app.command()
def html(source: SnippetArgument) -> None:
    """Render Markdown to HTML."""
    typer.echo(markdownify(source.read()))
