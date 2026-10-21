# kindergarten-core-values - 幼儿园核心价值观课程技能
Markdown + JSON + Python 3.11+ + Node.js 22+ + docx 9.12.0

```text
kindergarten-core-values/
|-- SKILL.md                 技能入口与六部分课程要求
|-- references/              主题、案例、写法、结构契约与格式规范
|   |-- teacher-materials/   教师材料摘要与 DOC01—DOC20 框架研究
|   `-- games/               按年龄组织的活动卡与取舍记录
|-- scripts/                 环境配置、Word 生成、独立检查与回归测试
|-- agents/                  技能显示与默认提示词
|-- README.md                安装、使用和实际验证范围
|-- 使用说明.txt             教师可复制的使用指令
|-- package.json             工具版本和固定 docx 依赖
|-- package-lock.json        npm 依赖锁定
|-- requirements.txt         PDF 检查依赖锁定
`-- .gitignore               排除环境、依赖和生成文件
```

职责边界：SKILL.md 定义设计行为，references/curriculum-framework.md 解释六部分写法，references/course-structure.json 是生成与检查共同使用的结构契约。案例描述不是当前班情，程序校验不证明课程成效。

开发规范：修改结构时同步入口、参考、样例、生成器和检查器；改变文档生成行为时运行 scripts/test_word.py 并渲染实际样稿。保留现有资料路径，不为目录整齐移动无关案例。新增代码使用 INPUT/OUTPUT/POS 头部；模块成员见各目录 AGENTS.md。

分发范围：仅源文件、摘要和锁定依赖；不提交原始教师 Word、课程输出、node_modules、.runtime 或本机路径配置。安装副本由维护者在校验后同步，不能反向覆盖未核对的本机改动。

变更记录：2026-10-22，v1.4.0 改为六部分课程框架，恢复情境缘起、独立目标和横向四格脉络，实施以叙述为主，新增二十份 Word 框架研究和结构回归检查。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
