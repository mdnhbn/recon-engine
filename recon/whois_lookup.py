def get_whois(domain: str) -> dict:
    """ডোমেইনের Whois তথ্য বের করে। key ছাড়াই কাজ করে।"""
    try:
        import whois as whois_lib
    except ImportError:
        return {"error": "python-whois ইনস্টল নেই (pip install python-whois)"}

    try:
        w = whois_lib.whois(domain)
        return {
            "registrar": _stringify(w.get("registrar")),
            "creation_date": _stringify(w.get("creation_date")),
            "expiration_date": _stringify(w.get("expiration_date")),
            "updated_date": _stringify(w.get("updated_date")),
            "name_servers": _stringify(w.get("name_servers")),
            "status": _stringify(w.get("status")),
            "org": _stringify(w.get("org")),
            "country": _stringify(w.get("country")),
        }
    except Exception as e:
        return {"error": f"Whois lookup ব্যর্থ: {e}"}


def _stringify(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)
    return str(value)

