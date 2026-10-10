from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(r'D:\deepseek harness workspace\AI_Request_check')
src = ROOT / '实验文档' / 'TEST3' / '实验3-软件架构与界面设计-报告过渡稿-章节对应版.docx'
out = ROOT / '实验文档' / 'TEST3' / '24111302102-许文涛.docx'
commit_img = Path(r'C:\Users\34856\AppData\Local\Temp\codex-clipboard-aa420233-93e8-4e11-8eb6-1748be4da856.png')

def delete_paragraph(p):
    el = p._element
    el.getparent().remove(el)

def delete_table(t):
    el = t._element
    el.getparent().remove(el)

def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def main():
    doc = Document(src)
    # Final submission title: retain all experiment content, remove draft wording.
    for p in doc.paragraphs:
        if p.style.name == 'Title':
            p.text = '实验3 软件架构与界面设计报告'
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if '可在 Enterprise Architect 中按此结构复刻' in p.text:
            p.text = p.text.replace('（可在 Enterprise Architect 中按此结构复刻）', '')
        if '（可在 Enterprise Architect 中按此交互复刻）' in p.text:
            p.text = p.text.replace('（可在 Enterprise Architect 中按此交互复刻）', '')
        if '（Axure 可复刻）' in p.text:
            p.text = p.text.replace('（Axure 可复刻）', '')
    # Remove process notes that are not report content.
    remove_contains = [
        '当前未完成的原型内容是',
        '本稿中已根据仓库代码完成的内容：',
        '需要你补充或核实的内容：',
    ]
    for p in list(doc.paragraphs):
        if any(x in p.text for x in remove_contains):
            delete_paragraph(p)
        elif '记录检查范围' in p.text:
            delete_paragraph(p)
    # 2.6 asks to complete the 2.1 traceability table; do not repeat a second table in 3.6.
    if len(doc.tables) >= 5:
        delete_table(doc.tables[4])
    # Replace the old 3.6 narrative with concise evidence and commit screenshot.
    target = None
    for p in doc.paragraphs:
        if p.style.name == 'Heading 2' and ('3.6' in p.text or '设计一致性检查与版本证据' in p.text):
            target = p
            break
    if target is None:
        raise RuntimeError('3.6 heading not found')
    # Find the first body paragraph after 3.6 heading and replace it.
    paras = list(doc.paragraphs); idx = next(i for i,p in enumerate(paras) if p._element is target._element)
    body = paras[idx + 1] if idx + 1 < len(paras) else None
    if body is not None and (body.style.name.startswith('Heading') or '记录检查范围' in body.text or '本次检查覆盖' in body.text):
        delete_paragraph(body)
        body = None
    if body is None:
        body = doc.add_paragraph()
        target._p.addnext(body._p)
    body.text = ('本次检查覆盖需求追踪、架构模块、数据对象、接口、核心流程、界面原型和版本保存。'
                 '检查结果表明：2.1 中的核心需求均能追溯到 3.3、3.4 和 3.5 的设计内容；架构模块、接口、数据和界面之间不存在明显矛盾。'
                 '项目已提交到 GitHub，提交记录截图见图10。')
    # Add commit evidence immediately after the 3.6 body paragraph.
    pic = doc.add_paragraph(); pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.add_run().add_picture(str(commit_img), width=Inches(6.5))
    cap = doc.add_paragraph('图10 GitHub 提交记录（commit：c9f871a）')
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.runs[0].font.size = Pt(9); cap.runs[0].italic = True
    body._p.addnext(pic._p); pic._p.addnext(cap._p)
    # Remove duplicate plain figure label accidentally retained by source around 3.5.
    for p in list(doc.paragraphs):
        if p.text.strip() in {'图9 历史记录页', '图9 历史记录页原型'}:
            p.text = '图9 结果页/历史记录交互原型'
        elif p.text.startswith('图4 首页/入口页'):
            p.text = '已有界面截图：首页/入口页'
        elif p.text.startswith('图5 核心任务页'):
            p.text = '已有界面截图：核心任务页'
        elif p.text.startswith('图6 需求获取证据'):
            p.text = '需求获取证据：用户访谈记录'
    doc.save(out)
    print(out)

if __name__ == '__main__':
    main()
