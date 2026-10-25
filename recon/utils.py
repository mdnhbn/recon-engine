from urllib.parse import urlparse


def normalize_domain(target: str) -> str:
    """URL দিলেও শুধু ডোমেইনটা বের করে আনে, www. বাদ দেয়।"""
    target = target.strip()
    if "://" in target:
        target = urlparse(target).netloc
    target = target.split("/")[0].strip()
    if target.startswith("www."):
        target = target[4:]
    return target.lower()

