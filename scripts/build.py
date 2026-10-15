#!/usr/bin/env python3
"""从两个 CSS 源文件生成 Stylus JSON 和 Mozilla-format CSS；仅使用标准库。"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "知乎阅读优化 · 整理版"
SECTIONS = (
    ("global.css", "zhihu.com"),
    ("article.css", "zhuanlan.zhihu.com"),
)


def render():
    sections = []
    blocks = []
    for filename, domain in SECTIONS:
        code = (ROOT / "src" / filename).read_text(encoding="utf-8").strip() + "\n"
        sections.append({"code": code, "domains": [domain]})
        indented = "\n".join("    " + line if line else "" for line in code.splitlines())
        blocks.append(f'@-moz-document domain("{domain}") {{\n{indented}\n}}')

    # 不携带旧样式 ID、扩展 settings 或浏览器配置，作为独立样式供验收。
    styles = [{"name": NAME, "enabled": True, "sections": sections}]
    return {
        "zhihu-reading.stylus.json": json.dumps(styles, ensure_ascii=False, indent=2) + "\n",
        "zhihu-reading.css": "\n\n".join(blocks) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="检查产物是否与源码一致，不写文件")
    args = parser.parse_args()
    stale = []
    for name, content in render().items():
        path = ROOT / "dist" / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(path.relative_to(ROOT))
    if stale:
        parser.error("产物需要重新生成：" + ", ".join(stale))
    if args.check:
        print("构建产物与源码一致")


if __name__ == "__main__":
    main()
