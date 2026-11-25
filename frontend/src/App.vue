<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ShieldCheck, ClipboardCheck, History, Upload, Play, RotateCcw, Send, Trash2, ArrowLeft, FileText, ChevronRight, CircleAlert, CheckCircle2, ScanSearch, Search, Layers3, Sparkles, ArrowRight, FileCheck2, BarChart3, Download, Pencil, Save, Ban, UserCheck, RefreshCw, Database } from 'lucide-vue-next'
import AcceptanceResult from './components/AcceptanceResult.vue'

type Issue={id:string;type:string;severity:string;quote:string;location:string;explanation:string;missingConditions:string[];questions:string[];acceptanceCriteria:string[];relatedRoles:string[];reworkRisk:string}
type RagChunk={id:string;source:string;title:string;score:number;text:string}
type DocumentSource={fileName:string;visualCount:number;recognizedVisuals:number;visualKind:string;warnings:string[]}
type Report={document?:DocumentSource;summary:string;riskLevel:string;counts:{high:number;medium:number;low:number};issues:Issue[];promptVersion?:string;promptLabel?:string;promptChangeEffect?:string;rag?:{method:string;topK:number;resultCount:number;chunks:RagChunk[];context:string;answerRule:string};ragAnswer?:string}
type Review={id:string;text:string;mode:string;createdAt:string;report:Report;versions:Report[]}
type HistoryItem={id:string;createdAt:string;summary:string;riskLevel:string;counts:{high:number;medium:number;low:number}}
type AgentStep={index:number;tool:string;args:string;resultPreview:string;status:string;durationMs:number}
type AgentRun={taskId:string;status:string;answer:string;steps:AgentStep[];confirm?:{tool:string;impact:string};error?:string}
type AcceptanceCriterion={id:string;title:string;given:string;when:string;then:string;sourceQuote:string;priority:string}
type AcceptanceTestSample={id:string;kind:string;input:string;expected:string;sourceQuote:string}
type AcceptanceReport={summary:string;requirementKind?:string;acceptanceCriteria:AcceptanceCriterion[];testSamples:AcceptanceTestSample[];openQuestions:string[];limits?:string[]}
type AcceptanceChecks={schemaOk:boolean;groundingOk:boolean;structureOk:boolean;coverageOk:boolean;messages:string[]}
type AcceptanceRun={runId:string;status:string;promptVersion:string;model:string;durationMs:number;usage:{promptTokens:number;completionTokens:number;totalTokens:number};report?:AcceptanceReport;checks?:AcceptanceChecks;attempts?:number;error?:string;errorCode?:string}
type AcceptanceSource={id:string;source:string;title:string;score:number;text:string}
type AcceptanceTask={taskId:string;reviewId?:string|null;status:string;statusLabel:string;phase:string;promptVersion:string;mode:string;model:string;degraded:boolean;degradeReason?:string;errorCode?:string;errorMessage?:string;retryable:boolean;duplicate:boolean;attempts:number;durationMs:number;promptTokens:number;completionTokens:number;createdAt?:string;startedAt?:string;finishedAt?:string;cancelRequested:boolean;decision:string;edited:boolean;saved:boolean;savedAt?:string;retryOf?:string;report?:AcceptanceReport;checks?:AcceptanceChecks;sources:AcceptanceSource[];actions:string[]}
type SavedAcceptance={saved:boolean;savedAt?:string;acceptance?:{taskId:string;mode:string;model:string;degraded:boolean;edited:boolean;report:AcceptanceReport;checks?:AcceptanceChecks}}

const API=import.meta.env.VITE_API_BASE_URL||'http://localhost:8080/api'
const page=ref<'home'|'review'|'result'|'history'|'agent'|'acceptance'>('home'); const text=ref(''); const mode=ref('全面审查'); const promptVersion=ref('revised'); const loading=ref(false); const uploading=ref(false); const error=ref(''); const fileName=ref(''); const current=ref<Review|null>(null); const history=ref<HistoryItem[]>([]); const filter=ref('all'); const question=ref(''); const selectedIssueId=ref('')
const typeNames:Record<string,string>={ambiguous_term:'模糊表达',missing_boundary:'边界缺口',conflict:'需求冲突',permission:'角色权限',testability:'可测试性',security:'安全风险',operational:'运营异常',out_of_scope:'超出任务范围'}
const visibleIssues=computed(()=>current.value?.report.issues.filter(i=>filter.value==='all'||i.type===filter.value)||[])
const selectedIssue=computed<Issue|null>(()=>visibleIssues.value.find(i=>i.id===selectedIssueId.value)||visibleIssues.value[0]||null)
const riskLabel=(x:string)=>x==='high'?'高风险':x==='medium'?'中风险':'低风险'
const issueTypes=computed(()=>Object.entries(typeNames).filter(([key])=>current.value?.report.issues.some(i=>i.type===key)))
async function request(path:string,options:RequestInit={}){const res=await fetch(API+path,options);const data=await res.json().catch(()=>({error:'服务器返回无效内容'}));if(!res.ok){const err:any=new Error(data.error||'请求失败');err.code=data.code;err.status=res.status;err.actions=data.actions;throw err}return data}
const documentSource=ref<DocumentSource|null>(null); const exporting=ref('')
async function upload(file:any){
  if(uploading.value)return
  uploading.value=true;error.value=''
  try{
    if(file.size>10*1024*1024)throw new Error('文件不能超过 10 MB')
    const form=new FormData();form.append('file',file.raw)
    const data=await request('/reviews/upload',{method:'POST',body:form})
    text.value=data.text;fileName.value=data.fileName;documentSource.value=data.document
    ElMessage.success(data.document?.warnings?.length?'文件已解析，请留意识别范围提示':'文档已就绪')
  }catch(e:any){error.value=e.message}finally{uploading.value=false}
}
async function exportPdf(id:string){
  if(exporting.value)return
  exporting.value=id;error.value=''
  try{
    const response=await fetch(`${API}/reviews/${id}/report.pdf`)
    if(!response.ok){const data=await response.json().catch(()=>({error:'PDF 导出失败'}));throw new Error(data.error||'PDF 导出失败')}
    const blob=await response.blob()
    if(!blob.type.includes('application/pdf'))throw new Error('服务器没有返回 PDF 文件')
    const url=URL.createObjectURL(blob);const link=document.createElement('a')
    link.href=url;link.download=`需求审查报告-${id.slice(0,8)}.pdf`;document.body.appendChild(link);link.click();link.remove()
    setTimeout(()=>URL.revokeObjectURL(url),1000)
    ElMessage.success('PDF 报告已导出')
  }catch(e:any){error.value=e.message}finally{exporting.value=''}
}
async function review(){if(!text.value.trim()){error.value='请先输入或上传需求文本';return}if(text.value.length>20000){error.value='需求文本不能超过 20000 个字符';return}loading.value=true;error.value='';try{const result=await request('/reviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text.value,mode:mode.value,promptVersion:promptVersion.value,document:documentSource.value})}) as Review;current.value=result;filter.value='all';selectedIssueId.value=result.report.issues[0]?.id||'';page.value='result'}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function follow(){const reviewId=current.value?.id;if(!question.value.trim()||!reviewId){error.value='追问内容不能为空';return}loading.value=true;error.value='';try{const result=await request(`/reviews/${reviewId}/follow-up`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:question.value})}) as Review;current.value=result;selectedIssueId.value=result.report.issues[0]?.id||'';question.value='';ElMessage.success('新版本已生成')}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function loadHistory(){try{history.value=await request('/reviews')}catch(e:any){if(page.value!=='home')error.value=e.message}}
async function openHistory(id:string){loading.value=true;error.value='';try{const result=await request(`/reviews/${id}`) as Review;current.value=result;filter.value='all';selectedIssueId.value=result.report.issues[0]?.id||'';page.value='result';void acLoadForReview(id)}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function remove(id:string){try{await ElMessageBox.confirm('删除后不可恢复，确认删除？','删除审查档案',{type:'warning'});await request(`/reviews/${id}`,{method:'DELETE'});await loadHistory();ElMessage.success('档案已删除')}catch(e:any){if(e!=='cancel'&&e!=='close')error.value=e instanceof Error?e.message:String(e)}}
function reset(){text.value='';fileName.value='';documentSource.value=null;current.value=null;selectedIssueId.value='';error.value='';acStopPoll();acTask.value=null;acTaskList.value=[];acSaved.value=null;acEditMode.value=false;acDraft.value=null;acNotice.value='';acError.value='';page.value='review'}
function editAgain(){if(current.value){text.value=current.value.text;documentSource.value=current.value.report.document||null;fileName.value=documentSource.value?.fileName||'';page.value='review'}}
function selectIssue(id:string){selectedIssueId.value=id}
const agentQuestion=ref('现在有多少份档案，风险分布如何？'); const agentRun=ref<AgentRun|null>(null); const agentLoading=ref(false)
const agentStatus=(s:string)=>s==='SUCCESS'?'已完成':s==='NEED_CONFIRM'?'等待确认':s==='DENIED'?'已取消':s==='STEP_LIMIT'?'达到步数上限':s==='TIMEOUT'?'超时终止':s==='CHECK_FAILED'?'校验未通过':'失败'
async function askAgent(){
  if(!agentQuestion.value.trim()){error.value='请输入问题';return}
  agentLoading.value=true;error.value=''
  try{
    const r=await request('/agent/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:agentQuestion.value})}) as AgentRun
    agentRun.value=r
    if(r.status==='NEED_CONFIRM')await decideAgent(r)
  }catch(e:any){error.value=e.message}finally{agentLoading.value=false}
}
async function decideAgent(run:AgentRun){
  const impact=run.confirm?.impact||'该操作会修改数据'
  let approved=true
  try{ await ElMessageBox.confirm(impact,'需要人工确认',{type:'warning',confirmButtonText:'允许执行',cancelButtonText:'拒绝'}) }catch{ approved=false }
  try{
    const r=await request(`/agent/runs/${run.taskId}/confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved})}) as AgentRun
    agentRun.value=r
    if(r.status==='NEED_CONFIRM')await decideAgent(r)
  }catch(e:any){error.value=e.message}
}
const acText=ref(''); const acRun=ref<AcceptanceRun|null>(null); const acLoading=ref(false); const acVersion=ref('revised')
const acSamples=[
  {label:'正常需求',text:'用户可以上传 DOCX 或 PDF 格式的需求文档，单个文件不超过 10MB。上传后系统解析正文和内嵌图片，解析时间不超过 60 秒。文件超过 10MB 或格式不支持时，页面提示具体原因并拒绝上传。扫描版 PDF 需要调用视觉模型识别，识别失败的页面应在结果中标注未识别范围。'},
  {label:'信息不足',text:'用户可以上传文件然后得到结果。'},
  {label:'超出范围',text:'帮我采购 20 台服务器，要求报价最低的供应商，并在本周内完成付款审批。服务器到货后由行政部分配给各项目组。'}
]
const acStatus=(s:string)=>s==='SUCCESS'?'已生成':s==='FAILED'?'生成失败':s==='CHECK_FAILED'?'校验未通过':s==='OUT_OF_SCOPE'?'超出范围':s==='REFUSED'?'已拒绝':s
const acKind=(k?:string)=>k==='insufficient'?'信息不足':k==='out_of_scope'?'超出范围':k==='normal'?'正常需求':'未标注'
const acRunMeta=computed(()=>{const r=acRun.value;if(!r)return[];const m:string[]=[];if(r.model)m.push('模型 '+r.model);if(r.usage)m.push('Token '+r.usage.totalTokens);if(r.attempts)m.push('尝试 '+r.attempts+' 次');m.push('耗时 '+(r.durationMs/1000).toFixed(1)+' 秒');return m})
async function generateAcceptance(){
  if(!acText.value.trim()){error.value='请先输入需求原文';return}
  if(acText.value.length>3000){error.value='需求文本不能超过 3000 个字符';return}
  acLoading.value=true;error.value=''
  try{
    acRun.value=await request('/acceptance/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:acText.value,promptVersion:acVersion.value,mode:acVersion.value==='rule'?'rule':'model'})}) as AcceptanceRun
  }catch(e:any){error.value=e.message}finally{acLoading.value=false}
}
const AC_ERRORS:Record<string,string>={
  INPUT_INVALID:'输入不合法：需求原文为空或超过 3000 字，请修改后重试。',
  MODEL_TIMEOUT:'模型调用超时：本次没有可用结果，可重试或改用规则流程。',
  MODEL_UNAVAILABLE:'模型暂不可用：密钥或通道异常，可改用规则流程或转人工。',
  MODEL_ERROR:'模型调用失败：本次没有可用结果，可重试或改用规则流程。',
  OUTPUT_INVALID:'模型输出不符合约定格式：本次结果已丢弃，可重试。',
  CHECK_FAILED:'结果未通过程序检查：引用或覆盖不完整，可修改后保存或重试。',
  SCOPE_REJECTED:'输入不是软件需求：已在调用模型前拒绝，未产生模型费用。',
  CANCELLED:'任务已取消：返回结果已丢弃，可重新发起。',
  TASK_NOT_FOUND:'任务不存在或已过保留期（30 天），请重新发起。',
  TASK_FINISHED:'任务已结束，无法取消。',
  TASK_NOT_READY:'只有“已生成”的结果才能保存到档案。',
  TASK_NOT_EDITABLE:'当前状态不能编辑，请重新生成或转人工。',
  ALREADY_SAVED:'结果已保存到档案，需先在档案中清除后再放弃。',
  QUEUE_FULL:'排队任务过多，请稍后重试或改用规则流程。',
  NO_REVIEW:'该任务不是从审查档案发起的，无法保存到档案。'
}
const acErrorText=(e:any)=>{const code=e?.code;const message=e?.message;if(message&&code)return `${message}（${code}）`;return message||AC_ERRORS[code]||'生成失败，请重试'}
const acTask=ref<AcceptanceTask|null>(null); const acTaskList=ref<AcceptanceTask[]>([]); const acSaved=ref<SavedAcceptance|null>(null)
const acBusy=ref(false); const acNotice=ref(''); const acError=ref(''); const acEditMode=ref(false); const acDraft=ref<AcceptanceReport|null>(null)
const acQuestionsText=ref(''); const acLimitsText=ref(''); const acNow=ref(Date.now())
let acPollTimer:number|null=null; let acTickTimer:number|null=null
const acIsActive=(t:AcceptanceTask|null)=>!!t&&(t.status==='QUEUED'||t.status==='RUNNING')
const acChecksPass=(c?:AcceptanceChecks)=>!!c&&c.schemaOk&&c.groundingOk&&c.structureOk&&c.coverageOk
const acTaskKey=(reviewId:string)=>'acceptanceTask:'+reviewId
const acElapsed=computed(()=>{const t=acTask.value;if(!t)return 0;if(!acIsActive(t))return Math.max(0,Math.round((t.durationMs||0)/1000));const start=t.startedAt?Date.parse(t.startedAt.replace(' ','T')):t.createdAt?Date.parse(t.createdAt.replace(' ','T')):Date.now();return Math.max(0,Math.floor((acNow.value-start)/1000))})
const acTaskMeta=computed(()=>{const t=acTask.value;if(!t)return[];const m:string[]=[];if(t.model)m.push('模型 '+t.model);if(t.mode)m.push('模式 '+t.mode);if(t.attempts)m.push('尝试 '+t.attempts+' 次');if(t.promptTokens||t.completionTokens)m.push('Token '+(t.promptTokens+t.completionTokens));if(t.durationMs)m.push('耗时 '+(t.durationMs/1000).toFixed(1)+' 秒');if(t.edited)m.push('已人工修改');return m})
function acStopPoll(){if(acPollTimer!==null){window.clearInterval(acPollTimer);acPollTimer=null}}
function acStartPoll(){if(acPollTimer!==null)return;acPollTimer=window.setInterval(()=>{void acRefreshTask()},1200)}
async function acRefreshTask(){
  const cur=acTask.value;if(!cur)return
  try{
    const fresh=await request(`/acceptance/tasks/${cur.taskId}`) as AcceptanceTask
    acTask.value=fresh
    if(acIsActive(fresh))acStartPoll()
    else{acStopPoll();if(fresh.reviewId)await acLoadTaskList(fresh.reviewId)}
  }catch(e:any){
    acStopPoll();acError.value=acErrorText(e)
    if(e?.code==='TASK_NOT_FOUND'){acTask.value=null;if(cur.reviewId)localStorage.removeItem(acTaskKey(cur.reviewId))}
  }
}
async function acLoadTaskList(reviewId:string){try{acTaskList.value=await request('/acceptance/tasks?reviewId='+encodeURIComponent(reviewId)) as AcceptanceTask[]}catch{acTaskList.value=[]}}
async function acLoadForReview(reviewId:string){
  acTask.value=null;acTaskList.value=[];acEditMode.value=false;acDraft.value=null;acNotice.value='';acError.value='';acStopPoll()
  try{acSaved.value=await request(`/reviews/${reviewId}/acceptance`) as SavedAcceptance}catch{acSaved.value=null}
  await acLoadTaskList(reviewId)
  const stored=localStorage.getItem(acTaskKey(reviewId));let target:AcceptanceTask|null=null
  if(stored){try{target=await request('/acceptance/tasks/'+stored) as AcceptanceTask}catch{localStorage.removeItem(acTaskKey(reviewId))}}
  if(!target){
    const active=acTaskList.value.find(t=>acIsActive(t))
    // 本地没有任务编号时：有进行中的任务就恢复它；否则若档案里已保存验收标准，优先展示已保存结果，而不是最近一次（可能失败的）任务。
    if(active)target=active
    else if(!(acSaved.value&&acSaved.value.saved))target=acTaskList.value[0]||null
  }
  acTask.value=target
  if(acIsActive(target))acStartPoll()
}
async function acGenerate(){
  const reviewId=current.value?.id;if(!reviewId){acError.value='请先打开一份审查档案';return}
  if(acIsActive(acTask.value))return
  acBusy.value=true;acError.value='';acNotice.value=''
  try{
    const t=await request('/acceptance/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reviewId,promptVersion:'revised',mode:'model'})}) as AcceptanceTask
    acTask.value=t;acEditMode.value=false;localStorage.setItem(acTaskKey(reviewId),t.taskId)
    acNotice.value=t.duplicate?'已有进行中的任务，已恢复该任务（重复提交未新建任务）':'任务已提交，正在后台生成'
    if(acIsActive(t))acStartPoll()
    await acLoadTaskList(reviewId)
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
async function acCancel(){
  const t=acTask.value;if(!t)return
  acBusy.value=true
  try{
    acTask.value=await request(`/acceptance/tasks/${t.taskId}/cancel`,{method:'POST'}) as AcceptanceTask
    acNotice.value='已请求取消：排队任务立即取消，处理中的任务会在当前模型调用返回后丢弃结果'
    acStartPoll()
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
async function acRetry(){
  const t=acTask.value;if(!t)return
  acBusy.value=true;acError.value=''
  try{
    const fresh=await request(`/acceptance/tasks/${t.taskId}/retry`,{method:'POST'}) as AcceptanceTask
    acTask.value=fresh;if(fresh.reviewId)localStorage.setItem(acTaskKey(fresh.reviewId),fresh.taskId)
    acNotice.value='已创建新的重试任务，原任务与失败原因保留可追溯'
    acStartPoll();if(fresh.reviewId)await acLoadTaskList(fresh.reviewId)
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
async function acFallback(){
  const t=acTask.value;if(!t)return
  acBusy.value=true;acError.value=''
  try{
    const fresh=await request(`/acceptance/tasks/${t.taskId}/fallback`,{method:'POST'}) as AcceptanceTask
    acTask.value=fresh;if(fresh.reviewId)localStorage.setItem(acTaskKey(fresh.reviewId),fresh.taskId)
    acNotice.value='模型不可用，已用规则流程生成本地结果（非 AI），请人工补全后再保存'
    if(fresh.reviewId)await acLoadTaskList(fresh.reviewId)
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
async function acHandoff(){
  const t=acTask.value;if(!t)return
  acBusy.value=true;acError.value=''
  try{
    const fresh=await request(`/acceptance/tasks/${t.taskId}/handoff`,{method:'POST'}) as AcceptanceTask
    acTask.value=fresh;if(fresh.reviewId)localStorage.setItem(acTaskKey(fresh.reviewId),fresh.taskId)
    if(fresh.reviewId)await acLoadTaskList(fresh.reviewId)
    acBeginEdit();acNotice.value='已转人工：请补齐验收标准与测试样例，保存后由你确认结果'
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
function acBeginEdit(){
  const r=acTask.value?.report;if(!r)return
  acDraft.value=JSON.parse(JSON.stringify(r)) as AcceptanceReport
  acQuestionsText.value=(r.openQuestions||[]).join('\n')
  acLimitsText.value=(r.limits||[]).join('\n')
  acEditMode.value=true
  acNotice.value=acTask.value?.mode==='manual'?'人工填写：至少保留一条验收标准与一类测试样例':'修改保存后会重新做程序检查，引用不匹配会明确标出'
}
function acCancelEdit(){acEditMode.value=false;acDraft.value=null}
function acAddCriterion(){const d=acDraft.value;if(!d)return;d.acceptanceCriteria.push({id:'AC-'+(d.acceptanceCriteria.length+1),title:'',given:'',when:'',then:'',sourceQuote:'',priority:'must'})}
function acRemoveCriterion(i:number){acDraft.value?.acceptanceCriteria.splice(i,1)}
function acAddSample(){const d=acDraft.value;if(!d)return;d.testSamples.push({id:'TS-'+(d.testSamples.length+1),kind:'normal',input:'',expected:'',sourceQuote:''})}
function acRemoveSample(i:number){acDraft.value?.testSamples.splice(i,1)}
async function acSaveEdit(){
  const t=acTask.value;const d=acDraft.value;if(!t||!d)return
  d.openQuestions=acQuestionsText.value.split('\n').map(x=>x.trim()).filter(Boolean)
  d.limits=acLimitsText.value.split('\n').map(x=>x.trim()).filter(Boolean)
  acBusy.value=true;acError.value=''
  try{
    const fresh=await request(`/acceptance/tasks/${t.taskId}/result`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({report:d})}) as AcceptanceTask
    acTask.value=fresh;acEditMode.value=false;acDraft.value=null
    acNotice.value=acChecksPass(fresh.checks)?'修改已保存，程序检查通过':'修改已保存，但仍有检查项未通过，请核对引用与覆盖'
    if(fresh.reviewId)await acLoadTaskList(fresh.reviewId)
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
async function acApply(){
  const t=acTask.value;if(!t)return
  acBusy.value=true;acError.value=''
  try{
    const res=await request(`/acceptance/tasks/${t.taskId}/apply`,{method:'POST'}) as {task:AcceptanceTask;reviewId:string}
    acTask.value=res.task
    if(res.reviewId){acSaved.value=await request(`/reviews/${res.reviewId}/acceptance`) as SavedAcceptance;localStorage.setItem(acTaskKey(res.reviewId),res.task.taskId)}
    acNotice.value='已保存到审查档案，刷新页面或重新打开档案仍可读取'
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
async function acDiscard(){
  const t=acTask.value;if(!t)return
  try{await ElMessageBox.confirm('放弃后结果不再作为交付内容，任务记录仍保留用于追溯。确认放弃？','放弃结果',{type:'warning',confirmButtonText:'放弃结果',cancelButtonText:'保留'})}catch{return}
  acBusy.value=true
  try{
    acTask.value=await request(`/acceptance/tasks/${t.taskId}/discard`,{method:'POST'}) as AcceptanceTask
    acNotice.value='已放弃本次结果，任务记录保留用于追溯'
  }catch(e:any){acError.value=acErrorText(e)}finally{acBusy.value=false}
}
function acOpenTask(t:AcceptanceTask){
  acTask.value=t;acEditMode.value=false;acDraft.value=null;acNotice.value='';acError.value=''
  if(t.reviewId)localStorage.setItem(acTaskKey(t.reviewId),t.taskId)
  if(acIsActive(t))acStartPoll();else acStopPoll()
}
onMounted(()=>{acTickTimer=window.setInterval(()=>{acNow.value=Date.now()},1000);loadHistory()})
onUnmounted(()=>{if(acTickTimer!==null)window.clearInterval(acTickTimer);acStopPoll()})
</script>
<template>
<div class="app-shell">
  <aside class="sidebar">
    <button class="brand brand-button" @click="page='home'" aria-label="返回首页"><div class="brand-mark"><ShieldCheck :size="19"/></div><div><strong>审查台</strong><span>REQUIREMENT REVIEW</span></div></button>
    <div class="workspace-label">工作区</div>
    <button class="side-link" :class="{active:page==='review'||page==='result'}" @click="page='review'"><ClipboardCheck :size="17"/><span>新建审查</span><ChevronRight :size="14"/></button>
    <button class="side-link" :class="{active:page==='history'}" @click="page='history';loadHistory()"><History :size="17"/><span>审查档案</span><small>{{history.length}}</small></button>
    <button class="side-link" :class="{active:page==='agent'}" @click="page='agent'"><Sparkles :size="17"/><span>档案分析</span><ChevronRight :size="14"/></button>
    <button class="side-link" :class="{active:page==='acceptance'}" @click="page='acceptance'"><FileCheck2 :size="17"/><span>验收标准</span><ChevronRight :size="14"/></button>
    <div class="sidebar-divider"></div><div class="sidebar-tip"><Layers3 :size="15"/><div><b>审查工作区</b><span>从原文到可执行证据</span></div></div>
    <div class="sidebar-foot"><div class="status-dot"></div><div><b>本地工作区</b><span>Mock / Qwen 可用</span></div></div>
  </aside>
  <main class="main-shell">
    <header class="topbar"><div><span class="crumb">{{page==='home'?'REQUIREMENT QUALITY WORKSPACE':'工作区 / '+(page==='history'?'审查档案':page==='result'?'审查 Dashboard':page==='acceptance'?'验收标准生成':'新建审查')}}</span><h1>{{page==='home'?'AI 需求歧义审查器':page==='history'?'审查档案':page==='result'?'需求质量报告':page==='acceptance'?'验收标准生成':'开始一次需求审查'}}</h1></div><div class="top-meta"><span class="secure"><CheckCircle2 :size="14"/>后端密钥隔离</span><span class="avatar">AI</span></div></header>
    <section v-if="page==='home'" class="home-page content">
      <div class="home-hero"><div class="home-copy"><div class="eyebrow"><Sparkles :size="13"/> REQUIREMENT QUALITY WORKSPACE</div><h2>让需求在<br/><span>进入开发前</span>变得清晰</h2><p>把自然语言需求转换为带原文证据、风险分级和可测试验收标准的审查报告。先理解问题，再开始构建。</p><div class="hero-actions"><button class="hero-primary" @click="page='review'">开始一次审查 <ArrowRight :size="16"/></button><button class="hero-secondary" @click="page='history';loadHistory()"><History :size="15"/>查看审查档案</button></div><div class="hero-meta"><span><i class="meta-dot green"></i>Mock 模式无需密钥</span><span><i class="meta-dot blue"></i>支持 DOCX / PDF</span><span><i class="meta-dot purple"></i>报告可继续追问</span></div></div><div class="hero-orbit"><div class="orbit-ring ring-one"></div><div class="orbit-ring ring-two"></div><div class="orbit-core"><ShieldCheck :size="42"/><span>SPEC<br/>LENS</span></div><div class="orbit-node node-one"><CircleAlert :size="14"/>风险</div><div class="orbit-node node-two"><FileCheck2 :size="14"/>证据</div><div class="orbit-node node-three"><BarChart3 :size="14"/>报告</div></div></div>
      <div class="home-section-head"><div><span class="section-kicker">HOW IT WORKS</span><h3>一条清晰的审查路径</h3></div><span>从原文到可执行证据</span></div>
      <div class="home-flow"><article><div class="flow-number">01</div><Upload :size="20"/><h4>输入需求</h4><p>粘贴原文或上传 Word、PDF，保留业务上下文。</p></article><div class="flow-line"></div><article><div class="flow-number">02</div><ScanSearch :size="20"/><h4>识别风险</h4><p>从边界、角色、测试和运营维度定位问题。</p></article><div class="flow-line"></div><article><div class="flow-number">03</div><FileCheck2 :size="20"/><h4>确认行动</h4><p>查看引用、待确认问题和可测试验收标准。</p></article></div>
      <div class="home-feature-grid"><article class="home-feature"><div class="feature-icon purple"><CircleAlert :size="19"/></div><div><h4>发现隐藏缺口</h4><p>识别模糊表达、权限缺失、边界遗漏和异常流程。</p></div></article><article class="home-feature"><div class="feature-icon blue"><FileCheck2 :size="19"/></div><div><h4>证据化报告</h4><p>每个结论都绑定原文引用，方便评审、讨论和验收。</p></div></article><article class="home-feature"><div class="feature-icon green"><History :size="19"/></div><div><h4>版本持续追问</h4><p>围绕同一份报告继续提问，旧版本自动保留。</p></div></article></div>
    </section>
    <section v-if="page==='review'" class="content review-page">
      <div class="page-intro"><div><div class="eyebrow">01 / INPUT & SCOPE</div><h2>把需求交给审查台</h2><p>上传需求文档或粘贴原文，系统结合正文与图中信息进行审查。</p></div><div class="step-rail"><span class="active">01 输入与范围</span><span>02 审查 Dashboard</span><span>03 审查档案</span></div></div>
      <div class="workspace-grid"><div class="source-workspace panel"><div class="card-head"><div><span class="section-kicker">UPLOAD WORKSPACE</span><h3>来源文档</h3><p class="card-subtitle">正文与图片识别结果在后台参与审查，无需展开文档内容。</p></div><button class="ghost" :disabled="uploading||loading" @click="reset"><RotateCcw :size="14"/>清空</button></div><div class="source-toolbar"><div class="source-title"><FileText :size="16"/><span>{{fileName||'未选择文件'}}</span></div><span class="source-limit">DOCX / PDF · 10 MB</span></div><div v-if="fileName" class="document-file" aria-live="polite"><div class="document-file-icon"><FileText :size="32"/></div><div class="document-file-main"><span class="section-kicker">SOURCE DOCUMENT</span><h4>{{fileName}}</h4><p>已提取 {{text.length.toLocaleString()}} 个字符 · 正文已在后台保留</p><p v-if="documentSource?.visualCount">{{documentSource.visualKind==='page'?'页面视觉识别':'内嵌图片识别'}}：{{documentSource.recognizedVisuals}} / {{documentSource.visualCount}} {{documentSource.visualKind==='page'?'页':'张'}}</p><span class="document-ready"><CheckCircle2 :size="14"/>文件已就绪，可开始审查</span></div></div><div v-if="documentSource?.warnings.length" class="document-warnings" role="status"><p v-for="warning in documentSource.warnings" :key="warning"><CircleAlert :size="14"/>{{warning}}</p></div><el-input v-else-if="!fileName" v-model="text" :disabled="uploading||loading" type="textarea" :rows="15" maxlength="20000" show-word-limit placeholder="粘贴需求原文，保留完整上下文和业务约束……"/><div class="upload-zone" :class="{busy:uploading}"><el-upload :auto-upload="false" :show-file-list="false" :disabled="uploading||loading" accept=".docx,.pdf" :on-change="upload"><button class="upload-btn" :disabled="uploading||loading"><Upload :size="15"/>{{uploading?'正在解析与识别…':fileName?'更换文档':'导入 Word / PDF'}}</button></el-upload><div><b>{{uploading?'正在读取文档':'把文件放进审查工作区'}}</b><span>{{uploading?'图片较多时需等待，请勿重复上传':'支持 DOCX / PDF；上传后显示文件，清空后可粘贴文字'}}</span></div><CheckCircle2 v-if="fileName&&!uploading" class="upload-ok" :size="17"/></div></div>
        <aside class="protocol-card"><div class="section-kicker">REVIEW PROTOCOL</div><div class="protocol-icon"><Sparkles :size="18"/></div><h3>配置这次审查</h3><p>选择分析视角，结果会保存为一份可以继续追问的审查档案。</p><label>分析视角</label><el-select v-model="mode"><el-option label="全面审查" value="全面审查"/><el-option label="重点关注可测试性" value="可测试性"/><el-option label="重点关注安全与权限" value="安全与权限"/></el-select><label class="prompt-label">Prompt版本</label><el-select v-model="promptVersion"><el-option label="原Prompt" value="original"/><el-option label="修改后Prompt" value="revised"/></el-select><div class="protocol-list"><div><span>引用证据</span><b>原文保留</b></div><div><span>输出格式</span><b>结构化报告</b></div><div><span>模型通道</span><b>Mock / Qwen</b></div></div><button class="run-btn" :disabled="loading||uploading" @click="review"><Play :size="16"/>{{loading?'审查处理中':'开始审查'}}<span>⌘ ↵</span></button></aside></div>
      <div class="method-note panel"><div class="method-icon"><ScanSearch :size="17"/></div><div><b>审查方式</b><span>每个问题都必须绑定原文引用、缺失条件、待确认问题和可测试验收标准。</span></div><span class="method-tag">EVIDENCE FIRST</span></div>
    </section>
    <section v-else-if="page==='result'&&current" class="content result-page">
      <div class="result-toolbar"><button class="back-link" @click="page='review'" aria-label="返回需求原文"><ArrowLeft :size="15"/>返回需求原文</button><div class="toolbar-actions"><span class="version-chip">{{current.mode}} · {{current.versions.length+1}} 个版本</span><button class="outline-btn" :disabled="!!exporting" @click="exportPdf(current.id)"><Download :size="14"/>{{exporting===current.id?'正在导出…':'导出 PDF'}}</button><button class="outline-btn" @click="editAgain">修改后重审</button></div></div>
      <div class="dashboard-head"><div><div class="eyebrow">02 / REVIEW DASHBOARD</div><h2>需求质量审查报告</h2><p>{{new Date(current.createdAt).toLocaleString('zh-CN')}} · ID {{current.id.slice(0,8)}} · {{current.report.promptLabel||'修改后Prompt'}}</p></div><div class="health-card" :class="current.report.riskLevel"><div class="health-label"><Search :size="14"/>总体风险</div><strong>{{riskLabel(current.report.riskLevel)}}</strong><span>{{current.report.issues.length}} 个发现项</span></div></div>
      <div class="metric-row dashboard-metrics"><div class="metric"><span>高风险</span><strong class="high">{{current.report.counts.high}}</strong><small>需要优先确认</small></div><div class="metric"><span>中风险</span><strong class="medium">{{current.report.counts.medium}}</strong><small>建议进入评审</small></div><div class="metric"><span>低风险</span><strong class="low">{{current.report.counts.low}}</strong><small>可在迭代完善</small></div><div class="metric summary-metric"><span>执行摘要</span><strong>{{current.report.summary}}</strong></div></div>
      <div v-if="current.report.document" class="report-source panel"><FileText :size="20"/><div><b>{{current.report.document.fileName}}</b><p>本报告结合文档正文与已识别的图像内容生成。</p><p v-if="current.report.document.visualCount">视觉识别：{{current.report.document.recognizedVisuals}} / {{current.report.document.visualCount}} {{current.report.document.visualKind==='page'?'页':'张图片'}}</p><p v-for="warning in current.report.document.warnings" :key="warning" class="source-warning">{{warning}}</p></div></div><div v-if="current.report.rag" class="rag-evidence panel"><div><span class="section-kicker">RAG EVIDENCE</span><h3>检索依据与来源</h3><p>{{current.report.ragAnswer}} 方法：{{current.report.rag.method}}，Top-{{current.report.rag.topK}}，命中 {{current.report.rag.resultCount}} 个片段。</p></div><ul><li v-for="chunk in current.report.rag.chunks" :key="chunk.id"><b>[{{chunk.id}}]</b> {{chunk.source}} / {{chunk.title}} · 得分 {{chunk.score}}</li></ul></div>
      <div class="dashboard-grid"><aside class="findings-panel panel"><div class="findings-head"><div><span class="section-kicker">FINDINGS</span><h3>发现项</h3></div><span class="findings-count">{{current.report.issues.length}}</span></div><div class="filter-strip"><button :class="{selected:filter==='all'}" @click="filter='all'">全部 <b>{{current.report.issues.length}}</b></button><button v-for="([key,name]) in issueTypes" :key="key" :class="{selected:filter===key}" @click="filter=key">{{name}}</button></div><div v-if="!visibleIssues.length" class="findings-empty"><CheckCircle2 :size="25"/><span>当前筛选没有问题</span></div><button v-for="issue in visibleIssues" :key="issue.id" class="finding-row" :class="{selected:selectedIssue?.id===issue.id}" @click="selectIssue(issue.id)"><span class="finding-severity" :class="issue.severity"></span><span class="finding-copy"><b>{{issue.explanation}}</b><small>{{issue.id}} · {{typeNames[issue.type]||issue.type}}</small></span><ChevronRight :size="15"/></button></aside>
        <article v-if="selectedIssue" class="finding-detail panel"><div class="detail-top"><div><span class="issue-id">{{selectedIssue.id}} · {{typeNames[selectedIssue.type]||selectedIssue.type}}</span><h3>{{selectedIssue.explanation}}</h3></div><span class="severity" :class="selectedIssue.severity"><CircleAlert :size="14"/>{{riskLabel(selectedIssue.severity)}}</span></div><div class="quote"><span>原文证据 · {{selectedIssue.location}}</span><p>“{{selectedIssue.quote}}”</p></div><div class="detail-grid"><div><span class="label">缺失条件</span><ul><li v-for="x in selectedIssue.missingConditions" :key="x">{{x}}</li></ul></div><div><span class="label">待确认问题</span><ul><li v-for="x in selectedIssue.questions" :key="x">{{x}}</li></ul></div><div><span class="label">验收标准</span><ul><li v-for="x in selectedIssue.acceptanceCriteria" :key="x">{{x}}</li></ul></div><div><span class="label">相关角色 / 返工风险</span><p class="roles">{{selectedIssue.relatedRoles.join(' · ')}}</p><p>{{selectedIssue.reworkRisk}}</p></div></div></article><div v-else class="finding-detail panel empty-detail"><CheckCircle2 :size="34"/><h3>暂未发现明显问题</h3><p>{{current.report.summary}}</p></div></div>
      <div class="follow panel"><div class="follow-copy"><span class="section-kicker">FOLLOW-UP</span><h3>继续追问这份报告</h3><p>AI 会结合原始需求和当前模式生成新的分析版本，旧报告会自动保留。</p><div class="follow-examples"><span>可以问：</span><button @click="question='哪个问题最可能导致返工？'">哪个问题最可能导致返工？</button><button @click="question='请把高风险问题改写成验收标准'">改写成验收标准</button><button @click="question='还缺少哪些边界条件？'">补充边界条件</button></div></div><div class="follow-input"><el-input v-model="question" placeholder="输入你想进一步确认的问题……" @keyup.enter="follow"><template #prefix><span class="question-mark">?</span></template></el-input><button class="send-btn" :disabled="loading" @click="follow"><Send :size="15"/>发送</button></div></div>
      <section class="acceptance-integration panel">
        <div class="integration-head">
          <div><span class="section-kicker">ACCEPTANCE INTEGRATION / 实验8 集成</span><h3>把这份档案变成可验收的测试</h3><p>从当前档案原文生成验收标准与测试样例。生成中可以取消；失败时可以重试、改用规则流程或转人工；核对无误后再保存回档案。</p></div>
          <span class="status-chip" :class="acTask?.status">{{acTask?acTask.statusLabel:'未开始'}}</span>
        </div>
        <div class="integration-bar">
          <button class="run-btn integration-run" :disabled="acBusy||acIsActive(acTask)" @click="acGenerate"><Play :size="16"/>{{acIsActive(acTask)?'处理中…':acTask?'重新生成':'生成验收标准'}}</button>
          <button v-if="acIsActive(acTask)" class="ghost" :disabled="acBusy" @click="acCancel"><Ban :size="14"/>取消</button>
          <span class="integration-task">
            <template v-if="acTask">任务 {{acTask.taskId}} · {{acTask.phase}} · {{acElapsed}} 秒<template v-if="acTask.attempts"> · 尝试 {{acTask.attempts}} 次</template></template>
            <template v-else>档案正文 {{current.text.length}} 字 · 生成上限 3000 字</template>
          </span>
        </div>
        <p v-if="acIsActive(acTask)" class="integration-hint"><RefreshCw :size="13"/>处理中：模型返回前无法获知真实进度，这里只显示阶段和已用时间，不显示百分比。</p>
        <div v-if="acNotice" class="integration-notice">{{acNotice}}</div>
        <div v-if="acError" class="acceptance-error integration-error">
          <b>{{acError}}</b>
          <div v-if="acTask&&!acIsActive(acTask)" class="error-actions">
            <button v-if="acTask.retryable" class="ghost" @click="acRetry"><RefreshCw :size="13"/>重试</button>
            <button class="ghost" @click="acFallback"><Database :size="13"/>规则流程</button>
            <button class="ghost" @click="acHandoff"><UserCheck :size="13"/>转人工</button>
          </div>
        </div>
        <div v-if="acTask?.degraded" class="degraded-banner"><b>非 AI 结果</b><span>{{acTask.degradeReason||'规则流程生成，字段可能不完整，需要人工补全。'}}</span></div>
        <div v-else-if="acTask?.status==='SUCCEEDED'" class="uncertain-banner"><CircleAlert :size="15"/><span>AI 生成结果，需人工核验：确认每条引用都来自原文、边界条件已覆盖，再保存到档案。</span></div>

        <div v-if="acEditMode&&acDraft" class="acceptance-edit">
          <div class="edit-toolbar"><b>编辑结果（人工核对后保存）</b><div><button class="ghost" @click="acCancelEdit">取消编辑</button><button class="run-btn small" :disabled="acBusy" @click="acSaveEdit"><Save :size="14"/>保存修改</button></div></div>
          <label>摘要</label><el-input v-model="acDraft.summary" type="textarea" :rows="2" placeholder="摘要"/>
          <div v-for="(ac,i) in acDraft.acceptanceCriteria" :key="'c'+i" class="edit-grid">
            <div class="edit-card-head"><b>验收标准 {{i+1}}</b><button class="ghost danger" @click="acRemoveCriterion(i)"><Trash2 :size="13"/>删除</button></div>
            <div class="edit-row"><el-input v-model="ac.id" placeholder="编号"/><el-input v-model="ac.title" placeholder="标题"/><el-select v-model="ac.priority"><el-option label="must" value="must"/><el-option label="should" value="should"/><el-option label="could" value="could"/></el-select></div>
            <el-input v-model="ac.given" type="textarea" :rows="1" placeholder="Given"/>
            <el-input v-model="ac.when" type="textarea" :rows="1" placeholder="When"/>
            <el-input v-model="ac.then" type="textarea" :rows="1" placeholder="Then"/>
            <el-input v-model="ac.sourceQuote" placeholder="原文引用（必须逐字来自需求原文）"/>
          </div>
          <button class="ghost" @click="acAddCriterion">添加验收标准</button>
          <div v-for="(ts,i) in acDraft.testSamples" :key="'s'+i" class="edit-grid">
            <div class="edit-card-head"><b>测试样例 {{i+1}}</b><button class="ghost danger" @click="acRemoveSample(i)"><Trash2 :size="13"/>删除</button></div>
            <div class="edit-row"><el-input v-model="ts.id" placeholder="编号"/><el-select v-model="ts.kind"><el-option label="normal" value="normal"/><el-option label="boundary" value="boundary"/><el-option label="exception" value="exception"/></el-select></div>
            <el-input v-model="ts.input" placeholder="输入"/>
            <el-input v-model="ts.expected" placeholder="预期结果"/>
            <el-input v-model="ts.sourceQuote" placeholder="原文引用"/>
          </div>
          <button class="ghost" @click="acAddSample">添加测试样例</button>
          <label>待确认问题（每行一条）</label><el-input v-model="acQuestionsText" type="textarea" :rows="3"/>
          <label>本次限制（每行一条）</label><el-input v-model="acLimitsText" type="textarea" :rows="2"/>
        </div>

        <div v-else-if="acTask?.report" class="integration-result">
          <AcceptanceResult :report="acTask.report" :checks="acTask.checks" :meta="acTaskMeta"/>
        </div>
        <div v-if="acTask&&!acEditMode&&!acIsActive(acTask)" class="integration-actions">
          <button v-if="acTask.actions.includes('edit')" class="ghost" @click="acBeginEdit"><Pencil :size="14"/>编辑</button>
          <button v-if="acTask.actions.includes('apply')" class="run-btn small" :disabled="acBusy||acTask.saved" @click="acApply"><Save :size="14"/>{{acTask.saved?'已保存到档案':'保存到档案'}}</button>
          <button v-if="acTask.actions.includes('retry')" class="ghost" :disabled="acBusy" @click="acRetry"><RefreshCw :size="14"/>重新生成</button>
          <button v-if="acTask.actions.includes('fallback')" class="ghost" :disabled="acBusy" @click="acFallback"><Database :size="14"/>规则流程</button>
          <button v-if="acTask.actions.includes('handoff')" class="ghost" :disabled="acBusy" @click="acHandoff"><UserCheck :size="14"/>转人工</button>
          <button v-if="acTask.actions.includes('discard')" class="ghost danger" :disabled="acBusy" @click="acDiscard"><Ban :size="14"/>放弃结果</button>
        </div>
        <p v-if="acTask?.saved" class="saved-note"><CheckCircle2 :size="14"/>已保存到档案：{{acTask.savedAt}}（任务 {{acTask.taskId}}）</p>

        <div v-if="!acTask&&acSaved?.saved&&acSaved.acceptance" class="integration-saved">
          <p class="saved-note"><CheckCircle2 :size="14"/>档案中已保存的验收标准 · {{acSaved.savedAt}} · 任务 {{acSaved.acceptance.taskId}}</p>
          <AcceptanceResult :report="acSaved.acceptance.report" :checks="acSaved.acceptance.checks"/>
        </div>

        <div v-if="acTask&&acTask.sources.length" class="integration-sources">
          <span class="section-kicker">SOURCES / 检索来源</span>
          <ul><li v-for="s in acTask.sources" :key="s.id"><b>[{{s.id}}]</b> {{s.source}} / {{s.title}} · 得分 {{s.score}}</li></ul>
          <p>来源为当前档案审查时使用的检索片段，随任务快照保存，便于核对生成依据。</p>
        </div>
        <div v-else-if="acTask" class="integration-sources muted">本次任务的来源只有档案原文与逐条引用（未使用检索片段）。</div>

        <div v-if="acTaskList.length>1" class="integration-history">
          <span class="section-kicker">TASK HISTORY / 本档案任务</span>
          <button v-for="t in acTaskList" :key="t.taskId" class="task-row" :class="{active:t.taskId===acTask?.taskId}" @click="acOpenTask(t)">
            <span class="task-status" :class="t.status">{{t.statusLabel}}</span>
            <span class="task-id">{{t.taskId}}</span>
            <span class="task-meta">{{t.mode}} · {{t.attempts}} 次尝试 · {{Math.round((t.durationMs||0)/1000)}} 秒<template v-if="t.degraded"> · 降级</template><template v-if="t.decision==='DISCARDED'"> · 已放弃</template></span>
          </button>
        </div>
      </section>
    </section>
    <section v-else-if="page==='agent'" class="content agent-page">
      <div class="page-intro"><div><div class="eyebrow">AGENT / TOOL CALLING</div><h2>档案分析助手</h2><p>用自然语言询问审查档案的风险情况。Agent 先调用工具取数，再给出可核对的结论；删除档案需要你确认。</p></div><div class="archive-note"><Sparkles :size="16"/><span>单 Agent · 5 个工具</span></div></div>
      <div class="agent-grid">
        <div class="panel agent-ask"><div class="card-head"><div><span class="section-kicker">ASK</span><h3>这次想问什么</h3><p class="card-subtitle">统计类问题必须先调用 compute_risk_stats；工具结果由程序校验。</p></div></div>
          <el-input v-model="agentQuestion" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="例如：现在有多少份档案，风险分布如何？" :disabled="agentLoading"/>
          <div class="agent-examples"><span>示例：</span><button @click="agentQuestion='现在有多少份档案，风险分布如何？'">风险分布</button><button @click="agentQuestion='最近一条档案讲了什么，最严重的问题是什么？'">最近档案</button><button @click="agentQuestion='知识库里文件上传有什么限制？'">知识库</button></div>
          <button class="run-btn" :disabled="agentLoading" @click="askAgent"><Sparkles :size="16"/>{{agentLoading?'Agent 运行中…':'开始分析'}}</button>
          <p class="agent-note">任务编号：{{agentRun?agentRun.taskId:'—'}} · 状态：{{agentRun?agentStatus(agentRun.status):'未开始'}}</p>
        </div>
        <div class="panel agent-answer"><div class="card-head"><div><span class="section-kicker">ANSWER</span><h3>分析结果</h3></div><span v-if="agentRun" class="status-chip" :class="agentRun.status">{{agentStatus(agentRun.status)}}</span></div>
          <p v-if="!agentRun" class="agent-empty">还没有运行记录。输入问题后点击“开始分析”。</p>
          <template v-else>
            <p class="agent-text">{{agentRun.answer}}</p>
            <div v-if="agentRun.confirm" class="agent-confirm"><b>等待确认：{{agentRun.confirm.tool}}</b><span>{{agentRun.confirm.impact}}</span></div>
            <h4 class="agent-steps-title">工具轨迹（{{agentRun.steps.length}}）</h4>
            <ul class="agent-steps"><li v-for="(step,i) in agentRun.steps" :key="i"><b :class="step.status">{{step.tool}}</b><span>{{step.resultPreview}}</span><small>{{step.durationMs}} ms</small></li></ul>
          </template>
        </div>
      </div>
    </section>
    <section v-else-if="page==='acceptance'" class="content acceptance-page">
      <div class="page-intro">
        <div><div class="eyebrow">ACCEPTANCE CRITERIA / CORE AI</div><h2>把需求变成可验收的测试</h2><p>实验7 的同步原型入口：输入一段软件需求，生成带原文引用的验收标准（Given / When / Then）和正常、边界、异常三类测试样例；信息不足或超出范围时给出待确认问题，而不是编造。正式使用请从审查档案发起，那里有任务状态、取消、重试、降级与保存。</p></div>
        <div class="archive-note"><button class="ghost" @click="page='history';loadHistory()"><FileCheck2 :size="16"/>从审查档案生成（集成入口）</button><span>{{acVersion==='original'?'初版 Prompt':acVersion==='rule'?'无 AI 基线':'修订版 Prompt'}} · {{acRun?acRun.model:'qwen-plus'}}</span></div>
      </div>
      <div class="acceptance-grid">
        <div class="panel acceptance-input">
          <div class="card-head"><div><span class="section-kicker">REQUIREMENT INPUT</span><h3>需求原文</h3><p class="card-subtitle">最多 3000 字；每条验收标准都必须能在原文中找到依据。</p></div><button class="ghost" :disabled="acLoading" @click="acText='';acRun=null"><RotateCcw :size="14"/>清空</button></div>
          <el-input v-model="acText" type="textarea" :rows="13" maxlength="3000" show-word-limit :disabled="acLoading" placeholder="例如：用户可以上传 DOCX 或 PDF 格式的需求文档，单个文件不超过 10MB……"/>
          <div class="agent-examples"><span>示例：</span><button v-for="s in acSamples" :key="s.label" @click="acText=s.text;acRun=null">{{s.label}}</button></div>
          <div class="acceptance-config"><label>生成方案</label><el-select v-model="acVersion" :disabled="acLoading"><el-option label="修订版（v2）" value="revised"/><el-option label="初版（v1）" value="original"/><el-option label="无 AI 基线" value="rule"/></el-select></div>
          <button class="run-btn acceptance-run-btn" :disabled="acLoading" @click="generateAcceptance"><Play :size="16"/>{{acLoading?'生成中…':'生成验收标准'}}</button>
          <p class="agent-note">运行编号：{{acRun?acRun.runId:'—'}} · 状态：{{acRun?acStatus(acRun.status):'未开始'}} · 耗时 {{acRun?acRun.durationMs:0}} ms</p>
        </div>
        <div class="panel acceptance-result">
          <div class="card-head"><div><span class="section-kicker">VERIFICATION OUTPUT</span><h3>验收标准与测试样例</h3></div><span v-if="acRun" class="status-chip" :class="acRun.status">{{acStatus(acRun.status)}}</span></div>
          <p v-if="!acRun" class="agent-empty">还没有生成记录。输入需求后点击“生成验收标准”。</p>
          <template v-else>
            <p v-if="acRun.error" class="acceptance-error">{{acRun.error}}</p>
            <AcceptanceResult v-if="acRun.report" :report="acRun.report" :checks="acRun.checks" :meta="acRunMeta"/>
          </template>
        </div>
      </div>
    </section>
    <section v-else-if="page==='history'" class="content history-page"><div class="page-intro"><div><div class="eyebrow">03 / REVIEW ARCHIVE</div><h2>审查档案</h2><p>每一次审查都保留输入、风险摘要和版本轨迹，方便回看需求如何变得清晰。</p></div><div class="archive-note"><History :size="16"/><span>{{history.length}} 份本地档案</span></div></div><div v-if="!history.length" class="empty panel"><History :size="36"/><h3>还没有审查档案</h3><p>完成一次审查后，结果会出现在这里。</p><button class="run-btn small" @click="page='review'">开始第一次审查</button></div><div v-else class="archive-list"><article v-for="item in history" :key="item.id" class="archive-row panel"><div class="archive-mark"><FileText :size="18"/></div><div class="archive-main"><span>{{new Date(item.createdAt).toLocaleString('zh-CN')}} · {{item.id.slice(0,8)}}</span><h3>{{item.summary}}</h3></div><div class="archive-risk" :class="item.riskLevel">{{riskLabel(item.riskLevel)}}</div><div class="archive-counts"><b class="high">{{item.counts.high||0}}</b><b class="medium">{{item.counts.medium||0}}</b><b class="low">{{item.counts.low||0}}</b></div><button class="icon-btn" :disabled="!!exporting" @click="exportPdf(item.id)" :aria-label="exporting===item.id?'正在导出 PDF':'导出 PDF 报告'" title="导出 PDF 报告"><Download :size="17"/></button><button class="icon-btn" @click="openHistory(item.id)" aria-label="查看档案"><ChevronRight :size="17"/></button><button class="icon-btn danger" @click="remove(item.id)" aria-label="删除档案"><Trash2 :size="16"/></button></article></div></section>
    <el-alert v-if="error" class="error" type="error" :closable="false" show-icon>{{error}}</el-alert>
  </main>
</div>
</template>
