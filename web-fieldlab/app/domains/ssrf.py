from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urlparse, urlunparse
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


# =====================================================================
# 批次 3：SSRF L05-L12 共 8 个新关卡
# =====================================================================

# ---------- L05 IP 多种编码绕过 ----------
def _vuln_ip_string_blacklist(host: str) -> bool:
    """vuln：只看字符串，禁掉 127.0.0.1 / localhost 的字面写法。"""
    bad = {'127.0.0.1', 'localhost', '0.0.0.0', '::1', 'intranet'}
    return host.lower() in bad


def _safe_ip_resolve(host: str) -> bool:
    """safe：解析 hostname 后用 ipaddress 对象判 loopback/private。"""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(host))
        except Exception:
            return False
    return not (ip.is_loopback or ip.is_private or ip.is_reserved or ip.is_link_local)


@bp.route('/labs/ssrf/ip-encoding', methods=['GET', 'POST'])
def ip_encoding():
    target_url = 'http://intranet:7001/internal/metadata'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            host = parsed.hostname or ''
            if current_mode() == 'vuln':
                if _vuln_ip_string_blacklist(host):
                    raise ValueError(f'字符串黑名单拒绝：{host}')
            else:
                if not _safe_ip_resolve(host):
                    raise ValueError('安全模式：解析后的 IP 属于内网/loopback/保留。')
                if parsed.scheme not in {'http', 'https'}:
                    raise ValueError('安全模式：仅允许 http/https。')
            code, body, final_url = fetch_url(target_url)
            response_preview = {'status': code, 'body': body, 'final_url': final_url}
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'ip_encoding.html', 'ip-encoding',
        target_url=target_url, response_preview=response_preview, error=error,
    )


# ---------- L06 云元数据 ----------
@bp.route('/labs/ssrf/cloud-metadata', methods=['GET', 'POST'])
def cloud_metadata():
    target_url = 'http://intranet:7001/latest/meta-data/iam/security-credentials/lab-role'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            if current_mode() == 'safe':
                # ✅ 拒绝 link-local 169.254.0.0/16；同时拒绝 path 含 /latest/meta-data
                host = parsed.hostname or ''
                try:
                    ip = ipaddress.ip_address(host if not host.replace('.', '').isdigit() else host)
                    if ip.is_link_local:
                        raise ValueError('安全模式：禁止访问 link-local 元数据地址。')
                except ValueError:
                    try:
                        ip = ipaddress.ip_address(socket.gethostbyname(host))
                        if ip.is_link_local:
                            raise ValueError('安全模式：解析后的 IP 是 link-local。')
                    except (socket.gaierror, ValueError):
                        pass
                if '/latest/meta-data' in (parsed.path or ''):
                    raise ValueError('安全模式：路径包含云元数据特征。')
            code, body, final_url = fetch_url(target_url)
            response_preview = {'status': code, 'body': body, 'final_url': final_url}
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'cloud_metadata.html', 'cloud-metadata',
        target_url=target_url, response_preview=response_preview, error=error,
    )


# ---------- L07 请求头注入 ----------
_FORBIDDEN_HEADER_PREFIX = ('x-internal-', 'authorization', 'cookie')


@bp.route('/labs/ssrf/header-injection', methods=['GET', 'POST'])
def header_injection():
    target_url = 'http://intranet:7001/internal/secret-export'
    headers_text = ''
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        headers_text = request.form.get('headers', '')
        try:
            extra_headers = {}
            for line in headers_text.splitlines():
                line = line.strip()
                if not line or ':' not in line:
                    continue
                k, v = line.split(':', 1)
                k, v = k.strip(), v.strip()
                if current_mode() == 'safe':
                    if k.lower().startswith(_FORBIDDEN_HEADER_PREFIX):
                        raise ValueError(f'安全模式：禁止自定义敏感头 {k}')
                extra_headers[k] = v
            req = Request(target_url, headers={'User-Agent': 'FieldLab-Preview/1.0', **extra_headers})
            with urlopen(req, timeout=4) as resp:
                body = resp.read(1500).decode('utf-8', errors='replace')
                response_preview = {'status': resp.getcode(), 'body': body, 'final_url': resp.geturl()}
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'header_injection.html', 'header-injection',
        target_url=target_url, headers=headers_text,
        response_preview=response_preview, error=error,
    )


# ---------- L08 file:// 协议 ----------
@bp.route('/labs/ssrf/file-protocol', methods=['GET', 'POST'])
def file_protocol():
    target_url = 'file:///etc/hostname'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            if current_mode() == 'vuln':
                # ❌ 只检查"以 http 开头"——但 file:// 不在黑名单
                if target_url.startswith('http://') or target_url.startswith('https://'):
                    pass  # 允许
                elif parsed.scheme == 'file':
                    pass  # 没禁
                else:
                    raise ValueError('未知协议')
            else:
                if parsed.scheme not in {'http', 'https'}:
                    raise ValueError('安全模式：仅允许 http/https 协议。')
            with urlopen(target_url, timeout=4) as resp:
                body = resp.read(1500).decode('utf-8', errors='replace')
                response_preview = {'status': getattr(resp, 'status', 200), 'body': body, 'final_url': target_url}
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'file_protocol.html', 'file-protocol',
        target_url=target_url, response_preview=response_preview, error=error,
    )


# ---------- L09 CRLF 走私（用裸 socket 拼请求模拟） ----------
@bp.route('/labs/ssrf/crlf-smuggling', methods=['GET', 'POST'])
def crlf_smuggling():
    host_default = 'intranet'
    port_default = 7001
    path_default = '/internal/echo-headers'
    host = host_default
    port = port_default
    path = path_default
    response_preview = None
    error = None
    if request.method == 'POST':
        host = request.form.get('host', host_default).strip()
        port = int(request.form.get('port', port_default))
        path = request.form.get('path', path_default)
        try:
            if current_mode() == 'safe':
                if any(ch in path for ch in ('\r', '\n', '%0d', '%0a', '%0D', '%0A')):
                    raise ValueError('安全模式：path 含控制字符或编码后的 CRLF。')
            # vuln 模式：把用户 path 里的 %0d%0a 解码后直接拼进 raw HTTP 请求
            raw_path = path.replace('%0d', '\r').replace('%0D', '\r').replace('%0a', '\n').replace('%0A', '\n')
            payload = f'GET {raw_path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: FieldLab/1.0\r\nConnection: close\r\n\r\n'
            with socket.create_connection((host, port), timeout=4) as sock:
                sock.sendall(payload.encode('latin-1', errors='replace'))
                chunks = []
                while True:
                    buf = sock.recv(2048)
                    if not buf:
                        break
                    chunks.append(buf)
                    if sum(len(c) for c in chunks) > 4096:
                        break
            raw = b''.join(chunks).decode('utf-8', errors='replace')
            response_preview = {'raw_request': payload, 'raw_response': raw[:2000]}
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'crlf_smuggling.html', 'crlf-smuggling',
        host=host, port=port, path=path,
        response_preview=response_preview, error=error,
    )


# ---------- L10 DNS 重绑定 / 双次解析 ----------
# 模拟：rebind.lab 主机名第一次解析回公网 IP，第二次解析回 intranet
_REBIND_STATE = {'count': 0}


def _resolve_rebind(host: str) -> str:
    """教学等价模拟：第 1 次返回 1.1.1.1（公网），之后返回 intranet 的 IP。"""
    if host != 'rebind.lab':
        return socket.gethostbyname(host)
    _REBIND_STATE['count'] += 1
    if _REBIND_STATE['count'] == 1:
        return '1.1.1.1'
    return socket.gethostbyname('intranet')


@bp.route('/labs/ssrf/dns-rebinding', methods=['GET', 'POST'])
def dns_rebinding():
    target_url = 'http://rebind.lab:7001/internal/metadata'
    response_preview = None
    error = None
    note = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            host = parsed.hostname or ''
            # 第 1 次解析：用于"白名单校验"
            ip1 = _resolve_rebind(host)
            try:
                ip_obj = ipaddress.ip_address(ip1)
                if ip_obj.is_private or ip_obj.is_loopback:
                    raise ValueError(f'白名单校验失败：第一次解析得到 {ip1}')
            except ValueError as exc:
                raise exc
            note = f'校验阶段解析 → {ip1}（看起来是公网 IP，放行）'
            if current_mode() == 'vuln':
                # ❌ vuln：放行后重新发请求，又触发一次 DNS 解析
                ip2 = _resolve_rebind(host)
                rebuilt = urlunparse(parsed._replace(netloc=f'{ip2}:{parsed.port or 80}'))
                code, body, final_url = fetch_url(rebuilt)
                note += f'；实际请求阶段解析 → {ip2}（→ 内网！）'
                response_preview = {'status': code, 'body': body, 'final_url': final_url}
            else:
                # ✅ safe：用第一次拿到的 IP 直接发请求，不再二次解析
                rebuilt = urlunparse(parsed._replace(netloc=f'{ip1}:{parsed.port or 80}'))
                code, body, final_url = fetch_url(rebuilt)
                note += '；安全模式直接复用第一次解析结果。'
                response_preview = {'status': code, 'body': body, 'final_url': final_url}
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'dns_rebinding.html', 'dns-rebinding',
        target_url=target_url, response_preview=response_preview, error=error,
        note=note, rebind_count=_REBIND_STATE['count'],
    )


# ---------- L11 响应反射型外带 ----------
@bp.route('/labs/ssrf/response-reflection', methods=['GET', 'POST'])
def response_reflection():
    target_url = 'http://intranet:7001/redirect/metadata'
    response_preview = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        try:
            parsed = urlparse(target_url)
            if parsed.hostname != 'intranet':
                raise ValueError('only intranet host accepted')
            code, body, final_url = fetch_url(target_url, follow_redirects=True)
            if current_mode() == 'vuln':
                # ❌ 完整回显 final_url，攻击者可借助 redirect path 外带任意数据
                response_preview = {'status': code, 'final_url': final_url, 'final_url_redacted': None}
            else:
                # ✅ 仅回显 hostname + 状态码
                redacted = urlparse(final_url)
                response_preview = {
                    'status': code,
                    'final_url': None,
                    'final_url_redacted': f'{redacted.scheme}://{redacted.hostname}',
                }
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'response_reflection.html', 'response-reflection',
        target_url=target_url, response_preview=response_preview, error=error,
    )


# ---------- L12 时间差盲 SSRF ----------
@bp.route('/labs/ssrf/time-based-blind', methods=['GET', 'POST'])
def time_based_blind():
    target_url = 'http://intranet:7001/slow?seconds=2'
    elapsed = None
    error = None
    if request.method == 'POST':
        target_url = request.form.get('target_url', '')
        start = time.perf_counter()
        try:
            parsed = urlparse(target_url)
            if parsed.scheme not in {'http', 'https'}:
                raise ValueError('only http/https')
            try:
                fetch_url(target_url, follow_redirects=False, timeout=6)
            except Exception:
                # 即使错误也吞掉（vuln 模式无回显），仍然测耗时
                pass
            elapsed = round(time.perf_counter() - start, 3)
            if current_mode() == 'safe':
                # ✅ 安全模式：补足固定耗时（time-based padding）
                pad = max(0.0, 3.0 - elapsed)
                time.sleep(pad)
                elapsed = round(time.perf_counter() - start, 3)
        except Exception as exc:
            error = str(exc)
    return render_lab(
        'time_based_blind.html', 'time-based-blind',
        target_url=target_url, elapsed=elapsed, error=error,
    )


def domain_taxonomy():
    return build_taxonomy(), '主轴：请求路径与绕过模型', '请求路径与绕过模型', '观测方式'
