"""
Subdomain Discovery
--------------------
Passive: crt.sh, certspotter, hackertarget — এগুলো সবগুলোই ফ্রি, কোনো API
         key লাগে না (DNSDumpster-এর কাজ এগুলো মিলেই করে)।
Active:  ছোট built-in wordlist দিয়ে DNS brute force (Subfinder-এর active
         অংশের সরলীকৃত ভার্সন)।
"""

import concurrent.futures

import requests

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "webmail", "smtp", "pop", "ns1", "ns2", "cpanel",
    "whm", "autodiscover", "autoconfig", "m", "mobile", "blog", "dev", "test",
    "staging", "api", "app", "admin", "portal", "vpn", "remote", "shop",
    "store", "support", "help", "docs", "cdn", "static", "media", "images",
    "img", "assets", "secure", "login", "mx", "mx1", "mx2", "dns", "dns1",
    "dns2", "ns", "ns3", "server", "host", "panel", "demo", "beta", "old",
    "new", "web", "web1", "web2", "cloud", "git", "gitlab", "jenkins", "ci",
    "jira", "confluence", "wiki", "chat", "status", "monitor", "stats",
    "analytics", "dashboard", "console", "internal", "intranet", "crm",
    "erp", "payment", "pay", "billing", "account", "accounts", "sso", "auth",
    "id", "db", "database", "sql", "backup", "files", "file", "upload",
    "download", "s3", "storage", "video", "stream", "live",
]


def passive_subdomains(domain: str) -> list:
    found = set()
    found |= _from_crtsh(domain)
    found |= _from_certspotter(domain)
    found |= _from_hackertarget(domain)
    return sorted(s for s in found if s.endswith(domain))


def _from_crtsh(domain: str) -> set:
    out = set()
    try:
        resp = requests.get(
            f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20
        )
        resp.raise_for_status()
        for entry in resp.json():
            for line in entry.get("name_value", "").split("\n"):
                line = line.strip().lstrip("*.")
                if line:
                    out.add(line)
    except Exception:
        pass
    return out


def _from_certspotter(domain: str) -> set:
    out = set()
    try:
        resp = requests.get(
            "https://api.certspotter.com/v1/issuances",
            params={
                "domain": domain,
                "include_subdomains": "true",
                "expand": "dns_names",
            },
            timeout=20,
        )
        if resp.status_code == 200:
            for entry in resp.json():
                for name in entry.get("dns_names", []):
                    out.add(name.lstrip("*."))
    except Exception:
        pass
    return out


def _from_hackertarget(domain: str) -> set:
    out = set()
    try:
        resp = requests.get(
            "https://api.hackertarget.com/hostsearch/",
            params={"q": domain},
            timeout=20,
        )
        if resp.status_code == 200 and "error" not in resp.text.lower():
            for line in resp.text.strip().split("\n"):
                if "," in line:
                    out.add(line.split(",")[0].strip())
    except Exception:
        pass
    return out


def brute_force_subdomains(domain: str, wordlist=None, max_workers: int = 20) -> list:
    """ছোট wordlist দিয়ে সমান্তরালে DNS resolve করে চেক করে কোন সাবডোমেইন আসলেই আছে।"""
    try:
        import dns.resolver
    except ImportError:
        return []

    words = wordlist or COMMON_SUBDOMAINS
    found = []

    def _resolve(word):
        candidate = f"{word}.{domain}"
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3
            resolver.lifetime = 3
            resolver.resolve(candidate, "A")
            return candidate
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        for result in pool.map(_resolve, words):
            if result:
                found.append(result)

    return sorted(found)

