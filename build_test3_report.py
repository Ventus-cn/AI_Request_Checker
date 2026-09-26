from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(r'D:\deepseek harness workspace\AI_Request_check')
OUT = ROOT / '实验文档' / 'TEST3'
OUT.mkdir(exist_ok=True)
FONT = r'C:\Windows\Fonts\msyh.ttc'

def fnt(size, bold=False):
    return ImageFont.truetype(FONT, size=size, index=0)

def box(draw, xy, text, fill='#F4F7F8', outline='#5F7D86', width=2, size=22):
    x1,y1,x2,y2=xy; draw.rounded_rectangle(xy, radius=12, fill=fill, outline=outline, width=width)
    lines=[]
    for line in text.split('\n'):
        words='';
        for ch in line:
            if draw.textlength(words+ch, font=fnt(size)) < (x2-x1-30): words += ch
            else: lines.append(words); words=ch
        lines.append(words)
    y=y1+(y2-y1-len(lines)*(size+6))//2
    for line in lines:
        w=draw.textlength(line,font=fnt(size)); draw.text((x1+(x2-x1-w)/2,y),line,font=fnt(size),fill='#17212B'); y+=size+6

def arrow(draw, a, b, color='#176B87', width=4):
    draw.line([a,b], fill=color, width=width)
    import math
    ang=math.atan2(b[1]-a[1],b[0]-a[0]); L=14
    p1=(b[0]-L*math.cos(ang-0.5),b[1]-L*math.sin(ang-0.5)); p2=(b[0]-L*math.cos(ang+0.5),b[1]-L*math.sin(ang+0.5))
    draw.polygon([b,p1,p2],fill=color)

def save_context(path):
    im=Image.new('RGB',(1500,820),'white'); d=ImageDraw.Draw(im)
    box(d,(70,310,350,500),'用户\n学生/教师',fill='#EAF4F6')
    box(d,(540,240,960,570),'AI 需求歧义审查器\n前端：Vue 3 + Element Plus\n后端：Spring Boot REST\n数据：H2 历史记录',fill='#EEF6F2')
    box(d,(1130,120,1430,300),'模型服务\nMock / 千问云端',fill='#FFF5DF')
    box(d,(1130,420,1430,600),'本地文件\nDOCX / 文字型 PDF',fill='#F6EFFA')
    arrow(d,(350,405),(540,405)); arrow(d,(960,310),(1130,210)); arrow(d,(960,470),(1130,510))
    d.text((410,360),'输入、查看报告、追问',font=fnt(22),fill='#176B87'); d.text((970,250),'AI 审查请求/结构化结果',font=fnt(20),fill='#176B87'); d.text((970,495),'上传与文本解析',font=fnt(20),fill='#176B87')
    im.save(path)

def save_arch(path):
    im=Image.new('RGB',(1500,940),'white'); d=ImageDraw.Draw(im)
    box(d,(60,110,420,350),'表示层\nReview / Result / History\nElement Plus 组件',fill='#EAF4F6')
    box(d,(60,500,420,760),'接口层\nReviewController\n/api/reviews',fill='#EAF4F6')
    box(d,(550,110,930,350),'应用服务层\nReviewService\nDocumentService',fill='#EEF6F2')
    box(d,(550,500,930,760),'AI 能力层\nAiReviewService\nMock / Qwen 适配',fill='#FFF5DF')
    box(d,(1060,110,1440,350),'持久化层\nReviewRepository\nReview 实体',fill='#F6EFFA')
    box(d,(1060,500,1440,760),'外部依赖\nH2 文件数据库\nDOCX/PDF 解析库',fill='#F6EFFA')
    for a,b in [((240,350),(240,500)),((420,230),(550,230)),((420,630),(550,630)),((930,230),(1060,230)),((930,630),(1060,630)),((740,350),(740,500))]: arrow(d,a,b)
    d.text((650,40),'分层 + MVC 风格总体架构',font=fnt(30,True),fill='#17212B'); im.save(path)

def save_modules(path):
    im=Image.new('RGB',(1500,980),'white'); d=ImageDraw.Draw(im)
    d.text((515,35),'模块结构图：功能模块与代码模块对应关系',font=fnt(30,True),fill='#17212B')
    box(d,(570,90,930,190),'需求歧义审查器',fill='#DCEEF2',size=24)
    box(d,(90,280,390,430),'审查工作区\nReview 页面\n输入/上传/模式选择',fill='#EAF4F6',size=20)
    box(d,(600,280,900,430),'结果与追问\nResult 页面\n筛选/确认/追问',fill='#EAF4F6',size=20)
    box(d,(1110,280,1410,430),'历史记录\nHistory 页面\n查看/删除/版本',fill='#EAF4F6',size=20)
    box(d,(90,610,390,790),'接口模块\nReviewController\nREST 路由与错误响应',fill='#EEF6F2',size=19)
    box(d,(600,610,900,790),'审查业务模块\nReviewService\n编排、版本与校验',fill='#EEF6F2',size=19)
    box(d,(1110,610,1410,790),'文档与 AI 模块\nDocumentService\nAiReviewService',fill='#FFF5DF',size=19)
    box(d,(600,850,900,950),'数据模块\nReview / Repository / H2',fill='#F6EFFA',size=19)
    for a,b in [((750,190),(240,280)),((750,190),(750,280)),((750,190),(1260,280)),((240,430),(240,610)),((750,430),(750,610)),((1260,430),(1260,610)),((240,790),(750,850)),((750,790),(750,850)),((1260,790),(750,850))]: arrow(d,a,b)
    im.save(path)

def save_flow(path):
    im=Image.new('RGB',(1500,900),'white'); d=ImageDraw.Draw(im)
    nodes=[('输入需求\n粘贴或上传',80,110),('解析并校验\n非空/格式/大小',430,110),('调用 AI 审查\nMock 或千问',780,110),('结构化校验\n风险/问题/验收标准',1130,110),('结果页\n筛选与人工确认',780,500),('保存历史\nH2 版本',1130,500),('失败处理\n提示并返回编辑',430,500)]
    for t,x,y in nodes: box(d,(x,y,x+270,y+150),t,fill='#EEF6F2' if '失败' not in t else '#FCEFED')
    for a,b in [((350,185),(430,185)),((700,185),(780,185)),((1050,185),(1130,185)),((1265,260),(915,500)),((1050,575),(1130,575)),((565,260),(565,500)),((700,575),(565,575))]: arrow(d,a,b)
    d.text((625,35),'核心用户流程：一次需求审查与结果确认',font=fnt(30,True),fill='#17212B'); im.save(path)

def save_class(path):
    im=Image.new('RGB',(1700,1050),'white'); d=ImageDraw.Draw(im)
    d.text((610,25),'核心类图：审查记录、服务与控制器关系',font=fnt(30,True),fill='#17212B')
    box(d,(60,130,420,430),'Review\n----------------\nid: UUID\ntext: String\nmode: String\nreportJson: String\nversionsJson: String\ncreatedAt: DateTime',fill='#F6EFFA',size=18)
    box(d,(640,130,1050,390),'ReviewController\n----------------\ncreate(req)\nupload(file)\nfollow(id, question)\nhistory() / get(id)\ndelete(id)',fill='#EAF4F6',size=18)
    box(d,(640,520,1050,800),'ReviewService\n----------------\ncreate(request)\nfollow(id, question)\nhistory() / get(id)\ndelete(id)\nresponse(review)',fill='#EEF6F2',size=18)
    box(d,(1250,120,1630,390),'ReviewRepository\n----------------\nfindById(id)\nsave(review)\nfindAll()\ndeleteById(id)',fill='#F6EFFA',size=18)
    box(d,(1190,530,1630,800),'AiReviewService\n----------------\nreview(text, mode)\nMock/Qwen adapter\nJSON schema validation',fill='#FFF5DF',size=18)
    box(d,(80,650,430,900),'DocumentService\n----------------\nextract(file)\nDOCX/PDF text\nformat/size errors',fill='#FFF5DF',size=18)
    arrow(d,(420,260),(640,260)); arrow(d,(845,390),(845,520)); arrow(d,(1050,260),(1250,260)); arrow(d,(1050,660),(1190,660)); arrow(d,(640,700),(430,770)); arrow(d,(640,300),(430,300))
    d.text((455,225),'调用',font=fnt(20),fill='#176B87'); d.text((855,455),'编排',font=fnt(20),fill='#176B87'); d.text((1080,225),'持久化',font=fnt(20),fill='#176B87'); d.text((1080,625),'AI 调用',font=fnt(20),fill='#176B87'); d.text((450,735),'文档解析',font=fnt(20),fill='#176B87')
    im.save(path)

def save_sequence(path):
    im=Image.new('RGB',(1750,1100),'white'); d=ImageDraw.Draw(im)
    actors=[('用户',120),('前端',410),('ReviewController',720),('ReviewService',1030),('AiReviewService',1340),('H2',1620)]
    for name,x in actors:
        d.text((x-45,30),name,font=fnt(22,True),fill='#17212B'); d.line((x,90,x,1020),fill='#AAB8BE',width=2)
    msgs=[(120,410,150,'1. 输入需求/点击开始审查'),(410,720,260,'2. POST /api/reviews'),(720,1030,370,'3. create(request)'),(1030,1340,480,'4. review(text, mode)'),(1340,1030,590,'5. 返回结构化报告'),(1030,1620,700,'6. save(review)'),(1620,1030,810,'7. 保存成功'),(1030,720,900,'8. 返回 ReviewResponse'),(720,410,990,'9. 展示结果页')]
    for x1,x2,y,t in msgs:
        arrow(d,(x1,y),(x2,y)); d.text(((x1+x2)//2-100,y-28),t,font=fnt(17),fill='#176B87')
    d.text((620,1035),'正常路径：提交需求 → 后端编排 → AI 分析 → H2 保存 → 前端展示',font=fnt(23,True),fill='#17212B'); im.save(path)

def proto_base(path, title, step, body_lines, right_lines):
    im=Image.new('RGB',(1600,980),'#F4F6F8'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,1600,76),fill='white'); d.line((0,76,1600,76),fill='#E5E9ED',width=2)
    d.rounded_rectangle((35,20,73,58),radius=8,fill='#176B87'); d.text((48,28),'✓',font=fnt(22,True),fill='white')
    d.text((88,20),'需求歧义审查器',font=fnt(22,True),fill='#17212B'); d.text((88,47),'把不确定性变成可验证的任务',font=fnt(13),fill='#8A969F')
    d.text((1320,27),'审查',font=fnt(16,True),fill='#176B87'); d.text((1430,27),'历史记录',font=fnt(16),fill='#66737D')
    d.text((70,130),step,font=fnt(15,True),fill='#176B87'); d.text((70,165),title,font=fnt(34,True),fill='#17212B')
    d.text((70,220),'AI 需求歧义审查器 / 原型界面',font=fnt(16),fill='#74818B')
    d.rounded_rectangle((70,290,1060,900),radius=10,fill='white',outline='#E5E9ED',width=2)
    y=325
    for line in body_lines:
        d.text((105,y),line,font=fnt(22 if len(line)<28 else 18),fill='#33424A'); y+=58
    d.rounded_rectangle((1110,290,1530,900),radius=10,fill='white',outline='#E5E9ED',width=2)
    y=335
    for line in right_lines:
        d.text((1150,y),line,font=fnt(18),fill='#52616A'); y+=52
    im.save(path)

def save_prototypes(folder):
    p1=folder/'图7-界面原型-首页.png'; p2=folder/'图8-界面原型-核心审查页.png'; p3=folder/'图9-界面原型-结果页.png'
    proto_base(p1,'先把需求说清楚，再开始开发','01  输入需求',['需求内容','粘贴课程作业需求，或上传 Word / 文字型 PDF','用户可以尽快完成注册，并方便地查看自己的订单……','[ 上传 Word / PDF ]     支持 .docx、.pdf，单文件不超过 10MB'],['审查设置','审查模式：全面审查','● 原文引用        已启用','● AI 分析          Mock / 千问','● 历史保存        H2 数据库','[ 开始审查 ]'])
    proto_base(p2,'需求审查任务','02  执行审查',['需求内容（可编辑）','用户可以尽快完成注册，并方便地查看自己的订单。','审查模式：全面审查','[ 开始审查 ]   [ 清空 ]'],['处理状态','正在解析需求文本…','AI 分析：Mock / 千问','完成后自动进入结果页','错误时返回编辑并提示原因'])
    proto_base(p3,'审查结果','03  查看结果',['高风险  2 个高风险问题','“尽快完成注册”缺少时间边界','缺失条件：完成时间、失败处理','可测试验收标准：5 秒内返回结果'],['问题清单','全部 5   模糊表达 2','边界条件 1   不可测试 1','[ 修改后重新审查 ]','继续追问：先处理哪个问题？'])
    return p1,p2,p3

def set_cell_shading(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement('w:shd'); shd.set(qn('w:fill'),fill); tcPr.append(shd)
def set_cell_text(cell, text, bold=False):
    cell.text=''; p=cell.paragraphs[0]; r=p.add_run(str(text)); r.bold=bold; r.font.name='微软雅黑'; r.font.size=Pt(9); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
def table(doc, headers, rows, widths=None):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'
    for i,h in enumerate(headers): set_cell_text(t.rows[0].cells[i],h,True); set_cell_shading(t.rows[0].cells[i],'D9EAF0')
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row): set_cell_text(cells[i],v)
    return t

def add_pic(doc, path, caption, width=6.3):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(path),width=Inches(width))
    cp=doc.add_paragraph(caption); cp.alignment=WD_ALIGN_PARAGRAPH.CENTER; cp.runs[0].italic=True; cp.runs[0].font.size=Pt(9)

def main():
    md=(OUT/'实验3-软件架构与界面设计.md').read_text(encoding='utf-8')
    first_two=md.split('## 3. 操作记录')[0].rstrip()
    ctx=OUT/'图1-软件与外部环境关系图.png'; arch=OUT/'图2-总体架构图.png'; modules=OUT/'图3-模块结构图.png'; flow=OUT/'图4-核心流程图.png'; classimg=OUT/'图5-核心类图.png'; seq=OUT/'图6-核心顺序图.png'
    save_context(ctx); save_arch(arch); save_modules(modules); save_flow(flow); save_class(classimg); save_sequence(seq); p1,p2,p3=save_prototypes(OUT)
    doc=Document(); sec=doc.sections[0]; sec.top_margin=Inches(.7); sec.bottom_margin=Inches(.7); sec.left_margin=Inches(.8); sec.right_margin=Inches(.8)
    styles=doc.styles; styles['Normal'].font.name='微软雅黑'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'微软雅黑'); styles['Normal'].font.size=Pt(10.5)
    p=doc.add_paragraph(); p.style='Title'; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('实验3 软件架构与界面设计报告（过渡稿）')
    p=doc.add_paragraph('项目：AI 需求歧义审查器'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    for line in first_two.splitlines():
        if line.startswith('# '): continue
        if line.startswith('## '): doc.add_heading(line[3:],1)
        elif line.startswith('### '): doc.add_heading(line[4:],2)
        elif line.startswith('- '): doc.add_paragraph(line[2:],style='List Bullet')
        elif line.strip(): doc.add_paragraph(line)
    doc.add_heading('3. 操作记录',1)
    doc.add_paragraph('以下记录围绕实验2确定的核心流程“提交需求文本并获得结构化歧义审查报告”展开。图中方框表示本软件或外部依赖，箭头表示数据或调用方向。')
    doc.add_heading('3.1 需求与设计对应表',2)
    table(doc,['需求编号','核心需求/验收条件','设计内容','对应图或文档'],[
        ['R1','用户可粘贴需求文本并启动审查；空文本应提示错误','Review 页面输入区、非空校验、POST /api/reviews','图4、接口表'],
        ['R2','支持 DOCX/文字型 PDF 上传并回填文本；非法格式或超限应失败','DocumentService 解析、上传接口、前端上传状态','图1、图4'],
        ['R3','报告应包含原文引用、风险等级、问题类型、待确认问题和验收标准','AiReviewService 结构化 JSON、结果页筛选与人工确认','图2、图3、图5'],
        ['R4','用户可追问并保留历史版本','follow-up 接口、Review.versionsJson、结果页追问区','接口表、数据模型说明'],
        ['R5','结果可按问题类型筛选，便于定位返工风险','前端 visibleIssues 过滤、结果页问题卡片','图5'],
        ['NFR1','API Key 不暴露给浏览器，模型异常需可理解地反馈','模型调用仅在后端；异常统一转为 error 响应','架构决策 ADR-03'],
        ['NFR2','本地演示无需外部模型服务','AI_MODE=mock，保留 Qwen 适配替代路径','ADR-04']])
    doc.add_heading('3.2 技术选型与架构决策',2)
    table(doc,['决策项','候选方案','最终选择','理由与不足'],[
        ['前端','Vue 3 / React','Vue 3 + Vite + Element Plus','已有项目基础、组件丰富、适合快速原型；不足是依赖生态版本需维护'],
        ['后端','Spring Boot / Node.js','Spring Boot 3 + Java 17','熟悉 Java，REST、文件上传和异常处理清晰；不足是启动和依赖体积较大'],
        ['数据','H2 / SQLite / 云数据库','H2 文件数据库','零配置、适合课程演示和历史版本；不足是单机并发与持久化能力有限'],
        ['AI 接入','仅 Mock / 直接前端调用 / 后端适配','后端 AiReviewService 适配 Mock 与千问','保护 API Key，便于替换模型；不足是模型输出仍需加强约束'],
        ['架构风格','单体脚本 / 分层 MVC','分层 + MVC','界面、接口、业务、AI、数据边界清楚；不足是当前规模下存在少量样板代码']])
    doc.add_paragraph('ADR-01：选择 Vue 3 + Spring Boot 分层架构，解决课程原型需要快速迭代且保持模块边界的问题。ADR-02：选择 H2 文件数据库，降低部署成本。ADR-03：模型调用放在后端，避免密钥泄露。ADR-04：模型服务不可用时使用 Mock 报告作为替代方案，保证核心流程仍可演示。')
    doc.add_heading('3.3 软件架构与模块设计',2)
    doc.add_paragraph('本节对应实验内容 2.3，采用软件与外部环境关系图、总体架构图和模块结构图逐层说明系统边界、分层职责和模块依赖。')
    add_pic(doc,ctx,'图1 软件与外部环境关系图')
    doc.add_paragraph('用户、前端与后端属于本软件；Mock/Qwen 模型服务、DOCX/PDF 文件和 H2 运行文件属于外部依赖或运行环境。当前默认使用 Mock，接入千问时由后端访问云端模型服务。')
    add_pic(doc,arch,'图2 总体架构图')
    doc.add_paragraph('总体架构图与模块结构图的对应关系：表示层对应审查工作区、结果与追问、历史记录三个前端模块；接口层对应 ReviewController；应用服务层对应 ReviewService；AI 能力层对应 AiReviewService，文档解析由 DocumentService 负责；持久化层对应 Review、ReviewRepository 和 H2。模块之间按“页面模块→接口模块→业务/能力模块→数据模块”方向调用，外部模型服务和 DOCX/PDF 解析库只通过 AI 或文档模块进入系统。')
    add_pic(doc,modules,'图3 模块结构图')
    table(doc,['模块','主要职责','依赖模块'],[
        ['审查工作区','输入需求、上传文件、选择审查模式、展示加载和错误状态','接口模块'],
        ['结果与追问','展示风险与问题、按类型筛选、提交追问、人工确认','接口模块'],
        ['历史记录','查询、打开和删除历史审查记录','接口模块'],
        ['接口模块','提供 REST 路由、参数接收和统一错误响应','审查业务模块、文档与 AI 模块'],
        ['审查业务模块','编排审查、保存当前报告、维护追问版本','文档与 AI 模块、数据模块'],
        ['文档与 AI 模块','解析 DOCX/PDF，调用 Mock 或 Qwen 并生成结构化结果','外部文件、模型服务'],
        ['数据模块','保存 Review、报告 JSON、版本 JSON 和创建时间','H2 文件数据库']])
    table(doc,['参与方','主要职责','结果检查者'],[
        ['用户','提供需求、选择模式、查看报告、确认待补条件、追问或重新提交','用户最终确认需求是否可接受'],
        ['普通程序','文本解析、格式/空值校验、接口编排、历史保存、筛选展示','后端校验字段和请求错误'],
        ['模型','识别模糊表达、边界缺口、冲突、权限和可测试性问题，生成结构化建议','程序做 JSON 字段校验，用户做业务确认'],
        ['工具/外部依赖','DOCX/PDF 解析、H2 持久化、云端 Qwen（可选）','程序检查解析异常、超时和服务错误']])
    doc.add_heading('3.4 数据、接口与核心流程设计',2)
    doc.add_paragraph('核心数据对象为 Review：id（UUID，主键）、text（原始需求文本）、mode（审查模式）、reportJson（当前结构化报告）、versionsJson（追问前版本数组）、createdAt（创建时间）。报告内部包含 summary、riskLevel、counts 和 issues；issues 包含引用、位置、解释、缺失条件、待确认问题、验收标准、相关角色及返工风险。原始需求可能包含课程项目内容，不应上传敏感个人信息；当前版本未实现登录和多用户隔离。')
    table(doc,['接口','调用者/提供者','输入','输出','失败情况'],[
        ['POST /api/reviews','前端 / ReviewController','text、mode','ReviewResponse（报告与版本）','空文本、AI 异常、保存失败'],
        ['POST /api/reviews/upload','前端 / ReviewController + DocumentService','multipart file（DOCX/PDF）','fileName、text、characters','格式不支持、解析失败、文件超限'],
        ['POST /api/reviews/{id}/follow-up','结果页 / ReviewService','question','更新后的 ReviewResponse','记录不存在、追问为空、模型异常'],
        ['GET /api/reviews、GET /api/reviews/{id}','历史页 / ReviewService','id（详情接口）','历史摘要或完整报告','记录不存在'],
        ['DELETE /api/reviews/{id}','历史页 / ReviewController','id','204 No Content','记录不存在或删除失败']])
    doc.add_paragraph('正常调用示例：POST /api/reviews，JSON 为 {"text":"用户可以尽快完成注册","mode":"全面审查"}，返回 200 和包含 issues 的结构化报告。错误调用示例：POST /api/reviews，JSON 为 {"text":"   ","mode":"全面审查"}，前端阻止提交并显示“请先输入或上传需求文本”；若服务端异常，则返回 400 与 {"error":"..."}。')
    add_pic(doc,flow,'图4 核心流程图')
    add_pic(doc,classimg,'图5 核心类图（可在 Enterprise Architect 中按此结构复刻）',width=6.5)
    add_pic(doc,seq,'图6 核心顺序图（可在 Enterprise Architect 中按此交互复刻）',width=6.5)
    doc.add_paragraph('类图与顺序图说明：Review 是核心持久化实体；ReviewController 接收前端请求并调用 ReviewService；ReviewService 编排 AI 审查、版本保存和历史查询；AiReviewService 负责 Mock/Qwen 适配与结构化校验；DocumentService 负责 DOCX/PDF 文本提取。顺序图展示一次正常审查请求，错误路径为解析失败或 AI 失败时由 Controller 返回 error，前端停留在编辑页。')
    doc.add_paragraph('正常路径为输入、解析校验、调用模型、结构化校验、结果展示、保存历史；解析失败或模型失败时回到编辑页并提示错误。结果页的“需要确认”与“可测试验收标准”是人工确认点，系统不把模型建议直接视为最终需求。')
    doc.add_heading('3.5 界面原型与交互设计',2)
    doc.add_paragraph('页面导航为：审查入口 → 结果页；结果页可返回编辑、修改后重新审查或追问；历史记录页可查看详情、删除记录并返回审查入口。项目现有界面已实现首页输入、结果报告和历史列表三类页面，以下截图作为关键界面原型/实现参考。')
    imgs=[('图4 首页/入口页：输入需求、上传文件和选择审查模式',ROOT/'实验文档'/'TEST2'/'项目启动截图'/'图3.项目前端界面首页.png'),('图5 核心任务页：需求文本编辑与开始审查操作',ROOT/'实验文档'/'TEST2'/'项目启动截图'/'图2.前端启动截图.png'),('图6 需求获取证据：用户访谈与需求询问记录',ROOT/'实验文档'/'TEST2'/'需求获取截图'/'需求的访谈得到.png')]
    for cap,pth in imgs:
        if pth.exists(): add_pic(doc,pth,cap,width=6.2)
    add_pic(doc,p1,'图7 首页/入口页原型（Axure 可复刻）',width=6.4)
    add_pic(doc,p2,'图8 核心审查页原型（Axure 可复刻）',width=6.4)
    add_pic(doc,p3,'图9 结果页原型（Axure 可复刻）',width=6.4)
    doc.add_paragraph('交互状态说明：空数据状态为“还没有审查记录”；加载状态由按钮 loading 表示；错误状态通过页面底部错误提示显示；结果筛选支持全部、模糊表达、边界条件、冲突、角色/权限、不可测试、安全风险和运营异常；用户可以从结果页返回编辑并重新操作。当前未完成的原型内容是独立的手绘导航图、独立结果页原型稿，以及对所有错误状态逐项截图留证。')
    doc.add_heading('3.6 设计一致性检查与版本证据',2)
    table(doc,['检查范围','检查结果','调整或待办'],[
        ['需求—接口','R1-R5 均有对应 REST 接口和前端操作','通过；需补充真实运行时的接口截图'],
        ['架构—代码','前端页面、Controller、Service、Repository 与图2一致','通过；AiReviewService 的模型输出校验仍可加强'],
        ['数据—历史版本','Review 保存当前报告和 versionsJson，追问会追加旧版本','通过；未实现用户隔离'],
        ['界面—流程','入口、结果、历史三页覆盖主流程','基本通过；需补独立原型导航图'],
        ['仓库—版本','项目文件、TEST2截图和本报告源文件在本地仓库','需你在 GitHub/Gitee 提交本报告、图1-图6并补 commit 链接']])
    doc.add_paragraph('本稿中已根据仓库代码完成的内容：架构与模块说明、需求追踪、接口与数据设计、流程图、技术选型和已有界面截图整理。需要你补充或核实的内容：学习通要求的最终班级-学号-姓名信息、实际 GitHub/Gitee 提交链接与 commit 号、若教师要求的独立手绘/原型工具截图，以及模型真实调用成功或失败的运行截图。')
    doc.add_heading('4. 实验小结',1)
    doc.add_paragraph('本实验将实验2中的“需求歧义审查”核心用户流程转化为可开发的设计基线。通过需求—设计对应表，明确了输入、解析、AI 审查、结果确认和历史追踪之间的追踪关系；通过分层架构，划分了前端展示、REST 接口、业务服务、AI 适配和 H2 持久化职责；通过数据与接口设计，明确了 Review、报告问题和追问版本的主要字段及失败处理；通过流程图和界面截图，补齐了从提交需求到查看结果的交互路径。')
    doc.add_paragraph('当前设计仍有边界：Mock 报告不能替代真实模型判断，扫描型 PDF 尚未支持 OCR，系统尚未提供登录、权限隔离、限流和文件安全扫描。后续开发应优先完成接口异常测试、模型输出严格校验、文件大小与内容安全检查，并在 GitHub/Gitee 提交图表和运行证据，作为实验4开发的基线。')
    out=OUT/'实验3-软件架构与界面设计-报告过渡稿-章节对应版.docx'; doc.save(out); print(out)

if __name__=='__main__': main()
