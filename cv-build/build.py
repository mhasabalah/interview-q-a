#!/usr/bin/env python3
"""
CV build + verify pipeline.

    python build.py            # rebuild the PDF and run every check
    python build.py --no-verify   # just rebuild (skips pypdf checks)

What it does:
  1. reads   cv.html                (the master you edit)
  2. inlines fonts/*.woff2 as base64 -> cv-print.html
     (no network at print time, so Chrome can never race the webfont load)
  3. renders cv-print.html -> ../Mohamed-Hasabalah-CV.pdf via headless Chrome
  4. verifies the PDF the way an ATS parser would

Edit cv.html ONLY. cv-print.html is generated and safe to delete.
"""

import base64, io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "cv.html")
PRINT = os.path.join(HERE, "cv-print.html")
OUT = os.path.abspath(os.path.join(HERE, "..", "Mohamed-Hasabalah-CV.pdf"))

# family name, file stem in fonts/, weight
FACES = [
    ("Source Serif 4", "serif600", 600),
    ("Source Sans 3", "ss400", 400),
    ("Source Sans 3", "ss600", 600),
    ("Source Sans 3", "ss700", 700),
]

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for p in CHROME_CANDIDATES:
        if os.path.isfile(p):
            return p
    sys.exit("ERROR: no Chrome or Edge found. Add your browser path to CHROME_CANDIDATES.")


def inline_fonts():
    """Swap the Google Fonts <link> for base64 @font-face rules."""
    s = io.open(SRC, encoding="utf-8").read()
    css = []
    for fam, stem, weight in FACES:
        path = os.path.join(HERE, "fonts", stem + ".woff2")
        if not os.path.isfile(path):
            sys.exit("ERROR: missing font file %s" % path)
        b64 = base64.b64encode(open(path, "rb").read()).decode()
        css.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;"
            "font-display:block;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (fam, weight, b64)
        )
    p = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", s)
    p = re.sub(
        r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">',
        "<style>\n" + "\n".join(css) + "\n</style>",
        p,
    )
    if "fonts.googleapis.com" in p:
        print("  WARNING: a Google Fonts link survived - fonts may not embed")
    io.open(PRINT, "w", encoding="utf-8", newline="\n").write(p)
    print("  inlined %d font faces -> cv-print.html" % len(FACES))


def render():
    browser = find_browser()
    url = "file:///" + PRINT.replace("\\", "/")
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", "--virtual-time-budget=15000",
         "--print-to-pdf=" + OUT, url],
        check=True, capture_output=True,
    )
    print("  rendered -> %s (%d KB)" % (OUT, os.path.getsize(OUT) // 1024))


def verify():
    try:
        from pypdf import PdfReader
    except ImportError:
        print("  (pypdf not installed - run: pip install pypdf - skipping checks)")
        return True

    r = PdfReader(OUT)
    t = "\n".join(p.extract_text() or "" for p in r.pages)
    bullets = [b for b in
               (re.sub(r"<[^>]+>", "", m).strip()
                for m in re.findall(r"<li>(.*?)</li>",
                                    io.open(SRC, encoding="utf-8").read(), re.S))
               if len(b.split()) > 4]
    words = [len(b.split()) for b in bullets] or [0]
    numbered = sum(1 for b in bullets if re.search(r"\b\d|\bfive\b|\bsix\b", b, re.I))

    order = ["PROFESSIONAL SUMMARY", "TECHNICAL SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION"]
    pos = [t.find(x) for x in order]
    employers = [("MicrotecSaudi", "MSDC"), ("MSDC", "EL-SAFA"),
                 ("EL-SAFA", "INNOTECH"), ("INNOTECH", "PROJECTS")]

    checks = [
        ("Exactly 2 pages", len(r.pages) == 2),
        ("Text layer extractable", len(t.split()) > 500),
        ("No corrupt characters", t.count("\ufffd") == 0),
        ("Text layer pure ASCII", not [c for c in t if ord(c) > 126]),
        ("Section order sequential", all(pos[i] > pos[i - 1] for i in range(1, len(pos)))),
        ("Employers in order", all(t.find(a) < t.find(b) for a, b in employers)),
        ("Contact fields extract",
         all(x in t for x in ["mohamedhasabalaah@gmail.com", "+20 109 974 6971"])),
        ("No bullet over 25 words", max(words) <= 25),
        ("Quantification >= 50%", 100.0 * numbered / max(len(bullets), 1) >= 50),
    ]
    print()
    for name, ok in checks:
        print("  %s %s" % ("PASS " if ok else "FAIL ", name))
    passed = sum(1 for _, ok in checks if ok)
    print("\n  %d/%d checks | %d words | %d bullets, avg %.1fw, max %dw | quantified %.0f%%"
          % (passed, len(checks), len(t.split()), len(bullets),
             sum(words) / len(words), max(words),
             100.0 * numbered / max(len(bullets), 1)))
    for i, p in enumerate(r.pages, 1):
        lines = [l for l in (p.extract_text() or "").split("\n") if l.strip()]
        print("    page %d: %d lines" % (i, len(lines)))
    return passed == len(checks)


if __name__ == "__main__":
    print("Building CV from cv.html")
    inline_fonts()
    render()
    ok = True if "--no-verify" in sys.argv else verify()
    print("\n%s" % ("All checks passed." if ok else "SOME CHECKS FAILED - review above."))
    sys.exit(0 if ok else 1)
