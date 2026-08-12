"""Ứng dụng desktop rà soát chính tả tiếng Việt – ngoại tuyến hoàn toàn."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request, send_file
from werkzeug.utils import secure_filename

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from docx_processor import DocxReview
from engine import VietnameseSpellChecker
from offline_server import run_desktop_app


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024
WORK_DIR = Path(tempfile.mkdtemp(prefix="ra_chinh_ta_"))
CHECKER = VietnameseSpellChecker()
JOBS = {}


PAGE = r'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rà soát chính tả offline</title>
<style>
:root{--navy:#102a43;--blue:#2563eb;--red:#b42318;--amber:#b54708;--cyan:#087e8b;--line:#d8e2ec;--paper:#fff;--bg:#f4f7fb}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",Arial,sans-serif;background:var(--bg);color:#243b53}
.top{background:linear-gradient(135deg,#0b2743,#164e7a);color:white;padding:22px 28px;box-shadow:0 4px 18px #102a4322}
.top h1{margin:0 0 5px;font-size:25px}.top p{margin:0;color:#d9eaf7}.wrap{max-width:1200px;margin:24px auto;padding:0 18px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:14px;box-shadow:0 8px 28px #102a430d;padding:22px;margin-bottom:18px}
.drop{border:2px dashed #84a9c5;border-radius:12px;padding:32px;text-align:center;background:#f8fbfe;transition:.2s}.drop.drag{border-color:var(--blue);background:#eff6ff}
input[type=file]{display:none}.btn{border:0;border-radius:9px;background:var(--blue);color:white;padding:11px 17px;font-weight:700;cursor:pointer}.btn:disabled{opacity:.45;cursor:not-allowed}.btn.secondary{background:#526d82}.btn.green{background:#18794e}.btn.light{background:#e8eef4;color:#243b53}
.privacy{margin-top:14px;font-size:13px;color:#526d82}.privacy strong{color:#18794e}.hidden{display:none!important}.status{padding:12px;border-radius:9px;background:#eef5fb;margin-top:14px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.stat{border:1px solid var(--line);border-radius:10px;padding:14px}.stat b{display:block;font-size:26px;color:var(--navy)}
.layout{display:grid;grid-template-columns:1fr 390px;gap:16px}.preview{height:570px;overflow:auto;white-space:pre-wrap;line-height:1.7;border:1px solid var(--line);border-radius:10px;padding:18px;background:#fff}
.issues{height:570px;overflow:auto}.issue{border:1px solid var(--line);border-left:5px solid var(--amber);border-radius:9px;padding:12px;margin-bottom:10px;background:white}.issue.error{border-left-color:var(--red)}.issue.style{border-left-color:var(--cyan)}
.issue .head{display:flex;gap:8px;align-items:center}.issue .word{font-weight:800;color:var(--red)}.issue .suggest{color:#18794e;font-weight:800}.meta{font-size:12px;color:#627d98;margin:7px 0}.context{font-size:13px;background:#f6f8fa;padding:8px;border-radius:6px}.choice{margin-top:9px;display:flex;align-items:center;gap:8px}
mark.error{background:#ffc9c5}mark.warning{background:#ffe8a3}mark.style{background:#a9edf0}.filters{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.filters button{padding:7px 10px;border:1px solid var(--line);background:white;border-radius:20px;cursor:pointer}.filters button.active{background:var(--navy);color:white}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.bulk-actions{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin:10px 0}.bulk-actions .btn{padding:8px 11px;font-size:12px}.accepted-count{margin-left:auto;color:#526d82;font-size:12px;font-weight:700}.note{font-size:13px;color:#627d98;margin-top:10px}@media(max-width:850px){.layout{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}.preview,.issues{height:420px}.accepted-count{width:100%;margin-left:0}}
</style></head><body>
<header class="top"><h1>RÀ SOÁT CHÍNH TẢ TIẾNG VIỆT</h1><p>Kiểm tra DOCX ngay trên máy · Không AI · Không gửi dữ liệu lên mạng</p></header>
<main class="wrap">
<section class="card" id="uploadCard"><div class="drop" id="drop">
  <h2>Thả tệp Word vào đây</h2><p>Hỗ trợ .docx, tối đa 50 MB</p>
  <label class="btn" for="file">CHỌN TỆP WORD</label><input id="file" type="file" accept=".docx">
  <div class="privacy"><strong>✓ Xử lý ngoại tuyến:</strong> tệp chỉ đi qua máy chủ nội bộ 127.0.0.1 trên chính máy tính này.</div>
</div><div class="status hidden" id="status"></div></section>

<section id="result" class="hidden">
<div class="card"><div class="stats">
 <div class="stat"><b id="wordCount">0</b>Từ đã rà</div><div class="stat"><b id="errorCount">0</b>Lỗi chắc chắn</div>
 <div class="stat"><b id="warningCount">0</b>Điểm nghi vấn</div><div class="stat"><b id="styleCount">0</b>Trình bày</div>
</div><div class="filters"><button class="active" data-filter="all">Tất cả</button><button data-filter="error">Lỗi chắc chắn</button><button data-filter="warning">Nghi vấn</button><button data-filter="style">Trình bày</button></div></div>
<div class="layout"><div class="card"><h3>Nội dung và vị trí lỗi</h3><div class="preview" id="preview"></div></div>
<div class="card"><h3>Danh sách lỗi</h3><div class="bulk-actions"><button class="btn" id="acceptVisible">PHÊ DUYỆT TẤT CẢ ĐANG HIỂN THỊ</button><button class="btn light" id="clearVisible">BỎ PHÊ DUYỆT ĐANG HIỂN THỊ</button><span class="accepted-count" id="acceptedCount">Đã phê duyệt: 0</span></div><div class="issues" id="issues"></div></div></div>
<div class="card"><div class="actions">
 <button class="btn secondary" id="marked">TẢI BẢN CÓ ĐÁNH DẤU</button>
 <button class="btn green" id="corrected">TẢI BẢN ĐÃ CHẤP NHẬN SỬA</button>
 <button class="btn" id="both">TẢI CẢ HAI</button><button class="btn light" onclick="location.reload()">RÀ TỆP KHÁC</button>
</div><div class="note">Bản gốc không bao giờ bị ghi đè. Trong bản có đánh dấu, mọi vị trí cần kiểm tra chỉ được tô vàng, không chèn nhận xét Word. Chỉ các mục được tích “Chấp nhận sửa” mới xuất hiện trong bản đã sửa.</div></div>
</section></main>
<script>
let job=null, data=null, filter='all', acceptedSet=new Set(); const $=s=>document.querySelector(s); const esc=s=>(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const drop=$('#drop'), file=$('#file'), status=$('#status');
['dragenter','dragover'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.add('drag')}));
['dragleave','drop'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.remove('drag')}));
drop.addEventListener('drop',e=>upload(e.dataTransfer.files[0])); file.addEventListener('change',()=>upload(file.files[0]));
async function upload(f){if(!f)return;if(!f.name.toLowerCase().endsWith('.docx')){alert('Chỉ hỗ trợ tệp .docx');return}status.classList.remove('hidden');status.textContent='Đang đọc và rà soát '+f.name+'…';
 const fd=new FormData();fd.append('file',f);try{const r=await fetch('/api/analyze',{method:'POST',body:fd});const j=await r.json();if(!r.ok)throw Error(j.error||'Không thể xử lý tệp');job=j.job;data=j;acceptedSet=new Set(j.issues.filter(i=>i.severity==='error').map(i=>i.id));render();status.textContent='Đã rà xong '+f.name;}catch(e){status.textContent='Lỗi: '+e.message}}
function render(){ $('#result').classList.remove('hidden');$('#wordCount').textContent=data.word_count;$('#errorCount').textContent=data.counts.error;$('#warningCount').textContent=data.counts.warning;$('#styleCount').textContent=data.counts.style;renderPreview();renderIssues();$('#result').scrollIntoView({behavior:'smooth'}) }
function renderPreview(){let html='';for(const p of data.paragraphs){let pos=0;const list=p.issues.filter(i=>filter==='all'||i.severity===filter).sort((a,b)=>a.start-b.start);for(const i of list){html+=esc(p.text.slice(pos,i.start));html+='<mark class="'+i.severity+'" title="'+esc(i.message)+'">'+esc(p.text.slice(i.start,i.end))+'</mark>';pos=i.end}html+=esc(p.text.slice(pos))+'\n\n'}$('#preview').innerHTML=html}
 function visibleIssues(){return data.issues.filter(i=>filter==='all'||i.severity===filter)}
 function updateAcceptedCount(){const total=data?data.issues.length:0;$('#acceptedCount').textContent=`Đã phê duyệt: ${acceptedSet.size}/${total}`}
 function renderIssues(){const list=visibleIssues();$('#issues').innerHTML=list.length?list.map(i=>`<article class="issue ${i.severity}" id="card-${i.id}"><div class="head"><span class="word">${esc(i.original)}</span><span>→</span><span class="suggest">${esc(i.suggestion||'Kiểm tra')}</span></div><div class="meta">${esc(i.kind)} · ${esc(i.location)} · tin cậy ${i.confidence}%</div><div>${esc(i.message)}</div><div class="context">${esc(i.context)}</div><label class="choice"><input type="checkbox" class="accept" value="${i.id}" ${acceptedSet.has(i.id)?'checked':''}> Chấp nhận sửa đề xuất này</label></article>`).join(''):'<p>Không có lỗi thuộc nhóm này.</p>';document.querySelectorAll('.accept').forEach(x=>x.onchange=()=>{x.checked?acceptedSet.add(x.value):acceptedSet.delete(x.value);updateAcceptedCount()});updateAcceptedCount()}
document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.filters button').forEach(x=>x.classList.remove('active'));b.classList.add('active');filter=b.dataset.filter;renderPreview();renderIssues()});
 function accepted(){return [...acceptedSet]}
 $('#acceptVisible').onclick=()=>{visibleIssues().forEach(i=>acceptedSet.add(i.id));renderIssues()};
 $('#clearVisible').onclick=()=>{visibleIssues().forEach(i=>acceptedSet.delete(i.id));renderIssues()};
async function download(mode){const r=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({job,mode,accepted:accepted()})});if(!r.ok){const j=await r.json();alert(j.error||'Không thể xuất tệp');return}const blob=await r.blob(),a=document.createElement('a');a.href=URL.createObjectURL(blob);const cd=r.headers.get('content-disposition')||'';const m=cd.match(/filename="?([^";]+)"?/);a.download=m?m[1]:'ket_qua.docx';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}
$('#marked').onclick=()=>download('marked');$('#corrected').onclick=()=>download('corrected');$('#both').onclick=()=>download('both');
</script></body></html>'''


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Tệp vượt quá giới hạn 50 MB."), 413


@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/api/analyze")
def analyze():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Chưa chọn tệp."), 400
    if not uploaded.filename.lower().endswith(".docx"):
        return jsonify(error="Chỉ hỗ trợ tệp Word .docx."), 400
    job_id = uuid.uuid4().hex
    original_name = secure_filename(uploaded.filename) or "van_ban.docx"
    path = WORK_DIR / f"{job_id}_{original_name}"
    uploaded.save(path)
    try:
        review = DocxReview(path, CHECKER)
        issues, word_count = review.analyze()
    except Exception as exc:
        path.unlink(missing_ok=True)
        return jsonify(error=f"Không đọc được tệp Word: {exc}"), 400
    JOBS[job_id] = {"path": path, "name": Path(original_name).stem, "review": review}
    paragraphs = []
    for ref in review.refs.values():
        local = [item.to_dict() for item in issues if item.paragraph_id == ref.key]
        if ref.paragraph.text.strip():
            paragraphs.append({"id": ref.key, "text": ref.paragraph.text, "issues": local})
    counts = {
        "error": sum(i.severity == "error" for i in issues),
        "warning": sum(i.severity == "warning" for i in issues),
        "style": sum(i.severity == "style" for i in issues),
    }
    return jsonify(job=job_id, word_count=word_count, counts=counts,
                   issues=[item.to_dict() for item in issues], paragraphs=paragraphs)


@app.post("/api/export")
def export():
    payload = request.get_json(silent=True) or {}
    job = JOBS.get(str(payload.get("job", "")))
    if not job:
        return jsonify(error="Phiên rà soát không còn tồn tại. Vui lòng chọn lại tệp."), 400
    mode = payload.get("mode")
    if mode not in {"marked", "corrected", "both"}:
        return jsonify(error="Kiểu xuất tệp không hợp lệ."), 400
    accepted = {str(value) for value in payload.get("accepted", [])}
    base = job["name"]
    review = job["review"]
    marked = WORK_DIR / f"{uuid.uuid4().hex}_{base}_BAN_RA_SOAT.docx"
    corrected = WORK_DIR / f"{uuid.uuid4().hex}_{base}_DA_SUA.docx"
    if mode in {"marked", "both"}:
        # Nạp lại tài liệu để mỗi lần xuất không cộng dồn phần tô màu.
        fresh = DocxReview(job["path"], CHECKER); fresh.analyze(); fresh.save_marked(marked)
    if mode in {"corrected", "both"}:
        fresh = DocxReview(job["path"], CHECKER); fresh.analyze(); fresh.save_corrected(corrected, accepted)
    if mode == "marked":
        return send_file(marked, as_attachment=True, download_name=f"{base}_BAN_RA_SOAT.docx")
    if mode == "corrected":
        return send_file(corrected, as_attachment=True, download_name=f"{base}_DA_SUA.docx")
    archive = WORK_DIR / f"{uuid.uuid4().hex}_{base}_KET_QUA.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
        output.write(marked, f"{base}_BAN_RA_SOAT.docx")
        output.write(corrected, f"{base}_DA_SUA.docx")
    return send_file(archive, as_attachment=True, download_name=f"{base}_KET_QUA.zip")


def main():
    run_desktop_app(
        app, "ra-soat-chinh-ta", preferred_port=5790,
        open_browser=os.environ.get("SPELLCHECK_NO_BROWSER") != "1",
    )


if __name__ == "__main__":
    main()
