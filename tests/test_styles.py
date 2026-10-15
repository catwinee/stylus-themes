"""语法、构建一致性与离线 Firefox 样式回归；不访问真实知乎或浏览器个人配置。"""
import json
import os
import re
from urllib.parse import urlsplit
from pathlib import Path
import subprocess
import unittest

import tinycss2
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / "reference/original-styles.json").read_text())
CURRENT = json.loads((ROOT / "dist/zhihu-reading.stylus.json").read_text())


def applies(section, address):
    url = address if "://" in address else f"https://{address}/"
    host = urlsplit(url).hostname or ""
    return (any(host == domain or host.endswith("." + domain)
                for domain in section.get("domains", []))
            or any(re.fullmatch(pattern, url) for pattern in section.get("regexps", [])))


def css_for(styles, host):
    return "\n".join(section["code"] for style in styles
                     for section in style["sections"] if applies(section, host))


class StructureTests(unittest.TestCase):
    def test_build_is_current(self):
        subprocess.run(["python3", "scripts/build.py", "--check"], cwd=ROOT, check=True)

    def test_import_shape_and_scopes(self):
        self.assertEqual(len(CURRENT), 1)
        style = CURRENT[0]
        self.assertEqual(set(style), {"name", "enabled", "sections"})
        self.assertTrue(style["enabled"])
        self.assertEqual(len(style["sections"]), 3)
        self.assertEqual([s["domains"] for s in style["sections"][:2]],
                         [["zhihu.com"], ["zhuanlan.zhihu.com"]])
        self.assertEqual(set(style["sections"][2]), {"code", "regexps"})
        self.assertFalse(css_for(CURRENT, "example.com"))
        self.assertFalse(css_for(CURRENT, "notzhihu.com"))
        self.assertNotIn("--reading-width", css_for(CURRENT, "www.zhihu.com"))
        self.assertIn("--reading-width", css_for(CURRENT, "zhuanlan.zhihu.com"))

    def test_home_scope_is_limited_to_five_entry_paths(self):
        section = CURRENT[0]["sections"][2]
        for path in ("/", "/follow", "/hot", "/ring-feeds", "/column-square"):
            for suffix in ("", "?test=1", "#section", "?test=1#section"):
                self.assertTrue(applies(section, "https://www.zhihu.com" + path + suffix))
            if path != "/":
                self.assertTrue(applies(section, "https://www.zhihu.com" + path + "/"))
        for url in (
            "https://www.zhihu.com/question/123", "https://www.zhihu.com/people/test",
            "https://www.zhihu.com/search?q=hot", "https://www.zhihu.com/hotter",
            "https://www.zhihu.com/follow/123", "https://www.zhihu.com/column-square/post",
            "https://zhuanlan.zhihu.com/p/123", "https://evil.example/?https://www.zhihu.com/",
            "https://www.zhihu.com.evil.example/", "https://www.zhihu.com//",
        ):
            self.assertFalse(applies(section, url), url)

    def test_css_syntax_and_no_duplicate_declarations(self):
        for section in CURRENT[0]["sections"]:
            seen = set()
            rules = tinycss2.parse_stylesheet(section["code"], skip_comments=True, skip_whitespace=True)
            for rule in rules:
                self.assertEqual(rule.type, "qualified-rule")
                selector = tinycss2.serialize(rule.prelude).strip()
                declarations = tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
                for declaration in declarations:
                    self.assertEqual(declaration.type, "declaration")
                    # 当前选择器没有属性值中的逗号，可按逗号拆分检查冗余声明。
                    for individual in selector.split(","):
                        key = (individual.strip(), declaration.name)
                        self.assertNotIn(key, seen, f"重复声明：{key}")
                        seen.add(key)

    def test_mozilla_format_has_same_three_sections(self):
        rules = tinycss2.parse_stylesheet((ROOT / "dist/zhihu-reading.css").read_text(),
                                         skip_comments=False, skip_whitespace=True)
        self.assertEqual(len(rules), 3)
        for rule, section in zip(rules, CURRENT[0]["sections"]):
            self.assertEqual(rule.type, "at-rule")
            self.assertEqual(rule.lower_at_keyword, "-moz-document")
            scope = "domains" if "domains" in section else "regexps"
            function = "domain" if scope == "domains" else "regexp"
            self.assertEqual(tinycss2.serialize(rule.prelude).strip(),
                             f'{function}({json.dumps(section[scope][0])})')
            normalize = lambda s: "".join(s.split())
            self.assertEqual(normalize(tinycss2.serialize(rule.content)), normalize(section["code"]))


class FirefoxRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        override = os.environ.get("PLAYWRIGHT_FIREFOX_EXECUTABLE")
        default = Path(cls.pw.firefox.executable_path)
        cached = sorted((Path.home() / ".cache/ms-playwright").glob("firefox-*/firefox/firefox"))
        executable = override or (str(default) if default.exists() else str(cached[-1]) if cached else None)
        if executable is None:
            cls.pw.stop()
            raise RuntimeError("缺少测试 Firefox；运行 uv run playwright install firefox")
        try:
            cls.browser = cls.pw.firefox.launch(executable_path=executable, headless=True)
        except Exception:
            cls.pw.stop()
            raise
        print("离线回归 Firefox:", cls.browser.version)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def snapshot(self, styles, host, width, fixture="fixture.html"):
        context = self.browser.new_context(viewport={"width": width, "height": 900})
        # 使用全新临时上下文；禁止请求，不读取真实站点、cookies 或个人 Firefox 配置。
        context.route("**/*", lambda route: route.abort())
        page = context.new_page()
        try:
            page.set_content((ROOT / "tests" / fixture).read_text())
            css = css_for(styles, host)
            if css:
                page.add_style_tag(content=css)
            return page.evaluate("""() => Object.fromEntries(
                [...document.querySelectorAll('[id]')].map(el => {
                    const s = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    const props = ['display', 'width', 'max-width', 'min-width',
                        'margin-left', 'margin-right', 'padding-left', 'padding-right',
                        'column-gap', 'box-sizing', 'box-shadow', 'position', 'top',
                        'left', 'right', 'overflow', '--reading-width'];
                    return [el.id, {
                        ...Object.fromEntries(props.map(p => [p, s.getPropertyValue(p)])),
                        rect: [r.x, r.y, r.width, r.height]
                    }];
                })
            )""")
        finally:
            context.close()

    def test_original_and_cleaned_styles_have_same_computed_effect(self):
        for host in ("zhuanlan.zhihu.com", "www.zhihu.com", "example.com"):
            for width in (1339, 1000, 720):
                with self.subTest(host=host, width=width):
                    actual = self.snapshot(CURRENT, host, width)
                    # 原来的两个独立样式不依赖加载顺序；整理后两种情况都应保持效果。
                    for old in (BASELINE, list(reversed(BASELINE))):
                        self.assertEqual(self.snapshot(old, host, width), actual)

    def test_home_layout_on_confirmed_structure(self):
        for path in ("/", "/follow", "/hot", "/ring-feeds", "/column-square"):
            for width in (1339, 1000, 720, 390):
                with self.subTest(path=path, width=width):
                    s = self.snapshot(CURRENT, "https://www.zhihu.com" + path, width,
                                      fixture="home-fixture.html")
                    self.assertEqual(s["feed-sidebar"]["display"], "none")
                    self.assertEqual(s["feed-layout"]["display"], "block")
                    self.assertEqual(s["feed-layout"]["max-width"], "1100px")
                    x, _, actual_width, _ = s["feed-layout"]["rect"]
                    self.assertAlmostEqual(actual_width, min(1100, width - 32), delta=0.02)
                    self.assertAlmostEqual(x, (width - actual_width) / 2, delta=0.02)
                    self.assertNotEqual(s["feed-main"]["box-shadow"], "none")
                    for key in ("composer", "ask", "expand", "feed-vote", "unknown-sidebar"):
                        self.assertNotEqual(s[key]["display"], "none", key)
                    self.assertEqual(s["unknown-layout"]["display"], "flex")

    def test_home_rules_do_not_leak_to_other_routes(self):
        old_only = [{**CURRENT[0], "sections": CURRENT[0]["sections"][:2]}]
        for url in ("https://www.zhihu.com/question/123", "https://www.zhihu.com/people/test",
                    "https://www.zhihu.com/search?q=test", "https://zhuanlan.zhihu.com/p/123"):
            self.assertEqual(self.snapshot(CURRENT, url, 1339, "home-fixture.html"),
                             self.snapshot(old_only, url, 1339, "home-fixture.html"))

    def test_home_regexp_works_in_javascript(self):
        page = self.browser.new_page()
        try:
            pattern = CURRENT[0]["sections"][2]["regexps"][0]
            urls = ["https://www.zhihu.com" + p for p in
                    ("/", "/follow/?x=1", "/hot#top", "/ring-feeds", "/column-square",
                     "/question/123", "/hotter", "/follow/123")]
            result = page.evaluate("([pattern, urls]) => urls.map(url => new RegExp(pattern).test(url))",
                                   [pattern, urls])
            self.assertEqual(result, [True] * 5 + [False] * 3)
        finally:
            page.close()

    def test_article_features_and_preserved_controls(self):
        s = self.snapshot(CURRENT, "zhuanlan.zhihu.com", 1339)
        for key in ("ai", "story", "ai-relative", "story-relative", "zhida",
                    "kanshan", "explain", "answer-explain", "sidebar"):
            self.assertEqual(s[key]["display"], "none", key)
        for key in ("follow", "ring", "plus", "author", "local-zhihu-author-extra",
                    "vote", "save", "back-top"):
            self.assertNotEqual(s[key]["display"], "none", key)
        self.assertEqual(s["layout"]["max-width"], "1200px")
        self.assertEqual(s["card"]["padding-left"], "64px")
        self.assertNotEqual(s["card"]["box-shadow"], "none")
        self.assertEqual(s["catalog-outer"]["left"], "-92px")
        self.assertEqual(s["catalog-sticky"]["position"], "sticky")
        self.assertEqual(s["search"]["column-gap"], "16px")
        self.assertEqual(s["search-label"]["max-width"], "none")


if __name__ == "__main__":
    unittest.main(verbosity=2)
