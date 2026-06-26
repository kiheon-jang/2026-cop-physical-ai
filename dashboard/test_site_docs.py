import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

import site_docs


def _make_png(path, w, h):
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">II", w, h) + b"\x08\x06\x00\x00\x00"
    chunk = struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr))
    Path(path).write_bytes(sig + chunk)


class TestParse(unittest.TestCase):
    def test_parse_frontmatter_basic(self):
        text = '---\nid: home\ntitle: "Overview (홈)"\norder: 1\n---\n\n본문줄1\n'
        meta, body = site_docs.parse_frontmatter(text)
        self.assertEqual(meta["id"], "home")
        self.assertEqual(meta["title"], "Overview (홈)")
        self.assertEqual(meta["order"], "1")
        self.assertEqual(body.strip(), "본문줄1")

    def test_parse_frontmatter_none(self):
        meta, body = site_docs.parse_frontmatter("프론트매터 없음")
        self.assertEqual(meta, {})
        self.assertEqual(body, "프론트매터 없음")

    def test_split_doc_sections(self):
        body = "## 기능명세\n상세 A\n\n## 사용가이드\n쉬운 B\n"
        out = site_docs.split_doc_sections(body)
        self.assertEqual(out["spec"], "상세 A")
        self.assertEqual(out["guide"], "쉬운 B")

    def test_split_missing_one(self):
        out = site_docs.split_doc_sections("## 기능명세\n상세만\n")
        self.assertEqual(out["spec"], "상세만")
        self.assertEqual(out["guide"], "")

    def test_parse_frontmatter_requires_fence_newline(self):
        meta, body = site_docs.parse_frontmatter("---title\nx")
        self.assertEqual(meta, {})
        self.assertEqual(body, "---title\nx")

    def test_split_empty_section_body(self):
        out = site_docs.split_doc_sections("## 기능명세\n## 사용가이드\n")
        self.assertEqual(out["spec"], "")
        self.assertEqual(out["guide"], "")


class TestBuild(unittest.TestCase):
    def _fixture(self, root: Path):
        (root / "pages").mkdir(parents=True)
        (root / "system").mkdir()
        (root / "pages" / "01-home.md").write_text(
            '---\nid: home\ntitle: 홈\norder: 1\ncategory: 핵심\nscreenshot: home.png\n---\n'
            '## 기능명세\n홈 상세\n\n## 사용가이드\n홈 쉬움\n', encoding="utf-8")
        (root / "system" / "spec-arch.md").write_text(
            '---\ndoc: spec\nid: arch\ntitle: 아키텍처\norder: 99\n---\n구조 설명\n', encoding="utf-8")

    def test_build_site_docs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._fixture(root)
            docs = site_docs.build_site_docs(root, root, "테스트")
            self.assertEqual(docs["spec"]["title"], "기능명세서 — 테스트")
            ids = [s["id"] for s in docs["spec"]["slides"]]
            self.assertEqual(ids, ["home", "arch"])  # order 1, 99
            home = docs["spec"]["slides"][0]
            self.assertEqual(home["kind"], "page")
            self.assertEqual(home["screenshot"], "")  # SP2: no PNG/proj → "" (manifest contract)
            self.assertEqual(home["ui_hash"], "")
            self.assertEqual(home["body_md"], "홈 상세")
            self.assertIn("updated_at", home)
            self.assertEqual([s["id"] for s in docs["guide"]["slides"]], ["home"])
            self.assertEqual(docs["guide"]["slides"][0]["body_md"], "홈 쉬움")

    def test_build_missing_content_dir(self):
        with tempfile.TemporaryDirectory() as d:
            docs = site_docs.build_site_docs(Path(d) / "nope", Path(d), "X")
            self.assertEqual(docs["spec"]["slides"], [])
            self.assertEqual(docs["guide"]["slides"], [])

    def test_validate_ok_and_bad(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); self._fixture(root)
            docs = site_docs.build_site_docs(root, root, "X")
            self.assertEqual(site_docs.validate_docs(docs), [])
        problems = site_docs.validate_docs({"spec": {"slides": []}})
        self.assertIn("missing or invalid doc: guide", problems)


    def test_screenshot_rewrite_and_ui_hash(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pages = root / "content" / "pages"
            pages.mkdir(parents=True)
            (pages / "01-x.md").write_text(
                '---\nid: x\ntitle: X\norder: 1\nscreenshot: x.png\ncategory: 핵심\n---\n'
                '## 기능명세\nA\n## 사용가이드\nB\n', encoding="utf-8")
            shots = root / "screenshots"
            shots.mkdir()
            (shots / "manifest.json").write_text(
                json.dumps({"x": {"ui_hash": "abc123", "captured_at": "t"}}), encoding="utf-8")
            # PNG absent → screenshot becomes "" even though frontmatter had x.png
            docs = site_docs.build_site_docs(root / "content", root, "T", proj="hdel")
            s = docs["spec"]["slides"][0]
            self.assertEqual(s["ui_hash"], "abc123")
            self.assertEqual(s["screenshot"], "")
            # PNG present → /static path
            (shots / "x.png").write_bytes(b"\x89PNG")
            docs2 = site_docs.build_site_docs(root / "content", root, "T", proj="hdel")
            self.assertEqual(docs2["spec"]["slides"][0]["screenshot"], "/static/hdel/screenshots/x.png")

    def test_validate_detects_missing_contract_field(self):
        bad = {
            "spec": {"slides": [{"id": "x", "kind": "page", "title": "t",
                                 "order": 1, "body_md": "b"}]},  # missing category/screenshot/updated_at/commit/ui_hash
            "guide": {"slides": []},
        }
        problems = site_docs.validate_docs(bad)
        self.assertTrue(any("ui_hash" in p for p in problems))


class TestSplitMarkers(unittest.TestCase):
    def test_pre_plus_two_markers(self):
        s = site_docs.split_section_into_slides(
            'a\nb\n<!-- slide title="X" -->\nc\nd\n<!-- slide title="Y" screenshot="" -->\ne')
        self.assertEqual(len(s), 3)
        self.assertEqual(s[0]["attrs"], {})
        self.assertEqual(s[0]["body"], "a\nb")
        self.assertEqual(s[1]["attrs"].get("title"), "X")
        self.assertEqual(s[1]["body"], "c\nd")
        self.assertEqual(s[2]["attrs"].get("screenshot"), "")

    def test_no_markers_single_chunk(self):
        s = site_docs.split_section_into_slides("just text\nno markers")
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["body"], "just text\nno markers")

    def test_leading_marker_no_pre(self):
        s = site_docs.split_section_into_slides('<!-- slide title="Only" -->\nbody')
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["attrs"]["title"], "Only")
        self.assertEqual(s[0]["body"], "body")


class TestClassifyLayout(unittest.TestCase):
    def test_ratios(self):
        self.assertEqual(site_docs.classify_layout((1280, 720)), "top")     # 1.78
        self.assertEqual(site_docs.classify_layout((418, 628)), "side")     # 0.67
        self.assertEqual(site_docs.classify_layout((760, 594)), "split")    # 1.28
        self.assertEqual(site_docs.classify_layout(None), "none")

    def test_boundaries(self):
        self.assertEqual(site_docs.classify_layout((160, 100)), "top")      # 1.60
        self.assertEqual(site_docs.classify_layout((95, 100)), "side")      # 0.95


class TestReadPngSize(unittest.TestCase):
    def test_reads_ihdr(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.png"); _make_png(p, 1280, 720)
            self.assertEqual(site_docs.read_png_size(Path(p)), (1280, 720))

    def test_bad_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bad.png"); Path(p).write_bytes(b"notpng")
            self.assertIsNone(site_docs.read_png_size(Path(p)))


class TestBuildSlidesMulti(unittest.TestCase):
    BASE = {"id": "home", "kind": "page", "title": "Home", "category": "", "order": 1,
            "updated_at": "", "commit": "", "ui_hash": ""}

    def _shots(self):
        d = tempfile.mkdtemp()
        sdir = Path(d) / "screenshots"; sdir.mkdir()
        _make_png(sdir / "home.png", 1280, 720)   # top
        return sdir

    def test_ids_orders_inheritance(self):
        sdir = self._shots()
        section = ('overview\n'
                   '<!-- slide title="A" screenshot="" -->\n'
                   'detail a\n'
                   '<!-- slide title="B" -->\n'
                   'detail b')
        slides = site_docs._build_slides(self.BASE, section, "home.png", True, sdir, "cop")
        self.assertEqual([s["id"] for s in slides], ["home", "home--1", "home--2"])
        self.assertAlmostEqual(slides[1]["order"], 1.001, places=9)
        self.assertTrue(slides[0]["screenshot"].endswith("home.png"))
        self.assertEqual(slides[0]["image_layout"], "top")        # overview inherits page shot
        self.assertEqual(slides[1]["screenshot"], "")             # detail screenshot="" -> none
        self.assertEqual(slides[1]["image_layout"], "none")
        self.assertTrue(slides[2]["screenshot"].endswith("home.png"))  # no attr -> inherits
        self.assertEqual([s["title"] for s in slides[1:]], ["A", "B"])

    def test_empty_section_no_slides(self):
        self.assertEqual(site_docs._build_slides(self.BASE, "  \n ", "home.png", True, self._shots(), "cop"), [])

    def test_system_never_screenshot(self):
        slides = site_docs._build_slides(self.BASE, "sys body", "home.png", False, self._shots(), "cop")
        self.assertEqual(slides[0]["screenshot"], "")
        self.assertEqual(slides[0]["image_layout"], "none")

    def test_bad_layout_attr_falls_back_to_computed(self):
        section = '<!-- slide title="A" layout="bogus" -->\nbody'
        slides = site_docs._build_slides(self.BASE, section, "home.png", True, self._shots(), "cop")
        self.assertEqual(slides[0]["image_layout"], "top")        # bogus -> computed (wide png)


class TestValidateLayout(unittest.TestCase):
    def _slide(self, **over):
        s = {"id": "a", "kind": "page", "title": "A", "category": "", "order": 1,
             "screenshot": "", "updated_at": "", "commit": "", "ui_hash": "",
             "image_layout": "none", "body_md": "ok"}
        s.update(over); return s

    def test_bad_layout_flagged(self):
        docs = {"spec": {"slides": [self._slide(image_layout="weird")]}, "guide": {"slides": []}}
        self.assertTrue(any("bad image_layout" in p for p in site_docs.validate_docs(docs)))

    def test_too_long_flagged(self):
        docs = {"spec": {"slides": [self._slide(image_layout="side", body_md="x" * 800)]},
                "guide": {"slides": []}}
        self.assertTrue(any("too long" in p for p in site_docs.validate_docs(docs)))


if __name__ == "__main__":
    unittest.main()
