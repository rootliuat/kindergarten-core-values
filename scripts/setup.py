"""
[INPUT]: environment 提供的探测能力、package-lock.json 和 requirements.txt。
[OUTPUT]: 环境报告；显式 --install 时补齐技能目录内的依赖。
[POS]: scripts 的安装入口，默认只读检查。
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
import argparse, json, os, shutil, sys, venv
from environment import ROOT, RUNTIME, VENV, PYTHON, call, report, venv_ready, find_office

def main():
    ap=argparse.ArgumentParser(description='课程技能环境检查与本地依赖安装')
    ap.add_argument('--install',action='store_true',help='仅安装技能目录内的 npm 依赖和 Python 虚拟环境')
    ap.add_argument('--soffice',help='LibreOffice 可执行文件完整路径；安装模式保存此机器配置')
    args=ap.parse_args()
    if sys.version_info<(3,11): raise SystemExit('请使用 Python 3.11 或更高版本。')
    if args.soffice and not find_office(args.soffice): raise SystemExit('指定的 LibreOffice 文件不存在。')
    if args.install:
        status=report(args.soffice)
        if not status['node_ok']: raise SystemExit('请先安装 Node.js 22 或更高版本，推荐当前 LTS，并重新打开终端。')
        if not status['docx_library_ok']:
            # Invoke npm's JS entrypoint directly, avoiding shell interpolation on Windows.
            npm=shutil.which('npm.cmd' if os.name=='nt' else 'npm')
            if not npm: raise SystemExit('未找到 npm；请检查 Node.js 安装。')
            if os.name=='nt':
                cli=__import__('pathlib').Path(npm).parent/'node_modules/npm/bin/npm-cli.js'
                if not cli.is_file(): raise SystemExit('未找到 npm-cli.js，请在技能目录手动运行 npm ci --ignore-scripts。')
                command=[status['node'],cli]
            else: command=[npm]
            r=call(command+['ci','--ignore-scripts','--no-audit','--no-fund'],cwd=ROOT,timeout=600)
            print(r.stdout);print(r.stderr,file=sys.stderr)
            if r.returncode: raise SystemExit(r.returncode)
        if not PYTHON.is_file():
            print('创建技能专用 Python 环境……',flush=True)
            venv.EnvBuilder(with_pip=True).create(VENV)
        if not venv_ready():
            r=call([PYTHON,'-m','pip','install','-r',ROOT/'requirements.txt'],timeout=600)
            print(r.stdout);print(r.stderr,file=sys.stderr)
            if r.returncode: raise SystemExit(r.returncode)
        RUNTIME.mkdir(exist_ok=True)
        if args.soffice:
            (RUNTIME/'environment.json').write_text(json.dumps({'soffice':find_office(args.soffice)},ensure_ascii=False),encoding='utf-8')
    status=report(args.soffice)
    print(json.dumps(status,ensure_ascii=False,indent=2))
    if not status['word_generation_ready'] or not status['render_check_ready']:
        print('生成或验收所需环境仍有缺项，请按报告补齐；未完成渲染时不能宣称完成格式验收。')
        return 2
    print('Word 生成与渲染检查环境已就绪。')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as e: print(str(e),file=sys.stderr);sys.exit(1)
