import json
import socket

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from extensions import db
from models import ScanHistory, Settings
from recon.whois_lookup import get_whois
from recon.dns_lookup import get_dns_records
from recon.subdomains import passive_subdomains, brute_force_subdomains
from recon.live_check import check_live_hosts
from recon.techstack import identify_tech_stack
from recon.shodan_lookup import shodan_lookup
from recon.censys_lookup import censys_lookup
from recon.utils import normalize_domain

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    settings = Settings.get()
    return render_template(
        "index.html",
        scans_today=current_user.scans_today_count(),
        daily_limit=settings.daily_scan_limit,
        ad_snippet=settings.ad_snippet,
    )


@main_bp.route("/my-scans")
@login_required
def my_scans():
    scans = current_user.scans.order_by(ScanHistory.created_at.desc()).limit(50).all()
    return render_template("my_scans.html", scans=scans)


@main_bp.route("/api/recon", methods=["POST"])
@login_required
def recon():
    settings = Settings.get()

    # --- রেট লিমিট চেক (admin-এর জন্য কোনো লিমিট নেই) ---
    if not current_user.is_admin:
        if current_user.scans_today_count() >= settings.daily_scan_limit:
            return jsonify({
                "error": f"তোমার দৈনিক স্ক্যান লিমিট ({settings.daily_scan_limit} টি) শেষ। "
                         f"আগামীকাল আবার চেষ্টা করো।"
            }), 429

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict) or not isinstance(data.get("target", ""), str):
        return jsonify(error="একটি domain বা HTTP/HTTPS URL দিন।"), 400
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"error": "কোনো domain/URL দেওয়া হয়নি।"}), 400

    try:
        domain = normalize_domain(target)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    result = {"target": domain}

    # Stage 1: Passive Recon & OSINT
    result["whois"] = get_whois(domain)
    result["dns"] = get_dns_records(domain)
    result["passive_subdomains"] = passive_subdomains(domain)

    # Stage 2: Active Subdomain Discovery
    result["active_subdomains"] = brute_force_subdomains(domain)

    all_subs = set(result["passive_subdomains"]) | set(result["active_subdomains"])
    all_subs.add(domain)

    # Stage 3: Live host check
    result["live_hosts"] = check_live_hosts(sorted(all_subs))

    # Stage 4: Tech stack + (যদি key থাকে) Shodan/Censys
    for host in result["live_hosts"]:
        host["tech_stack"] = identify_tech_stack(host)
        try:
            ip = socket.gethostbyname(host["host"])
        except Exception:
            ip = None
        host["ip"] = ip

        if settings.shodan_api_key:
            host["shodan"] = shodan_lookup(ip, settings.shodan_api_key)
        if settings.censys_api_id and settings.censys_api_secret:
            host["censys"] = censys_lookup(ip, settings.censys_api_id, settings.censys_api_secret)

    # --- হিস্ট্রি সেভ ---
    history = ScanHistory(
        user_id=current_user.id,
        target=domain,
        subdomain_count=len(all_subs),
        live_host_count=len(result["live_hosts"]),
        result_json=json.dumps(result),
    )
    db.session.add(history)
    db.session.commit()

    result["scans_today"] = current_user.scans_today_count()
    result["daily_limit"] = settings.daily_scan_limit
    return jsonify(result)

