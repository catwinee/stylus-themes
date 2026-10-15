# 维护约定

- 这是多站点 Stylus 仓库，不是知乎专用仓库。按 `src/<site>/` 组织源码。
- `styles.manifest.json` 是站点清单。已有样式的 `name` 是重复导入时的匹配键，未经明确要求不要重命名，也不要生成随机 UUID 或浏览器本地数字 ID。
- 用户偏好每次从 Stylus 管理页完整导入 `dist/stylus.json`。始终更新这一统一文件，不再要求追加 CSS 补丁或逐站点导入。
- 改源码/清单后运行 `python3 scripts/build.py`；提交源码、清单、测试和生成产物。
- 每个分区必须限制作用范围，列表页不能意外扩展到问答、搜索等详情页。
- 运行 `uv run python -m unittest discover -s tests -v`。离线测试通过不能称为真实网页或扩展导入已验收。
- 没有新的 DOM 证据时，不将相似外观视为相同结构。保留用户已经验收的行为。
- 不直接改用户 Firefox/Stylus 的配置；由用户导入并验收。Tampermonkey 脚本另行管理，未导出前不要假定仓库内有其当前版本。
