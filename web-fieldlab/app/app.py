from __future__ import annotations

from urllib.request import urlopen

from flask import Flask, jsonify, render_template

from config import Config
from content_store import init_content_db, query_one
from domains.authz import bp as authz_bp, domain_info as authz_info, domain_taxonomy as authz_taxonomy
from domains.sqli import bp as sqli_bp, domain_info as sqli_info, domain_taxonomy as sqli_taxonomy
from domains.ssrf import bp as ssrf_bp, domain_info as ssrf_info, domain_taxonomy as ssrf_taxonomy
from domains.ssti import bp as ssti_bp, domain_info as ssti_info, domain_taxonomy as ssti_taxonomy
from domains.xss import bp as xss_bp, domain_info as xss_info, domain_taxonomy as xss_taxonomy
from shared import current_mode
from sqli_db import run_select

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
init_content_db(force=False)

app.register_blueprint(sqli_bp)
app.register_blueprint(xss_bp)
app.register_blueprint(ssti_bp)
app.register_blueprint(ssrf_bp)
app.register_blueprint(authz_bp)

DOMAIN_REGISTRY = {
    'sqli': {**sqli_info(), 'taxonomy_builder': sqli_taxonomy},
    'xss': {**xss_info(), 'taxonomy_builder': xss_taxonomy},
    'ssti': {**ssti_info(), 'taxonomy_builder': ssti_taxonomy},
    'ssrf': {**ssrf_info(), 'taxonomy_builder': ssrf_taxonomy},
    'authz': {**authz_info(), 'taxonomy_builder': authz_taxonomy},
}


@app.context_processor
def inject_globals():
    return {
        'mode': current_mode(),
        'app_public_port': Config.APP_PUBLIC_PORT,
        'show_event_dock': False,
    }


@app.route('/')
def index():
    domains = [DOMAIN_REGISTRY[key] for key in ['sqli', 'xss', 'ssti', 'ssrf', 'authz']]
    total_labs = sum(domain['count'] for domain in domains)
    return render_template('index.html', domains=domains, total_labs=total_labs)


@app.route('/labs')
def labs_overview():
    domains = [DOMAIN_REGISTRY[key] for key in ['sqli', 'xss', 'ssti', 'ssrf', 'authz']]
    return render_template('labs_overview.html', domains=domains)


@app.route('/domains/<domain_code>')
def domain_index(domain_code: str):
    domain = DOMAIN_REGISTRY[domain_code]
    taxonomy_groups, taxonomy_label, primary_label, secondary_label = domain['taxonomy_builder']()
    labs = []
    for group in taxonomy_groups:
        labs.extend(group['labs'])
    return render_template(
        'domain_index.html',
        domain=domain,
        taxonomy_groups=taxonomy_groups,
        taxonomy_label=taxonomy_label,
        primary_label=primary_label,
        secondary_label=secondary_label,
        labs=labs,
    )


@app.route('/healthz')
def healthz():
    status = {'status': 'ok'}
    try:
        status['content_db'] = query_one('SELECT 1 AS ok')['ok']
        status['sqli_db'] = run_select('SELECT 1 AS ok')[0]['ok']
        status['intranet'] = urlopen(Config.SSRF_INTERNAL_BASE + '/public/status', timeout=3).getcode()
        return jsonify(status)
    except Exception as exc:  # pragma: no cover
        status['status'] = 'error'
        status['message'] = str(exc)
        return jsonify(status), 500


if __name__ == '__main__':
    app.run(host=Config.APP_HOST, port=Config.APP_PORT, debug=False)
