# scripts/
> L2 | 父级: [AGENTS.md](../AGENTS.md)

成员清单
build_word.cjs: JSON 生成六部分 Word，支持一行四格脉络与二列或三列辅助表。
check_word.py: 独立检查 OOXML 结构、字体、表格与可选 LibreOffice PDF 输出。
environment.py: 发现当前运行时、字体及本机配置，提供子进程调用工具。
setup.py: 默认只读检查，--install 补齐包内依赖。
smoke_test.py: 从排版样例生成 Word 并调用渲染检查。
test_word.py: 生成器与检查器的有效输入、错误输入和输出篡改回归检查。

依赖：build_word.cjs 与 check_word.py 共读 references/course-structure.json；测试使用临时目录，不写教师原件。六部分是输出结构，不是六个教学步骤。
变更记录：2026-10-22，增加脉络表与三列表支持及相应测试。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
