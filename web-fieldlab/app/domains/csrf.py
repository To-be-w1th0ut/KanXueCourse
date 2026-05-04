from __future__ import annotations

import secrets
from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, render_template, request, session

from content_store import execute, query_all, query_one
from csrf_labs import LABS, build_taxonomy, get_lab
from shared import current_mode

bp = Blueprint('csrf', __name__)


def ensure_csrf_user():
    if 'csrf_user' not in session:
        session['csrf_user'] = 'alice'
    return session['csrf_user']


def current_account():
    username = ensure_csrf_user()
    return query_one('SELECT * FROM csrf_accounts WHERE username = ?', (username,))


def csrf_token() -> str:
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_hex(16)
        session['csrf_token'] = token
    return token


def render_lab(template_name: str, slug: str, **context):
    return render_template(
        f'csrf/labs/{template_name}',
        lab=get_lab(slug),
        mode=current_mode(),
        show_event_dock=False,
        csrf_account=current_account(),
        csrf_accounts=query_all('SELECT username, balance, email_pref, mfa_enabled FROM csrf_accounts ORDER BY username'),
        csrf_token_value=csrf_token(),
        **context,
    )


def domain_info() -> dict:
    return {
        'code': 'CSRF',
        'title': 'CSRF 轨道',
        'description': '围绕无 token 状态修改、伪来源校验、JSON API 与安全配置变更。',
        'summary': '用同一账户中心讲清“浏览器自动带身份”带来的跨站请求伪造风险。',
        'level': '进阶',
        'count': len(LABS),
        'href': '/domains/csrf',
        'teaching_points': [
            '先让学生理解 CSRF 与 XSS 的边界：攻击者不需要读响应，也能让受害者发状态请求。',
            '再讲 Token、Origin/Referer、SameSite 的组合防线。',
            '最后讲安全配置变更同样属于 CSRF 风险面。',
        ],
    }


def _log_transfer(from_user: str, to_user: str, amount: float, note: str, source: str):
    execute('INSERT INTO csrf_transfer_logs (from_user, to_user, amount, note, source, created_at) VALUES (?, ?, ?, ?, ?, datetime(\'now\'))', (from_user, to_user, amount, note, source))


def _check_token(submitted: str | None):
    return submitted and submitted == session.get('csrf_token')


def _referer_contains_host() -> bool:
    referer = request.headers.get('Referer', '')
    host = request.host_url.rstrip('/')
    return host in referer


@bp.route('/labs/csrf/switch/<username>')
def switch_csrf_user(username: str):
    session['csrf_user'] = username
    return redirect(request.args.get('next') or '/domains/csrf')


@bp.route('/labs/csrf/transfer-no-token', methods=['GET', 'POST'])
def transfer_no_token():
    message = None
    error = None
    account = current_account()
    if request.method == 'POST':
        to_user = request.form.get('to_user', 'bob')
        amount = float(request.form.get('amount', '0'))
        try:
            if current_mode() == 'safe' and not _check_token(request.form.get('csrf_token')):
                raise ValueError('安全模式：缺少或错误的 CSRF token。')
            if amount <= 0 or amount > account['balance']:
                raise ValueError('金额非法或余额不足。')
            execute('UPDATE csrf_accounts SET balance = balance - ? WHERE username = ?', (amount, account['username']))
            execute('UPDATE csrf_accounts SET balance = balance + ? WHERE username = ?', (amount, to_user))
            _log_transfer(account['username'], to_user, amount, 'wallet transfer', 'form')
            message = f'转账完成：{amount:.2f} -> {to_user}'
        except Exception as exc:
            error = str(exc)
    accounts = query_all('SELECT username, balance, email_pref, mfa_enabled FROM csrf_accounts ORDER BY username')
    logs = query_all('SELECT * FROM csrf_transfer_logs ORDER BY log_id DESC LIMIT 8')
    return render_lab('transfer_no_token.html', 'transfer-no-token', accounts=accounts, logs=logs, message=message, error=error)


@bp.route('/labs/csrf/referer-check', methods=['GET', 'POST'])
def referer_check():
    message = None
    error = None
    account = current_account()
    if request.method == 'POST':
        to_user = request.form.get('to_user', 'bob')
        amount = float(request.form.get('amount', '0'))
        try:
            if current_mode() == 'safe':
                if not _check_token(request.form.get('csrf_token')):
                    raise ValueError('安全模式：缺少 CSRF token。')
                parsed = urlparse(request.headers.get('Origin') or request.headers.get('Referer') or '')
                if parsed.netloc != request.host:
                    raise ValueError('安全模式：来源校验失败。')
            else:
                if not _referer_contains_host():
                    raise ValueError('漏洞模式：开发只做了 contains 检查，课堂可通过构造 Referer 观察差异。')
            if amount <= 0 or amount > account['balance']:
                raise ValueError('金额非法或余额不足。')
            execute('UPDATE csrf_accounts SET balance = balance - ? WHERE username = ?', (amount, account['username']))
            execute('UPDATE csrf_accounts SET balance = balance + ? WHERE username = ?', (amount, to_user))
            _log_transfer(account['username'], to_user, amount, 'referer-guard transfer', 'referer-check')
            message = f'转账完成：{amount:.2f} -> {to_user}'
        except Exception as exc:
            error = str(exc)
    logs = query_all('SELECT * FROM csrf_transfer_logs ORDER BY log_id DESC LIMIT 8')
    return render_lab('referer_check.html', 'referer-check', logs=logs, message=message, error=error)


@bp.route('/labs/csrf/json-settings')
def json_settings():
    account = current_account()
    logs = query_all('SELECT * FROM csrf_transfer_logs ORDER BY log_id DESC LIMIT 8')
    return render_lab('json_settings.html', 'json-settings', account=account, logs=logs)


@bp.route('/api/csrf/settings', methods=['POST'])
def api_csrf_settings():
    account = current_account()
    payload = request.get_json(silent=True) or {}
    email_pref = payload.get('email_pref', account['email_pref'])
    try:
        if current_mode() == 'safe' and request.headers.get('X-CSRF-Token') != session.get('csrf_token'):
            return jsonify({'error': 'invalid csrf token'}), 403
        execute('UPDATE csrf_accounts SET email_pref = ? WHERE username = ?', (email_pref, account['username']))
        _log_transfer(account['username'], account['username'], 0.0, f'email_pref -> {email_pref}', 'json-api')
        return jsonify({'status': 'updated', 'email_pref': email_pref})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@bp.route('/labs/csrf/logout-and-mfa', methods=['GET', 'POST'])
def logout_and_mfa():
    message = None
    error = None
    account = current_account()
    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if current_mode() == 'safe' and not _check_token(request.form.get('csrf_token')):
                raise ValueError('安全模式：缺少或错误的 CSRF token。')
            if action == 'toggle-mfa':
                new_value = 0 if account['mfa_enabled'] else 1
                execute('UPDATE csrf_accounts SET mfa_enabled = ? WHERE username = ?', (new_value, account['username']))
                _log_transfer(account['username'], account['username'], 0.0, f'mfa_enabled -> {new_value}', 'mfa-toggle')
                message = f'MFA 已更新为 {new_value}'
            elif action == 'logout':
                session.pop('csrf_user', None)
                session.pop('csrf_token', None)
                message = '当前账户已登出，刷新后会回到默认 alice。'
            else:
                raise ValueError('未知操作。')
        except Exception as exc:
            error = str(exc)
    account = current_account()
    logs = query_all('SELECT * FROM csrf_transfer_logs ORDER BY log_id DESC LIMIT 8')
    return render_lab('logout_and_mfa.html', 'logout-and-mfa', account=account, logs=logs, message=message, error=error)


@bp.route('/labs/csrf/attack-transfer')
def attack_transfer():
    return render_template('csrf/attack_transfer.html', mode=current_mode(), show_event_dock=False)


@bp.route('/labs/csrf/attack-settings')
def attack_settings():
    return render_template('csrf/attack_settings.html', mode=current_mode(), show_event_dock=False)


def domain_taxonomy():
    return build_taxonomy(), '主轴：CSRF 风险面', 'CSRF 风险面', '缺失的防护'
