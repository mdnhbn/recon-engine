"""Live Host Check — httpx-এর সরলীকৃত pure-Python ভার্সন।
কোন কোন host আসলে HTTP/HTTPS-এ সাড়া দেয়, তার status/title/server বের করে।"""

import concurrent.futures

import requests

requests.packages.urllib3.disable_warnings()  # noqa


def check_live_hosts(hosts: list, max_workers: int = 15) -> list:
    results = []

    def _check(host):
        for scheme in ("https", "http"):
            url = f"{scheme}://{host}"
            try:
                resp = requests.get(
                    url, timeout=6, verify=False, allow_redirects=True
                )
                title = _extract_title(resp.text)
                return {
                    "host": host,
                    "url": url,
                    "status_code": resp.status_code,
                    "title": title,
                    "server": resp.headers.get("Server"),
                    "headers": dict(resp.headers),
                    "body_snippet": resp.text[:2000],
                }
            except Exception:
                continue
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        for result in pool.map(_check, hosts):
            if result:
                results.append(result)

    return results


def _extract_title(html: str):
    try:
        import re
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:200]
    except Exception:
        pass
    return None

