import requests


def censys_lookup(ip: str, api_id: str, api_secret: str) -> dict:
    if not ip or not api_id or not api_secret:
        return None
    try:
        resp = requests.get(
            f"https://search.censys.io/api/v2/hosts/{ip}",
            auth=(api_id, api_secret),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("result", {})
        services = [
            {"port": s.get("port"), "service": s.get("service_name")}
            for s in data.get("services", [])
        ]
        location = data.get("location", {})
        return {
            "services": services,
            "city": location.get("city"),
            "country": location.get("country"),
        }
    except Exception as e:
        return {"error": str(e)}

