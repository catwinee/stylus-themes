# 知乎阅读优化

将已经逐步验收的 Stylus 补丁整理成 **一个样式、两个 Code 分区**。本次是等效整理，不重新设计页面，也不修改首页/问答页的正文布局。

## 导入验收

1. 保留原始备份 `/home/Catwine/Downloads/stylus-2026-10-15-15-04.json`。
2. 在 Stylus 管理页**禁用**原来的「知乎 article」和「知乎全站优化」，先不要删除。
3. 在管理页的「备份 / Backup」区域使用「导入 / Import」，选择：

   ```text
   /home/Catwine/Workspace/zhihu-reading/dist/zhihu-reading.stylus.json
   ```

4. 启用新增的 **「知乎阅读优化 · 整理版」**，确认编辑器里只有两个 Code 分区。
5. 刷新页面，按下面的清单验收。

这是 **Stylus 管理页导入的 JSON 文件**，不是要粘贴进 CSS 编辑框的代码。文件不包含扩展设置、原样式 ID 或其他站点样式，不要求修改 Firefox 配置。

现有 Tampermonkey「知乎专栏：文首作者补充信息」脚本应当继续启用。Stylus 导出不包含这个脚本，本仓库没有假装备份它，也没有重新安装或改动它。

### 另一种导入方式 / 后续更新

`dist/zhihu-reading.css` 是相同内容的 **Mozilla-format CSS**：

1. 新建样式，或打开已有的「知乎阅读优化 · 整理版」。
2. 使用编辑器的「导入 / Import」按钮，粘贴这个文件的全部内容。
3. 选择 **Overwrite style**，保存。

这样会生成/替换两个域名分区。后续更新推荐用这种方式明确替换现有样式，**不要继续 Append 补丁**。如果重复从管理页导入 JSON，请查看导入结果，确保没有留下多个同时启用的整理版。

### 回退

禁用整理版，重新启用两个旧样式即可。原始 Downloads 文件未被改动。

## Code 分区如何工作

| 分区 | Stylus 作用范围 | 内容 |
| --- | --- | --- |
| Code 1 | 域名 `zhihu.com` | 全站导航、搜索栏、直答、看山、解释入口 |
| Code 2 | 域名 `zhuanlan.zhihu.com` | 专栏正文宽度、留白、侧栏、目录、阴影 |

域名匹配包含子域名。因此在 `www.zhihu.com` 只应用 Code 1，在 `zhuanlan.zhihu.com` 同时应用 Code 1 和 Code 2。域名条件属于每个 Code 分区，不要求拆成两个独立样式。

两个分区源码分别是 `src/global.css` 和 `src/article.css`。它们**不含** `@-moz-document` 外壳；构建时自动生成 JSON 的 `domains` 或 Mozilla-format CSS 的域名外壳。

## 保留的最终效果

### 全站

- 隐藏顶部 AI Works、故事、直答。
- 隐藏看山入口和操作栏的「解释这篇内容」。
- 保留关注、推荐、热榜、专栏、圈子、`+`、返回顶部及常规互动按钮。
- 搜索框解除 365px 最大宽度，填满可用区域。
- 搜索区域内部按钮间距、与左侧导航间距均为 16 CSS px。

### 专栏

- 单栏居中；最大阅读区域宽度 **1200 CSS px**。
- 正文卡片左右留白 `clamp(24px, 5vw, 64px)`。
- 阴影 `0 1px 6px rgba(18, 18, 18, 0.10)`。
- 隐藏侧栏整列，但保留 DOM，兼容现有作者补充信息脚本。
- 目录入口宽 76px，外层左偏移 -92px，保持与正文 16px 的间隔。
- 保留目录内部 sticky 定位，不新增 `overflow: hidden`。

以上均为现有备份的最终有效值。140% 浏览器缩放会放大 CSS 像素对应的视觉尺寸。

## 本次清理了什么

- 将两个旧样式、合计 11 个 Code 分区，整理为一个样式、两个分区。
- 删除专栏里重复的全站规则，统一由 Code 1 负责。
- 宽度仅保留最终 1200px，移除被覆盖的 1000px、1100px。
- 搜索栏外边距仅保留最终 0，移除失效的 16px 外边距补丁。
- 合并相同声明，按功能注释；保留原选择器，不趁整理扩大修改范围。
- 保留 `reference/original-styles.json` 作为回归基线；仅提取原始样式名称、启用状态、代码及范围，不收入扩展设置和安装标识。

## 文件结构

```text
src/
  global.css                 全站样式源码
  article.css                专栏样式源码
scripts/build.py             标准库构建脚本
dist/
  zhihu-reading.stylus.json   管理页导入文件
  zhihu-reading.css          编辑器导入 / 后续覆盖更新
reference/original-styles.json
                             原始 CSS 基线，不作为日常导入文件
tests/
  fixture.html               离线测试页面
  test_styles.py             语法与 Firefox 样式回归测试
pyproject.toml / uv.lock      锁定测试依赖
```

## 修改与构建

**只编辑 `src/`，不要手动修改生成文件。**

```bash
cd /home/Catwine/Workspace/zhihu-reading
python3 scripts/build.py
python3 scripts/build.py --check
```

构建只用 Python 标准库，输出可重复，不携带构建时间戳。`dist/` 随 Git 提交，便于直接导入及查看版本差异。

测试使用 `uv` 管理开发依赖：

```bash
uv sync --locked
uv run python -m unittest discover -s tests -v
```

测试需要 Playwright Firefox。优先使用所需版本，若未安装则尝试本机已有的 Playwright Firefox 缓存；也可以通过 `PLAYWRIGHT_FIREFOX_EXECUTABLE` 指定。若没有浏览器或缓存版本不兼容，再执行：

```bash
uv run playwright install firefox
```

测试运行在全新的临时浏览器上下文内，拦截全部网络请求，不读取日常 Firefox 的个人配置、Cookie 或真实知乎页面。

测试覆盖：

- JSON 仅包含一个样式、两个正确的域名分区；无关域名不匹配。
- CSS 语法及同一选择器内的重复属性检查。
- JSON、Mozilla-format CSS 和源码内容一致。
- 离线 Firefox 中比较整理前后的计算样式和元素矩形。
- 1339 / 1000 / 720 CSS px 三种宽度、三个域名条件；原两个样式的两种加载顺序。
- 入口隐藏、正常按钮保留、最终正文宽度/留白/阴影、目录定位、搜索框间距。

**离线回归不等于真实页面验收。** 夹具依据已提供的 DOM 结构构造，不包含完整知乎页面、脚本动态行为或 Stylus 扩展自身的导入流程；窄窗口回归仅证明整理前后一致，并不保证原布局没有窄屏问题。

## 人工验收清单

- [ ] Stylus 中只启用整理版；两个旧样式禁用，编辑器显示两个 Code 分区。
- [ ] 首页、问答页：隐藏入口、搜索栏长度和两端间距与之前一致。
- [ ] 专栏文首：封面、标题、作者及脚本补充的共同关注/统计信息正常。
- [ ] 专栏正文：1200px 上限、左右留白、阴影正常，没有新增横向滚动条。
- [ ] 目录收起时不碰正文，展开后可见且可点击，滚动跟随正常。
- [ ] 评论、收藏、赞同、分享、返回顶部仍可用。
- [ ] 常用 140% 缩放正常；缩窄窗口时额外检查导航和目录。

## 已知维护点

`css-kjzwqj`、`css-c0fani`、`css-yq5nsh`、`css-1ni4jcm`、`css-1od93p9`、`css-1kerlqf`、`css-x84wzl`、`css-so42cc` 都是当前页面的生成类名，知乎更新后可能变化。本次为保持已验收效果而保留，没有在缺少真实 DOM 验证时换成猜测选择器。

目录左移方案面向当前宽屏阅读布局；极窄窗口和展开面板需要人工验收。阴影是近似设计值，不声称与问答卡片完全一致。

Tampermonkey 脚本另行管理；如果以后要将它收入此仓库，请先导出正在使用的版本，避免将对话中的旧草稿当作已安装版本。
