$ErrorActionPreference = 'Stop'
$baseDir = 'D:\deepseek harness workspace\AI_Request_check\实验文档\TEST7\图'
$modelPath = Join-Path $baseDir '实验7-数据流图.eapx'
$pdfPath = Join-Path $baseDir '实验7-数据流图-ea.pdf'
Copy-Item 'D:\软件需求分析与建模\Enterprise Architect v15\EA\EABase.eapx' $modelPath -Force

$ea = New-Object -ComObject EA.Repository
try {
    if (-not $ea.OpenFile($modelPath)) { throw 'EA OpenFile failed' }
    $model = $ea.Models.GetAt(0)
    $pkg = $model.Packages.AddNew('验收标准生成原型', '')
    [void]$pkg.Update()
    $dia = $pkg.Diagrams.AddNew('图3-5 验收标准生成数据流图', 'DataFlowDiagram')
    $dia.ShowDetails = 0
    [void]$dia.Update()

    function New-Node($name, $type, $stereo, $l, $t, $r, $b, $fontSize) {
        $el = $pkg.Elements.AddNew($name, $type)
        if ($stereo) { $el.Stereotype = $stereo }
        [void]$el.Update()
        $do = $dia.DiagramObjects.AddNew("l=$l;r=$r;t=$t;b=$b", '')
        $do.ElementID = $el.ElementID
        $do.fontSize = $fontSize
        $do.fontName = '微软雅黑'
        [void]$do.Update()
        return $el
    }

    function New-Flow($client, $supplier, $label) {
        $c = $client.Connectors.AddNew($label, 'Dependency')
        $c.Stereotype = 'DFD_DataFlow'
        $c.ClientID = $client.ElementID
        $c.SupplierID = $supplier.ElementID
        $c.Direction = 'Source -> Destination'
        [void]$c.Update()
        return $c
    }

    $user     = New-Node '用户 / 前端' 'Class' 'DFD_External' 40 40 200 100 9
    $pre      = New-Node '① 预处理' 'Activity' 'DFD_Process' 230 40 390 110 9
    $storeReq = New-Node '需求原文' 'Class' 'DFD_DataStore' 40 150 200 220 9
    $modelEl  = New-Node '② 模型生成' 'Activity' 'DFD_Process' 230 150 390 220 9
    $check    = New-Node '③ 程序检查' 'Activity' 'DFD_Process' 230 270 390 350 9
    $repair   = New-Node '④ 有限修复' 'Activity' 'DFD_Process' 420 270 550 350 9
    $show     = New-Node '⑤ 展示与保存' 'Activity' 'DFD_Process' 230 390 390 460 9
    $storeAC  = New-Node '验收标准 / 测试样例' 'Class' 'DFD_DataStore' 420 390 550 460 9
    $storeLog = New-Node '运行日志' 'Class' 'DFD_DataStore' 420 500 550 570 9
    $storeEval= New-Node '评测结果' 'Class' 'DFD_DataStore' 420 610 550 680 9

    $pre.Notes = '规范化空白、长度校验、非软件需求范围预判'
    $modelEl.Notes = 'qwen-plus + system Prompt（v1/v2），输出结构化 JSON'
    $check.Notes = '结构、逐字引用、GWT、三类覆盖；不通过进入修复'
    $repair.Notes = '回传检查错误，最多 3 次尝试'
    $show.Notes = '页面展示并通过 runId 写入日志'

    $archive = New-Node '审查档案（接入点）' 'Class' 'DFD_External' 40 500 200 570 8

    [void](New-Flow $user $pre '需求文本')
    [void](New-Flow $storeReq $pre '读取原文')
    [void](New-Flow $pre $modelEl '规范化文本 + Prompt')
    [void](New-Flow $modelEl $check '结构化 JSON')
    [void](New-Flow $check $repair '错误列表')
    [void](New-Flow $repair $modelEl '重写请求')
    [void](New-Flow $check $show '通过')
    [void](New-Flow $show $storeAC '保存报告')
    [void](New-Flow $show $storeLog 'runId / 事件')
    [void](New-Flow $show $storeEval '评测指标')
    [void](New-Flow $show $archive '回写档案')

    [void]$ea.SaveAllDiagrams()
    $dia.SaveAsPDF($pdfPath)
    "saved pdf: " + (Test-Path $pdfPath) + " size=" + (Get-Item $pdfPath).Length
} finally {
    $ea.CloseFile()
    $ea.Exit()
}
