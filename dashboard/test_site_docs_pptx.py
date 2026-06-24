# test_site_docs_pptx.py
import os
import tempfile
import unittest
import site_docs_pptx as sd
from pptx.util import Inches, Pt, Emu


class TestInline(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(sd.inline("hello 한글"), [{"t": "text", "s": "hello 한글"}])

    def test_bold(self):
        self.assertEqual(
            sd.inline("a **b** c"),
            [{"t": "text", "s": "a "}, {"t": "bold", "s": "b"}, {"t": "text", "s": " c"}],
        )

    def test_code(self):
        self.assertEqual(
            sd.inline("run `x = 1` now"),
            [{"t": "text", "s": "run "}, {"t": "code", "s": "x = 1"}, {"t": "text", "s": " now"}],
        )

    def test_link_allowed_scheme_keeps_text_drops_url(self):
        self.assertEqual(
            sd.inline("see [docs](https://x.io/y)"),
            [{"t": "text", "s": "see "}, {"t": "link", "s": "docs"}],
        )

    def test_link_disallowed_scheme_stripped_to_text(self):
        # url group [^)]+ stops at the FIRST ')', so the trailing ')' is literal text.
        self.assertEqual(
            sd.inline("[bad](javascript:alert(1))"),
            [{"t": "link", "s": "bad"}, {"t": "text", "s": ")"}],
        )

    def test_italic_is_literal(self):
        self.assertEqual(sd.inline("a *b* c"), [{"t": "text", "s": "a *b* c"}])


class TestParseBlocks(unittest.TestCase):
    def test_heading_levels_clamped(self):
        b = sd.parse_markdown("# A\n## B\n### C\n#### D")
        self.assertEqual([(x["type"], x["level"]) for x in b],
                         [("heading", 1), ("heading", 2), ("heading", 3), ("heading", 3)])

    def test_paragraph_softwrap(self):
        b = sd.parse_markdown("line one\nline two\n\nnext para")
        self.assertEqual(b[0]["type"], "para")
        self.assertEqual(sd._runs_text(b[0]["runs"]), "line one line two")
        self.assertEqual(sd._runs_text(b[1]["runs"]), "next para")

    def test_unordered_list_flat(self):
        b = sd.parse_markdown("- a\n- b\n  - c")     # indented line is NOT nested
        ul = [x for x in b if x["type"] == "ulist"][0]
        self.assertEqual([sd._runs_text(i) for i in ul["items"]], ["a", "b"])
        self.assertTrue(any(x["type"] == "para" and sd._runs_text(x["runs"]) == "- c" for x in b))

    def test_ordered_list(self):
        b = sd.parse_markdown("1. first\n2. second")
        ol = [x for x in b if x["type"] == "olist"][0]
        self.assertEqual([sd._runs_text(i) for i in ol["items"]], ["first", "second"])

    def test_blockquote(self):
        b = sd.parse_markdown("> quoted")
        self.assertEqual(b[0]["type"], "quote")
        self.assertEqual(sd._runs_text(b[0]["runs"]), "quoted")

    def test_code_fence_raw_and_autoclose(self):
        b = sd.parse_markdown("```\n**not bold** 한글\nmore")
        code = [x for x in b if x["type"] == "code"][0]
        self.assertEqual(code["text"], "**not bold** 한글\nmore")

    def test_empty_body(self):
        self.assertEqual(sd.parse_markdown("   \n\n"), [{"type": "empty"}])


class TestParseTable(unittest.TestCase):
    def test_gfm_table(self):
        md = "| 이름 | 값 |\n| --- | --- |\n| a | **b** |"
        b = sd.parse_markdown(md)
        t = [x for x in b if x["type"] == "table"][0]
        self.assertEqual([sd._runs_text(c) for c in t["header"]], ["이름", "값"])
        self.assertEqual(sd._runs_text(t["rows"][0][0]), "a")
        self.assertEqual(t["rows"][0][1], [{"t": "bold", "s": "b"}])

    def test_pipe_without_separator_is_paragraph(self):
        b = sd.parse_markdown("| not | a table |\njust text")
        self.assertFalse(any(x["type"] == "table" for x in b))
        self.assertTrue(any(x["type"] == "para" for x in b))

    def test_table_then_text(self):
        md = "| h |\n| - |\n| x |\n\nafter"
        b = sd.parse_markdown(md)
        self.assertEqual([x["type"] for x in b], ["table", "para"])

    def test_table_ragged_rows_normalized_to_header(self):
        md = "| a | b |\n| - | - |\n| x | y | z |\n| only |"
        t = [x for x in sd.parse_markdown(md) if x["type"] == "table"][0]
        self.assertTrue(all(len(r) == 2 for r in t["rows"]))   # extra dropped, missing padded
        self.assertEqual(sd._runs_text(t["rows"][0][0]), "x")  # first cell kept
        self.assertEqual(sd._runs_text(t["rows"][1][1]), "")   # padded empty cell


class TestHelpers(unittest.TestCase):
    def test_pick_base_pt_bins(self):
        self.assertEqual(sd.pick_base_pt(100), 12)
        self.assertEqual(sd.pick_base_pt(800), 11)
        self.assertEqual(sd.pick_base_pt(2000), 10)
        self.assertEqual(sd.pick_base_pt(5000), 9)

    def test_resolve_screenshot_basename(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "home.png"), "wb").close()
            self.assertEqual(sd.resolve_screenshot("/static/cop/screenshots/home.png", d),
                             os.path.join(d, "home.png"))
            self.assertEqual(sd.resolve_screenshot("home.png", d), os.path.join(d, "home.png"))
            self.assertIsNone(sd.resolve_screenshot("missing.png", d))
            self.assertIsNone(sd.resolve_screenshot("", d))
            self.assertIsNone(sd.resolve_screenshot("noext", d))

    def test_load_site_docs_precedence(self):
        sg = {"spec": {"slides": []}, "guide": {"slides": []}}
        self.assertEqual(sd.load_site_docs({"docs": sg})["spec"], {"slides": []})   # docs wins
        self.assertEqual(sd.load_site_docs(sg)["guide"], {"slides": []})            # top-level
        self.assertEqual(sd.load_site_docs({"data": sg})["spec"], {"slides": []})   # one unwrap
        with self.assertRaises(ValueError):
            sd.load_site_docs({"nope": 1})


class TestDeckStructure(unittest.TestCase):
    OPTS = {"font": "Apple SD Gothic Neo", "mono_font": "Menlo", "title_prefix": "", "label": "cop"}

    def test_new_prs_is_16x9(self):
        prs = sd._new_prs()
        self.assertEqual(round(prs.slide_width / 914400, 3), 13.333)
        self.assertEqual(round(prs.slide_height / 914400, 3), 7.5)

    def test_title_slide_has_title_and_subtitle(self):
        prs = sd._new_prs()
        doc = {"title": "기능명세서 — CoP", "generatedAt": "2026-06-24T09:00:00+09:00",
               "slides": [{"id": "a"}, {"id": "b"}]}
        sd.add_title_slide(prs, doc, self.OPTS)
        texts = [sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame]
        self.assertTrue(any("기능명세서 — CoP" in t for t in texts))
        self.assertTrue(any("슬라이드 2장" in t for t in texts))   # N excludes title slide
        for sh in prs.slides[0].shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        self.assertEqual(r.font.name, "Apple SD Gothic Neo")


class TestPageSlideText(unittest.TestCase):
    OPTS = {"font": "Apple SD Gothic Neo", "mono_font": "Menlo", "title_prefix": "", "label": "cop"}

    def _slide(self, **over):
        s = {"id": "x", "kind": "system", "title": "아키텍처", "category": "시스템",
             "order": 1, "screenshot": "", "updated_at": "2026-06-24T09:00:00+09:00",
             "commit": "abc1234", "ui_hash": "", "body_md": "## 개요\n- 항목 하나\n- 항목 둘"}
        s.update(over); return s

    def test_system_slide_is_textonly_no_picture(self):
        prs = sd._new_prs()
        sd.add_page_slide(prs, self._slide(), "", 12, self.OPTS)
        sl = prs.slides[0]
        self.assertFalse(any(sh.shape_type == 13 for sh in sl.shapes))  # 13 = PICTURE
        all_text = "\n".join(sh.text_frame.text for sh in sl.shapes if sh.has_text_frame)
        self.assertIn("아키텍처", all_text)
        self.assertIn("개요", all_text)
        self.assertIn("• 항목 하나", all_text)
        self.assertIn("abc1234", all_text)            # footer provenance

    def test_empty_body_placeholder(self):
        prs = sd._new_prs()
        sd.add_page_slide(prs, self._slide(body_md="  "), "", 12, self.OPTS)
        all_text = "\n".join(sh.text_frame.text for sh in prs.slides[0].shapes if sh.has_text_frame)
        self.assertIn("본문 없음", all_text)


if __name__ == "__main__":
    unittest.main()
