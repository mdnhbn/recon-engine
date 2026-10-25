"""Tech Stack Identification — Wappalyzer/WhatWeb/BuiltWith-এর সরলীকৃত ভার্সন।
Response headers আর HTML body-তে পরিচিত প্যাটার্ন খুঁজে টেক স্ট্যাক অনুমান করে।"""

import re

SIGNATURES = {
    "WordPress": [r"wp-content", r"wp-includes", r'name="generator" content="WordPress'],
    "Joomla": [r"/media/jui/", r'content="Joomla'],
    "Drupal": [r"Drupal\.settings", r'content="Drupal'],
    "Shopify": [r"cdn\.shopify\.com", r"Shopify\.theme"],
    "Wix": [r"static\.wixstatic\.com", r"wix-code"],
    "Next.js": [r"__NEXT_DATA__", r"_next/static"],
    "React": [r"react-dom", r"data-reactroot"],
    "Vue.js": [r"__vue__", r"vue\.js"],
    "Angular": [r"ng-version", r"angular\.js"],
    "jQuery": [r"jquery(?:\.min)?\.js"],
    "Bootstrap": [r"bootstrap(?:\.min)?\.css"],
    "Laravel": [r"laravel_session"],
    "Django": [r"csrftoken"],
    "Cloudflare": [r"cloudflare"],
    "Nginx": [r"nginx"],
    "Apache": [r"apache"],
    "PHP": [r"\.php(?:\?|\"|')"],
    "Google Analytics": [r"google-analytics\.com", r"gtag\("],
    "Google Tag Manager": [r"googletagmanager\.com"],
}


def identify_tech_stack(host_info: dict) -> list:
    detected = set()
    server_header = (host_info.get("server") or "")
    headers_text = " ".join(f"{k}:{v}" for k, v in (host_info.get("headers") or {}).items())
    body = host_info.get("body_snippet") or ""
    haystack = f"{server_header} {headers_text} {body}"
    for tech, patterns in SIGNATURES.items():
        for pattern in patterns:
            if re.search(pattern, haystack, re.IGNORECASE):
                detected.add(tech)
                break

    # Server/Powered-By header থেকে সরাসরি
    powered_by = (host_info.get("headers") or {}).get("X-Powered-By")
    if powered_by:
        detected.add(powered_by)
    if server_header:
        detected.add(server_header)

    return sorted(detected)

