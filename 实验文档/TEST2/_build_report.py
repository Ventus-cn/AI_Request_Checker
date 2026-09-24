from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
import re, base64

ROOT = Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST2')
SOURCE = ROOT / '实验2-个人软件选题与需求分析.md'
DRAFT = ROOT / '实验2报告_第3-4部分草稿.md'
OUT = ROOT / '实验2-个人软件选题与需求分析-报告初版.docx'
IMG_USECASE = ROOT / '用例图' / '初始用例图.png'
IMG_BACK = ROOT / '项目启动截图' / '图1.项目后端启动截图.png'
IMG_FRONT = ROOT / '项目启动截图' / '图2.前端启动截图.png'
IMG_HOME = ROOT / '项目启动截图' / '图3.项目前端界面首页.png'

NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
PIC_NS = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT_NS = 'http://schemas.openxmlformats.org/package/2006/content-types'

def q(ns, tag): return f'{{{ns}}}{tag}'
def esc(s): return escape(str(s))

def run(text, bold=False, italic=False):
    props = ''
    if bold: props += '<w:b/>'
    if italic: props += '<w:i/>'
    return f'<w:r>{("<w:rPr>"+props+"</w:rPr>") if props else ""}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

def para(text='', style=None, bold=False, italic=False, keep=False):
    ppr = ''
    if style: ppr += f'<w:pStyle w:val="{style}"/>'
    if keep: ppr += '<w:keepNext/>'
    return f'<w:p>{("<w:pPr>"+ppr+"</w:pPr>") if ppr else ""}{run(text,bold,italic)}</w:p>'

def rich_para(text, style=None):
    ppr = f'<w:pStyle w:val="{style}"/>' if style else ''
    parts=[]; pos=0
    pattern=re.compile(r'(\*\*.*?\*\*|`.*?`|\[.*?\]\(.*?\))')
    for m in pattern.finditer(text):
        if m.start()>pos: parts.append(run(text[pos:m.start()]))
        token=m.group(0)
        if token.startswith('**'): parts.append(run(token[2:-2], bold=True))
        elif token.startswith('`'): parts.append(run(token[1:-1]))
        else:
            mm=re.match(r'\[(.*?)\]\((.*?)\)',token)
            parts.append(run(mm.group(1)+' ('+mm.group(2)+')' if mm else token))
        pos=m.end()
    if pos<len(text): parts.append(run(text[pos:]))
    if not parts: parts=[run('')]
    return f'<w:p>{("<w:pPr>"+ppr+"</w:pPr>") if ppr else ""}{"".join(parts)}</w:p>'

def table(rows):
    cols=max(len(r) for r in rows)
    grid=''.join('<w:gridCol w:w="1800"/>' for _ in range(cols))
    out=f'<w:tbl><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/><w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/><w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/></w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>'
    for ri,row in enumerate(rows):
        out+='<w:tr>'
        for cell in row+['']*(cols-len(row)):
            text=re.sub(r'\*\*|`','',cell.strip())
            out+=f'<w:tc><w:tcPr><w:tcW w:w="1800" w:type="dxa"/></w:tcPr>{para(text,bold=(ri==0))}</w:tc>'
        out+='</w:tr>'
    return out+'</w:tbl>'

def image_part(rel_id, name, width=5700000, height=3200000):
    cx,cy=width,height
    return f'''<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{rel_id}" name="{esc(name)}"/><a:graphic xmlns:a="{A_NS}"><a:graphicData uri="{PIC_NS}"><pic:pic xmlns:pic="{PIC_NS}"><pic:nvPicPr><pic:cNvPr id="{rel_id}" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''

def parse_md(text, start_rel=1):
    blocks=[]; lines=text.splitlines(); i=0; rel=start_rel
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c or '') for c in cells): rows.append(cells)
                i+=1
            if rows: blocks.append(('table',rows))
            continue
        m=re.match(r'^(#{1,4})\s+(.*)',line)
        if m:
            level=len(m.group(1)); text=m.group(2).strip(); style={1:'Heading1',2:'Heading2',3:'Heading3',4:'Heading4'}[level]
            blocks.append(('p',text,style)); i+=1; continue
        if line.startswith('> '): blocks.append(('p',line[2:], 'Quote')); i+=1; continue
        if re.match(r'^[-*]\s+',line): blocks.append(('p','• '+re.sub(r'^[-*]\s+','',line),'List')); i+=1; continue
        if re.match(r'^\d+\.\s+',line): blocks.append(('p',line,'List')); i+=1; continue
        blocks.append(('rich',line)); i+=1
    return blocks, rel

def add_image(blocks, path, caption, rel_id, height=3000000):
    blocks.append(('p',caption,'Caption'))
    blocks.append(('img',str(path),caption,rel_id,height))

orig=SOURCE.read_text(encoding='utf-8')
# 保留原始文档第1、2部分；第3、4部分使用已整理的报告内容，避免重复原要求。
orig=orig.split('\n## 3. 操作记录',1)[0].rstrip()+'\n'
draft=DRAFT.read_text(encoding='utf-8')
draft=draft.replace('# 实验2报告补充稿：第3、4部分\n\n> 使用说明：本文件只对应实验要求文档的第3部分“操作记录”和第4部分“实验小结”，没有改写实验要求中的第1、2部分。当前内容依据项目 README 和源代码整理；凡是需要本次实际操作才能确认的地方，统一使用“【待补充】”标记。完成报告时，将本文件内容接到你自己的第1、2部分之后，并根据实际证据替换标记。\n\n','')
# Separate source first 2 sections and draft sections
orig_blocks,_=parse_md(orig)
pre4,post4 = draft.split('## 4. 实验小结',1)
blocks,_=parse_md(pre4)
# Insert use case image after the paragraph mentioning figure placeholder
new=[]
for b in blocks:
    new.append(b)
    if b[0] in ('p','rich') and ('用例图完成后' in b[1] or '本项目用例图由报告作者' in b[1]):
        new.append(('p','图1 AI需求歧义审查器用例图','Caption'))
        new.append(('img',str(IMG_USECASE),'图1 AI需求歧义审查器用例图',3,3200000))
blocks=new
# Runtime evidence section from existing material
runtime='''## 3.7 运行环境与启动证据

本项目已在 Windows 11 环境下进行启动验证。操作系统版本为 Windows 11，版本号 10.0.26200.9457，amd64；Node.js 版本为 v24.16.0，npm 版本为 11.13.0；Java 版本为 17.0.16 LTS；后端启动脚本可找到 Apache Maven 3.9.10。前端启动命令为 `npm run dev`，默认运行地址为 `http://localhost:5173/`；后端启动命令为 `.\\run-local.ps1`，默认地址为 `http://localhost:8080`，API 前缀为 `/api`。

已有启动证据如下。图2为后端启动截图，图3为前端启动截图，图4为项目前端首页截图。截图文件保存在 TEST2\项目启动截图 目录中。
'''
runtime_blocks,_=parse_md(runtime)
blocks.extend(runtime_blocks)
blocks.append(('p','图2 项目后端启动截图','Caption')); blocks.append(('img',str(IMG_BACK),'图2 项目后端启动截图',4,3000000))
blocks.append(('p','图3 前端启动截图','Caption')); blocks.append(('img',str(IMG_FRONT),'图3 前端启动截图',5,2400000))
blocks.append(('p','图4 项目前端界面首页','Caption')); blocks.append(('img',str(IMG_HOME),'图4 项目前端界面首页',6,3200000))
# Add remaining draft 4 section
post_blocks,_=parse_md('## 4. 实验小结'+post4)
blocks.extend(post_blocks)

body=[]
for b in orig_blocks:
    if b[0]=='table': body.append(table(b[1]))
    elif b[0]=='p': body.append(para(b[1],b[2]))
    else: body.append(rich_para(b[1]))
# page break between untouched parts and operation report
body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
body.append(para('实验2报告正文（第3、4部分）','Title'))
for b in blocks:
    if b[0]=='table': body.append(table(b[1]))
    elif b[0]=='p': body.append(para(b[1],b[2]))
    elif b[0]=='rich': body.append(rich_para(b[1]))
    elif b[0]=='img': body.append(image_part(b[3],b[2],height=b[4]))

sect='<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
styles=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{NS}"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Arial" w:eastAsia="宋体"/><w:sz w:val="22"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:jc w:val="center"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>'''
for sid,size in [('Heading1',30),('Heading2',26),('Heading3',24),('Heading4',22)]:
    styles+=f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{sid}"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="{size}"/></w:rPr></w:style>'
styles+='''<w:style w:type="paragraph" w:styleId="List"><w:name w:val="List"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/></w:pPr></w:style><w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360"/></w:pPr><w:rPr><w:i/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="Caption"/><w:basedOn w:val="Normal"/><w:pPr><w:jc w:val="center"/></w:pPr><w:rPr><w:i/><w:sz w:val="20"/></w:rPr></w:style></w:styles>'''
document=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{NS}" xmlns:r="{R_NS}" xmlns:a="{A_NS}" xmlns:wp="{WP_NS}" xmlns:pic="{PIC_NS}"><w:body>{''.join(body)}{sect}</w:body></w:document>'''

rels=['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="'+REL_NS+'"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="word/styles.xml"/>']
media=[]
for idx,path in enumerate([IMG_USECASE,IMG_BACK,IMG_FRONT,IMG_HOME], start=1):
    rid=idx+2; name=f'image{idx}.png'; rels.append(f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>'); media.append((name,path))
rels.append('</Relationships>')
content_types=f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="{CT_NS}"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
root_rels='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="'+REL_NS+'"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml',content_types)
    z.writestr('_rels/.rels',root_rels)
    z.writestr('word/document.xml',document)
    z.writestr('word/styles.xml',styles)
    z.writestr('word/_rels/document.xml.rels',''.join(rels))
    for name,path in media: z.writestr('word/media/'+name,path.read_bytes())
print(OUT)
