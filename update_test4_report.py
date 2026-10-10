from docx import Document
from pathlib import Path
p=Path(r'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST4\实验四报告.docx')
d=Document(str(p))
for para in d.paragraphs:
    if '前端生产构建已在本地执行通过；后端 Maven 测试因依赖下载环境受限' in para.text:
        for r in para.runs: r.text=r.text.replace('前端生产构建已在本地执行通过；后端 Maven 测试因依赖下载环境受限，需在可访问 Maven Central 的环境补跑并填入最终日志。','前端生产构建和后端启动验证已在本地执行通过；后端编译阶段无测试源文件，需补充浏览器端完整测试日志。')
    if '后端验证：需在可下载 Maven 依赖的环境执行 mvn test 或 run-local.ps1' in para.text:
        for r in para.runs: r.text=r.text.replace('后端验证：需在可下载 Maven 依赖的环境执行 mvn test 或 run-local.ps1，补充成功日志和测试截图。','后端已通过 run-local.ps1 完成编译并启动，日志显示 Tomcat 运行在 8080、H2 连接成功；项目当前没有 src/test 测试源文件，因此需补充浏览器端和接口端测试截图。')
    if '前端验证结果：执行 npm run build' in para.text:
        for r in para.runs: r.text=r.text.replace('前端验证结果：执行 npm run build，Vite 构建成功。','前端验证结果：执行 npm run build，Vite 构建成功。实际接口验证：正常审查返回 200 并保存记录；空文本返回 400；不存在记录返回 404。')
# tables
for t in d.tables:
    for row in t.rows:
        cells=[c.text for c in row.cells]
        if cells and cells[0]=='TC-01': row.cells[3].text='已通过：Mock报告保存并展示'; row.cells[4].text='已通过接口验证；待补页面截图'
        if cells and cells[0]=='TC-02': row.cells[3].text='前端提示，服务端原先未统一校验'; row.cells[4].text='已通过：HTTP 400，提示需求文本不能为空'
        if cells and cells[0]=='TC-08': row.cells[3].text='统一 400'; row.cells[4].text='已通过：HTTP 404，提示审查记录不存在'
        if cells and cells[0]=='TC-11': row.cells[4].text='已通过创建/读取；删除页面操作待补截图'
# preserve formatting only text updates; save
d.save(str(p))
print('updated',p)
