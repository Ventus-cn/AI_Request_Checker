const props = defineProps();
const kind = (k) => k === 'insufficient' ? '信息不足' : k === 'out_of_scope' ? '超出范围' : k === 'normal' ? '正常需求' : '未标注';
const testKind = (k) => k === 'normal' ? '正常' : k === 'boundary' ? '边界' : '异常';
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "acceptance-body" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "acceptance-summary" },
});
(props.report.summary);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "acceptance-meta" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(__VLS_ctx.kind(props.report.requirementKind));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(props.report.acceptanceCriteria?.length || 0);
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
(props.report.testSamples?.length || 0);
for (const [m] of __VLS_getVForSourceType((props.meta || []))) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        key: (m),
    });
    (m);
}
if (props.checks) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "acceptance-checks" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: ({ pass: props.checks.schemaOk }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (props.checks.schemaOk ? '通过' : '未通过');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: ({ pass: props.checks.groundingOk }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (props.checks.groundingOk ? '可核验' : '不可核验');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: ({ pass: props.checks.structureOk }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (props.checks.structureOk ? '完整' : '有缺项');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: ({ pass: props.checks.coverageOk }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    (props.checks.coverageOk ? '正常/边界/异常' : '不完整');
}
if (props.checks && props.checks.messages.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "check-messages" },
    });
    (props.checks.messages.join('；'));
}
if (props.report.acceptanceCriteria?.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "acceptance-list" },
    });
    for (const [ac] of __VLS_getVForSourceType((props.report.acceptanceCriteria))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
            key: (ac.id),
            ...{ class: "ac-card" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "ac-head" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
        (ac.id);
        (ac.title);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "ac-priority" },
            ...{ class: (ac.priority) },
        });
        (ac.priority);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "ac-gwt" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (ac.given);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "ac-gwt" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (ac.when);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "ac-gwt" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (ac.then);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "ac-quote" },
            ...{ class: ({ unverified: props.checks && !props.checks.groundingOk }) },
        });
        (ac.sourceQuote);
    }
}
if (props.report.testSamples?.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "acceptance-tests" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
    for (const [ts] of __VLS_getVForSourceType((props.report.testSamples))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
            key: (ts.id),
            ...{ class: "ts-row" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "kind-badge" },
            ...{ class: (ts.kind) },
        });
        (__VLS_ctx.testKind(ts.kind));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
        (ts.id);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        (ts.input);
        (ts.expected);
    }
}
if (props.report.openQuestions?.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "acceptance-questions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
    for (const [q, i] of __VLS_getVForSourceType((props.report.openQuestions))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
            key: (i),
        });
        (q);
    }
}
if (props.report.limits?.length) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "acceptance-questions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
    for (const [q, i] of __VLS_getVForSourceType((props.report.limits))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
            key: (i),
        });
        (q);
    }
}
/** @type {__VLS_StyleScopedClasses['acceptance-body']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-summary']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-checks']} */ ;
/** @type {__VLS_StyleScopedClasses['check-messages']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-list']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-card']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-head']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-priority']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-gwt']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-gwt']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-gwt']} */ ;
/** @type {__VLS_StyleScopedClasses['ac-quote']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-tests']} */ ;
/** @type {__VLS_StyleScopedClasses['ts-row']} */ ;
/** @type {__VLS_StyleScopedClasses['kind-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-questions']} */ ;
/** @type {__VLS_StyleScopedClasses['acceptance-questions']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            kind: kind,
            testKind: testKind,
        };
    },
    __typeProps: {},
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
    __typeProps: {},
});
; /* PartiallyEnd: #4569/main.vue */
