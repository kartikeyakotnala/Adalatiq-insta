"""Render an AdalatIQ carousel post (post.json) into 1080x1350 JPEG slides.

Usage:
  python3 scripts/render.py queue/<folder>            # renders <folder>/post.json into that folder
  python3 scripts/render.py queue/<folder> another/   # several at once

Each folder gets slide-01.jpg ... slide-NN.jpg and caption.txt.
Instagram's API accepts JPEG only and at most 10 slides per carousel.
"""
import html, json, shutil, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FONTS = (ROOT / "fonts").as_uri()

UI = {
    "en": {"swipe": "Swipe for the answer", "sources": "Sources",
           "disclaimer": "AI-assisted, for general awareness only. This is not legal advice. For your situation, speak to a lawyer.",
           "cta": "Stuck with a legal problem?", "cta2": "Ask AdalatIQ free", "font": "Inter"},
    "hi": {"swipe": "जवाब के लिए स्वाइप करें", "sources": "स्रोत",
           "disclaimer": "यह पोस्ट AI की मदद से बनी है और सिर्फ़ जागरूकता के लिए है। यह क़ानूनी सलाह नहीं है। अपने मामले के लिए किसी वकील से बात करें।",
           "cta": "क़ानूनी परेशानी है?", "cta2": "AdalatIQ से मुफ़्त पूछें", "font": "NotoDeva"},
    "mr": {"swipe": "उत्तरासाठी स्वाइप करा", "sources": "स्रोत",
           "disclaimer": "ही पोस्ट AI च्या मदतीने तयार केली आहे आणि फक्त सर्वसाधारण जागरूकतेसाठी आहे. हा कायदेशीर सल्ला नाही. तुमच्या परिस्थितीसाठी वकिलाशी बोला.",
           "cta": "कायदेशीर अडचण आहे?", "cta2": "AdalatIQ ला मोफत विचारा", "font": "NotoDeva"},
    "ta": {"swipe": "பதிலுக்கு ஸ்வைப் செய்யவும்", "sources": "ஆதாரங்கள்",
           "disclaimer": "இந்தப் பதிவு AI உதவியுடன் உருவாக்கப்பட்டது, பொது விழிப்புணர்வுக்காக மட்டுமே. இது சட்ட ஆலோசனை அல்ல. உங்கள் சூழ்நிலைக்கு ஒரு வழக்கறிஞரை அணுகவும்.",
           "cta": "சட்டப் பிரச்சனையா?", "cta2": "AdalatIQ-இடம் இலவசமாகக் கேளுங்கள்", "font": "NotoTamil"},
    "te": {"swipe": "సమాధానం కోసం స్వైప్ చేయండి", "sources": "మూలాలు",
           "disclaimer": "ఈ పోస్ట్ AI సహాయంతో రూపొందించబడింది, సాధారణ అవగాహన కోసం మాత్రమే. ఇది న్యాయ సలహా కాదు. మీ పరిస్థితి కోసం న్యాయవాదిని సంప్రదించండి.",
           "cta": "న్యాయపరమైన సమస్య ఉందా?", "cta2": "AdalatIQని ఉచితంగా అడగండి", "font": "NotoTelugu"},
    "kn": {"swipe": "ಉತ್ತರಕ್ಕಾಗಿ ಸ್ವೈಪ್ ಮಾಡಿ", "sources": "ಮೂಲಗಳು",
           "disclaimer": "ಈ ಪೋಸ್ಟ್ AI ನೆರವಿನಿಂದ ಸಿದ್ಧಪಡಿಸಲಾಗಿದೆ, ಸಾಮಾನ್ಯ ಅರಿವಿಗಾಗಿ ಮಾತ್ರ. ಇದು ಕಾನೂನು ಸಲಹೆಯಲ್ಲ. ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿಗಾಗಿ ವಕೀಲರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
           "cta": "ಕಾನೂನು ಸಮಸ್ಯೆಯೇ?", "cta2": "AdalatIQ ಅನ್ನು ಉಚಿತವಾಗಿ ಕೇಳಿ", "font": "NotoKannada"},
}

LOGO = """<svg viewBox="0 0 32 32" width="44" height="44" aria-hidden="true"><g fill="none" stroke="#161616" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M16 5v22M9 27h14M6 9h20"/><path d="M6 9l-3.5 8h7z" fill="#E8523A" stroke="#E8523A"/><path d="M26 9l-3.5 8h7z" fill="#E8523A" stroke="#E8523A"/></g></svg>"""
LOGO_W = LOGO.replace("#161616", "#FBF7F2")


def face(fam, file, weight):
    return f"@font-face{{font-family:{fam};src:url({FONTS}/{file});font-weight:{weight}}}\n"


FACES = "".join(face("Inter", f"Inter-{n}.otf", w) for n, w in
                [("Medium", 500), ("Bold", 700), ("ExtraBold", 800), ("Black", 900)])
for fam, slug in [("NotoDeva", "devanagari"), ("NotoTamil", "tamil"), ("NotoTelugu", "telugu"), ("NotoKannada", "kannada")]:
    for w, ws in [(500, "500"), (700, "700"), (800, "800 900")]:
        FACES += face(fam, f"noto-sans-{slug}-{slug}-{w}-normal.woff2", ws)

CSS = FACES + """
:root{--paper:#FBF7F2;--ink:#161616;--soft:#4a4540;--muted:#8a8178;--coral:#E8523A;--coral-soft:#FBE3DD;--line:#E9E0D5}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px}
body{background:var(--paper);color:var(--ink);font-family:var(--f),Inter,sans-serif;-webkit-font-smoothing:antialiased}
.s{position:relative;width:1080px;height:1350px;padding:84px 92px 92px;display:flex;flex-direction:column}
.top{display:flex;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center;gap:14px;font-family:Inter;font-weight:800;font-size:34px;letter-spacing:-.5px}
.brand b{color:var(--coral);font-weight:800}
.count{font-family:Inter;font-weight:700;font-size:26px;color:var(--muted);letter-spacing:1px}
.fit{flex:1;display:flex;flex-direction:column;justify-content:center;overflow:hidden}
.q{font-family:Inter;font-weight:900;font-size:150px;line-height:1;color:var(--coral);margin-bottom:28px}
.hook{font-weight:800;font-size:92px;line-height:1.12;letter-spacing:-2px}
.hookq{font-weight:800;font-size:92px;line-height:1.12;letter-spacing:-2px;color:var(--coral);margin-top:26px}
.swipe{font-weight:700;font-size:30px;color:var(--ink);display:flex;align-items:center;gap:14px}
.swipe span{display:inline-block;width:64px;height:4px;background:var(--coral);position:relative}
.swipe span:after{content:"";position:absolute;right:-2px;top:-8px;border:10px solid transparent;border-left:14px solid var(--coral);border-right:0}
.num{font-family:Inter;font-weight:900;font-size:40px;color:var(--coral);margin-bottom:30px;letter-spacing:1px}
.title{font-weight:800;font-size:78px;line-height:1.14;letter-spacing:-1.5px;margin-bottom:40px}
.body{font-weight:500;font-size:42px;line-height:1.45;color:var(--soft)}
ul{list-style:none}
li{font-weight:500;font-size:40px;line-height:1.38;color:var(--soft);padding:20px 0 20px 50px;border-top:2px solid var(--line);position:relative}
li:last-child{border-bottom:2px solid var(--line)}
li:before{content:"";position:absolute;left:4px;top:36px;width:18px;height:18px;border-radius:50%;background:var(--coral)}
.ref{align-self:flex-start;font-family:Inter,var(--f);font-weight:700;font-size:26px;color:var(--coral);background:var(--coral-soft);padding:14px 22px;border-radius:999px}
.end{background:var(--ink);color:var(--paper)}
.end .count{color:#8f877e}
.end h3{font-weight:700;font-size:30px;letter-spacing:2px;text-transform:uppercase;color:var(--coral);margin-bottom:22px}
.end .src{font-weight:500;font-size:34px;line-height:1.4;margin-bottom:12px}
.end .disc{font-weight:500;font-size:30px;line-height:1.5;color:#bdb4aa;border-top:2px solid #333;padding-top:40px;margin-top:40px}
.cta{background:var(--coral);color:#fff;border-radius:28px;padding:44px 48px}
.cta p{font-weight:500;font-size:34px;margin-bottom:8px;opacity:.92}
.cta strong{display:block;font-weight:800;font-size:56px;letter-spacing:-1px;line-height:1.2}
.cta em{font-style:normal;font-family:Inter;font-weight:800;font-size:40px;display:block;margin-top:14px}
"""

FIT_JS = """
for (const el of document.querySelectorAll('.fit, .cta')) {
  let guard = 0;
  while (el.scrollHeight > el.clientHeight + 1 && guard++ < 60) {
    for (const t of el.querySelectorAll('.hook,.hookq,.title,.body,li,.src,.q,.disc,strong')) {
      t.style.fontSize = (parseFloat(getComputedStyle(t).fontSize) * 0.96) + 'px';
    }
  }
}
"""

e = html.escape


def validate(spec):
    for k in ("id", "lang", "hook", "hook_q", "slides", "sources", "caption"):
        if k not in spec:
            raise ValueError(f"post.json missing '{k}'")
    if spec["lang"] not in UI:
        raise ValueError(f"unknown lang {spec['lang']}")
    n = len(spec["slides"]) + 2
    if not 3 <= n <= 10:
        raise ValueError(f"carousel would have {n} slides; Instagram allows 2-10 (keep 1-8 answer slides)")
    for s in spec["slides"]:
        if not s.get("ref"):
            raise ValueError(f"slide '{s.get('title')}' has no legal reference")
    if "adalatiq.com" not in spec["caption"]:
        raise ValueError("caption must link to adalatiq.com")
    if len(spec["caption"]) > 2200:
        raise ValueError("caption longer than Instagram's 2,200 characters")


def page(inner, lang, extra_cls=""):
    return (f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><style>{CSS}</style>"
            f"</head><body style='--f:{UI[lang]['font']}'><div class='s {extra_cls}'>{inner}</div></body></html>")


def top(i, n, dark=False):
    return (f"<div class='top'><div class='brand'>{LOGO_W if dark else LOGO}<span>Adalat<b>IQ</b></span></div>"
            f"<div class='count'>{i}/{n}</div></div>")


def build(spec):
    lang, ui, slides = spec["lang"], UI[spec["lang"]], spec["slides"]
    n = len(slides) + 2
    pages = [page(
        top(1, n) +
        f"<div class='fit'><div class='q'>Q.</div><div class='hook'>{e(spec['hook'])}</div>"
        f"<div class='hookq'>{e(spec['hook_q'])}</div></div>"
        f"<div class='swipe'>{e(ui['swipe'])} <span></span></div>", lang)]
    for k, s in enumerate(slides, start=2):
        content = f"<div class='num'>{k-1:02d}</div><div class='title'>{e(s['title'])}</div>"
        if "body" in s:
            content += f"<div class='body'>{e(s['body'])}</div>"
        if "list" in s:
            content += "<ul>" + "".join(f"<li>{e(x)}</li>" for x in s["list"]) + "</ul>"
        pages.append(page(top(k, n) + f"<div class='fit'>{content}</div><div class='ref'>{e(s['ref'])}</div>", lang))
    srcs = "".join(f"<div class='src'>{e(x)}</div>" for x in spec["sources"])
    pages.append(page(
        top(n, n, dark=True) +
        f"<div class='fit'><h3>{e(ui['sources'])}</h3>{srcs}<div class='disc'>{e(ui['disclaimer'])}</div></div>"
        f"<div class='cta'><p>{e(ui['cta'])}</p><strong>{e(ui['cta2'])}</strong><em>adalatiq.com →</em></div>",
        lang, "end"))
    return pages


def chrome_path():
    for p in ("/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if Path(p).exists():
            return p
    return None


def render(folders):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome_path(), args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        tmp = Path(tempfile.mkdtemp())
        for folder in map(Path, folders):
            spec = json.loads((folder / "post.json").read_text(encoding="utf-8"))
            validate(spec)
            for old in folder.glob("slide-*.jpg"):
                old.unlink()
            for i, h in enumerate(build(spec), start=1):
                f = tmp / f"s{i}.html"
                f.write_text(h, encoding="utf-8")
                pg.goto(f.as_uri())
                pg.evaluate("document.fonts.ready")
                pg.evaluate(FIT_JS)
                pg.screenshot(path=str(folder / f"slide-{i:02d}.jpg"), type="jpeg", quality=92)
            (folder / "caption.txt").write_text(spec["caption"], encoding="utf-8")
            print("rendered", folder)
        shutil.rmtree(tmp)
        b.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    render(sys.argv[1:])
