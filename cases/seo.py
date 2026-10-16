"""Search essentials for every page: canonical URL, social tags, structured data, sitemap and robots.
Safe to run repeatedly; it replaces its own block each time."""
import glob, html, json, os, re, datetime

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site")
BASE = "https://reaustudio.com"
START, END = "<!-- seo -->", "<!-- /seo -->"

ORG = {
    "@type": "ProfessionalService",
    "@id": BASE + "/#org",
    "name": "REAU Studio",
    "legalName": "REAU Studio LTD",
    "url": BASE + "/",
    "logo": BASE + "/assets/favicon-512.png",
    "image": BASE + "/assets/og.png",
    "email": "hello@reaustudio.com",
    "foundingDate": "2023",
    "description": "A global consulting agency advising start-ups, agencies, professional services firms, investors and brand-led founders on business development, strategy and positioning, operations, creative direction, AI workflows and digital platforms.",
    "areaServed": "Worldwide",
    "knowsAbout": ["Business development", "Brand strategy", "Positioning", "Operations consulting",
                   "Creative direction", "Social media strategy", "AI workflows", "Website design", "App design"],
    "sameAs": ["https://instagram.com/reau.studio", "https://linkedin.com/in/reaustudio"],
}

HOME_TITLE = "REAU Studio | Business Advisory, Brand Strategy &amp; Operations Consultancy"


def url_for(path):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    if rel == "index.html":
        return BASE + "/"
    return BASE + "/" + rel


def meta(s, name):
    m = re.search(r'<meta name="%s" content="([^"]*)"' % name, s)
    return html.unescape(m.group(1)) if m else ""


def title(s):
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    return html.unescape(m.group(1)).strip() if m else "REAU Studio"


def block(path, s):
    url = url_for(path)
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    t, d = title(s), meta(s, "description")
    graph = [ORG, {"@type": "WebSite", "@id": BASE + "/#site", "url": BASE + "/", "name": "REAU Studio", "publisher": {"@id": BASE + "/#org"}}]
    kind = "website"
    if rel.startswith("work/"):
        kind = "article"
        graph.append({"@type": "Article", "headline": t.replace(" · REAU Studio", "") + " case study", "description": d,
                      "url": url, "mainEntityOfPage": url, "author": {"@id": BASE + "/#org"}, "publisher": {"@id": BASE + "/#org"},
                      "image": BASE + "/assets/og.png", "articleSection": "Case studies"})
    elif rel.startswith("journal/"):
        kind = "article"
        graph.append({"@type": "BlogPosting", "headline": t.replace(" · REAU Studio", ""), "description": d,
                      "url": url, "mainEntityOfPage": url, "author": {"@id": BASE + "/#org"}, "publisher": {"@id": BASE + "/#org"},
                      "image": BASE + "/assets/og.png"})
    if rel != "index.html":
        crumbs = [{"@type": "ListItem", "position": 1, "name": "REAU Studio", "item": BASE + "/"}]
        if rel.startswith("work/"):
            crumbs.append({"@type": "ListItem", "position": 2, "name": "Case studies", "item": BASE + "/#work"})
        if rel.startswith("journal/"):
            crumbs.append({"@type": "ListItem", "position": 2, "name": "Journal", "item": BASE + "/#journal"})
        crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": t.replace(" · REAU Studio", ""), "item": url})
        graph.append({"@type": "BreadcrumbList", "itemListElement": crumbs})
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
    e = lambda x: html.escape(x, quote=True)
    tags = [f'<link rel="canonical" href="{url}">']
    want = [("og:title", t), ("og:description", d), ("og:image", BASE + "/assets/og.png"), ("og:type", kind)]
    for k, v in want:
        if f'property="{k}"' not in s:
            tags.append(f'<meta property="{k}" content="{e(v)}">')
    if 'name="twitter:card"' not in s:
        tags.append('<meta name="twitter:card" content="summary_large_image">')
    tags += [f'<meta property="og:url" content="{url}">', '<meta property="og:site_name" content="REAU Studio">',
             '<meta property="og:locale" content="en_GB">',
             f'<script type="application/ld+json">{ld}</script>']
    return START + "\n" + "\n".join(tags) + "\n" + END


def run():
    pages = []
    for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        s = open(path, encoding="utf-8").read()
        s = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", s, flags=re.S)
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        if rel == "index.html":
            s = re.sub(r"<title>.*?</title>", f"<title>{HOME_TITLE}</title>", s, count=1, flags=re.S)
            # the home page keeps its own og tags; drop the relative og:image in favour of an absolute one
            s = s.replace('<meta property="og:image" content="/assets/og.png">', f'<meta property="og:image" content="{BASE}/assets/og.png">')
        s = s.replace("</head>", block(path, s) + "\n</head>", 1)
        open(path, "w", encoding="utf-8").write(s)
        pages.append((url_for(path), datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat(), rel))
    pri = lambda r: "1.0" if r == "index.html" else ("0.8" if r.startswith("work/") else "0.6")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, d, r in pages:
        sm.append(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod><priority>{pri(r)}</priority></url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")
    open(os.path.join(ROOT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    return [p[2] for p in pages]


if __name__ == "__main__":
    print("seo:", ", ".join(run()))
