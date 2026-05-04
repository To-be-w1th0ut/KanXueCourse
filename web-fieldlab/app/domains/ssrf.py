from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler, urlopen

from flask import Blueprint, render_template, request

from config import Config
from content_store import execute, query_all
from shared import current_mode
from ssrf_labs import LABS, build_taxonomy, get_lab

bp = Blueprint('ssrf', __name__)
PREVIEW_GATEWAY = 'http://preview-gateway:7001'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'ssrf/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=False, preview_gateway=PREVIEW_GATEWAY, **context)


def domain_info() -> dict:
    return {
        'code': 'SSRF',
        'title': 'SSRF 轨道',
        'description': '围绕服务端代发请求、URL 解析差异、重定向链和盲 SSRF 副作用。',
        'summary': '同一套内网服务上讲清协议、主机、网段、重定向与日志。',
        'level': '高级',
        'count': len(LABS),
        'href': '/domains/ssrf',
        'teaching_points': [
            '先让学生确认“请求是谁发的”。',
            '再讲解析差异和重定向链。',
            '最后讲无回显情况下如何通过副作用验证。',
        ],
    }


def is_private_host(hostname: str | None) -> bool:
    if not hostname:
        return True
    lowered = hostname.lower()
    if lowered in {'localhost', '127.0.0.1', '::1', 'db', 'intranet', 'preview-gateway'}:
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        pass
    try:
        resolved = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except Exception:
        return True


def fetch_url(url: str, follow_redirects: bool = True, timeout: int = 4):
    request_obj = Request(url, headers={'User-Agent': 'FieldLab-Preview/1.0'})
    if follow_redirects:
        with urlopen(request_obj, timeout=timeout) as response:
            body = response.read(1200).decode('utf-8', errors='replace')
            return response.getcode(), body, response.geturl()
    opener = build_opener(NoRedirect)
    try:
        with opener.open(request_obj, timeout=timeout) as response:
            body = response.read(1200).decode('utf-8', errors='replace')
            return response.getcode(), body, response.geturl()
    except Exception as exc:
        body = getattr(exc, 'read', lambda: b'')()
        preview = body.decode('utf-8', errors='replace') if body else str(exc)
        code = getattr(exc, 'code', 0) or 0
        return code, preview, url


def log_ssrf(lab_slug: str, target_url: str, outcome: str, preview: str):
    execute('INSERT INTO ssrf_logs (lab_slug, target_url, outcome, preview, created_at) VALUES (?, ?, ?, ?, datetime(\'now\'))', (lab_slug, target_url, outcome, preview[:400]))


@bp.route('/labs/ssrf/basic-fetch', methods=['GET', 'POST'])
def basic_fetch():
    target_url = PREVIEW_GATEWAY + '/public/status'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            if current_mode() == 'safe' and (parsed.scheme not in {'http', 'https'} or is_private_host(parsed.hostname)):
                raise ValueError('安全模式禁止抓取私有主机或非 http(s) 协议')
            code, body, final_url = fetch_url(target_url)
            response_preview = {'status': code, 'body': body, 'final_url': final_url}
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '目标地址不符合预览策略。'
    return render_lab('basic_fetch.html', 'basic-fetch', target_url=target_url, response_preview=response_preview, error=error)


@bp.route('/labs/ssrf/allowlist-bypass', methods=['GET', 'POST'])
def allowlist_bypass():
    target_url = PREVIEW_GATEWAY + '/public/card'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            if current_mode() == 'vuln':
                if not target_url.startswith(PREVIEW_GATEWAY + '/'):
                    raise ValueError('only preview-gateway URLs are allowed')
            else:
                parsed = urlparse(target_url)
                if parsed.scheme not in {'http', 'https'} or parsed.username or parsed.password or parsed.hostname != 'preview-gateway' or not parsed.path.startswith('/public'):
                    raise ValueError('安全模式要求显式解析后验证 preview-gateway /public 路径')
            code, body, final_url = fetch_url(target_url)
            response_preview = {'status': code, 'body': body, 'final_url': final_url}
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '安全模式拒绝该目标地址。'
    return render_lab('allowlist_bypass.html', 'allowlist-bypass', target_url=target_url, response_preview=response_preview, error=error)


@bp.route('/labs/ssrf/redirect-follow', methods=['GET', 'POST'])
def redirect_follow():
    target_url = PREVIEW_GATEWAY + '/redirect/metadata'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            if parsed.hostname != 'preview-gateway':
                raise ValueError('only preview-gateway host is accepted')
            code, body, final_url = fetch_url(target_url, follow_redirects=(current_mode() == 'vuln'))
            response_preview = {'status': code, 'body': body, 'final_url': final_url}
        except Exception as exc:
            error = str(exc) if current_mode() == 'vuln' else '安全模式不再自动跟随重定向。'
    return render_lab('redirect_follow.html', 'redirect-follow', target_url=target_url, response_preview=response_preview, error=error)


@bp.route('/labs/ssrf/blind-log', methods=['GET', 'POST'])
def blind_log():
    target_url = PREVIEW_GATEWAY + '/slow?seconds=2'
    message = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        start = time.perf_counter()
        try:
            parsed = urlparse(target_url)
            if current_mode() == 'safe' and (parsed.scheme not in {'http', 'https'} or is_private_host(parsed.hostname)):
                raise ValueError('安全模式禁止向内网和保留地址发起探测')
            code, body, final_url = fetch_url(target_url, follow_redirects=True, timeout=5)
            elapsed = round(time.perf_counter() - start, 3)
            log_ssrf('blind-log', target_url, f'status={code} elapsed={elapsed}s final={final_url}', body)
            message = f'任务已完成：status={code}，elapsed={elapsed}s，结果写入下方日志。'
        except Exception as exc:
            log_ssrf('blind-log', target_url, 'blocked' if current_mode() == 'safe' else 'error', str(exc))
            error = str(exc) if current_mode() == 'vuln' else '目标地址被安全模式拒绝。'
    logs = query_all('SELECT log_id, lab_slug, target_url, outcome, preview, created_at FROM ssrf_logs ORDER BY log_id DESC LIMIT 10')
    return render_lab('blind_log.html', 'blind-log', target_url=target_url, message=message, error=error, logs=logs)


def domain_taxonomy():
    return build_taxonomy(), '主轴：请求路径与绕过模型', '请求路径与绕过模型', '观测方式'
