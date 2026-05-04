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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7001)
