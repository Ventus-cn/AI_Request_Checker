from __future__ import annotations
import json, re, time
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
SOURCES = [ROOT / 'README.md'] + [p for p in ROOT.iterdir() if p.is_dir() and any(x.suffix.lower()=='.md' for x in p.iterdir()) for p in p.iterdir() if p.suffix.lower()=='.md' and p.parent.name not in ('实验文档', '实验文档')]

def clean(text: str) -> str:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return re.sub(r'\n{3,}', '\n\n', text).strip()

def chunk_file(path: Path, max_chars: int = 500, overlap: int = 60):
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', clean(path.read_text(encoding='utf-8-sig'))) if p.strip()]
    chunks, buffer, heading = [], '', ''
    for p in paragraphs:
        if p.startswith('#'):
            heading = p.lstrip('#').strip()
        candidate = f'{buffer}\n\n{p}'.strip() if buffer else p
        if buffer and len(candidate) > max_chars:
            chunks.append((heading, buffer))
            buffer = f'{buffer[-overlap:]}\n\n{p}'.strip()
        else:
            buffer = candidate
    if buffer:
        chunks.append((heading, buffer))
    return chunks

def tokenize(text: str):
    return re.findall(r'[\u4e00-\u9fff]{2,}|[A-Za-z_][A-Za-z0-9_./-]*|\d+', text.lower())

def build_kb():
    kb = []
    counters = Counter()
    for path in SOURCES:
        counters[path.name] += 1
        for heading, body in chunk_file(path):
            counters[path.name] += 1
            kb.append({'id': f'S{len(kb)+1:03d}', 'source': path.name,
                       'path': str(path.relative_to(ROOT)), 'heading': heading or '正文',
                       'chunk_index': counters[path.name], 'text': body})
    return kb

def retrieve(kb, query, k=3):
    q = Counter(tokenize(query))
    scored = []
    for item in kb:
        tokens = Counter(tokenize(item['text']))
        overlap = sum(min(q[t], tokens[t]) for t in q)
        phrase_bonus = sum(2 for t in q if t in item['text'])
        score = overlap * 3 + phrase_bonus
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1]['id']))
    return scored[:k]

def context(scored):
    return '\n\n'.join(f'[{item["id"]}] {item["source"]} / {item["heading"]}\n{item["text"]}' for _, item in scored)

def main():
    kb = build_kb()
    questions = [
        '\u7cfb\u7edf\u652f\u6301\u54ea\u4e9b\u8f93\u5165\u65b9\u5f0f\u548c\u6587\u4ef6\u9650\u5236\uff1f',
        'AI \u670d\u52a1\u5931\u8d25\u65f6\u5982\u4f55\u5904\u7406\uff0c\u662f\u5426\u4fdd\u5b58\u65e0\u6548\u62a5\u544a\uff1f',
        '\u8ffd\u95ee\u540e\u65e7\u7248\u672c\u5982\u4f55\u4fdd\u5b58\uff1f',
        '\u7cfb\u7edf\u5982\u4f55\u4fdd\u62a4 API Key \u548c\u9700\u6c42\u539f\u6587\uff1f',
        '\u662f\u5426\u5b9e\u73b0\u4e86\u5411\u91cf\u6570\u636e\u5e93\u548c\u771f\u6b63\u7684 RAG\uff1f',
        '\u626b\u63cf PDF \u80fd\u5426\u76f4\u63a5\u751f\u6210\u62a5\u544a\uff1f',
    ]
    rows = []
    for q in questions:
        t0 = time.perf_counter(); top = retrieve(kb, q, 3)
        rows.append({'question': q,
            'top_k': [{'score': s, 'id': item['id'], 'source': item['source'], 'heading': item['heading']} for s, item in top],
            'context': context(top), 'elapsed_ms': round((time.perf_counter()-t0)*1000, 2),
            'answer_rule': '\u4ec5\u4f9d\u636e\u68c0\u7d22\u7247\u6bb5\u4f5c\u7b54\uff1b\u65e0\u652f\u6301\u7247\u6bb5\u65f6\u8fd4\u56de\u201c\u8d44\u6599\u4e0d\u8db3\uff0c\u9700\u4eba\u5de5\u786e\u8ba4\u201d\u3002'})
    out = {'chunk_count': len(kb), 'sources': [str(p.relative_to(ROOT)) for p in SOURCES], 'questions': rows}
    (OUT / 'rag_experiment_results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
