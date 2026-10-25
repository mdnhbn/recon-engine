import ipaddress
import re
from urllib.parse import urlsplit


def normalize_domain(target: str) -> str:
    """Accept a domain or HTTP(S) URL, never a database connection string."""
    target = target.strip()
    if not target or len(target) > 2048 or any(c.isspace() for c in target):
        raise ValueError("সঠিক domain বা HTTP/HTTPS URL দিন।")
    parsed = urlsplit(target if "://" in target else "//" + target)
    if parsed.scheme and parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("শুধু domain অথবা http:// ও https:// URL ব্যবহার করুন।")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL-এ username বা password দেওয়া যাবে না।")
    # Accessing port also rejects malformed/out-of-range ports.
    if parsed.port is not None:
        raise ValueError("শুধু domain দিন; port নম্বর বাদ দিন।")
    domain = (parsed.hostname or "").rstrip(".")
    if domain.startswith("www."):
        domain = domain[4:]
    try:
        domain = domain.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise ValueError("সঠিক domain দিন।") from error
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("এই স্ক্যানের জন্য IP address-এর বদলে domain দিন।")
    labels = domain.split(".")
    if (len(domain) > 253 or len(labels) < 2 or
            any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
                for part in labels)):
        raise ValueError("সঠিক domain দিন, যেমন example.com।")
    return domain
