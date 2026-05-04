from __future__ import annotations

import json
import re

from flask import Blueprint, Response, jsonify, render_template, request

from content_store import query_all, query_one
from jsonp_labs import LABS, build_taxonomy, get_lab
from shared import current_mode

bp = Blueprint('jsonp', __name__)
CALLBACK_RE = re.compile(r'^[A-Za-z_$][0-9A-Za-z_$.]{0,63}$')


def render_lab(template_name: str, slug: str, **context):
    return render_template(f'jsonp/labs/{template_name}', lab=get_lab(slug), mode=current_mode(), show_event_dock=True, **context)


def domain_info() -> dict:
    return {
        'code': 'JSONP',
        'title': 'JSONP 轨道',
        'description': '围绕 callback 可控、敏感数据跨域泄露与黑名单伪修复。',
        'summary': '帮助学生理解：JSONP 不是“老兼容”，而是脚本执行与跨域读取的组合风险。',
        'level': '进阶',
        'count': len(LABS),
        'href': '/domains/jsonp',
        'teaching_points': [
            '先讲 JSONP 为什么天然是 JavaScript 而不是 JSON。',
            '再讲 callback 参数为什么本质是代码位。',
            '最后讲敏感数据为什么不应通过 JSONP 返回。',
        ],
    }


def _jsonp(callback: str, payload: dict) -> Response:
    return Response(f'{callback}({json.dumps(payload, ensure_ascii=False)})', mimetype='application/javascript')


@bp.route('/api/jsonp/search')
def api_jsonp_search():
    callback = request.args.get('callback', 'console.log')
    q = request.args.get('q', 'kanxue')
    rows = [{'title': 'search-preview', 'query': q, 'note': 'jsonp response is executable JavaScript'}]
    if current_mode() == 'safe':
        if not CALLBACK_RE.fullmatch(callback):
            return jsonify({'error': 'invalid callback', 'rows': rows}), 400
    return _jsonp(callback, {'query': q, 'rows': rows})


@bp.route('/api/jsonp/profile')
def api_jsonp_profile():
    callback = request.args.get('callback', 'console.log')
    username = request.args.get('username', 'alice')
    profile = query_one('SELECT username, email, role, private_note FROM jsonp_profiles WHERE username = ?', (username,))
    if current_mode() == 'safe':
        return jsonify({'username': profile['username'], 'role': profile['role']})
    return _jsonp(callback, profile)


@bp.route('/api/jsonp/legacy')
def api_jsonp_legacy():
    callback = request.args.get('callback', 'console.log')
    filtered = callback.replace('alert', '').replace('eval', '') if current_mode() == 'vuln' else callback
    payload = {'status': 'ok', 'note': 'legacy callback filter only strips a few words'}
    if current_mode() == 'safe':
        if not CALLBACK_RE.fullmatch(callback):
            return jsonify({'error': 'invalid callback', 'payload': payload}), 400
        return _jsonp(callback, payload)
    return _jsonp(filtered, payload)


@bp.route('/labs/jsonp/callback-reflect')
def callback_reflect():
    return render_lab('callback_reflect.html', 'callback-reflect')


@bp.route('/labs/jsonp/profile-leak')
def profile_leak():
    profiles = query_all('SELECT username, role FROM jsonp_profiles ORDER BY username')
    return render_lab('profile_leak.html', 'profile-leak', profiles=profiles)


@bp.route('/labs/jsonp/callback-blacklist')
def callback_blacklist():
    return render_lab('callback_blacklist.html', 'callback-blacklist')


def domain_taxonomy():
    return build_taxonomy(), '主轴：JSONP 风险路径', 'JSONP 风险路径', '问题所在'
