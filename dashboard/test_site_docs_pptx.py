# test_site_docs_pptx.py
import unittest
import site_docs_pptx as sd


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


if __name__ == "__main__":
    unittest.main()
