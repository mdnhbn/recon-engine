import requests


def shodan_lookup(ip: str, api_key: str) -> dict:
    if not ip or not api_key:
        return None
    try:
        resp = requests.get(
            f"https://api.shodan.io/shodan/host/{ip}",
            params={"key": api_key},
            timeout=15,
        )
        if resp.status_code == 404:
            return {"info": "Shodan-এ কোনো তথ্য নেই"}
        resp.raise_for_status()
        data = resp.json()
        return {
            "org": data.get("org"),
            "os": data.get("os"),
            "ports": data.get("ports"),
            "vulns": list(data.get("vulns", [])) if data.get("vulns") else [],
        }
    except Exception as e:
        return {"error": str(e)}

