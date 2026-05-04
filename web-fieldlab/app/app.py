from __future__ import annotations

from urllib.request import urlopen

from flask import Flask, jsonify, render_template

from config import Config
from content_store import init_content_db, query_one
from domains.authz import bp as authz_bp, domain_info as authz_info, domain_taxonomy as authz_taxonomy
from domains.injection import bp as injection_bp, domain_info as injection_info, domain_taxonomy as injection_taxonomy
from domains.jsonp import bp as jsonp_bp, domain_info as jsonp_info, domain_taxonomy as jsonp_taxonomy
from domains.payment import bp as payment_bp, domain_info as payment_info, domain_taxonomy as payment_taxonomy
from domains.race import bp as race_bp, domain_info as race_info, domain_taxonomy as race_taxonomy
from domains.sqli import bp as sqli_bp, domain_info as sqli_info, domain_taxonomy as sqli_taxonomy
from domains.ssrf import bp as ssrf_bp, domain_info as ssrf_info, domain_taxonomy as ssrf_taxonomy
from domains.ssti import bp as ssti_bp, domain_info as ssti_info, domain_taxonomy as ssti_taxonomy
from domains.upload import bp as upload_bp, domain_info as upload_info, domain_taxonomy as upload_taxonomy
from domains.xss import bp as xss_bp, domain_info as xss_info, domain_taxonomy as xss_taxonomy
from domains.xxe import bp as xxe_bp, domain_info as xxe_info, domain_taxonomy as xxe_taxonomy
from shared import current_mode
from sqli_db import run_select

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
init_content_db(force=False)

for blueprint in [sqli_bp, xss_bp, ssti_bp, ssrf_bp, authz_bp, upload_bp, payment_bp, injection_bp, xxe_bp, jsonp_bp, race_bp]:
    app.register_blueprint(blueprint)

DOMAIN_ORDER = ['sqli', 'xss', 'ssti', 'ssrf', 'authz', 'upload', 'payment', 'injection', 'xxe', 'jsonp', 'race']
DOMAIN_REGISTRY = {
    'sqli': {**sqli_info(), 'taxonomy_builder': sqli_taxonomy},
    'xss': {**xss_info(), 'taxonomy_builder': xss_taxonomy},
    'ssti': {**ssti_info(), 'taxonomy_builder': ssti_taxonomy},
    'ssrf': {**ssrf_info(), 'taxonomy_builder': ssrf_taxonomy},
    'authz': {**authz_info(), 'taxonomy_builder': authz_taxonomy},
    'upload': {**upload_info(), 'taxonomy_builder': upload_taxonomy},
    'payment': {**payment_info(), 'taxonomy_builder': payment_taxonomy},
    'injection': {**injection_info(), 'taxonomy_builder': injection_taxonomy},
    'xxe': {**xxe_info(), 'taxonomy_builder': xxe_taxonomy},
    'jsonp': {**jsonp_info(), 'taxonomy_builder': jsonp_taxonomy},
    'race': {**race_info(), 'taxonomy_builder': race_taxonomy},
}


@app.context_processor
def inject_globals():
    return {'mode': current_mode(), 'app_public_port': Config.APP_PUBLIC_PORT, 'show_event_dock': False}


@app.route('/')
def index():
    domains = [DOMAIN_REGISTRY[key] for key in DOMAIN_ORDER]
    return render_template('index.html', domains=domains, total_labs=sum(domain['count'] for domain in domains))


@app.route('/labs')
def labs_overview():
    return render_template('labs_overview.html', domains=[DOMAIN_REGISTRY[key] for key in DOMAIN_ORDER])


@app.route('/domains/<domain_code>')
def domain_index(domain_code: str):
    domain = DOMAIN_REGISTRY[domain_code]
    taxonomy_groups, taxonomy_label, primary_label, secondary_label = domain['taxonomy_builder']()
    labs = []
    for group in taxonomy_groups:
        labs.extend(group['labs'])
    return render_template('domain_index.html', domain=domain, taxonomy_groups=taxonomy_groups, taxonomy_label=taxonomy_label, primary_label=primary_label, secondary_label=secondary_label, labs=labs)


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
