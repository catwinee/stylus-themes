# Stylus Themes

个人网站样式仓库：按网站维护源码，用 Git 追踪，**统一生成一份 JSON，每次完整导入 Stylus 管理页**。

仓库路径：`/home/Catwine/Workspace/stylus-themes`。原 `zhihu-reading` → `stylus` 仓库已整体改名，Git 历史保留。

## 唯一的导入文件

```text
/home/Catwine/Workspace/stylus-themes/dist/stylus.json
```

每次更新后，在 **Stylus 管理页 → 备份 / Backup → 导入 / Import** 选择这个文件。不再需要粘贴 CSS，也不使用编辑器中的 Append / Overwrite。旧的 `dist/zhihu-reading.*` 导出已移除，避免导入过时文件。

目前 JSON 中包含一个样式 **「知乎阅读优化 · 整理版」**，内部有三个 Code 分区。以后新增网站会加入同一 JSON，成为独立样式，便于分别开关。

### 反复完整导入的行为

- 保持每个样式的 **`name` 唯一且稳定**。本次沿用已安装的「知乎阅读优化 · 整理版」，不会因仓库改名而改动样式名称。
- 已核对 Stylus 上游导入实现：优先按 UUID、本地 ID 匹配，再按名称匹配。因此本仓库不写本地数字 ID，靠稳定名称更新已有条目；首次出现的新名称则新增。
- 文件不包含扩展设置、排序或同步配置，也不是自动清空浏览器的“全量镜像”。**文件中没有的其他样式不会自动删除**；不要随意点击导入报告中针对额外样式的删除/禁用按钮。
- `enabled` 状态来自仓库清单，目前知乎为 `true`，重新导入可能重新启用它。只在浏览器中修改的代码会被后续导入覆盖；长期修改应回到仓库维护。
- 不要在清单里随意重命名已有样式。如果浏览器已有多个同名副本，先人工确认并清理；名称匹配不是自动合并重复项的机制。
- 第一次切换到统一 JSON 后，请检查导入报告：现有知乎样式应显示更新或相同，而不是额外新增一份。已核对上游逻辑，尚未自动操作你的扩展验证导入流程。

上游参考：<https://github.com/openstyles/stylus/blob/master/src/manage/import-export.js>，`importFromString` / `analyze` / `renderOrphans`。

### 保留与回退

- 原来的「知乎 article」「知乎全站优化」继续保持禁用，避免与整理版叠加。
- 原始备份 `/home/Catwine/Downloads/stylus-2026-10-15-15-04.json` 未改动。回退到原版可以禁用整理版、重新启用这两个旧样式。
- 现有 Tampermonkey 作者补充信息脚本继续启用；它不属于 Stylus JSON，本仓库未备份或更改其已安装版本。
- 更新前若在扩展里做过临时修改，请先导出备份。

## 仓库结构

```text
styles.manifest.json           多站点清单：稳定名称、启用状态、作用范围和源码路径
src/
  zhihu/
    global.css                 知乎全站界面
    article.css                专栏阅读布局
    home.css                   五条列表页入口
scripts/build.py               标准库构建脚本
dist/stylus.json                唯一完整导入文件
reference/zhihu/original-styles.json
                               原始 CSS 回归基线，不是导入文件
tests/                         离线 Firefox 夹具及测试
pyproject.toml / uv.lock        测试依赖
```

**只修改清单和 `src/` 源码，然后重新构建，不手改生成 JSON。** `dist/stylus.json` 随 Git 提交，便于直接导入和查看版本变化。

## 增加其他网站

1. 在 `src/<网站>/` 下放置 CSS 源文件。
2. 在 `styles.manifest.json` 数组中增加一个样式条目，指定唯一的 `key` 和长期稳定的 `name`。
3. 每个 section 指向一个源码文件，并明确限定 `domains`、`urls`、`urlPrefixes` 或 `regexps`。清单的 `key` 和 `source` 仅供构建使用，不会输出给 Stylus。
4. 运行构建和测试，提交 Git，再完整导入 `dist/stylus.json`。

一个网站可有多个 Code 分区；没有必要为每个页面新建样式。CSS 源文件不包含 `@-moz-document` 外壳，适用范围由清单维护。

构建器拒绝空/重复名称或 key、空作用范围、空 CSS 和 `src/` 以外的源文件路径，以防意外生成全局样式或错误匹配。

## 当前知乎样式

| 分区 | 作用范围 | 效果 |
| --- | --- | --- |
| Code 1 | 域名 `zhihu.com`，含子域名 | 精简导航、加长搜索栏、隐藏直答/看山/解释入口 |
| Code 2 | 域名 `zhuanlan.zhihu.com` | 正文单栏居中、留白、目录、阴影 |
| Code 3 | `https://www.zhihu.com` 的五条列表入口，URL 正则限定 | 隐藏右列、信息流加宽居中 |

### 全站与专栏：保留已验收效果

- 隐藏 AI Works、故事、直答、看山、「解释这篇内容」，保留正常导航和互动按钮。
- 搜索框解除 365px 限宽，内部按钮间距及与左侧导航间距均为 16 CSS px。
- 专栏阅读区域最大宽度 1200 CSS px，左右留白 `clamp(24px, 5vw, 64px)`。
- 目录宽 76px、左偏移 -92px；保留内部 sticky，不用 `overflow: hidden` 裁剪目录。
- 阴影 `0 1px 6px rgba(18, 18, 18, 0.10)`，是近似设计值，不是从问答卡片精确提取。
- 侧栏整列隐藏但 DOM 保留，供现有 Tampermonkey 脚本读取作者统计并展示在文首。

### 列表页：待真实页面验收

- 只匹配 `/`、`/follow`、`/hot`、`/ring-feeds`、`/column-square`，允许尾斜杠、query 和 hash；不覆盖问答、个人主页、搜索或下级详情页。
- 基于推荐页已提供的 `.Topstory-container` / `.Topstory-mainColumn` / `.css-bkewaf` 结构隐藏整个右列。
- 信息流最大总宽 1100 CSS px，左右内边距 `clamp(20px, 3vw, 40px)`，白色背景、轻阴影；卡片原有内边距保留。
- 推荐内容项使用已确认的 `.Feed:has(.ContentItem)`，增加上下各 28px 内边距，最小高度 180px（包含这层内边距，外层原有留白另外保留）。不设置固定高度，展开后自然增长。
- 左栏顶部发布入口、正常交互和摘要折叠保留；没有 ContentItem 的 Feed 不调整高度。
- **其余四个入口只有路径已确认，不代表已验证其 DOM。** 不同结构会暂时不生效，需进一步采集后补充适配。

### 已知限制

网站生成的 `css-…` 类名可能变化，目前保留已确认的选择器，未猜测替代结构。极窄窗口下目录及展开面板需人工验证；列表页白色底色尚未适配深色主题。CSS 像素会随浏览器缩放放大。

## 构建与测试

```bash
cd /home/Catwine/Workspace/stylus-themes
python3 scripts/build.py
python3 scripts/build.py --check
uv sync --locked
uv run python -m unittest discover -s tests -v
```

构建只用 Python 标准库，输出可重复、不携带构建时间戳。测试需要 Playwright Firefox；优先使用匹配版本，否则尝试已有缓存。可以通过 `PLAYWRIGHT_FIREFOX_EXECUTABLE` 指定，缺少或不兼容时运行 `uv run playwright install firefox`。

测试使用全新临时浏览器上下文和离线夹具，不读取日常 Firefox 的配置/Cookie，不访问真实知乎页面。验证构建一致性、多站点输出、名称唯一性、作用范围、CSS 语法、既有全站/专栏回归和新增列表布局。

离线列表夹具在五条路径和多个宽度下运行，**不能替代其他四页的真实结构验证或扩展导入验收**。

## 人工验收

- [ ] 反复导入统一 JSON 后，知乎只有一个启用的整理版，没有新增同名副本。
- [ ] 知乎整理版仍有三个 Code 分区，Tampermonkey 作者脚本正常。
- [ ] 全站导航与搜索栏、专栏正文/目录/阴影与此前一致。
- [ ] 推荐页右列隐藏、信息流居中；内容项纵向留白合适，发布区没有被加高。
- [ ] 内容项展开全文后自然增长、不截断；收起后恢复，互动按钮正常。
- [ ] 分别检查关注、热榜、圈子和专栏广场，记录哪些还需要结构适配。
- [ ] 问答/详情页不受列表页规则影响。
