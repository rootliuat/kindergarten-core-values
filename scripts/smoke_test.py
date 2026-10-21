"""
[INPUT]: sample-input.json、build_word.cjs、check_word.py 与可用运行时。
[OUTPUT]: 六部分排版样例及渲染检查结果，不验证教学效果。
[POS]: scripts 的排版冒烟检查入口。
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from pathlib import Path
import argparse, shutil, subprocess, sys
from environment import ROOT

ap=argparse.ArgumentParser(description='生成六部分格式样例并进行渲染核对，不测试教学效果')
ap.add_argument('--out',required=True,type=Path)
ap.add_argument('--soffice')
args=ap.parse_args()
node=shutil.which('node')
if not node: raise SystemExit('未找到 Node.js；先运行环境检查。')
out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
doc=out/'排版自检样例.docx'
subprocess.run([node,str(ROOT/'scripts/build_word.cjs'),str(ROOT/'references/sample-input.json'),str(doc)],check=True)
command=[sys.executable,str(ROOT/'scripts/check_word.py'),str(doc),'--out',str(out/'核查')]
if args.soffice: command+=['--soffice',args.soffice]
raise SystemExit(subprocess.run(command).returncode)
