#!/usr/bin/env python3
"""读取多站点清单和 CSS 源码，生成唯一的完整 Stylus 导入文件。仅使用标准库。"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("dist/stylus.json")
SCOPES = {"domains", "urls", "urlPrefixes", "regexps"}


def build_styles(root=ROOT):
    manifest = json.loads((root / "styles.manifest.json").read_text(encoding="utf-8"))
    styles = []
    names, keys = set(), set()
    for entry in manifest:
        name, key = entry["name"], entry["key"]
        if not name.strip() or name != name.strip() or name in names or not key or key in keys:
            raise ValueError("样式名称与 key 必须非空、唯一，名称不能带首尾空格")
        names.add(name)
        keys.add(key)
        sections = []
        for item in entry["sections"]:
            if set(item) - SCOPES - {"source"}:
                raise ValueError(f"{name}: 不支持的分区字段")
            targets = {scope: item[scope] for scope in SCOPES if scope in item}
            if not targets or any(not isinstance(values, list) or not values or
                                  any(not isinstance(v, str) or not v.strip() for v in values)
                                  for values in targets.values()):
                raise ValueError(f"{name}: 每个分区必须明确提供非空作用范围")
            source = (root / item["source"]).resolve()
            if not source.is_relative_to((root / "src").resolve()):
                raise ValueError(f"{name}: CSS 源文件必须位于 src/ 中")
            code = source.read_text(encoding="utf-8").strip() + "\n"
            if not code.strip():
                raise ValueError(f"{name}: CSS 不能为空")
            sections.append({"code": code, **dict(sorted(targets.items()))})
        if not sections or not isinstance(entry["enabled"], bool):
            raise ValueError(f"{name}: 需要分区与布尔 enabled 值")
        # 保持名称稳定，供 Stylus 按名称匹配并更新已安装样式。
        # 不写浏览器本地数字 ID，也不混入扩展设置或排序。
        styles.append({"name": name, "enabled": entry["enabled"], "sections": sections})
    return styles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="检查产物是否与源码一致，不写文件")
    args = parser.parse_args()
    content = json.dumps(build_styles(), ensure_ascii=False, indent=2) + "\n"
    path = ROOT / OUTPUT
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            parser.error("产物需要重新生成：" + str(OUTPUT))
        print("完整导入文件与源码一致")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
