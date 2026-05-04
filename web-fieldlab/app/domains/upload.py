from __future__ import annotations

import mimetypes
import os
import secrets
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


@bp.route('/uploads/public/<int:upload_id>')
def serve_public_upload(upload_id: int):
    row = query_one('SELECT * FROM upload_entries WHERE upload_id = ? AND is_public = 1', (upload_id,))
    if not row:
        abort(404)
    path = data_root() / row['stored_path']
    if not path.exists():
        abort(404)
    if current_mode() == 'vuln':
        guessed = row['declared_type'] or mimetypes.guess_type(row['original_name'])[0] or 'application/octet-stream'
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


def domain_taxonomy():
    return build_taxonomy(), '主轴：文件上传风险面', '文件上传风险面', '放大点'
