<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ShieldCheck, ClipboardCheck, History, Upload, Play, RotateCcw, Send, Trash2, ArrowLeft, FileText, ChevronRight, CircleAlert, CheckCircle2, ScanSearch } from 'lucide-vue-next'

type Issue={id:string;type:string;severity:string;quote:string;location:string;explanation:string;missingConditions:string[];questions:string[];acceptanceCriteria:string[];relatedRoles:string[];reworkRisk:string}
type Report={summary:string;riskLevel:string;counts:{high:number;medium:number;low:number};issues:Issue[]}
type Review={id:string;text:string;mode:string;createdAt:string;report:Report;versions:Report[]}
type HistoryItem={id:string;createdAt:string;summary:string;riskLevel:string;counts:{high:number;medium:number;low:number}}
const API=import.meta.env.VITE_API_BASE_URL||'http://localhost:8080/api'
const page=ref<'review'|'result'|'history'>('review'); const text=ref(''); const mode=ref('全面审查'); const loading=ref(false); const uploading=ref(false); const error=ref(''); const fileName=ref(''); const current=ref<Review|null>(null); const history=ref<HistoryItem[]>([]); const filter=ref('all'); const question=ref('')
const typeNames:Record<string,string>={ambiguous_term:'模糊表达',missing_boundary:'边界缺口',conflict:'需求冲突',permission:'角色权限',testability:'可测试性',security:'安全风险',operational:'运营异常'}
const visibleIssues=computed(()=>current.value?.report.issues.filter(i=>filter.value==='all'||i.type===filter.value)||[])
const riskLabel=(x:string)=>x==='high'?'高风险':x==='medium'?'中风险':'低风险'
const issueTypes=computed(()=>Object.entries(typeNames).filter(([key])=>current.value?.report.issues.some(i=>i.type===key)))
async function request(path:string,options:RequestInit={}){const res=await fetch(API+path,options);const data=await res.json().catch(()=>({error:'服务器返回无效内容'}));if(!res.ok)throw new Error(data.error||'请求失败');return data}
async function upload(file:any){uploading.value=true;error.value='';try{if(file.size>10*1024*1024)throw new Error('文件不能超过 10 MB');const form=new FormData();form.append('file',file.raw);const data=await request('/reviews/upload',{method:'POST',body:form});text.value=data.text;fileName.value=data.fileName;ElMessage.success(`已解析 ${data.characters} 个字符`)}catch(e:any){error.value=e.message}finally{uploading.value=false}}
async function review(){if(!text.value.trim()){error.value='请先输入或上传需求文本';return}if(text.value.length>20000){error.value='需求文本不能超过 20000 个字符';return}loading.value=true;error.value='';try{current.value=await request('/reviews',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:text.value,mode:mode.value})});filter.value='all';page.value='result'}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function follow(){if(!question.value.trim()||!current.value)return;loading.value=true;try{current.value=await request(`/reviews/${current.value.id}/follow-up`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:question.value})});question.value='';ElMessage.success('新版本已生成')}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function loadHistory(){try{history.value=await request('/reviews')}catch(e:any){error.value=e.message}}
async function openHistory(id:string){loading.value=true;try{current.value=await request(`/reviews/${id}`);page.value='result'}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function remove(id:string){await ElMessageBox.confirm('删除后不可恢复，确认删除？','删除审查档案',{type:'warning'});try{await request(`/reviews/${id}`,{method:'DELETE'});await loadHistory();ElMessage.success('档案已删除')}catch(e:any){error.value=e.message}}
function reset(){text.value='';fileName.value='';current.value=null;error.value='';page.value='review'}
function editAgain(){if(current.value){text.value=current.value.text;page.value='review'}}
onMounted(loadHistory)
</script>
<template>
<div class="app-shell">
  <aside class="sidebar">
    <div class="brand"><div class="brand-mark"><ShieldCheck :size="19"/></div><div><strong>审查台</strong><span>REQUIREMENT REVIEW</span></div></div>
    <div class="workspace-label">工作区</div>
    <button class="side-link" :class="{active:page==='review'||page==='result'}" @click="page=current?'result':'review'"><ClipboardCheck :size="17"/><span>新建审查</span><ChevronRight :size="14"/></button>
    <button class="side-link" :class="{active:page==='history'}" @click="page='history';loadHistory()"><History :size="17"/><span>审查档案</span><small>{{history.length}}</small></button>
    <div class="sidebar-foot"><div class="status-dot"></div><div><b>本地工作区</b><span>Mock / Qwen 可用</span></div></div>
  </aside>
  <main class="main-shell">
    <header class="topbar"><div><span class="crumb">工作区 / {{page==='history'?'审查档案':page==='result'?'审查报告':'新建审查'}}</span><h1>{{page==='history'?'审查档案':page==='result'?'需求质量报告':'开始一次需求审查'}}</h1></div><div class="top-meta"><span class="secure"><CheckCircle2 :size="14"/>后端密钥隔离</span><span class="avatar">AI</span></div></header>
    <section v-if="page==='review'" class="content review-layout">
      <div class="intro"><div class="eyebrow">01 / INPUT & SCOPE</div><h2>把需求交给审查台</h2><p>输入原始需求，系统会从边界、角色、可测试性和运营风险四个维度建立审查证据。</p></div>
      <div class="input-card panel"><div class="card-head"><div><span class="section-kicker">SOURCE DOCUMENT</span><h3>需求原文</h3></div><button class="ghost" @click="reset"><RotateCcw :size="14"/>清空</button></div><el-input v-model="text" type="textarea" :rows="15" maxlength="20000" show-word-limit placeholder="粘贴需求原文，保留完整上下文和业务约束……"/><div class="upload-line"><el-upload :auto-upload="false" :show-file-list="false" accept=".docx,.pdf" :on-change="upload"><button class="upload-btn"><Upload :size="15"/>导入 Word / PDF</button></el-upload><span v-if="fileName" class="file-tag"><FileText :size="14"/>{{fileName}}</span><span v-else>支持文字型 PDF，单文件不超过 10 MB</span></div></div>
      <aside class="control-card"><div class="section-kicker">REVIEW PROTOCOL</div><h3>审查协议</h3><p>选择本次审查的关注范围。结果会保存为一份可追踪档案。</p><label>分析视角</label><el-select v-model="mode"><el-option label="全面审查" value="全面审查"/><el-option label="重点关注可测试性" value="可测试性"/><el-option label="重点关注安全与权限" value="安全与权限"/></el-select><div class="protocol-list"><div><span>引用证据</span><b>原文保留</b></div><div><span>输出格式</span><b>结构化报告</b></div><div><span>模型通道</span><b>Mock / Qwen</b></div></div><button class="run-btn" :disabled="loading" @click="review"><Play :size="16"/>{{loading?'审查处理中':'开始审查'}}<span>⌘ ↵</span></button></aside>
      <div class="method-note"><ScanSearch :size="17"/><div><b>审查方式</b><span>系统不会改写原文。每个问题都必须绑定引用、缺失条件和可测试验收标准。</span></div></div>
    </section>
    <section v-else-if="page==='result'&&current" class="content result-page">
      <div class="result-toolbar"><button class="back-link" @click="page='review'"><ArrowLeft :size="15"/>返回需求原文</button><div class="toolbar-actions"><span class="version-chip">{{current.mode}} · {{current.versions.length+1}} 个版本</span><button class="outline-btn" @click="editAgain">修改后重审</button></div></div>
      <div class="report-hero"><div><div class="eyebrow">02 / REVIEW REPORT</div><h2>需求质量审查报告</h2><p>{{new Date(current.createdAt).toLocaleString('zh-CN')}} · ID {{current.id.slice(0,8)}}</p></div><div class="risk-score" :class="current.report.riskLevel"><span>总体判断</span><strong>{{riskLabel(current.report.riskLevel)}}</strong><small>{{current.report.issues.length}} 个待处理问题</small></div></div>
      <div class="metric-row"><div class="metric"><span>高风险</span><strong class="high">{{current.report.counts.high}}</strong><small>需要优先确认</small></div><div class="metric"><span>中风险</span><strong class="medium">{{current.report.counts.medium}}</strong><small>建议进入评审</small></div><div class="metric"><span>低风险</span><strong class="low">{{current.report.counts.low}}</strong><small>可在迭代中完善</small></div><div class="metric summary-metric"><span>审查结论</span><strong>{{current.report.summary}}</strong></div></div>
      <div class="filter-strip"><span>问题证据</span><button :class="{selected:filter==='all'}" @click="filter='all'">全部 <b>{{current.report.issues.length}}</b></button><button v-for="([key,name]) in issueTypes" :key="key" :class="{selected:filter===key}" @click="filter=key">{{name}}</button></div>
      <div v-if="!visibleIssues.length" class="empty panel"><CheckCircle2 :size="34"/><h3>当前筛选没有待处理问题</h3><p>可以切换其他问题类型查看完整证据。</p></div>
      <article v-for="issue in visibleIssues" :key="issue.id" class="evidence-card panel"><div class="evidence-top"><div><span class="issue-id">{{issue.id}} · {{typeNames[issue.type]||issue.type}}</span><h3>{{issue.explanation}}</h3></div><span class="severity" :class="issue.severity"><CircleAlert :size="14"/>{{riskLabel(issue.severity)}}</span></div><div class="quote"><span>原文证据 · {{issue.location}}</span><p>“{{issue.quote}}”</p></div><div class="evidence-grid"><div><span class="label">缺失条件</span><ul><li v-for="x in issue.missingConditions" :key="x">{{x}}</li></ul></div><div><span class="label">待确认问题</span><ul><li v-for="x in issue.questions" :key="x">{{x}}</li></ul></div><div><span class="label">验收标准</span><ul><li v-for="x in issue.acceptanceCriteria" :key="x">{{x}}</li></ul></div><div><span class="label">相关角色 / 返工风险</span><p class="roles">{{issue.relatedRoles.join(' · ')}}</p><p>{{issue.reworkRisk}}</p></div></div></article>
      <div class="follow panel"><div class="follow-copy"><span class="section-kicker">FOLLOW-UP</span><h3>继续追问这份报告</h3><p>这里可以针对当前审查结果继续提问，AI 会结合原始需求和问题证据生成新的分析版本，旧报告会自动保留。</p><div class="follow-examples"><span>可以问：</span><button @click="question='哪个问题最可能导致返工？'">哪个问题最可能导致返工？</button><button @click="question='请把高风险问题改写成验收标准'">改写成验收标准</button><button @click="question='还缺少哪些边界条件？'">补充边界条件</button></div></div><div class="follow-input"><el-input v-model="question" placeholder="输入你想进一步确认的问题……" @keyup.enter="follow"><template #prefix><span class="question-mark">?</span></template></el-input><button class="send-btn" :disabled="loading" @click="follow"><Send :size="15"/>发送</button></div></div>
    </section>
    <section v-else class="content history-page"><div class="intro"><div class="eyebrow">03 / REVIEW ARCHIVE</div><h2>审查档案</h2><p>每一次审查都保留输入、风险摘要和版本轨迹，方便回看需求如何变得清晰。</p></div><div v-if="!history.length" class="empty panel"><History :size="36"/><h3>还没有审查档案</h3><button class="run-btn small" @click="page='review'">开始第一次审查</button></div><div v-else class="archive-list"><article v-for="item in history" :key="item.id" class="archive-row panel"><div class="archive-mark"><FileText :size="18"/></div><div class="archive-main"><span>{{new Date(item.createdAt).toLocaleString('zh-CN')}} · {{item.id.slice(0,8)}}</span><h3>{{item.summary}}</h3></div><div class="archive-risk" :class="item.riskLevel">{{riskLabel(item.riskLevel)}}</div><div class="archive-counts"><b class="high">{{item.counts.high||0}}</b><b class="medium">{{item.counts.medium||0}}</b><b class="low">{{item.counts.low||0}}</b></div><button class="icon-btn" @click="openHistory(item.id)"><ChevronRight :size="17"/></button><button class="icon-btn danger" @click="remove(item.id)"><Trash2 :size="16"/></button></article></div></section>
    <el-alert v-if="error" class="error" type="error" :closable="false" show-icon>{{error}}</el-alert>
  </main>
</div>
</template>

