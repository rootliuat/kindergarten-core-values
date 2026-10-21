"""Verify DOCX formatting, render to a fresh PDF, and inspect text/bounds/fonts.
The report never claims that programmatic checks replace visual review.
"""
from pathlib import Path
import argparse, json, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as ET
from environment import PYTHON, VENV, FONTS, call, find_office, installed_fonts

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W='{'+NS['w']+'}'
FACE={'title':'方正小标宋简体','h1':'黑体','h2':'楷体_GB2312','h3':'仿宋_GB2312','body':'仿宋_GB2312'}

def xml_check(doc):
    errors=[]; warnings=[]; expected=[]; used=set()
    def check(ok,msg):
        if not ok: errors.append(msg)
    def attr(parent,path,name):
        e=parent.find(path,NS)
        return e.get(W+name) if e is not None else None
    with zipfile.ZipFile(doc) as z:
        tree=ET.fromstring(z.read('word/document.xml'))
        roots=[tree]+[ET.fromstring(z.read(n)) for n in z.namelist() if re.fullmatch(r'word/(header|footer)\d+\.xml',n)]
    titles=[]
    for root in roots:
        for p in root.findall('.//w:p',NS):
            txt=''.join(t.text or '' for t in p.findall('.//w:t',NS))
            if not txt: continue
            if root is tree: expected.append(txt)
            props=p.find('w:pPr',NS)
            if props is None: errors.append('缺段落格式：'+txt[:24]);continue
            role=attr(props,'w:pStyle','val')
            # Footer uses direct run formatting rather than a paragraph style.
            if role is None and root is not tree: role='body'
            if role not in FACE: errors.append('未识别的段落样式：'+str(role));continue
            used.add(FACE[role])
            if role=='h1': titles.append(txt)
            center=attr(props,'w:jc','val')=='center'
            check(attr(props,'w:spacing','line')=='560' and attr(props,'w:spacing','lineRule')=='exact','固定行距应为２８磅：'+txt[:24])
            check(attr(props,'w:spacing','before')=='0' and attr(props,'w:spacing','after')=='0','段前后应为０：'+txt[:24])
            if root is tree:
                if role=='title': check(center,'标题应居中')
                else:
                    check(attr(props,'w:ind','firstLineChars')==('0' if center else '200'),'首行缩进：'+txt[:24])
                    check(attr(props,'w:ind','firstLine')==('0' if center else '640'),'首行缩进磅值：'+txt[:24])
                    check(attr(props,'w:jc','val')==('center' if center else 'both' if role=='body' else 'left'),'对齐：'+txt[:24])
            for run in p.findall('.//w:r',NS):
                rp=run.find('w:rPr',NS)
                if rp is None: errors.append('缺文字格式：'+txt[:24]);continue
                check(all(attr(rp,'w:rFonts',k)==FACE[role] for k in ('ascii','hAnsi','eastAsia','cs')),'字体：'+txt[:24])
                check(attr(rp,'w:sz','val')==('44' if role=='title' else '32'),'字号：'+txt[:24])
                b=rp.find('w:b',NS)
                bold=b is not None and b.get(W+'val') not in ('false','0','off')
                check(bold==(role in ('h2','h3')),'加粗：'+txt[:24])
    check(titles==['一、课程缘起','二、课程实施','三、儿童发展','四、教师反思'],'四个一级部分与顺序')
    for table in tree.findall('.//w:tbl',NS):
        for i,row in enumerate(table.findall('w:tr',NS)):
            if i==0: check(row.find('w:trPr/w:tblHeader',NS) is not None,'表头应重复')
            check(row.find('w:trPr/w:cantSplit',NS) is not None,'表格短行不应跨页拆分')
            cells=row.findall('w:tc',NS)
            check(len(cells)==2,'默认表格必须为两列')
            for j,cell in enumerate(cells):
                if i==0 or j==0:
                    check(attr(cell,'w:tcPr/w:vAlign','val')=='center','表头、左栏应垂直居中')
                    for p in cell.findall('w:p',NS):
                        check(attr(p,'w:pPr/w:jc','val')=='center','表头、左栏应水平居中')
    for sec in tree.findall('.//w:sectPr',NS):
        check(attr(sec,'w:pgSz','w')=='11906' and attr(sec,'w:pgSz','h')=='16838','纸张应为Ａ４纵向')
    return errors,warnings,expected,used

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('docx',type=Path)
    ap.add_argument('--out',required=True,type=Path,help='该文件专用的检查输出目录')
    ap.add_argument('--soffice',help='覆盖自动发现的 LibreOffice 程序路径')
    ap.add_argument('--xml-only',action='store_true',help='只核对文档 XML，不声称完成渲染检查')
    args=ap.parse_args()
    if not args.xml_only and Path(sys.prefix).resolve()!=VENV.resolve():
        if not PYTHON.is_file(): raise SystemExit('先运行 python scripts/setup.py --install 配置 PDF 检查环境。')
        return subprocess.run([str(PYTHON),str(Path(__file__).resolve()),*sys.argv[1:]]).returncode
    doc=args.docx.resolve(); output=args.out.resolve();output.mkdir(parents=True,exist_ok=True)
    errors,warnings,expected,used=xml_check(doc)
    result={'document':str(doc),'xml_passed':not errors,'errors':errors,'warnings':warnings,'rendered':False,'visual_review':'未自动确认；请查看所有 page-*.png 后人工记录。'}
    if not args.xml_only:
        office=find_office(args.soffice)
        if not office: errors.append('未找到 LibreOffice，未进行渲染。')
        else:
            import fitz
            # Fresh temporary output avoids treating a stale PDF as current success.
            with tempfile.TemporaryDirectory(prefix='curriculum-render-') as tmp:
                tmp=Path(tmp);profile=tmp/'profile'
                r=call([office,'-env:UserInstallation='+profile.as_uri(),'--headless','--convert-to','pdf','--outdir',tmp,doc],timeout=180)
                rendered=tmp/(doc.stem+'.pdf')
                if r.returncode or not rendered.is_file():
                    errors.append('PDF 转换失败：'+r.stdout[-600:]+r.stderr[-600:])
                else:
                    import shutil
                    target=output/(doc.stem+'.pdf');shutil.copy2(rendered,target)
                    result['rendered']=True;result['pdf']=str(target)
                    pdf=fitz.open(target);result['pages']=len(pdf)
                    text=''.join(p.get_text() for p in pdf)
                    flat=lambda s:re.sub(r'\s+','',s)
                    missing=[t[:80] for t in expected if flat(t) not in flat(text)]
                    result['missing_text']=missing
                    if missing: errors.append('PDF 提取未覆盖全部正文，需核对缺字、截断或特殊字形。')
                    # A separate image directory per run prevents stale extra pages
                    # from a previous, longer document being mistaken for current output.
                    image_output=Path(tempfile.mkdtemp(prefix='pages-',dir=output))
                    result['image_directory']=str(image_output)
                    found=set(); page_info=[]; images=[]
                    for i,p in enumerate(pdf):
                        found.update(f[3] for f in p.get_fonts())
                        lines=[l for b in p.get_text('dict')['blocks'] if 'lines' in b for l in b['lines']]
                        # Allow normal glyph overhang near the 20 mm margin, but flag material overflow.
                        bad=[l['bbox'] for l in lines if l['bbox'][0]<45 or l['bbox'][2]>p.rect.width-45 or l['bbox'][1]<40 or l['bbox'][3]>p.rect.height-15]
                        if bad: errors.append(f'第{i+1}页文字超出检查边界：{bad}')
                        image=image_output/f'page-{i+1:03}.png';p.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(image);images.append(str(image))
                        page_info.append({'page':i+1,'text_lines':len(lines),'start':p.get_text()[:60],'end':p.get_text()[-60:]})
                    result['images']=images;result['page_details']=page_info;result['pdf_fonts']=sorted(found)
                    # Inspect font names actually used in this rendering, not just installed names.
                    norm=lambda s:re.sub(r'[^a-z0-9\u3400-\u9fff]','',s.lower().split('+')[-1])
                    unmatched=[family for family in used if not any(norm(a) in norm(f) for a in FONTS[family] for f in found)]
                    result['unmatched_fonts']=unmatched
                    if unmatched: errors.append('PDF 未匹配指定字体：'+str(unmatched))
                    # Contact sheets for visual layout review, no extra image libraries needed.
                    for start in range(0,len(pdf),6):
                        sheet=fitz.open();page=sheet.new_page(width=900,height=900)
                        for j in range(start,min(start+6,len(pdf))):
                            k=j-start;rect=fitz.Rect((k%3)*300,(k//3)*450,(k%3+1)*300,(k//3+1)*450)
                            page.show_pdf_page(rect,pdf,j)
                        page.get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(image_output/f'overview-{start//6+1:02}.png');sheet.close()
                    pdf.close()
    result['automated_checks_passed']=not errors
    (output/'check-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('page_details','images')},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':
    try: sys.exit(main())
    except Exception as e: print(str(e),file=sys.stderr);sys.exit(1)
