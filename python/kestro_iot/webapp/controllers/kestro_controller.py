from flask import (
    Blueprint, jsonify
)

api = Blueprint('kestro', __name__, url_prefix='/api/kestro')

@api.route('/status')
def status():
    return jsonify(version="1.0", status="Running")