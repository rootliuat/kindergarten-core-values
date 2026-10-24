# scripts/
> L2 | 父级: [AGENTS.md](../AGENTS.md)

成员清单
build_word.cjs: JSON 生成六部分 Word，支持横向脉络与辅助表，定向清除三级标题编号后的空白。
check_word.py: 独立检查 OOXML 结构、字体、编号空白、表格与可选 LibreOffice PDF 输出。
environment.py: 发现当前运行时、字体及本机配置，提供子进程调用工具。
setup.py: 默认只读检查，--install 补齐包内依赖。
smoke_test.py: 从排版样例生成 Word 并调用渲染检查。
test_word.py: 有效生成、标题空白定向规范与正文保留、错误输入及输出篡改的回归检查。

依赖：build_word.cjs 与 check_word.py 共读 references/course-structure.json；测试使用临时目录，不写教师原件。六部分是输出结构，不是六个教学步骤。
变更记录：2026-10-22，增加脉络表与三列表支持及相应测试。
变更记录：2026-10-23，三级标题编号后不留空白；增加生成、非目标内容保留与空格或制表符篡改检测测试，不批量修改已有课程。
验证范围：本次六项回归测试通过；临时排版样例经 Word 原生导出，五页完成目视检查。验证不涉及课程效果，也未重生成已有课程文件。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
