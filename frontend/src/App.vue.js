import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ShieldCheck, ClipboardCheck, History, Upload, Play, RotateCcw, Send, Trash2, ArrowLeft, FileText, ChevronRight, CircleAlert, CheckCircle2, ScanSearch } from 'lucide-vue-next';
const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
const page = ref('review');
const text = ref('');
const mode = ref('全面审查');
const loading = ref(false);
const uploading = ref(false);
const error = ref('');
const fileName = ref('');
const current = ref(null);
const history = ref([]);
const filter = ref('all');
const question = ref('');
const typeNames = { ambiguous_term: '模糊表达', missing_boundary: '边界缺口', conflict: '需求冲突', permission: '角色权限', testability: '可测试性', security: '安全风险', operational: '运营异常' };
const visibleIssues = computed(() => current.value?.report.issues.filter(i => filter.value === 'all' || i.type === filter.value) || []);
const riskLabel = (x) => x === 'high' ? '高风险' : x === 'medium' ? '中风险' : '低风险';
const issueTypes = computed(() => Object.entries(typeNames).filter(([key]) => current.value?.report.issues.some(i => i.type === key)));
async function request(path, options = {}) { const res = await fetch(API + path, options); const data = await res.json().catch(() => ({ error: '服务器返回无效内容' })); if (!res.ok)
    throw new Error(data.error || '请求失败'); return data; }
async function upload(file) { uploading.value = true; error.value = ''; try {
    if (file.size > 10 * 1024 * 1024)
        throw new Error('文件不能超过 10 MB');
    const form = new FormData();
    form.append('file', file.raw);
    const data = await request('/reviews/upload', { method: 'POST', body: form });
    text.value = data.text;
    fileName.value = data.fileName;
    ElMessage.success(`已解析 ${data.characters} 个字符`);
}
catch (e) {
    error.value = e.message;
}
finally {
    uploading.value = false;
} }
async function review() { if (!text.value.trim()) {
    error.value = '请先输入或上传需求文本';
    return;
} if (text.value.length > 20000) {
    error.value = '需求文本不能超过 20000 个字符';
    return;
} loading.value = true; error.value = ''; try {
    current.value = await request('/reviews', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: text.value, mode: mode.value }) });
    filter.value = 'all';
    page.value = 'result';
}
catch (e) {
    error.value = e.message;
}
finally {
    loading.value = false;
} }
async function follow() { if (!question.value.trim() || !current.value)
    return; loading.value = true; try {
    current.value = await request(`/reviews/${current.value.id}/follow-up`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: question.value }) });
    question.value = '';
    ElMessage.success('新版本已生成');
}
catch (e) {
    error.value = e.message;
}
finally {
    loading.value = false;
} }
async function loadHistory() { try {
    history.value = await request('/reviews');
}
catch (e) {
    error.value = e.message;
} }
async function openHistory(id) { loading.value = true; try {
    current.value = await request(`/reviews/${id}`);
    page.value = 'result';
}
catch (e) {
    error.value = e.message;
}
finally {
    loading.value = false;
} }
async function remove(id) { await ElMessageBox.confirm('删除后不可恢复，确认删除？', '删除审查档案', { type: 'warning' }); try {
    await request(`/reviews/${id}`, { method: 'DELETE' });
    await loadHistory();
    ElMessage.success('档案已删除');
}
catch (e) {
    error.value = e.message;
} }
function reset() { text.value = ''; fileName.value = ''; current.value = null; error.value = ''; page.value = 'review'; }
function editAgain() { if (current.value) {
    text.value = current.value.text;
    page.value = 'review';
} }
onMounted(loadHistory);
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "app-shell" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
    ...{ class: "sidebar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "brand-mark" },
});
const __VLS_0 = {}.ShieldCheck;
/** @type {[typeof __VLS_components.ShieldCheck, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({
    size: (19),
}));
const __VLS_2 = __VLS_1({
    size: (19),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "workspace-label" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.page = __VLS_ctx.current ? 'result' : 'review';
        } },
    ...{ class: "side-link" },
    ...{ class: ({ active: __VLS_ctx.page === 'review' || __VLS_ctx.page === 'result' }) },
});
const __VLS_4 = {}.ClipboardCheck;
/** @type {[typeof __VLS_components.ClipboardCheck, ]} */ ;
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
    size: (17),
}));
const __VLS_6 = __VLS_5({
    size: (17),
}, ...__VLS_functionalComponentArgsRest(__VLS_5));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
const __VLS_8 = {}.ChevronRight;
/** @type {[typeof __VLS_components.ChevronRight, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    size: (14),
}));
const __VLS_10 = __VLS_9({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.page = 'history';
            __VLS_ctx.loadHistory();
        } },
    ...{ class: "side-link" },
    ...{ class: ({ active: __VLS_ctx.page === 'history' }) },
});
const __VLS_12 = {}.History;
/** @type {[typeof __VLS_components.History, ]} */ ;
// @ts-ignore
const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
    size: (17),
}));
const __VLS_14 = __VLS_13({
    size: (17),
}, ...__VLS_functionalComponentArgsRest(__VLS_13));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
(__VLS_ctx.history.length);
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "sidebar-foot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "status-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({
    ...{ class: "main-shell" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "topbar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "crumb" },
});
(__VLS_ctx.page === 'history' ? '审查档案' : __VLS_ctx.page === 'result' ? '审查报告' : '新建审查');
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({});
(__VLS_ctx.page === 'history' ? '审查档案' : __VLS_ctx.page === 'result' ? '需求质量报告' : '开始一次需求审查');
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "top-meta" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "secure" },
});
const __VLS_16 = {}.CheckCircle2;
/** @type {[typeof __VLS_components.CheckCircle2, ]} */ ;
// @ts-ignore
const __VLS_17 = __VLS_asFunctionalComponent(__VLS_16, new __VLS_16({
    size: (14),
}));
const __VLS_18 = __VLS_17({
    size: (14),
}, ...__VLS_functionalComponentArgsRest(__VLS_17));
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "avatar" },
});
if (__VLS_ctx.page === 'review') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content review-layout" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "intro" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "eyebrow" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-card panel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "card-head" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "section-kicker" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.reset) },
        ...{ class: "ghost" },
    });
    const __VLS_20 = {}.RotateCcw;
    /** @type {[typeof __VLS_components.RotateCcw, ]} */ ;
    // @ts-ignore
    const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
        size: (14),
    }));
    const __VLS_22 = __VLS_21({
        size: (14),
    }, ...__VLS_functionalComponentArgsRest(__VLS_21));
    const __VLS_24 = {}.ElInput;
    /** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
    // @ts-ignore
    const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({
        modelValue: (__VLS_ctx.text),
        type: "textarea",
        rows: (15),
        maxlength: "20000",
        showWordLimit: true,
        placeholder: "粘贴需求原文，保留完整上下文和业务约束……",
    }));
    const __VLS_26 = __VLS_25({
        modelValue: (__VLS_ctx.text),
        type: "textarea",
        rows: (15),
        maxlength: "20000",
        showWordLimit: true,
        placeholder: "粘贴需求原文，保留完整上下文和业务约束……",
    }, ...__VLS_functionalComponentArgsRest(__VLS_25));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "upload-line" },
    });
    const __VLS_28 = {}.ElUpload;
    /** @type {[typeof __VLS_components.ElUpload, typeof __VLS_components.elUpload, typeof __VLS_components.ElUpload, typeof __VLS_components.elUpload, ]} */ ;
    // @ts-ignore
    const __VLS_29 = __VLS_asFunctionalComponent(__VLS_28, new __VLS_28({
        autoUpload: (false),
        showFileList: (false),
        accept: ".docx,.pdf",
        onChange: (__VLS_ctx.upload),
    }));
    const __VLS_30 = __VLS_29({
        autoUpload: (false),
        showFileList: (false),
        accept: ".docx,.pdf",
        onChange: (__VLS_ctx.upload),
    }, ...__VLS_functionalComponentArgsRest(__VLS_29));
    __VLS_31.slots.default;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ class: "upload-btn" },
    });
    const __VLS_32 = {}.Upload;
    /** @type {[typeof __VLS_components.Upload, ]} */ ;
    // @ts-ignore
    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
        size: (15),
    }));
    const __VLS_34 = __VLS_33({
        size: (15),
    }, ...__VLS_functionalComponentArgsRest(__VLS_33));
    var __VLS_31;
    if (__VLS_ctx.fileName) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "file-tag" },
        });
        const __VLS_36 = {}.FileText;
        /** @type {[typeof __VLS_components.FileText, ]} */ ;
        // @ts-ignore
        const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({
            size: (14),
        }));
        const __VLS_38 = __VLS_37({
            size: (14),
        }, ...__VLS_functionalComponentArgsRest(__VLS_37));
        (__VLS_ctx.fileName);
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
        ...{ class: "control-card" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "section-kicker" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({});
    const __VLS_40 = {}.ElSelect;
    /** @type {[typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, ]} */ ;
    // @ts-ignore
    const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({
        modelValue: (__VLS_ctx.mode),
    }));
    const __VLS_42 = __VLS_41({
        modelValue: (__VLS_ctx.mode),
    }, ...__VLS_functionalComponentArgsRest(__VLS_41));
    __VLS_43.slots.default;
    const __VLS_44 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({
        label: "全面审查",
        value: "全面审查",
    }));
    const __VLS_46 = __VLS_45({
        label: "全面审查",
        value: "全面审查",
    }, ...__VLS_functionalComponentArgsRest(__VLS_45));
    const __VLS_48 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
        label: "重点关注可测试性",
        value: "可测试性",
    }));
    const __VLS_50 = __VLS_49({
        label: "重点关注可测试性",
        value: "可测试性",
    }, ...__VLS_functionalComponentArgsRest(__VLS_49));
    const __VLS_52 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    const __VLS_53 = __VLS_asFunctionalComponent(__VLS_52, new __VLS_52({
        label: "重点关注安全与权限",
        value: "安全与权限",
    }));
    const __VLS_54 = __VLS_53({
        label: "重点关注安全与权限",
        value: "安全与权限",
    }, ...__VLS_functionalComponentArgsRest(__VLS_53));
    var __VLS_43;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "protocol-list" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.review) },
        ...{ class: "run-btn" },
        disabled: (__VLS_ctx.loading),
    });
    const __VLS_56 = {}.Play;
    /** @type {[typeof __VLS_components.Play, ]} */ ;
    // @ts-ignore
    const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({
        size: (16),
    }));
    const __VLS_58 = __VLS_57({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_57));
    (__VLS_ctx.loading ? '审查处理中' : '开始审查');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "method-note" },
    });
    const __VLS_60 = {}.ScanSearch;
    /** @type {[typeof __VLS_components.ScanSearch, ]} */ ;
    // @ts-ignore
    const __VLS_61 = __VLS_asFunctionalComponent(__VLS_60, new __VLS_60({
        size: (17),
    }));
    const __VLS_62 = __VLS_61({
        size: (17),
    }, ...__VLS_functionalComponentArgsRest(__VLS_61));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
}
else if (__VLS_ctx.page === 'result' && __VLS_ctx.current) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content result-page" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "result-toolbar" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                __VLS_ctx.page = 'review';
            } },
        ...{ class: "back-link" },
    });
    const __VLS_64 = {}.ArrowLeft;
    /** @type {[typeof __VLS_components.ArrowLeft, ]} */ ;
    // @ts-ignore
    const __VLS_65 = __VLS_asFunctionalComponent(__VLS_64, new __VLS_64({
        size: (15),
    }));
    const __VLS_66 = __VLS_65({
        size: (15),
    }, ...__VLS_functionalComponentArgsRest(__VLS_65));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "toolbar-actions" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "version-chip" },
    });
    (__VLS_ctx.current.mode);
    (__VLS_ctx.current.versions.length + 1);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.editAgain) },
        ...{ class: "outline-btn" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "report-hero" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "eyebrow" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    (new Date(__VLS_ctx.current.createdAt).toLocaleString('zh-CN'));
    (__VLS_ctx.current.id.slice(0, 8));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "risk-score" },
        ...{ class: (__VLS_ctx.current.report.riskLevel) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
    (__VLS_ctx.riskLabel(__VLS_ctx.current.report.riskLevel));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
    (__VLS_ctx.current.report.issues.length);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "metric-row" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "metric" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({
        ...{ class: "high" },
    });
    (__VLS_ctx.current.report.counts.high);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "metric" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({
        ...{ class: "medium" },
    });
    (__VLS_ctx.current.report.counts.medium);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "metric" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({
        ...{ class: "low" },
    });
    (__VLS_ctx.current.report.counts.low);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "metric summary-metric" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
    (__VLS_ctx.current.report.summary);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "filter-strip" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                __VLS_ctx.filter = 'all';
            } },
        ...{ class: ({ selected: __VLS_ctx.filter === 'all' }) },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    (__VLS_ctx.current.report.issues.length);
    for (const [[key, name]] of __VLS_getVForSourceType((__VLS_ctx.issueTypes))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.page === 'review'))
                        return;
                    if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                        return;
                    __VLS_ctx.filter = key;
                } },
            key: (key),
            ...{ class: ({ selected: __VLS_ctx.filter === key }) },
        });
        (name);
    }
    if (!__VLS_ctx.visibleIssues.length) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty panel" },
        });
        const __VLS_68 = {}.CheckCircle2;
        /** @type {[typeof __VLS_components.CheckCircle2, ]} */ ;
        // @ts-ignore
        const __VLS_69 = __VLS_asFunctionalComponent(__VLS_68, new __VLS_68({
            size: (34),
        }));
        const __VLS_70 = __VLS_69({
            size: (34),
        }, ...__VLS_functionalComponentArgsRest(__VLS_69));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    }
    for (const [issue] of __VLS_getVForSourceType((__VLS_ctx.visibleIssues))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
            key: (issue.id),
            ...{ class: "evidence-card panel" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "evidence-top" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "issue-id" },
        });
        (issue.id);
        (__VLS_ctx.typeNames[issue.type] || issue.type);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        (issue.explanation);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "severity" },
            ...{ class: (issue.severity) },
        });
        const __VLS_72 = {}.CircleAlert;
        /** @type {[typeof __VLS_components.CircleAlert, ]} */ ;
        // @ts-ignore
        const __VLS_73 = __VLS_asFunctionalComponent(__VLS_72, new __VLS_72({
            size: (14),
        }));
        const __VLS_74 = __VLS_73({
            size: (14),
        }, ...__VLS_functionalComponentArgsRest(__VLS_73));
        (__VLS_ctx.riskLabel(issue.severity));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "quote" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
        (issue.location);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        (issue.quote);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "evidence-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
        for (const [x] of __VLS_getVForSourceType((issue.missingConditions))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
                key: (x),
            });
            (x);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
        for (const [x] of __VLS_getVForSourceType((issue.questions))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
                key: (x),
            });
            (x);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
        for (const [x] of __VLS_getVForSourceType((issue.acceptanceCriteria))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
                key: (x),
            });
            (x);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "label" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "roles" },
        });
        (issue.relatedRoles.join(' · '));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        (issue.reworkRisk);
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "follow panel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "follow-copy" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "section-kicker" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "follow-examples" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                __VLS_ctx.question = '哪个问题最可能导致返工？';
            } },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                __VLS_ctx.question = '请把高风险问题改写成验收标准';
            } },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                __VLS_ctx.question = '还缺少哪些边界条件？';
            } },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "follow-input" },
    });
    const __VLS_76 = {}.ElInput;
    /** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
    // @ts-ignore
    const __VLS_77 = __VLS_asFunctionalComponent(__VLS_76, new __VLS_76({
        ...{ 'onKeyup': {} },
        modelValue: (__VLS_ctx.question),
        placeholder: "输入你想进一步确认的问题……",
    }));
    const __VLS_78 = __VLS_77({
        ...{ 'onKeyup': {} },
        modelValue: (__VLS_ctx.question),
        placeholder: "输入你想进一步确认的问题……",
    }, ...__VLS_functionalComponentArgsRest(__VLS_77));
    let __VLS_80;
    let __VLS_81;
    let __VLS_82;
    const __VLS_83 = {
        onKeyup: (__VLS_ctx.follow)
    };
    __VLS_79.slots.default;
    {
        const { prefix: __VLS_thisSlot } = __VLS_79.slots;
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "question-mark" },
        });
    }
    var __VLS_79;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.follow) },
        ...{ class: "send-btn" },
        disabled: (__VLS_ctx.loading),
    });
    const __VLS_84 = {}.Send;
    /** @type {[typeof __VLS_components.Send, ]} */ ;
    // @ts-ignore
    const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({
        size: (15),
    }));
    const __VLS_86 = __VLS_85({
        size: (15),
    }, ...__VLS_functionalComponentArgsRest(__VLS_85));
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "content history-page" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "intro" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "eyebrow" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    if (!__VLS_ctx.history.length) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty panel" },
        });
        const __VLS_88 = {}.History;
        /** @type {[typeof __VLS_components.History, ]} */ ;
        // @ts-ignore
        const __VLS_89 = __VLS_asFunctionalComponent(__VLS_88, new __VLS_88({
            size: (36),
        }));
        const __VLS_90 = __VLS_89({
            size: (36),
        }, ...__VLS_functionalComponentArgsRest(__VLS_89));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
            ...{ onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.page === 'review'))
                        return;
                    if (!!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                        return;
                    if (!(!__VLS_ctx.history.length))
                        return;
                    __VLS_ctx.page = 'review';
                } },
            ...{ class: "run-btn small" },
        });
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "archive-list" },
        });
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.history))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
                key: (item.id),
                ...{ class: "archive-row panel" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "archive-mark" },
            });
            const __VLS_92 = {}.FileText;
            /** @type {[typeof __VLS_components.FileText, ]} */ ;
            // @ts-ignore
            const __VLS_93 = __VLS_asFunctionalComponent(__VLS_92, new __VLS_92({
                size: (18),
            }));
            const __VLS_94 = __VLS_93({
                size: (18),
            }, ...__VLS_functionalComponentArgsRest(__VLS_93));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "archive-main" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
            (new Date(item.createdAt).toLocaleString('zh-CN'));
            (item.id.slice(0, 8));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
            (item.summary);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "archive-risk" },
                ...{ class: (item.riskLevel) },
            });
            (__VLS_ctx.riskLabel(item.riskLevel));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "archive-counts" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({
                ...{ class: "high" },
            });
            (item.counts.high || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({
                ...{ class: "medium" },
            });
            (item.counts.medium || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({
                ...{ class: "low" },
            });
            (item.counts.low || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(__VLS_ctx.page === 'review'))
                            return;
                        if (!!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                            return;
                        if (!!(!__VLS_ctx.history.length))
                            return;
                        __VLS_ctx.openHistory(item.id);
                    } },
                ...{ class: "icon-btn" },
            });
            const __VLS_96 = {}.ChevronRight;
            /** @type {[typeof __VLS_components.ChevronRight, ]} */ ;
            // @ts-ignore
            const __VLS_97 = __VLS_asFunctionalComponent(__VLS_96, new __VLS_96({
                size: (17),
            }));
            const __VLS_98 = __VLS_97({
                size: (17),
            }, ...__VLS_functionalComponentArgsRest(__VLS_97));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
                ...{ onClick: (...[$event]) => {
                        if (!!(__VLS_ctx.page === 'review'))
                            return;
                        if (!!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                            return;
                        if (!!(!__VLS_ctx.history.length))
                            return;
                        __VLS_ctx.remove(item.id);
                    } },
                ...{ class: "icon-btn danger" },
            });
            const __VLS_100 = {}.Trash2;
            /** @type {[typeof __VLS_components.Trash2, ]} */ ;
            // @ts-ignore
            const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({
                size: (16),
            }));
            const __VLS_102 = __VLS_101({
                size: (16),
            }, ...__VLS_functionalComponentArgsRest(__VLS_101));
        }
    }
}
if (__VLS_ctx.error) {
    const __VLS_104 = {}.ElAlert;
    /** @type {[typeof __VLS_components.ElAlert, typeof __VLS_components.elAlert, typeof __VLS_components.ElAlert, typeof __VLS_components.elAlert, ]} */ ;
    // @ts-ignore
    const __VLS_105 = __VLS_asFunctionalComponent(__VLS_104, new __VLS_104({
        ...{ class: "error" },
        type: "error",
        closable: (false),
        showIcon: true,
    }));
    const __VLS_106 = __VLS_105({
        ...{ class: "error" },
        type: "error",
        closable: (false),
        showIcon: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_105));
    __VLS_107.slots.default;
    (__VLS_ctx.error);
    var __VLS_107;
}
/** @type {__VLS_StyleScopedClasses['app-shell']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar']} */ ;
/** @type {__VLS_StyleScopedClasses['brand']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-mark']} */ ;
/** @type {__VLS_StyleScopedClasses['workspace-label']} */ ;
/** @type {__VLS_StyleScopedClasses['side-link']} */ ;
/** @type {__VLS_StyleScopedClasses['side-link']} */ ;
/** @type {__VLS_StyleScopedClasses['sidebar-foot']} */ ;
/** @type {__VLS_StyleScopedClasses['status-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['main-shell']} */ ;
/** @type {__VLS_StyleScopedClasses['topbar']} */ ;
/** @type {__VLS_StyleScopedClasses['crumb']} */ ;
/** @type {__VLS_StyleScopedClasses['top-meta']} */ ;
/** @type {__VLS_StyleScopedClasses['secure']} */ ;
/** @type {__VLS_StyleScopedClasses['avatar']} */ ;
/** @type {__VLS_StyleScopedClasses['content']} */ ;
/** @type {__VLS_StyleScopedClasses['review-layout']} */ ;
/** @type {__VLS_StyleScopedClasses['intro']} */ ;
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['input-card']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['card-head']} */ ;
/** @type {__VLS_StyleScopedClasses['section-kicker']} */ ;
/** @type {__VLS_StyleScopedClasses['ghost']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-line']} */ ;
/** @type {__VLS_StyleScopedClasses['upload-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['file-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['control-card']} */ ;
/** @type {__VLS_StyleScopedClasses['section-kicker']} */ ;
/** @type {__VLS_StyleScopedClasses['protocol-list']} */ ;
/** @type {__VLS_StyleScopedClasses['run-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['method-note']} */ ;
/** @type {__VLS_StyleScopedClasses['content']} */ ;
/** @type {__VLS_StyleScopedClasses['result-page']} */ ;
/** @type {__VLS_StyleScopedClasses['result-toolbar']} */ ;
/** @type {__VLS_StyleScopedClasses['back-link']} */ ;
/** @type {__VLS_StyleScopedClasses['toolbar-actions']} */ ;
/** @type {__VLS_StyleScopedClasses['version-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['outline-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['report-hero']} */ ;
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['risk-score']} */ ;
/** @type {__VLS_StyleScopedClasses['metric-row']} */ ;
/** @type {__VLS_StyleScopedClasses['metric']} */ ;
/** @type {__VLS_StyleScopedClasses['high']} */ ;
/** @type {__VLS_StyleScopedClasses['metric']} */ ;
/** @type {__VLS_StyleScopedClasses['medium']} */ ;
/** @type {__VLS_StyleScopedClasses['metric']} */ ;
/** @type {__VLS_StyleScopedClasses['low']} */ ;
/** @type {__VLS_StyleScopedClasses['metric']} */ ;
/** @type {__VLS_StyleScopedClasses['summary-metric']} */ ;
/** @type {__VLS_StyleScopedClasses['filter-strip']} */ ;
/** @type {__VLS_StyleScopedClasses['empty']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['evidence-card']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['evidence-top']} */ ;
/** @type {__VLS_StyleScopedClasses['issue-id']} */ ;
/** @type {__VLS_StyleScopedClasses['severity']} */ ;
/** @type {__VLS_StyleScopedClasses['quote']} */ ;
/** @type {__VLS_StyleScopedClasses['evidence-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['label']} */ ;
/** @type {__VLS_StyleScopedClasses['roles']} */ ;
/** @type {__VLS_StyleScopedClasses['follow']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['follow-copy']} */ ;
/** @type {__VLS_StyleScopedClasses['section-kicker']} */ ;
/** @type {__VLS_StyleScopedClasses['follow-examples']} */ ;
/** @type {__VLS_StyleScopedClasses['follow-input']} */ ;
/** @type {__VLS_StyleScopedClasses['question-mark']} */ ;
/** @type {__VLS_StyleScopedClasses['send-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['content']} */ ;
/** @type {__VLS_StyleScopedClasses['history-page']} */ ;
/** @type {__VLS_StyleScopedClasses['intro']} */ ;
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['empty']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['run-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['small']} */ ;
/** @type {__VLS_StyleScopedClasses['archive-list']} */ ;
/** @type {__VLS_StyleScopedClasses['archive-row']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['archive-mark']} */ ;
/** @type {__VLS_StyleScopedClasses['archive-main']} */ ;
/** @type {__VLS_StyleScopedClasses['archive-risk']} */ ;
/** @type {__VLS_StyleScopedClasses['archive-counts']} */ ;
/** @type {__VLS_StyleScopedClasses['high']} */ ;
/** @type {__VLS_StyleScopedClasses['medium']} */ ;
/** @type {__VLS_StyleScopedClasses['low']} */ ;
/** @type {__VLS_StyleScopedClasses['icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['icon-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['danger']} */ ;
/** @type {__VLS_StyleScopedClasses['error']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            ShieldCheck: ShieldCheck,
            ClipboardCheck: ClipboardCheck,
            History: History,
            Upload: Upload,
            Play: Play,
            RotateCcw: RotateCcw,
            Send: Send,
            Trash2: Trash2,
            ArrowLeft: ArrowLeft,
            FileText: FileText,
            ChevronRight: ChevronRight,
            CircleAlert: CircleAlert,
            CheckCircle2: CheckCircle2,
            ScanSearch: ScanSearch,
            page: page,
            text: text,
            mode: mode,
            loading: loading,
            error: error,
            fileName: fileName,
            current: current,
            history: history,
            filter: filter,
            question: question,
            typeNames: typeNames,
            visibleIssues: visibleIssues,
            riskLabel: riskLabel,
            issueTypes: issueTypes,
            upload: upload,
            review: review,
            follow: follow,
            loadHistory: loadHistory,
            openHistory: openHistory,
            remove: remove,
            reset: reset,
            editAgain: editAgain,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
