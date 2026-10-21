# 环境与迁移说明（１．４．０版）

## 迁移内容

复制整个 `kindergarten-core-values` 文件夹，保留内部层级，交给所用 Agent 的技能加载机制；不要只复制 SKILL.md。支持直接读取本地文件的 Agent 也可先读取本文件夹中的 SKILL.md 再执行。模型、可用工具和教师提供的班情会影响课程内容，本包不承诺不同模型逐字输出相同。

已带：十二主题入口、十七份教师材料的分析摘要（C01—C15 与 T01—T02）、二十份不同 Word 的框架研究（DOC01—DOC20）、六部分写作方法、来源与阅读范围、三十项游戏及评审、内容判断和 Word 排版工具。
未带：原始教师文件、调研原图视频、完整对话记忆、陈鹤琴独立人格技能、系统软件、字体文件、小红书程序与登录凭据。已有摘要够用时无需重新调研；引用原件内容要核对当前可用文件，不能宣称读取了包内不存在的原件。

## 先检查，再补缺项

在本技能文件夹打开终端，以下命令使用当前可用的 `python`（macOS／Linux 常用 `python3`）。脚本支持从其他工作目录通过完整路径调用。

```text
python scripts/setup.py
python scripts/setup.py --install
python scripts/smoke_test.py --out 自检输出
```

第一条只检查，第二条按缺项安装**技能目录内**的 npm 依赖和 `.runtime/venv` Python 环境，不安装全局包，不改变 MCP 或登录配置。已满足固定版本的依赖跳过，不重复安装。退出码２表示尚有缺项，非“全部完成”；安装失败时保留输出并处理具体问题，不无限重试。

基础工具需可用：Python ３．１１或更高版本、Node.js ２２或更高版本及 npm、LibreOffice。推荐当前受支持版本。官方获取地址：[Python](https://www.python.org/downloads/)、[Node.js](https://nodejs.org/en/download)、[LibreOffice](https://www.libreoffice.org/download/)。已有相应工具可直接使用，不为统一目录重装。

脚本通过 PATH、操作系统常见安装位置寻找 LibreOffice；特殊安装可显式指定：

```text
python scripts/setup.py --install --soffice "请替换成LibreOffice可执行文件完整路径"
```

此路径只保存到本机 `.runtime/environment.json`，不写回共享资料。也可用 `SOFFICE_PATH` 环境变量或检查命令的 `--soffice` 参数。本包不查找作者的 `.codex/tools` 目录。

## 字体与校验

需要已安装：方正小标宋简体、黑体、楷体_GB2312、仿宋_GB2312。由使用者提供可使用的字体并按系统方式安装，包内不分发字体。环境检查会列出找到的文件和缺项；生成后还会核对 PDF 实际使用的字体。缺少指定字体时，保留草稿并明确未完成格式验收，不默认为相近字体等价。

生成 Word 需要 Node.js 和本包的 docx 库。自动渲染检查还需要 LibreOffice 和专用 Python 环境中的 PyMuPDF；不依赖 Word 自动化、Poppler、Pillow 或独立 docx skill。已有 docx／pptx skill 可以辅助读取教师新材料，未安装时按实际文件类型使用可用工具，不把它们列为生成课程的强制前置。

`package-lock.json` 固定 npm 依赖树，`requirements.txt` 固定 PDF 工具版本。[npm ci](https://docs.npmjs.com/cli/v11/commands/npm-ci/)按锁定文件安装。升级工具后重新自检；锁定版本有助于复现排版，但不能保证不同办公软件分页完全一致。

## 小红书按需连接

使用包内已整理的活动与来源无需 MCP。只有用户要求新增小红书调研或确有资料缺口时，检查现有 MCP；没有再按[官方仓库](https://github.com/xpzouying/xiaohongshu-mcp)当时的安装说明配置并登录。本包没有安装器或登录凭据。仅浏览、检索、阅读详情与评论、记录出处，不点赞、收藏、评论或发布。

阅读详情后再判断玩法、年龄、参与机会、材料、必要调整和证据质量；评论区求资料、平台 AI 回复不是实施好评。互动量不作为质量分，也保留低互动但可分析的活动。适用完整的[活动选用规则](activity-selection.md)。

## 再次打包

分发源文件及锁定文件，不带 `node_modules`、`.runtime`、`__pycache__`、生成文档、个人资料、账号文件或本机配置。新电脑首次安装库需要网络；依赖已就绪后，包内资料的使用和文档生成检查不需要联网。当前验证范围另见交付说明，不把同一电脑的隔离目录试跑说成多台电脑或多系统实测。
