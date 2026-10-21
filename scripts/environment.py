"""
[INPUT]: 当前机器运行时、字体目录与本包 .runtime 配置。
[OUTPUT]: 环境发现、字体信息和子进程调用能力。
[POS]: scripts 的环境基础模块，不依赖原作者机器路径。
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from pathlib import Path
import json, os, shutil, struct, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runtime'
VENV = RUNTIME / 'venv'
PYTHON = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
FONTS = {
    '方正小标宋简体': ['方正小标宋简体', 'FZXiaoBiaoSong-B05S', 'FZXBSJW--GB1-0', 'FZXiaoBiaoSong'],
    '黑体': ['黑体', 'SimHei'],
    '楷体_GB2312': ['楷体_GB2312', 'KaiTi_GB2312'],
    '仿宋_GB2312': ['仿宋_GB2312', 'FangSong_GB2312'],
}
def call(args, **kwargs):
    return subprocess.run([str(a) for a in args], capture_output=True, text=True,
                          encoding='utf-8', errors='replace', timeout=kwargs.pop('timeout',60), **kwargs)

def find_office(explicit=None):
    if explicit:
        p=Path(explicit).expanduser()
        return str(p.resolve()) if p.is_file() else None
    config=RUNTIME/'environment.json'
    saved=json.loads(config.read_text('utf-8')).get('soffice') if config.exists() else None
    candidates=[os.environ.get('SOFFICE_PATH'),saved,shutil.which('soffice'),shutil.which('libreoffice')]
    if os.name=='nt':
        candidates += [str(Path(os.environ[k])/'LibreOffice/program/soffice.com') for k in ('ProgramFiles','ProgramFiles(x86)') if k in os.environ]
    elif sys.platform=='darwin':
        candidates += ['/Applications/LibreOffice.app/Contents/MacOS/soffice']
    return next((str(Path(x).resolve()) for x in candidates if x and Path(x).is_file()),None)

def font_dirs():
    if os.name=='nt':
        return [Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts',Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'AppData/Local')))/'Microsoft/Windows/Fonts']
    if sys.platform=='darwin':
        return [Path('/Library/Fonts'),Path('/System/Library/Fonts'),Path.home()/'Library/Fonts']
    return [Path('/usr/share/fonts'),Path('/usr/local/share/fonts'),Path.home()/'.local/share/fonts',Path.home()/'.fonts']

def font_names(path):
    # Read SFNT name tables, including TTC collections, using only Python stdlib.
    with path.open('rb') as f:
        header=f.read(12)
        if len(header)<12: return set()
        if header[:4]==b'ttcf':
            count=struct.unpack('>I',header[8:12])[0]
            offsets=struct.unpack('>'+str(count)+'I',f.read(4*count))
        else: offsets=[0]
        names=set()
        for offset in offsets:
            f.seek(offset); h=f.read(12)
            for _ in range(struct.unpack('>H',h[4:6])[0]):
                record=f.read(16)
                tag,_,pos,size=struct.unpack('>4sIII',record)
                if tag!=b'name': continue
                back=f.tell(); f.seek(pos); table=f.read(size);f.seek(back)
                if len(table)<6: continue
                _,n,base=struct.unpack('>HHH',table[:6])
                for j in range(n):
                    plat,enc,lang,nid,length,off=struct.unpack('>HHHHHH',table[6+12*j:18+12*j])
                    if nid not in (1,4,6,16): continue
                    raw=table[base+off:base+off+length]
                    try: names.add(raw.decode('utf-16-be' if plat in (0,3) else 'mac_roman'))
                    except UnicodeError: pass
        return names

def installed_fonts():
    found={name:[] for name in FONTS}
    for directory in font_dirs():
        if not directory.is_dir(): continue
        for path in directory.rglob('*'):
            if path.suffix.lower() not in ('.ttf','.ttc','.otf'): continue
            try: names=font_names(path)
            except (OSError,ValueError,struct.error): continue
            for family,aliases in FONTS.items():
                if any(a in names for a in aliases): found[family].append(str(path))
    return found

def venv_ready():
    if not PYTHON.is_file(): return False
    r=call([PYTHON,'-c',"import importlib.metadata as m; print(m.version('PyMuPDF'))"])
    return r.returncode==0 and r.stdout.strip()=='1.27.2.3'

def report(office=None):
    node=shutil.which('node')
    version=call([node,'--version']).stdout.strip() if node else ''
    node_ok=bool(version and int(version.lstrip('v').split('.')[0])>=22)
    library=ROOT/'node_modules/docx/package.json'
    docx_ok=library.is_file() and json.loads(library.read_text('utf-8')).get('version')=='9.12.0'
    if docx_ok and node_ok:
        probe=call([node,ROOT/'scripts/build_word.cjs','--probe'])
        docx_ok=probe.returncode==0
    fonts=installed_fonts(); soffice=find_office(office); pdf=venv_ready()
    return {'python':sys.version.split()[0], 'python_ok':sys.version_info>=(3,11),
            'node':node,'node_version':version,'node_ok':node_ok,
            'docx_library_ok':docx_ok,'pdf_tools_ok':pdf,'soffice':soffice,
            'fonts':fonts,'missing_fonts':[k for k,v in fonts.items() if not v],
            'word_generation_ready':node_ok and docx_ok,
            'render_check_ready':bool(soffice and pdf and all(fonts.values()))}
