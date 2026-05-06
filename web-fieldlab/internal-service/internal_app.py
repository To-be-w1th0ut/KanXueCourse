from __future__ import annotations

import time
from flask import Flask, jsonify, redirect, request, Response

app = Flask(__name__)

@app.route('/public/status')
def public_status():
    return jsonify({'service': 'preview-gateway', 'status': 'ok'})

@app.route('/public/card')
def public_card():
    return '<div><strong>Preview Gateway</strong><p>Only public snippets should be fetched here.</p></div>'

@app.route('/redirect/metadata')
def redirect_metadata():
    return redirect('http://intranet:7001/internal/metadata', code=302)

@app.route('/internal/metadata')
def internal_metadata():
    return jsonify({'instance': 'intranet-metadata', 'token': 'FLAG{ssrf_reaches_internal_metadata}', 'role': 'backend-only'})

@app.route('/internal/admin-panel')
def internal_admin_panel():
    return Response('<h1>Internal Admin Panel</h1><p>secret_export_token=FLAG{redirect_chain_reaches_admin}</p>', mimetype='text/html')

@app.route('/slow')
def slow():
    seconds = min(max(int(request.args.get('seconds', '2')), 1), 5)
    time.sleep(seconds)
    return jsonify({'slept': seconds, 'note': 'timing side effect observable from fetcher'})

@app.route('/webhook')
def webhook():
    msg = request.args.get('msg', 'ping')
    return jsonify({'received': msg, 'source': request.remote_addr})


# ----- 批次 3 SSRF 扩充用：模拟 AWS / 阿里云元数据服务 -----
@app.route('/latest/meta-data/<path:item>')
def cloud_metadata(item: str):
    """对应 169.254.169.254 上常见的元数据；这里挂在 intranet 的 /latest 路径下。"""
    fake = {
        'iam/security-credentials/lab-role': '{"AccessKeyId":"AKIA-LAB","SecretAccessKey":"FLAG{ssrf_steals_iam_token}","Token":"…"}',
        'instance-id': 'i-0fieldlab',
        'hostname': 'intranet.lab.local',
        'placement/region': 'lab-east-1',
    }
    return Response(fake.get(item, 'not-found'), mimetype='text/plain')


# ----- L07 后端 admin-only API（凭 X-Internal-Token 才能访问） -----
@app.route('/internal/secret-export')
def internal_secret_export():
    if request.headers.get('X-Internal-Token') == 'lab-internal-token':
        return jsonify({'flag': 'FLAG{ssrf_added_internal_header}', 'rows': 4242})
    return Response('forbidden', status=403)


# ----- L09 CRLF / 头部注入观察点 -----
@app.route('/internal/echo-headers')
def internal_echo_headers():
    return jsonify({k: v for k, v in request.headers.items()})


# ----- L11 自定义协议 / 长 URL 重绑定演示用 -----
@app.route('/internal/db-ping')
def internal_db_ping():
    """模拟一个内部服务；只接受来自 intranet 网段的请求。"""
    return jsonify({'service': 'mock-db-ping', 'flag': 'FLAG{ssrf_pings_internal_db}'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7001)
