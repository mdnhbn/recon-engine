# ReconEngine

একটা Google-এর মতো সার্চ বক্স দেখতে, কিন্তু কাজ করে Passive + Active Recon
& OSINT ওয়েব অ্যাপ হিসেবে — ইউজার লগইন, এডমিন প্যানেল, API key ম্যানেজমেন্ট,
রেট-লিমিট আর বিজ্ঞাপন স্লট সহ। লোকালে এবং Render-এর মতো হোস্টিংয়ে, দুই
জায়গাতেই চলার জন্য বানানো।

## ফিচার

**রিকন পাইপলাইন** (domain/URL দিলে একসাথে চলে):
1. Passive Recon & OSINT — Whois, DNS, crt.sh + certspotter + hackertarget
2. Active Subdomain Discovery — DNS brute force
3. Live Host Check — httpx-এর মতো
4. Tech Stack Identification — Wappalyzer-লাইট
5. (ঐচ্ছিক) Shodan + Censys — admin key বসালে অটো যোগ হয়

**ইউজার সিস্টেম:**
- Signup/Login (প্রথম যে সাইনআপ করে সে অটোমেটিক admin হয়)
- প্রতিটা ইউজারের নিজের স্ক্যান হিস্ট্রি (`/my-scans`)
- দৈনিক রেট-লিমিট (admin-এর জন্য আনলিমিটেড)

**এডমিন প্যানেল** (`/admin`):
- Dashboard — মোট ইউজার, মোট স্ক্যান, সাম্প্রতিক কার্যক্রম
- User management — admin বানানো/সরানো, ইউজার ব্লক/আনব্লক
- সব ইউজারের সব স্ক্যান হিস্ট্রি
- Settings — Shodan/Censys API key, দৈনিক রেট-লিমিট, বিজ্ঞাপন (AdSense) স্নিপেট

## লোকালি চালানো

```bash
git clone <তোমার-repo-url>
cd recon-tool

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env            # ইচ্ছেমতো SECRET_KEY বদলাও
python app.py
```
ব্রাউজারে যাও: **http://127.0.0.1:5000** — প্রথমে সাইনআপ করো (সেই ইউজার
অটোমেটিক admin হবে)।

## Render-এ ডিপ্লয় করা

1. কোড GitHub-এ push করো (নিচে দেখো)।
2. [render.com](https://render.com) এ গিয়ে **New → Blueprint** বেছে নাও এবং
   তোমার repo সিলেক্ট করো — `render.yaml` ফাইলটা দেখে Render নিজে থেকেই
   একটা **Web Service** আর একটা ফ্রি **PostgreSQL** ডাটাবেস বানিয়ে নেবে এবং
   `DATABASE_URL`/`SECRET_KEY` auto-সেট করে দেবে।
   - অথবা ম্যানুয়ালি: **New → Web Service** → repo সিলেক্ট করো →
     Build Command: `pip install -r requirements.txt`,
     Start Command: `gunicorn app:app` → একটা free Postgres ডাটাবেস যোগ করো
     এবং তার Internal Connection String-টা `DATABASE_URL` env var হিসেবে বসাও।
3. ডিপ্লয় হয়ে গেলে Render যে `.onrender.com` লিংক দেবে, সেখানে গিয়ে সাইনআপ
   করলেই তুমি admin হয়ে যাবে।

> **নোট:** SQLite দিয়ে Render-এ রাখা যাবে, কিন্তু Render-এর ফ্রি web service-এর
> filesystem ephemeral (রিডিপ্লয়/রিস্টার্টে ডেটা হারিয়ে যায়) — তাই
> প্রোডাকশনে Postgres ব্যবহার করাই ভালো, যেটা `render.yaml` অটো সেট করে দেয়।

## GitHub-এ পাবলিশ করার নিয়ম

```bash
cd recon-tool
git init
git add .
git commit -m "Initial commit: ReconEngine"
git branch -M main
git remote add origin https://github.com/<তোমার-ইউজারনেম>/recon-engine.git
git push -u origin main
```

## প্রজেক্ট স্ট্রাকচার

```
recon-tool/
├── app.py                 # App factory, blueprint wiring
├── config.py               # Env var থেকে কনফিগ
├── extensions.py           # db, login_manager
├── models.py                # User, ScanHistory, Settings
├── auth.py                 # signup/login/logout
├── admin.py                 # admin panel routes
├── main.py                   # search page + /api/recon
├── recon/
│   ├── whois_lookup.py
│   ├── dns_lookup.py
│   ├── subdomains.py        # passive + active discovery
│   ├── live_check.py
│   ├── techstack.py
│   ├── shodan_lookup.py
│   └── censys_lookup.py
├── templates/                # সব HTML (base, auth, admin/)
├── static/                   # style.css, script.js
├── requirements.txt
├── Procfile                  # Render/gunicorn
├── render.yaml                # Render blueprint (web + postgres)
└── .env.example
```

## পরে যোগ করা যেতে পারে

- gowitness-এর মতো স্ক্রিনশট (Playwright লাগবে)
- ইমেইল ভেরিফিকেশন / পাসওয়ার্ড রিসেট
- রেজাল্ট PDF/CSV এক্সপোর্ট
- প্রতি-ইউজার আলাদা rate limit override

