"""Production web dashboard for ADA Compliance Suite."""

import os
import sys
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitoring.monitor import ComplianceMonitor
from src.autonomous_engine import AutonomousEngine

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object("src.config.ProductionConfig")
CORS(app)

monitor = ComplianceMonitor()


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/status")
def status():
    sites = monitor.get_all_monitored_sites()
    stats = {
        "total_sites": len(sites),
        "compliant": sum(1 for s in sites if s.get("status") == "compliant"),
        "non_compliant": sum(1 for s in sites if s.get("status") != "compliant"),
        "last_updated": datetime.now().isoformat(),
    }
    return jsonify(stats)


@app.route("/api/sites")
def sites():
    sites = monitor.get_all_monitored_sites()
    return jsonify(sites)


@app.route("/api/sites/<path:url>")
def site_detail(url):
    history = monitor.get_site_history(url, days=30)
    return jsonify(history)


@app.route("/api/sites", methods=["POST"])
def add_site():
    data = request.json
    url = data.get("url")
    name = data.get("name")
    email = data.get("email")

    if not url:
        return jsonify({"error": "URL required"}), 400

    site_id = monitor.add_site(url, name, email)
    return jsonify({"id": site_id, "url": url})


@app.route("/api/sites/<path:url>", methods=["DELETE"])
def remove_site(url):
    success = monitor.remove_site(url)
    return jsonify({"success": success})


@app.route("/api/check/<path:url>")
def check_site(url):
    result = monitor.check_single_site(url)
    if result:
        return jsonify(result)
    return jsonify({"error": "Check failed"}), 500


@app.route("/api/run-cycle", methods=["POST"])
def run_cycle():
    try:
        engine = AutonomousEngine()
        engine.run_full_cycle()
        return jsonify({"status": "completed", "stats": engine.stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
