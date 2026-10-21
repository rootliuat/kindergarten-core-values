const fs = require('fs');
const path = require('path');
let lib;
try { lib = require(path.join(__dirname, '../node_modules/docx')); } catch {
  console.error('缺少技能目录内的 docx 库。先运行：python scripts/setup.py --install');
  process.exit(2);
}
if (process.argv[2] === '--probe') { console.log('docx loaded from skill directory'); process.exit(0); }
const {Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, LineRuleType, TableLayoutType, Footer,
  PageNumber, ExternalHyperlink} = lib;
const [input, output] = process.argv.slice(2);
if (!input || !output) throw Error('用法：node build_word.cjs 输入.json 输出.docx');
const data = JSON.parse(fs.readFileSync(input, 'utf8').replace(/^\uFEFF/, ''));
const expected = ['一、课程缘起', '二、课程实施', '三、儿童发展', '四、教师反思'];
if (!data.title || JSON.stringify(data.sections?.map(s => s.title)) !== JSON.stringify(expected))
  throw Error('需要标题及规定的四个一级部分');
const font = {title:'方正小标宋简体', h1:'黑体', h2:'楷体_GB2312', h3:'仿宋_GB2312', body:'仿宋_GB2312'};
const face = n => ({ascii:n, hAnsi:n, eastAsia:n, cs:n});
const spacing = {before:0, after:0, line:560, lineRule:LineRuleType.EXACT};
function run(text, role='body', extra={}) {
  return new TextRun({text, font:face(font[role]), size:role==='title'?36:32,
    bold:role==='h2'||role==='h3', language:{value:'zh-CN',eastAsia:'zh-CN'}, ...extra});
}
function para(text, role='body', url, centered=false, pageBreakBefore=false, lines) {
  if (typeof text !== 'string' || /[\r\n]/.test(text)) throw Error('段落必须是无换行的字符串；多段落请用多个 blocks 或单元格数组');
  let parts=[run(text,role)];
  if (lines) {
    if (!Array.isArray(lines) || lines.length<1 || lines.some(t=>typeof t!=='string'||/[\r\n]/.test(t)) || lines.join('')!==text)
      throw Error('titleLines 必须是分行字符串数组，拼接后与 title 相同');
    parts=lines.map((t,i)=>run(t,role,i?{break:1}:{}));
  }
  const children = url ? [new ExternalHyperlink({link:url, children:parts})] : parts;
  return new Paragraph({style:role, children, spacing, pageBreakBefore,
    overflowPunctuation:false,
    alignment:(centered||role==='title')?AlignmentType.CENTER:role==='body'?AlignmentType.JUSTIFIED:AlignmentType.LEFT,
    ...((role==='body'||role.startsWith('h'))?{indent:{firstLine:centered?0:640, firstLineChars:centered?0:200}}:{}),
    ...(role.startsWith('h')?{keepNext:true,keepLines:true,outlineLevel:Number(role[1])-1}:{}),
  });
}
function table(rows) {
  if (!Array.isArray(rows) || rows.length<2 || rows.some(r=>r.length!==2))
    throw Error('表格须为两列，含表头及至少一行正文');
  const widths=[2200,7438];
  return new Table({width:{size:9638,type:WidthType.DXA}, columnWidths:widths,
    layout:TableLayoutType.FIXED,
    rows:rows.map((r,i)=>new TableRow({tableHeader:i===0,cantSplit:true,
      children:r.map((v,j)=>new TableCell({verticalAlign:i===0||j===0?'center':'top',width:{size:widths[j],type:WidthType.DXA},
        margins:{top:80,bottom:80,left:100,right:100},
        children:(Array.isArray(v)?v:[v]).map(t=>para(String(t),'body',undefined,i===0||j===0))}))}))});
}
const children=[para(data.title,'title',undefined,false,false,data.titleLines)];
for (const s of data.sections) {
  children.push(para(s.title,'h1',undefined,false,!!s.pageBreakBefore));
  for (const b of s.blocks) {
    if (b.table) children.push(table(b.table));
    else {
      if (b.level && ![2,3].includes(b.level)) throw Error('只允许二、三级标题');
      children.push(para(b.text, b.level?'h'+b.level:'body', b.url,false,!!b.pageBreakBefore));
    }
  }
}
const doc=new Document({
  title:data.title, creator:'幼儿园课程设计',
  styles:{default:{document:{run:{font:face(font.body),size:32,bold:false},paragraph:{spacing}}},
    paragraphStyles:Object.keys(font).map(role=>({id:role,name:role,basedOn:'Normal',
      next:'body',run:{font:face(font[role]),size:role==='title'?36:32,bold:['h2','h3'].includes(role)},
      paragraph:{spacing,...((role==='body'||role.startsWith('h'))?{indent:{firstLine:640,firstLineChars:200}}:{}),...(role.startsWith('h')?{outlineLevel:Number(role[1])-1}:{})}}))},
  sections:[{properties:{page:{size:{width:11906,height:16838},
    margin:{top:1134,bottom:1134,left:1134,right:1134,footer:567}}},
    footers:{default:new Footer({children:[new Paragraph({spacing,alignment:AlignmentType.CENTER,
      children:[run('第'),run('','body',{children:[PageNumber.CURRENT]}),run('页')]})]})},children}]
});
Packer.toBuffer(doc).then(b=>{fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});fs.writeFileSync(output,b);console.log(output);})
  .catch(e=>{console.error(e);process.exitCode=1;});
