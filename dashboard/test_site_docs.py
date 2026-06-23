import tempfile
import unittest
from pathlib import Path

import site_docs


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


if __name__ == "__main__":
    unittest.main()
