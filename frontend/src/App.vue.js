import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { FileText, History, ClipboardCheck, Upload, Play, RotateCcw, Send, Trash2, ArrowLeft, ShieldCheck } from 'lucide-vue-next';
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
const typeNames = { ambiguous_term: '模糊表达', missing_boundary: '缺少边界条件', conflict: '相互矛盾', permission: '角色或权限', testability: '不可测试', security: '安全风险', operational: '运营异常' };
const visibleIssues = computed(() => current.value?.report.issues.filter(i => filter.value === 'all' || i.type === filter.value) || []);
async function request(path, options = {}) { const res = await fetch(API + path, options); const data = await res.json().catch(() => ({ error: '服务器返回无效内容' })); if (!res.ok)
    throw new Error(data.error || '请求失败'); return data; }
async function upload(file) { uploading.value = true; error.value = ''; try {
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
} loading.value = true; error.value = ''; try {
    current.value = await request('/reviews', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: text.value, mode: mode.value }) });
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
    ElMessage.success('已生成新版本');
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
async function remove(id) { await ElMessageBox.confirm('删除后不可恢复，确认删除？', '删除记录', { type: 'warning' }); try {
    await request(`/reviews/${id}`, { method: 'DELETE' });
    await loadHistory();
    ElMessage.success('已删除');
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
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "topbar" },
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
    size: (20),
}));
const __VLS_2 = __VLS_1({
    size: (20),
}, ...__VLS_functionalComponentArgsRest(__VLS_1));
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.strong, __VLS_intrinsicElements.strong)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.nav, __VLS_intrinsicElements.nav)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.page = __VLS_ctx.current ? 'result' : 'review';
        } },
    ...{ class: ({ active: __VLS_ctx.page === 'review' || __VLS_ctx.page === 'result' }) },
});
const __VLS_4 = {}.ClipboardCheck;
/** @type {[typeof __VLS_components.ClipboardCheck, ]} */ ;
// @ts-ignore
const __VLS_5 = __VLS_asFunctionalComponent(__VLS_4, new __VLS_4({
    size: (16),
}));
const __VLS_6 = __VLS_5({
    size: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_5));
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.page = 'history';
            __VLS_ctx.loadHistory();
        } },
    ...{ class: ({ active: __VLS_ctx.page === 'history' }) },
});
const __VLS_8 = {}.History;
/** @type {[typeof __VLS_components.History, ]} */ ;
// @ts-ignore
const __VLS_9 = __VLS_asFunctionalComponent(__VLS_8, new __VLS_8({
    size: (16),
}));
const __VLS_10 = __VLS_9({
    size: (16),
}, ...__VLS_functionalComponentArgsRest(__VLS_9));
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({});
if (__VLS_ctx.page === 'review') {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "workspace" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "page-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "eyebrow" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "muted" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "step" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "input-layout" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "panel input-panel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "panel-title" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    const __VLS_12 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_13 = __VLS_asFunctionalComponent(__VLS_12, new __VLS_12({
        ...{ 'onClick': {} },
        text: true,
    }));
    const __VLS_14 = __VLS_13({
        ...{ 'onClick': {} },
        text: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_13));
    let __VLS_16;
    let __VLS_17;
    let __VLS_18;
    const __VLS_19 = {
        onClick: (__VLS_ctx.reset)
    };
    __VLS_15.slots.default;
    const __VLS_20 = {}.RotateCcw;
    /** @type {[typeof __VLS_components.RotateCcw, ]} */ ;
    // @ts-ignore
    const __VLS_21 = __VLS_asFunctionalComponent(__VLS_20, new __VLS_20({
        size: (15),
    }));
    const __VLS_22 = __VLS_21({
        size: (15),
    }, ...__VLS_functionalComponentArgsRest(__VLS_21));
    var __VLS_15;
    const __VLS_24 = {}.ElInput;
    /** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
    // @ts-ignore
    const __VLS_25 = __VLS_asFunctionalComponent(__VLS_24, new __VLS_24({
        modelValue: (__VLS_ctx.text),
        type: "textarea",
        rows: (16),
        maxlength: "20000",
        showWordLimit: true,
        placeholder: "例如：用户可以尽快完成注册，并方便地查看自己的订单……",
    }));
    const __VLS_26 = __VLS_25({
        modelValue: (__VLS_ctx.text),
        type: "textarea",
        rows: (16),
        maxlength: "20000",
        showWordLimit: true,
        placeholder: "例如：用户可以尽快完成注册，并方便地查看自己的订单……",
    }, ...__VLS_functionalComponentArgsRest(__VLS_25));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "file-row" },
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
    const __VLS_32 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_33 = __VLS_asFunctionalComponent(__VLS_32, new __VLS_32({
        loading: (__VLS_ctx.uploading),
    }));
    const __VLS_34 = __VLS_33({
        loading: (__VLS_ctx.uploading),
    }, ...__VLS_functionalComponentArgsRest(__VLS_33));
    __VLS_35.slots.default;
    const __VLS_36 = {}.Upload;
    /** @type {[typeof __VLS_components.Upload, ]} */ ;
    // @ts-ignore
    const __VLS_37 = __VLS_asFunctionalComponent(__VLS_36, new __VLS_36({
        size: (16),
    }));
    const __VLS_38 = __VLS_37({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_37));
    var __VLS_35;
    var __VLS_31;
    if (__VLS_ctx.fileName) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "file-name" },
        });
        const __VLS_40 = {}.FileText;
        /** @type {[typeof __VLS_components.FileText, ]} */ ;
        // @ts-ignore
        const __VLS_41 = __VLS_asFunctionalComponent(__VLS_40, new __VLS_40({
            size: (15),
        }));
        const __VLS_42 = __VLS_41({
            size: (15),
        }, ...__VLS_functionalComponentArgsRest(__VLS_41));
        (__VLS_ctx.fileName);
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "muted" },
        });
    }
    __VLS_asFunctionalElement(__VLS_intrinsicElements.aside, __VLS_intrinsicElements.aside)({
        ...{ class: "panel options" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.label, __VLS_intrinsicElements.label)({});
    const __VLS_44 = {}.ElSelect;
    /** @type {[typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, typeof __VLS_components.ElSelect, typeof __VLS_components.elSelect, ]} */ ;
    // @ts-ignore
    const __VLS_45 = __VLS_asFunctionalComponent(__VLS_44, new __VLS_44({
        modelValue: (__VLS_ctx.mode),
    }));
    const __VLS_46 = __VLS_45({
        modelValue: (__VLS_ctx.mode),
    }, ...__VLS_functionalComponentArgsRest(__VLS_45));
    __VLS_47.slots.default;
    const __VLS_48 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    const __VLS_49 = __VLS_asFunctionalComponent(__VLS_48, new __VLS_48({
        label: "全面审查",
        value: "全面审查",
    }));
    const __VLS_50 = __VLS_49({
        label: "全面审查",
        value: "全面审查",
    }, ...__VLS_functionalComponentArgsRest(__VLS_49));
    const __VLS_52 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    const __VLS_53 = __VLS_asFunctionalComponent(__VLS_52, new __VLS_52({
        label: "重点关注可测试性",
        value: "可测试性",
    }));
    const __VLS_54 = __VLS_53({
        label: "重点关注可测试性",
        value: "可测试性",
    }, ...__VLS_functionalComponentArgsRest(__VLS_53));
    const __VLS_56 = {}.ElOption;
    /** @type {[typeof __VLS_components.ElOption, typeof __VLS_components.elOption, ]} */ ;
    // @ts-ignore
    const __VLS_57 = __VLS_asFunctionalComponent(__VLS_56, new __VLS_56({
        label: "重点关注安全与权限",
        value: "安全与权限",
    }));
    const __VLS_58 = __VLS_57({
        label: "重点关注安全与权限",
        value: "安全与权限",
    }, ...__VLS_functionalComponentArgsRest(__VLS_57));
    var __VLS_47;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "check-list" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "dot green" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "dot amber" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "dot blue" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({});
    const __VLS_60 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_61 = __VLS_asFunctionalComponent(__VLS_60, new __VLS_60({
        ...{ 'onClick': {} },
        type: "primary",
        size: "large",
        ...{ class: "start" },
        loading: (__VLS_ctx.loading),
    }));
    const __VLS_62 = __VLS_61({
        ...{ 'onClick': {} },
        type: "primary",
        size: "large",
        ...{ class: "start" },
        loading: (__VLS_ctx.loading),
    }, ...__VLS_functionalComponentArgsRest(__VLS_61));
    let __VLS_64;
    let __VLS_65;
    let __VLS_66;
    const __VLS_67 = {
        onClick: (__VLS_ctx.review)
    };
    __VLS_63.slots.default;
    const __VLS_68 = {}.Play;
    /** @type {[typeof __VLS_components.Play, ]} */ ;
    // @ts-ignore
    const __VLS_69 = __VLS_asFunctionalComponent(__VLS_68, new __VLS_68({
        size: (17),
    }));
    const __VLS_70 = __VLS_69({
        size: (17),
    }, ...__VLS_functionalComponentArgsRest(__VLS_69));
    var __VLS_63;
}
else if (__VLS_ctx.page === 'result' && __VLS_ctx.current) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "workspace" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "result-head" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                __VLS_ctx.page = 'review';
            } },
        ...{ class: "back" },
    });
    const __VLS_72 = {}.ArrowLeft;
    /** @type {[typeof __VLS_components.ArrowLeft, ]} */ ;
    // @ts-ignore
    const __VLS_73 = __VLS_asFunctionalComponent(__VLS_72, new __VLS_72({
        size: (16),
    }));
    const __VLS_74 = __VLS_73({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_73));
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "eyebrow" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "muted" },
    });
    (new Date(__VLS_ctx.current.createdAt).toLocaleString('zh-CN'));
    (__VLS_ctx.current.mode);
    const __VLS_76 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_77 = __VLS_asFunctionalComponent(__VLS_76, new __VLS_76({
        ...{ 'onClick': {} },
        type: "primary",
        plain: true,
    }));
    const __VLS_78 = __VLS_77({
        ...{ 'onClick': {} },
        type: "primary",
        plain: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_77));
    let __VLS_80;
    let __VLS_81;
    let __VLS_82;
    const __VLS_83 = {
        onClick: (__VLS_ctx.editAgain)
    };
    __VLS_79.slots.default;
    var __VLS_79;
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "summary panel" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
        ...{ class: "risk-pill" },
        ...{ class: (__VLS_ctx.current.report.riskLevel) },
    });
    (__VLS_ctx.current.report.riskLevel === 'high' ? '高风险' : __VLS_ctx.current.report.riskLevel === 'medium' ? '中风险' : '低风险');
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    (__VLS_ctx.current.report.summary);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "counts" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({
        ...{ class: "high" },
    });
    (__VLS_ctx.current.report.counts.high);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({
        ...{ class: "medium" },
    });
    (__VLS_ctx.current.report.counts.medium);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.b, __VLS_intrinsicElements.b)({
        ...{ class: "low" },
    });
    (__VLS_ctx.current.report.counts.low);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "filterbar" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    const __VLS_84 = {}.ElRadioGroup;
    /** @type {[typeof __VLS_components.ElRadioGroup, typeof __VLS_components.elRadioGroup, typeof __VLS_components.ElRadioGroup, typeof __VLS_components.elRadioGroup, ]} */ ;
    // @ts-ignore
    const __VLS_85 = __VLS_asFunctionalComponent(__VLS_84, new __VLS_84({
        modelValue: (__VLS_ctx.filter),
        size: "small",
    }));
    const __VLS_86 = __VLS_85({
        modelValue: (__VLS_ctx.filter),
        size: "small",
    }, ...__VLS_functionalComponentArgsRest(__VLS_85));
    __VLS_87.slots.default;
    const __VLS_88 = {}.ElRadioButton;
    /** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
    // @ts-ignore
    const __VLS_89 = __VLS_asFunctionalComponent(__VLS_88, new __VLS_88({
        label: "all",
    }));
    const __VLS_90 = __VLS_89({
        label: "all",
    }, ...__VLS_functionalComponentArgsRest(__VLS_89));
    __VLS_91.slots.default;
    (__VLS_ctx.current.report.issues.length);
    var __VLS_91;
    for (const [name, key] of __VLS_getVForSourceType((__VLS_ctx.typeNames))) {
        const __VLS_92 = {}.ElRadioButton;
        /** @type {[typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, typeof __VLS_components.ElRadioButton, typeof __VLS_components.elRadioButton, ]} */ ;
        // @ts-ignore
        const __VLS_93 = __VLS_asFunctionalComponent(__VLS_92, new __VLS_92({
            key: (key),
            label: (key),
        }));
        const __VLS_94 = __VLS_93({
            key: (key),
            label: (key),
        }, ...__VLS_functionalComponentArgsRest(__VLS_93));
        __VLS_95.slots.default;
        (name);
        var __VLS_95;
    }
    var __VLS_87;
    if (!__VLS_ctx.visibleIssues.length) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty panel" },
        });
        const __VLS_96 = {}.ClipboardCheck;
        /** @type {[typeof __VLS_components.ClipboardCheck, ]} */ ;
        // @ts-ignore
        const __VLS_97 = __VLS_asFunctionalComponent(__VLS_96, new __VLS_96({
            size: (38),
        }));
        const __VLS_98 = __VLS_97({
            size: (38),
        }, ...__VLS_functionalComponentArgsRest(__VLS_97));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
    }
    for (const [issue] of __VLS_getVForSourceType((__VLS_ctx.visibleIssues))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
            key: (issue.id),
            ...{ class: "issue panel" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "issue-head" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "type-label" },
        });
        (__VLS_ctx.typeNames[issue.type] || issue.type);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
        (issue.explanation);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
            ...{ class: "severity" },
            ...{ class: (issue.severity) },
        });
        (issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低');
        __VLS_asFunctionalElement(__VLS_intrinsicElements.blockquote, __VLS_intrinsicElements.blockquote)({});
        (issue.quote);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.small, __VLS_intrinsicElements.small)({});
        (issue.location);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "issue-grid" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
        for (const [x] of __VLS_getVForSourceType((issue.missingConditions))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
                key: (x),
            });
            (x);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
        for (const [x] of __VLS_getVForSourceType((issue.questions))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
                key: (x),
            });
            (x);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.ul, __VLS_intrinsicElements.ul)({});
        for (const [x] of __VLS_getVForSourceType((issue.acceptanceCriteria))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.li, __VLS_intrinsicElements.li)({
                key: (x),
            });
            (x);
        }
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
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
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "muted" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "follow-input" },
    });
    const __VLS_100 = {}.ElInput;
    /** @type {[typeof __VLS_components.ElInput, typeof __VLS_components.elInput, ]} */ ;
    // @ts-ignore
    const __VLS_101 = __VLS_asFunctionalComponent(__VLS_100, new __VLS_100({
        ...{ 'onKeyup': {} },
        modelValue: (__VLS_ctx.question),
        placeholder: "例如：先处理哪个问题？",
    }));
    const __VLS_102 = __VLS_101({
        ...{ 'onKeyup': {} },
        modelValue: (__VLS_ctx.question),
        placeholder: "例如：先处理哪个问题？",
    }, ...__VLS_functionalComponentArgsRest(__VLS_101));
    let __VLS_104;
    let __VLS_105;
    let __VLS_106;
    const __VLS_107 = {
        onKeyup: (__VLS_ctx.follow)
    };
    var __VLS_103;
    const __VLS_108 = {}.ElButton;
    /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
    // @ts-ignore
    const __VLS_109 = __VLS_asFunctionalComponent(__VLS_108, new __VLS_108({
        ...{ 'onClick': {} },
        type: "primary",
        loading: (__VLS_ctx.loading),
    }));
    const __VLS_110 = __VLS_109({
        ...{ 'onClick': {} },
        type: "primary",
        loading: (__VLS_ctx.loading),
    }, ...__VLS_functionalComponentArgsRest(__VLS_109));
    let __VLS_112;
    let __VLS_113;
    let __VLS_114;
    const __VLS_115 = {
        onClick: (__VLS_ctx.follow)
    };
    __VLS_111.slots.default;
    const __VLS_116 = {}.Send;
    /** @type {[typeof __VLS_components.Send, ]} */ ;
    // @ts-ignore
    const __VLS_117 = __VLS_asFunctionalComponent(__VLS_116, new __VLS_116({
        size: (16),
    }));
    const __VLS_118 = __VLS_117({
        size: (16),
    }, ...__VLS_functionalComponentArgsRest(__VLS_117));
    var __VLS_111;
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
        ...{ class: "workspace" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "page-heading" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "eyebrow" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({});
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "muted" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "step" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
    if (!__VLS_ctx.history.length) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "empty panel" },
        });
        const __VLS_120 = {}.History;
        /** @type {[typeof __VLS_components.History, ]} */ ;
        // @ts-ignore
        const __VLS_121 = __VLS_asFunctionalComponent(__VLS_120, new __VLS_120({
            size: (42),
        }));
        const __VLS_122 = __VLS_121({
            size: (42),
        }, ...__VLS_functionalComponentArgsRest(__VLS_121));
        __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
        const __VLS_124 = {}.ElButton;
        /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
        // @ts-ignore
        const __VLS_125 = __VLS_asFunctionalComponent(__VLS_124, new __VLS_124({
            ...{ 'onClick': {} },
            type: "primary",
        }));
        const __VLS_126 = __VLS_125({
            ...{ 'onClick': {} },
            type: "primary",
        }, ...__VLS_functionalComponentArgsRest(__VLS_125));
        let __VLS_128;
        let __VLS_129;
        let __VLS_130;
        const __VLS_131 = {
            onClick: (...[$event]) => {
                if (!!(__VLS_ctx.page === 'review'))
                    return;
                if (!!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                    return;
                if (!(!__VLS_ctx.history.length))
                    return;
                __VLS_ctx.page = 'review';
            }
        };
        __VLS_127.slots.default;
        var __VLS_127;
    }
    else {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            ...{ class: "history-list" },
        });
        for (const [item] of __VLS_getVForSourceType((__VLS_ctx.history))) {
            __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
                key: (item.id),
                ...{ class: "history-item panel" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-icon" },
            });
            const __VLS_132 = {}.FileText;
            /** @type {[typeof __VLS_components.FileText, ]} */ ;
            // @ts-ignore
            const __VLS_133 = __VLS_asFunctionalComponent(__VLS_132, new __VLS_132({
                size: (20),
            }));
            const __VLS_134 = __VLS_133({
                size: (20),
            }, ...__VLS_functionalComponentArgsRest(__VLS_133));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "history-main" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
            (item.summary);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
            (new Date(item.createdAt).toLocaleString('zh-CN'));
            __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
                ...{ class: "mini-counts" },
            });
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "high" },
            });
            (item.counts.high || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "medium" },
            });
            (item.counts.medium || 0);
            __VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
                ...{ class: "low" },
            });
            (item.counts.low || 0);
            const __VLS_136 = {}.ElButton;
            /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
            // @ts-ignore
            const __VLS_137 = __VLS_asFunctionalComponent(__VLS_136, new __VLS_136({
                ...{ 'onClick': {} },
                text: true,
            }));
            const __VLS_138 = __VLS_137({
                ...{ 'onClick': {} },
                text: true,
            }, ...__VLS_functionalComponentArgsRest(__VLS_137));
            let __VLS_140;
            let __VLS_141;
            let __VLS_142;
            const __VLS_143 = {
                onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.page === 'review'))
                        return;
                    if (!!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                        return;
                    if (!!(!__VLS_ctx.history.length))
                        return;
                    __VLS_ctx.openHistory(item.id);
                }
            };
            __VLS_139.slots.default;
            var __VLS_139;
            const __VLS_144 = {}.ElButton;
            /** @type {[typeof __VLS_components.ElButton, typeof __VLS_components.elButton, typeof __VLS_components.ElButton, typeof __VLS_components.elButton, ]} */ ;
            // @ts-ignore
            const __VLS_145 = __VLS_asFunctionalComponent(__VLS_144, new __VLS_144({
                ...{ 'onClick': {} },
                text: true,
                type: "danger",
            }));
            const __VLS_146 = __VLS_145({
                ...{ 'onClick': {} },
                text: true,
                type: "danger",
            }, ...__VLS_functionalComponentArgsRest(__VLS_145));
            let __VLS_148;
            let __VLS_149;
            let __VLS_150;
            const __VLS_151 = {
                onClick: (...[$event]) => {
                    if (!!(__VLS_ctx.page === 'review'))
                        return;
                    if (!!(__VLS_ctx.page === 'result' && __VLS_ctx.current))
                        return;
                    if (!!(!__VLS_ctx.history.length))
                        return;
                    __VLS_ctx.remove(item.id);
                }
            };
            __VLS_147.slots.default;
            const __VLS_152 = {}.Trash2;
            /** @type {[typeof __VLS_components.Trash2, ]} */ ;
            // @ts-ignore
            const __VLS_153 = __VLS_asFunctionalComponent(__VLS_152, new __VLS_152({
                size: (16),
            }));
            const __VLS_154 = __VLS_153({
                size: (16),
            }, ...__VLS_functionalComponentArgsRest(__VLS_153));
            var __VLS_147;
        }
    }
}
if (__VLS_ctx.error) {
    const __VLS_156 = {}.ElAlert;
    /** @type {[typeof __VLS_components.ElAlert, typeof __VLS_components.elAlert, typeof __VLS_components.ElAlert, typeof __VLS_components.elAlert, ]} */ ;
    // @ts-ignore
    const __VLS_157 = __VLS_asFunctionalComponent(__VLS_156, new __VLS_156({
        ...{ class: "error" },
        type: "error",
        closable: (false),
        showIcon: true,
    }));
    const __VLS_158 = __VLS_157({
        ...{ class: "error" },
        type: "error",
        closable: (false),
        showIcon: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_157));
    __VLS_159.slots.default;
    (__VLS_ctx.error);
    var __VLS_159;
}
/** @type {__VLS_StyleScopedClasses['app-shell']} */ ;
/** @type {__VLS_StyleScopedClasses['topbar']} */ ;
/** @type {__VLS_StyleScopedClasses['brand']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-mark']} */ ;
/** @type {__VLS_StyleScopedClasses['workspace']} */ ;
/** @type {__VLS_StyleScopedClasses['page-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['muted']} */ ;
/** @type {__VLS_StyleScopedClasses['step']} */ ;
/** @type {__VLS_StyleScopedClasses['input-layout']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['input-panel']} */ ;
/** @type {__VLS_StyleScopedClasses['panel-title']} */ ;
/** @type {__VLS_StyleScopedClasses['file-row']} */ ;
/** @type {__VLS_StyleScopedClasses['file-name']} */ ;
/** @type {__VLS_StyleScopedClasses['muted']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['options']} */ ;
/** @type {__VLS_StyleScopedClasses['check-list']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['green']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['amber']} */ ;
/** @type {__VLS_StyleScopedClasses['dot']} */ ;
/** @type {__VLS_StyleScopedClasses['blue']} */ ;
/** @type {__VLS_StyleScopedClasses['start']} */ ;
/** @type {__VLS_StyleScopedClasses['workspace']} */ ;
/** @type {__VLS_StyleScopedClasses['result-head']} */ ;
/** @type {__VLS_StyleScopedClasses['back']} */ ;
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['muted']} */ ;
/** @type {__VLS_StyleScopedClasses['summary']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['risk-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['counts']} */ ;
/** @type {__VLS_StyleScopedClasses['high']} */ ;
/** @type {__VLS_StyleScopedClasses['medium']} */ ;
/** @type {__VLS_StyleScopedClasses['low']} */ ;
/** @type {__VLS_StyleScopedClasses['filterbar']} */ ;
/** @type {__VLS_StyleScopedClasses['empty']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['issue']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['issue-head']} */ ;
/** @type {__VLS_StyleScopedClasses['type-label']} */ ;
/** @type {__VLS_StyleScopedClasses['severity']} */ ;
/** @type {__VLS_StyleScopedClasses['issue-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['roles']} */ ;
/** @type {__VLS_StyleScopedClasses['follow']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['muted']} */ ;
/** @type {__VLS_StyleScopedClasses['follow-input']} */ ;
/** @type {__VLS_StyleScopedClasses['workspace']} */ ;
/** @type {__VLS_StyleScopedClasses['page-heading']} */ ;
/** @type {__VLS_StyleScopedClasses['eyebrow']} */ ;
/** @type {__VLS_StyleScopedClasses['muted']} */ ;
/** @type {__VLS_StyleScopedClasses['step']} */ ;
/** @type {__VLS_StyleScopedClasses['empty']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['history-list']} */ ;
/** @type {__VLS_StyleScopedClasses['history-item']} */ ;
/** @type {__VLS_StyleScopedClasses['panel']} */ ;
/** @type {__VLS_StyleScopedClasses['history-icon']} */ ;
/** @type {__VLS_StyleScopedClasses['history-main']} */ ;
/** @type {__VLS_StyleScopedClasses['mini-counts']} */ ;
/** @type {__VLS_StyleScopedClasses['high']} */ ;
/** @type {__VLS_StyleScopedClasses['medium']} */ ;
/** @type {__VLS_StyleScopedClasses['low']} */ ;
/** @type {__VLS_StyleScopedClasses['error']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            FileText: FileText,
            History: History,
            ClipboardCheck: ClipboardCheck,
            Upload: Upload,
            Play: Play,
            RotateCcw: RotateCcw,
            Send: Send,
            Trash2: Trash2,
            ArrowLeft: ArrowLeft,
            ShieldCheck: ShieldCheck,
            page: page,
            text: text,
            mode: mode,
            loading: loading,
            uploading: uploading,
            error: error,
            fileName: fileName,
            current: current,
            history: history,
            filter: filter,
            question: question,
            typeNames: typeNames,
            visibleIssues: visibleIssues,
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
