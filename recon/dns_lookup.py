import socket


def get_dns_records(domain: str) -> dict:
    """A, AAAA, MX, NS, TXT, CNAME, SOA রেকর্ড বের করে। key ছাড়াই কাজ করে।"""
    try:
        import dns.resolver
    except ImportError:
        return {"error": "dnspython ইনস্টল নেই (pip install dnspython)"}

    records = {}
    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 5

    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
        try:
            answers = resolver.resolve(domain, rtype)
            records[rtype] = [str(r) for r in answers]
        except Exception:
            pass  # রেকর্ড না থাকলে স্কিপ

    try:
        records["resolved_ip"] = socket.gethostbyname(domain)
    except Exception:
        records["resolved_ip"] = None

    return records

