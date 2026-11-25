<script setup lang="ts">
type Criterion={id:string;title:string;given:string;when:string;then:string;sourceQuote:string;priority:string}
type TestSample={id:string;kind:string;input:string;expected:string;sourceQuote:string}
type Report={summary:string;requirementKind?:string;acceptanceCriteria:Criterion[];testSamples:TestSample[];openQuestions:string[];limits?:string[]}
type Checks={schemaOk:boolean;groundingOk:boolean;structureOk:boolean;coverageOk:boolean;messages:string[]}
const props=defineProps<{report:Report;checks?:Checks;meta?:string[]}>()
const kind=(k?:string)=>k==='insufficient'?'信息不足':k==='out_of_scope'?'超出范围':k==='normal'?'正常需求':'未标注'
const testKind=(k:string)=>k==='normal'?'正常':k==='boundary'?'边界':'异常'
</script>

<template>
  <div class="acceptance-body">
    <p class="acceptance-summary">{{props.report.summary}}</p>
    <div class="acceptance-meta">
      <span>类型：{{kind(props.report.requirementKind)}}</span>
      <span>验收标准 {{props.report.acceptanceCriteria?.length||0}} 条</span>
      <span>测试样例 {{props.report.testSamples?.length||0}} 条</span>
      <span v-for="m in props.meta||[]" :key="m">{{m}}</span>
    </div>
    <div v-if="props.checks" class="acceptance-checks">
      <div :class="{pass:props.checks.schemaOk}"><b>结构</b><span>{{props.checks.schemaOk?'通过':'未通过'}}</span></div>
      <div :class="{pass:props.checks.groundingOk}"><b>引用</b><span>{{props.checks.groundingOk?'可核验':'不可核验'}}</span></div>
      <div :class="{pass:props.checks.structureOk}"><b>GWT</b><span>{{props.checks.structureOk?'完整':'有缺项'}}</span></div>
      <div :class="{pass:props.checks.coverageOk}"><b>覆盖</b><span>{{props.checks.coverageOk?'正常/边界/异常':'不完整'}}</span></div>
    </div>
    <p v-if="props.checks&&props.checks.messages.length" class="check-messages">{{props.checks.messages.join('；')}}</p>
    <div v-if="props.report.acceptanceCriteria?.length" class="acceptance-list">
      <article v-for="ac in props.report.acceptanceCriteria" :key="ac.id" class="ac-card">
        <div class="ac-head"><b>{{ac.id}} · {{ac.title}}</b><span class="ac-priority" :class="ac.priority">{{ac.priority}}</span></div>
        <p class="ac-gwt"><span>Given</span>{{ac.given}}</p>
        <p class="ac-gwt"><span>When</span>{{ac.when}}</p>
        <p class="ac-gwt"><span>Then</span>{{ac.then}}</p>
        <p class="ac-quote" :class="{unverified:props.checks&&!props.checks.groundingOk}">“{{ac.sourceQuote}}”</p>
      </article>
    </div>
    <div v-if="props.report.testSamples?.length" class="acceptance-tests">
      <h4>测试样例</h4>
      <article v-for="ts in props.report.testSamples" :key="ts.id" class="ts-row">
        <span class="kind-badge" :class="ts.kind">{{testKind(ts.kind)}}</span>
        <div><b>{{ts.id}}</b><p>{{ts.input}} → {{ts.expected}}</p></div>
      </article>
    </div>
    <div v-if="props.report.openQuestions?.length" class="acceptance-questions">
      <h4>待确认问题</h4>
      <ul><li v-for="(q,i) in props.report.openQuestions" :key="i">{{q}}</li></ul>
    </div>
    <div v-if="props.report.limits?.length" class="acceptance-questions">
      <h4>本次限制</h4>
      <ul><li v-for="(q,i) in props.report.limits" :key="i">{{q}}</li></ul>
    </div>
  </div>
</template>