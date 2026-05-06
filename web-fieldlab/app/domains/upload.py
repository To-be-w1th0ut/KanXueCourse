from __future__ import annotations

import io
import json
import mimetypes
import os
import secrets
import threading
import time
import zipfile
from pathlib import Path

from flask import Blueprint, abort, render_template, request, send_file, url_for

from content_store import data_root, execute, query_all, query_one, uploads_root
from shared import current_mode
from upload_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('upload', __name__)
DANGEROUS_SUFFIXES = {'.html', '.htm', '.svg', '.js', '.mjs', '.xml'}


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'upload/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=True, **context)


def domain_info() -> dict:
    return {
        'code': 'UPLOAD',
        'title': '文件上传轨道',
        'description': '围绕公开可访问上传、MIME 信任与文件名路径控制。',
        'summary': '把“能传文件”拆成类型、存储位置、响应头和文件名四个风险面。',
        'level': '进阶',
        'count': len(LABS),
        'href': '/domains/upload',
        'teaching_points': [
            '不要把上传问题只等价成“后缀校验”。',
            '同源公开访问、响应头和文件名同样是核心面。',
            '文件内容、文件名、存储位置和返回方式要分开讲。',
        ],
    }


def _unique_name(original: str) -> str:
    suffix = Path(original).suffix.lower()
    return secrets.token_hex(8) + suffix


def _store_file(file_storage, lab_slug: str, declared_type: str, stored_name: str | None = None, public: bool = True) -> dict:
    root = uploads_root() / ('public' if public else 'private')
    safe_name = stored_name or _unique_name(file_storage.filename or 'upload.bin')
    target = root / safe_name
    target.parent.mkdir(parents=True, exist_ok=True)
    file_storage.save(target)
    rel_path = str(target.relative_to(data_root()))
    execute(
        'INSERT INTO upload_entries (lab_slug, original_name, stored_name, declared_type, stored_path, note, is_public, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime(\'now\'))',
        (lab_slug, file_storage.filename or 'upload.bin', safe_name, declared_type, rel_path, 'uploaded from lab', 1 if public else 0),
    )
    row = query_one('SELECT * FROM upload_entries ORDER BY upload_id DESC LIMIT 1')
    return row


def _load_mime_overrides() -> dict:
    """L09 演示：vuln 模式会消费此映射，把扩展名重定到任意 MIME。"""
    path = data_root() / 'mime_overrides.json'
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@bp.route('/uploads/public/<int:upload_id>')
def serve_public_upload(upload_id: int):
    row = query_one('SELECT * FROM upload_entries WHERE upload_id = ? AND is_public = 1', (upload_id,))
    if not row:
        abort(404)
    path = data_root() / row['stored_path']
    if not path.exists():
        abort(404)
    if current_mode() == 'vuln':
        # ❌ 先看 mime_overrides.json（L09 演示：被覆盖后影响所有访问）
        overrides = _load_mime_overrides()
        suffix = path.suffix.lower()
        original_suffix = Path(row['original_name']).suffix.lower()
        guessed = (overrides.get(suffix) or overrides.get(original_suffix)
                   or row['declared_type']
                   or mimetypes.guess_type(row['original_name'])[0]
                   or 'application/octet-stream')
        return send_file(path, mimetype=guessed, as_attachment=False, download_name=row['original_name'])
    safe_suffix = path.suffix.lower()
    if safe_suffix in {'.txt', '.png', '.jpg', '.jpeg', '.gif'}:
        return send_file(path, mimetype=mimetypes.guess_type(path.name)[0] or 'application/octet-stream', as_attachment=False, download_name=row['original_name'])
    return send_file(path, mimetype='application/octet-stream', as_attachment=True, download_name=row['original_name'])


@bp.route('/labs/upload/public-html', methods=['GET', 'POST'])
def public_html():
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择一个文件。'
        else:
            suffix = Path(upload_file.filename).suffix.lower()
            if current_mode() == 'safe' and suffix in DANGEROUS_SUFFIXES:
                error = '安全模式拒绝公开发布 HTML/SVG/JS/XML 等高风险文件。'
            else:
                row = _store_file(upload_file, 'public-html', upload_file.mimetype or 'application/octet-stream', public=True)
                message = f"文件已发布：{url_for('upload.serve_public_upload', upload_id=row['upload_id'])}"
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'public-html' ORDER BY upload_id DESC LIMIT 8")
    return render_lab('public_html.html', 'public-html', uploads=uploads, message=message, error=error)


@bp.route('/labs/upload/mime-trust', methods=['GET', 'POST'])
def mime_trust():
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        declared_type = request.form.get('declared_type', 'text/plain')
        if not upload_file or not upload_file.filename:
            error = '请选择一个文件。'
        else:
            if current_mode() == 'safe':
                suffix = Path(upload_file.filename).suffix.lower()
                if suffix in DANGEROUS_SUFFIXES:
                    declared_type = 'application/octet-stream'
                else:
                    declared_type = mimetypes.guess_type(upload_file.filename)[0] or 'application/octet-stream'
            row = _store_file(upload_file, 'mime-trust', declared_type, public=True)
            message = f"文件已保存，访问链接：{url_for('upload.serve_public_upload', upload_id=row['upload_id'])}"
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'mime-trust' ORDER BY upload_id DESC LIMIT 8")
    return render_lab('mime_trust.html', 'mime-trust', uploads=uploads, message=message, error=error)


@bp.route('/labs/upload/filename-traversal', methods=['GET', 'POST'])
def filename_traversal():
    message = None
    error = None
    banner_path = data_root() / 'upload_banner.html'
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        save_as = request.form.get('save_as', '')
        if not upload_file or not save_as:
            error = '请选择文件并填写保存名。'
        else:
            try:
                if current_mode() == 'vuln':
                    target = uploads_root() / 'public' / save_as
                else:
                    target = uploads_root() / 'public' / (Path(save_as).name or _unique_name(upload_file.filename or 'upload.bin'))
                target.parent.mkdir(parents=True, exist_ok=True)
                upload_file.save(target)
                message = f'已保存到：{target.relative_to(data_root())}'
            except Exception as exc:
                error = str(exc)
    banner_html = banner_path.read_text() if banner_path.exists() else '<em>missing banner</em>'
    return render_lab('filename_traversal.html', 'filename-traversal', banner_html=banner_html, message=message, error=error)


# =====================================================================
# 批次 4：upload L04-L11 共 8 个新关卡
# =====================================================================

_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
_DOUBLE_EXT_FIRSTKNOWN = {'.html', '.htm', '.svg', '.js', '.xml', '.php'}
_QUARANTINE_DIR_NAME = 'quarantine'


def _public_url(upload_id: int) -> str:
    return f'/uploads/public/{upload_id}'


# ---------- L04 双扩展名 ----------
@bp.route('/labs/upload/double-extension', methods=['GET', 'POST'])
def double_extension():
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择文件。'
        else:
            name = upload_file.filename
            last_suffix = Path(name).suffix.lower()
            parts = name.lower().split('.')
            try:
                if current_mode() == 'safe':
                    # ✅ 文件名只能出现一个扩展名
                    if len(parts) != 2:
                        raise ValueError('安全模式：拒绝多扩展名，文件名必须是 name.ext')
                    if last_suffix in DANGEROUS_SUFFIXES:
                        raise ValueError('安全模式：拒绝危险类型')
                    declared = mimetypes.guess_type(name)[0] or 'application/octet-stream'
                else:
                    # ❌ vuln：白名单只看最后一段，但响应按"第一个已知扩展"判定 mime
                    if last_suffix not in {'.png', '.jpg', '.jpeg', '.gif', '.txt'}:
                        raise ValueError('vuln 白名单：只接受 png/jpg/gif/txt')
                    declared = 'application/octet-stream'
                    for token in parts[1:]:
                        first_known = '.' + token
                        if first_known in _DOUBLE_EXT_FIRSTKNOWN:
                            declared = mimetypes.guess_type('a' + first_known)[0] or declared
                            break
                row = _store_file(upload_file, 'double-extension', declared, public=True)
                message = f"文件已保存：{_public_url(row['upload_id'])} （served as {declared}）"
            except Exception as exc:
                error = str(exc)
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'double-extension' ORDER BY upload_id DESC LIMIT 8")
    return render_lab('double_extension.html', 'double-extension',
                      uploads=uploads, message=message, error=error)


# ---------- L05 大小写 / 空白扩展名 ----------
@bp.route('/labs/upload/extension-case', methods=['GET', 'POST'])
def extension_case():
    """vuln：黑名单只精确比对小写 .html，因此 .HTML、'evil.html '、'evil.html.'、
    'evil.html\\x00.png' 全部能绕过；但落盘时按"截断到第一个 \\x00 / 去掉末尾点和空格"
    生成 stored_name，结果文件后缀是 .html，浏览器以 text/html 解析。
    safe：先 normalize（lower + strip + rstrip('. ') + 去 \\x00）再校验黑名单。"""
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择文件。'
        else:
            raw_name = upload_file.filename
            try:
                if current_mode() == 'safe':
                    normalized = raw_name.strip().rstrip('. ').replace('\x00', '').lower()
                    norm_suffix = Path(normalized).suffix
                    if norm_suffix in {'.html', '.htm', '.svg', '.js', '.xml', '.php'}:
                        raise ValueError(f'safe：normalize 后扩展名 {norm_suffix} 命中黑名单')
                    declared = mimetypes.guess_type(normalized)[0] or 'application/octet-stream'
                    row = _store_file(upload_file, 'extension-case', declared, public=True)
                else:
                    # ❌ 黑名单只看精确小写后缀
                    raw_suffix = Path(raw_name).suffix  # 不 lower、不 strip
                    if raw_suffix == '.html':
                        raise ValueError('vuln：精确匹配 .html 已拒绝（试试 .HTML / 末尾空格 / null 字节）')
                    # 模拟"操作系统会忽略末尾点/空格/null 字节"——落盘后真实后缀是 .html
                    landing = raw_name.split('\x00', 1)[0].rstrip('. ')
                    real_suffix = Path(landing).suffix.lower() or raw_suffix.lower()
                    declared = mimetypes.guess_type('a' + real_suffix)[0] or 'application/octet-stream'
                    stored_name = secrets.token_hex(8) + real_suffix
                    row = _store_file(upload_file, 'extension-case', declared,
                                      stored_name=stored_name, public=True)
                message = (f"已保存：{_public_url(row['upload_id'])}（stored_name="
                           f"{row['stored_name']}, declared={declared}）")
            except Exception as exc:
                error = str(exc)
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'extension-case' ORDER BY upload_id DESC LIMIT 8")
    return render_lab('extension_case.html', 'extension-case',
                      uploads=uploads, message=message, error=error)


# ---------- L06 Magic Bytes ----------
@bp.route('/labs/upload/magic-bytes', methods=['GET', 'POST'])
def magic_bytes():
    """vuln：前 8 字节是 PNG signature 就放行 → 学生可拼 PNG header + HTML payload，
    再起名 evil.html，stored_name 保留 .html，浏览器按 declared 的 text/html 解析。
    safe：除了 signature，还要求尾部是合法 PNG IEND chunk，并强制 stored_name 为 .png。"""
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择文件。'
        else:
            head = upload_file.stream.read(8)
            upload_file.stream.seek(0)
            try:
                if current_mode() == 'vuln':
                    if head != _PNG_SIGNATURE:
                        raise ValueError('vuln：前 8 字节不是 PNG signature')
                    # ❌ 服务端"以为是 png"，但落盘时尊重用户文件名后缀
                    real_suffix = Path(upload_file.filename).suffix.lower() or '.png'
                    declared = mimetypes.guess_type('a' + real_suffix)[0] or 'image/png'
                    stored_name = secrets.token_hex(8) + real_suffix
                    row = _store_file(upload_file, 'magic-bytes', declared,
                                      stored_name=stored_name, public=True)
                else:
                    if head != _PNG_SIGNATURE:
                        raise ValueError('safe：非 PNG signature')
                    body = upload_file.stream.read()
                    upload_file.stream.seek(0)
                    if not body.endswith(b'IEND\xaeB`\x82'):
                        raise ValueError('safe：尾部不是 PNG IEND chunk，疑似拼接载荷')
                    # ✅ 强制 .png 扩展 + 强制 image/png
                    stored_name = secrets.token_hex(8) + '.png'
                    row = _store_file(upload_file, 'magic-bytes', 'image/png',
                                      stored_name=stored_name, public=True)
                message = (f"已保存：{_public_url(row['upload_id'])}（stored_name="
                           f"{row['stored_name']}, declared={row['declared_type']}）")
            except Exception as exc:
                error = str(exc)
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'magic-bytes' ORDER BY upload_id DESC LIMIT 8")
    return render_lab('magic_bytes.html', 'magic-bytes',
                      uploads=uploads, message=message, error=error)


# ---------- L07 Zip Slip ----------
@bp.route('/labs/upload/zip-slip', methods=['GET', 'POST'])
def zip_slip():
    message = None
    error = None
    extracted = []
    escaped_paths = []
    target_root = uploads_root() / 'public' / 'zip-slip'
    if request.method == 'POST':
        action = request.form.get('action', 'upload')
        if action == 'sample':
            # 生成示例 zip 直接返回让学生下载
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w') as zf:
                zf.writestr('normal.txt', 'this is a normal entry\n')
                zf.writestr('../../escape.txt', 'I escaped uploads/public !\n')
            buf.seek(0)
            return send_file(buf, mimetype='application/zip',
                             as_attachment=True, download_name='zipslip-sample.zip')
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择 zip。'
        else:
            try:
                target_root.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(upload_file.stream) as zf:
                    for member in zf.namelist():
                        target = (target_root / member).resolve()
                        if current_mode() == 'safe':
                            # ✅ realpath 必须落在 target_root 内
                            try:
                                target.relative_to(target_root.resolve())
                            except ValueError:
                                escaped_paths.append(member)
                                continue
                        else:
                            # ❌ 不校验
                            pass
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
                        extracted.append(str(target))
                message = f'解压完成，共 {len(extracted)} 项；vuln 模式可能写到目标目录之外。'
            except Exception as exc:
                error = str(exc)
    return render_lab('zip_slip.html', 'zip-slip',
                      extracted=extracted, escaped_paths=escaped_paths,
                      target_root=str(target_root), message=message, error=error)


# ---------- L08 SVG XSS ----------
@bp.route('/labs/upload/svg-xss', methods=['GET', 'POST'])
def svg_xss():
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择 svg 文件。'
        else:
            try:
                content = upload_file.stream.read()
                upload_file.stream.seek(0)
                if current_mode() == 'safe':
                    # ✅ 简易 sanitize：剥 <script> 标签
                    if b'<script' in content.lower() or b'onload=' in content.lower():
                        raise ValueError('safe：检测到 <script> / onload，已拒绝')
                row = _store_file(upload_file, 'svg-xss', 'image/svg+xml', public=True)
                message = f"已保存：{_public_url(row['upload_id'])}"
            except Exception as exc:
                error = str(exc)
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'svg-xss' ORDER BY upload_id DESC LIMIT 8")
    return render_lab('svg_xss.html', 'svg-xss',
                      uploads=uploads, message=message, error=error)


# ---------- L09 .htaccess / 配置覆盖 ----------
_MIME_OVERRIDE_PATH = lambda: data_root() / 'mime_overrides.json'


@bp.route('/labs/upload/htaccess-overwrite', methods=['GET', 'POST'])
def htaccess_overwrite():
    message = None
    error = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择文件。'
        else:
            name = Path(upload_file.filename).name
            try:
                if current_mode() == 'safe':
                    if name.startswith('.') or name in {'mime_overrides.json', '.htaccess', 'web.config'}:
                        raise ValueError('safe：拒绝隐藏文件 / 关键配置文件名')
                    row = _store_file(upload_file, 'htaccess-overwrite', upload_file.mimetype or 'application/octet-stream', public=True)
                    message = f"已保存：{_public_url(row['upload_id'])}"
                else:
                    # ❌ 允许任意文件名，且会真的覆盖 mime_overrides.json
                    if name == 'mime_overrides.json':
                        _MIME_OVERRIDE_PATH().write_bytes(upload_file.stream.read())
                        message = 'vuln：mime_overrides.json 已被覆盖，后续访问会按其规则映射 MIME！'
                    else:
                        row = _store_file(upload_file, 'htaccess-overwrite', upload_file.mimetype or 'application/octet-stream', public=True)
                        message = f"已保存：{_public_url(row['upload_id'])}"
            except Exception as exc:
                error = str(exc)
    overrides = {}
    if _MIME_OVERRIDE_PATH().exists():
        try:
            overrides = json.loads(_MIME_OVERRIDE_PATH().read_text())
        except Exception:
            overrides = {'_error': 'invalid json'}
    return render_lab('htaccess_overwrite.html', 'htaccess-overwrite',
                      overrides=overrides, message=message, error=error)


# ---------- L10 TOCTOU 扫描 ----------
def _delayed_scan_and_remove(path: Path, delay: float = 1.5):
    """模拟"先存后扫"：sleep 后若文件含禁词则删掉。"""
    def worker():
        try:
            time.sleep(delay)
            if path.exists():
                content = path.read_bytes()
                if b'<script' in content.lower() or b'malicious' in content.lower():
                    path.unlink(missing_ok=True)
        except Exception:
            pass
    threading.Thread(target=worker, daemon=True).start()


@bp.route('/labs/upload/toctou-scan', methods=['GET', 'POST'])
def toctou_scan():
    message = None
    error = None
    public_url = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if not upload_file or not upload_file.filename:
            error = '请选择文件。'
        else:
            try:
                if current_mode() == 'vuln':
                    # ❌ 直接存 public，再延迟扫描
                    row = _store_file(upload_file, 'toctou-scan', upload_file.mimetype or 'application/octet-stream', public=True)
                    public_url = _public_url(row['upload_id'])
                    target = data_root() / row['stored_path']
                    _delayed_scan_and_remove(target, delay=1.5)
                    message = f'vuln：文件已立刻发布到 {public_url}，1.5 秒后才扫描。可在此期间抢访问。'
                else:
                    # ✅ 先存 quarantine，扫描通过才挪到 public
                    quarantine = uploads_root() / _QUARANTINE_DIR_NAME
                    quarantine.mkdir(parents=True, exist_ok=True)
                    safe_name = _unique_name(upload_file.filename)
                    qpath = quarantine / safe_name
                    upload_file.save(qpath)
                    body = qpath.read_bytes()
                    if b'<script' in body.lower() or b'malicious' in body.lower():
                        qpath.unlink(missing_ok=True)
                        raise ValueError('safe：扫描发现恶意内容，未发布。')
                    final = uploads_root() / 'public' / safe_name
                    qpath.rename(final)
                    rel_path = str(final.relative_to(data_root()))
                    execute(
                        'INSERT INTO upload_entries (lab_slug, original_name, stored_name, declared_type, stored_path, note, is_public, created_at) VALUES (?, ?, ?, ?, ?, ?, 1, datetime(\'now\'))',
                        ('toctou-scan', upload_file.filename, safe_name, upload_file.mimetype or 'application/octet-stream', rel_path, 'released after scan'),
                    )
                    row = query_one('SELECT * FROM upload_entries ORDER BY upload_id DESC LIMIT 1')
                    public_url = _public_url(row['upload_id'])
                    message = f'safe：扫描通过后才发布到 {public_url}。'
            except Exception as exc:
                error = str(exc)
    uploads = query_all("SELECT * FROM upload_entries WHERE lab_slug = 'toctou-scan' ORDER BY upload_id DESC LIMIT 6")
    return render_lab('toctou_scan.html', 'toctou-scan',
                      uploads=uploads, public_url=public_url,
                      message=message, error=error)


# ---------- L11 文件名反射 XSS ----------
@bp.route('/labs/upload/reflected-filename', methods=['GET', 'POST'])
def reflected_filename():
    raw_filename = None
    safe_message = None
    if request.method == 'POST':
        upload_file = request.files.get('upload_file')
        if upload_file and upload_file.filename:
            raw_filename = upload_file.filename
            safe_message = f'已收到文件：{raw_filename}'
    return render_lab('reflected_filename.html', 'reflected-filename',
                      raw_filename=raw_filename, safe_message=safe_message)


def domain_taxonomy():
    return build_taxonomy(), '主轴：文件上传风险面', '文件上传风险面', '放大点'
