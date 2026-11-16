from cmless.models import Author, Collection, Exhibit
from cmless.parse import (
    markdownify,
    parse_cmless,
    parse_cmless_thumbnail,
    parse_collections,
    parse_exhibits,
    parse_featured_markdown,
    parse_records_markdown,
    pasre_authors_markdown,
)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


class TestParseCmless:
    def test_sections_title_and_slug(self, tmp_path):
        file = write(
            tmp_path / "My Page.md",
            "\n  # My Title\n\n## Summary\nIt’s a \\_test\\_\n\n## Resources\n\n## Extra\nbody\n",
        )
        assert parse_cmless(file) == {
            "Title": "My Title",
            "Slug": "my-page",
            "Summary": "It's a _test_",
            "Resources": None,
            "Extra": "body",
        }

    def test_number_under_title_is_page(self, tmp_path):
        file = write(tmp_path / "p.md", "# T\n7\n\n## Summary\nx\n")
        assert parse_cmless(file)["Page"] == 7

    def test_other_text_under_title_is_not_a_page(self, tmp_path):
        file = write(tmp_path / "p.md", "# T\nsubtitle\n\n## Summary\nx\n")
        assert "Page" not in parse_cmless(file)


class TestParseCollections:
    def test_slug_comes_from_filename_and_non_markdown_is_ignored(self, tmp_path):
        write(tmp_path / "Some Name.md", "# Some\n\n## Summary\nHi\n")
        write(tmp_path / "notes.txt", "# Not markdown\n")
        (collection,) = parse_collections(str(tmp_path))
        assert isinstance(collection, Collection)
        assert collection.slug == "Some Name"
        assert collection.summary == "Hi"


class TestParseExhibits:
    def test_exhibit_without_directory_has_no_children_and_page_zero(self, tmp_path):
        write(tmp_path / "solo.md", "# Solo\n\n## Summary\nHi\n")
        (exhibit,) = parse_exhibits(str(tmp_path))
        assert isinstance(exhibit, Exhibit)
        assert (exhibit.slug, exhibit.page, exhibit.children) == ("solo", 0, None)

    def test_unnumbered_children_sort_before_numbered_ones(self, tmp_path):
        write(tmp_path / "tour.md", "# Tour\n")
        write(tmp_path / "tour" / "two.md", "# Two\n2\n")
        write(tmp_path / "tour" / "intro.md", "# Intro\n")
        write(tmp_path / "tour" / "one.md", "# One\n1\n")
        (tour,) = parse_exhibits(str(tmp_path))
        assert [c.slug for c in tour.children] == ["intro", "one", "two"]

    def test_invalid_child_is_skipped_but_siblings_are_kept(self, tmp_path):
        write(tmp_path / "tour.md", "# Tour\n")
        write(tmp_path / "tour" / "good.md", "# Good\n1\n")
        write(tmp_path / "tour" / "bad.md", "# Bad\n\n## Nonsense\nx\n")
        (tour,) = parse_exhibits(str(tmp_path))
        assert [c.slug for c in tour.children] == ["good"]

    def test_invalid_exhibit_is_skipped(self, tmp_path):
        write(tmp_path / "bad.md", "# Bad\n\n## Nonsense\nx\n")
        write(tmp_path / "good.md", "# Good\n")
        assert [e.slug for e in parse_exhibits(str(tmp_path))] == ["good"]


class TestParseCmlessThumbnail:
    def test_extracts_title_and_url_without_image_title_text(self):
        text = '![ A ](http://x/a.png "hover")\ntext\n![B](http://x/b.png)'
        assert parse_cmless_thumbnail(text) == [
            {"title": "A", "url": "http://x/a.png"},
            {"title": "B", "url": "http://x/b.png"},
        ]

    def test_no_images(self):
        assert parse_cmless_thumbnail("just text") == []


class TestParseFeaturedMarkdown:
    def test_extracts_guid_and_start_time(self):
        text = (
            "[![Fiddler on the Roof](http://img/a.jpg)]"
            "(/catalog/cpb-aacip_525-154dn40r4v#at_619.23963_s)\n"
            "[![No Time](http://img/b.jpg)](/catalog/cpb-aacip-1-abc)\n"
        )
        assert parse_featured_markdown(text) == [
            {
                "title": "Fiddler on the Roof",
                "guids": "cpb-aacip_525-154dn40r4v",
                "start_time": "619.23963",
            },
            {"title": "No Time", "guids": "cpb-aacip-1-abc", "start_time": None},
        ]

    def test_ignores_images_that_are_not_links(self):
        assert parse_featured_markdown("![A](http://img/a.jpg)") == []


class TestParseRecordsMarkdown:
    def test_extracts_guids_from_catalog_links_only(self):
        text = (
            "- [](/catalog/cpb-aacip-507-hh6c24rg48)\n"
            "- [A title](/catalog/cpb-aacip-507-jm23b5x502)\n"
            "- [Elsewhere](http://example.com/page)\n"
        )
        assert parse_records_markdown(text) == [
            "cpb-aacip-507-hh6c24rg48",
            "cpb-aacip-507-jm23b5x502",
        ]


class TestParseAuthorsMarkdown:
    def test_extracts_name_title_and_image(self):
        text = (
            '- <img class="img-circle" src="http://img/kate.jpg"/>\n'
            '  <a class="name">Kate Mitchell</a>\n'
            '  <a class="title">Junior Fellow</a>\n'
            '- <a class="name">Sam</a>'
        )
        assert pasre_authors_markdown(text) == [
            Author(name="Kate Mitchell", title="Junior Fellow", image="http://img/kate.jpg"),
            Author(name="Sam"),
        ]

    def test_entries_without_a_name_are_skipped(self, capsys):
        text = '- <a class="title">Nameless</a>\n- <a class="name">Sam</a>'
        assert [a.name for a in pasre_authors_markdown(text)] == ["Sam"]
        assert "No author name found" in capsys.readouterr().out


def test_markdownify_renders_html():
    assert markdownify("# Hi\n\n*there*") == "<h1>Hi</h1>\n<p><em>there</em></p>"
