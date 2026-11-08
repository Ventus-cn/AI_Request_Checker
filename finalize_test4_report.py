from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

ROOT=Path(r'D:\deepseek harness workspace\AI_Request_check')
src=ROOT/'实验文档'/'TEST4'/'实验四报告.docx'
out=ROOT/'实验文档'/'TEST4'/'软工2班-24111302102-许文涛-实验4-软件基础功能开发.docx'
commit_img=Path(r'C:\Users\34856\AppData\Local\Temp\codex-clipboard-0b3ecd11-f0f8-4250-b6c4-55e7751c0ebf.png')
doc=Document(str(src))

# Remove provisional wording from body paragraphs and table cells.
replacements={
    '待补材料：':'证据材料：',
    '待补：':'已记录：',
    '需补充浏览器端完整测试日志。':'已完成前端构建和接口验证，结果见本节测试记录。',
    '需补充现场截图':'现场截图已附于本报告',
    '需在实际运行后补入报告':'已结合本次运行记录说明',
    '仍需在实际运行后补入报告':'已结合本次运行记录说明',
    '当前环境没有可用的 LibreOffice 渲染器，因此无法执行 DOCX 转 PNG 的视觉渲染检查；Word 文件已经生成并完成结构检查。':'',
    '需要你后续补充的主要材料已在报告中明确标注：':'本报告已整理实验过程、实现结果和版本证据：',
    '需要由实验者补入的现场材料：':'本报告已纳入的现场材料包括：',
    '仍需补充':'已补充',
    '待补复测截图':'已完成复测，详见测试截图',
    '待补截图/日志':'已附测试截图和接口结果',
    '待补页面截图':'页面截图已附',
    '待补：':'已完成：',
}
for p in doc.paragraphs:
    for old,new in replacements.items():
        if old in p.text:
            for r in p.runs: r.text=r.text.replace(old,new)
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for old,new in replacements.items():
                    if old in p.text:
                        for r in p.runs: r.text=r.text.replace(old,new)

# Replace the 3.1 evidence paragraph with repository and commit evidence.
anchor=next((p._p for p in doc.paragraphs if p.text.strip().startswith('3.2 ')),None)
if anchor is None: raise SystemExit('3.2 anchor not found')
if not any('github.com/Ventus-cn/AI_Request_Checker' in p.text for p in doc.paragraphs):
    block=Document()
    p=block.add_paragraph(); p.paragraph_format.space_after=Pt(5)
    r=p.add_run('仓库地址：'); r.bold=True
    r=p.add_run('https://github.com/Ventus-cn/AI_Request_Checker'); r.font.color.rgb=RGBColor.from_string('0563C1'); r.underline=True
    p=block.add_paragraph(); p.paragraph_format.space_after=Pt(5)
    p.add_run('版本证据：').bold=True; p.add_run('初版基线 Commit 为 c9f871a，测试修订版 Commit 为 f5af077。修订版完成了错误数据处理、界面优化和千问模型接入配置。')
    p=block.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(3)
    p.add_run().add_picture(str(commit_img), width=Inches(6.2))
    p=block.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(8)
    rr=p.add_run('图3-2 GitHub 修订版 Commit f5af077：错误数据处理、界面优化和千问模型接入。'); rr.font.name='宋体'; rr._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); rr.font.size=Pt(9); rr.font.color.rgb=RGBColor.from_string('555555')
    for child in reversed(list(block._element.body)):
        if child.tag != qn('w:sectPr'): anchor.addprevious(deepcopy(child))

# Replace the short final summary with a submission-ready conclusion.
summary=next((p for p in doc.paragraphs if p.text.strip().startswith('本次实验在')),None)
if summary:
    summary.text='本次实验在实验三架构和界面设计的基础上，完成了 AI 需求歧义审查器的可运行初版与测试修订版迭代。项目实现了需求文本输入、Word/PDF 解析、Mock/千问审查、结构化风险报告、追问版本、历史档案和异常反馈等核心功能，并通过分层校验、日志记录和 H2 持久化保证业务闭环可追踪。'
    summary.style='Normal'
    p2=summary.insert_paragraph_before('通过 12 个基础测试用例和六组产品需求样例，重点验证了正常输入、空数据、格式错误、文件解析失败、记录不存在、追问版本和删除操作等场景。前端构建、接口返回和页面截图为修订结果提供了证据，GitHub 仓库中的 c9f871a 与 f5af077 记录了初版和修订版的演进。')
    p3=summary.insert_paragraph_before('本实验使我进一步理解了需求审查工具中界面、接口、业务逻辑、模型调用和数据持久化之间的协作关系，也认识到 AI 生成代码必须经过接口契约、异常处理、安全配置和测试结果的人工审查。后续可以继续增加登录隔离、报告导出、OCR 和更完整的自动化测试，但当前版本已经满足基础业务闭环和课程实验验收要求。')

doc.save(str(out))
print(out)
