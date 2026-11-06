"""Explainer-style carousel renderer (paper texture, serif headlines, highlighter marks, document clippings).

Usage: python3 scripts/render_explainer.py queue/<folder> [...]
Same post.json as render.py, plus optional extras:
  - **double asterisks** around words in hook, hook_q, title or body draw a coral highlighter stroke behind them
  - a slide may have "timeline": [{"date": "20 Dec 2004", "text": "..."}, ...] instead of body/list
  - a slide may have "note": a short handwritten aside (e.g. "the key date!")
Writes slide-NN.jpg + caption.txt like render.py. The look is AdalatIQ's own: coral highlighter, Nyaya stickers.
"""
import html, json, re, shutil, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mascot")); sys.path.insert(0, str(ROOT / "scripts"))
import nyaya   # noqa: E402
import render  # noqa: E402  (validate, UI strings, fonts, heart icon)

FONTS = render.FONTS
E = html.escape
SERIF = {"en": "Fraunces", "hi": "NotoSerifDeva", "mr": "NotoSerifDeva"}
KICKER = {"en": "EXPLAINED", "hi": "आसान भाषा में", "mr": "सोप्या भाषेत"}
LAW = {"en": "THE LAW", "hi": "क़ानून", "mr": "कायदा"}
TAGLINE = {"en": "Legal Made Simple", "hi": "क़ानून, आसान भाषा में", "mr": "कायदा, सोप्या भाषेत"}
BREAK = {"en": "let's break it down →", "hi": "चलिए समझते हैं →", "mr": "चला समजून घेऊ →"}

EXTRA_FACES = "".join(
    f"@font-face{{font-family:{fam};src:url({FONTS}/{file});font-weight:{w}}}\n" for fam, file, w in [
        ("Fraunces", "fraunces-latin-600-normal.woff2", 600), ("Fraunces", "fraunces-latin-800-normal.woff2", 800),
        ("Fraunces", "fraunces-latin-900-normal.woff2", 900),
        ("Caveat", "caveat-latin-600-normal.woff2", 600), ("Caveat", "caveat-latin-700-normal.woff2", 700),
        ("NotoSerifDeva", "noto-serif-devanagari-devanagari-600-normal.woff2", 600),
        ("NotoSerifDeva", "noto-serif-devanagari-devanagari-700-normal.woff2", 700),
        ("NotoSerifDeva", "noto-serif-devanagari-devanagari-800-normal.woff2", "800 900")])

PAPER = ("url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='400'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/>"
         "<feColorMatrix values='0 0 0 0 .35  0 0 0 0 .28  0 0 0 0 .2  0 0 0 .09 0'/></filter>"
         "<rect width='400' height='400' filter='url(%23n)'/></svg>\")")

CSS = render.FACES + EXTRA_FACES + f"""
:root{{--paper:#F5EFE3;--ink:#171514;--soft:#45403a;--coral:#E8523A;--hl:rgba(232,82,58,.38);--line:#E2D8C8}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1080px;height:1350px}}
body{{background:var(--paper);background-image:{PAPER};color:var(--ink);font-family:var(--f),Inter,sans-serif;-webkit-font-smoothing:antialiased}}
.s{{position:relative;width:1080px;height:1350px;padding:80px 90px 128px;display:flex;flex-direction:column}}
.s:before{{content:"";position:absolute;inset:34px;border:2px solid rgba(23,21,20,.12);pointer-events:none}}
.top{{display:flex;align-items:center;justify-content:space-between;font-family:Inter;position:relative}}
.brand{{display:flex;align-items:center;gap:12px;font-weight:800;font-size:32px}}
.brand b{{color:var(--coral)}}
.kick{{font-family:Inter,var(--f);font-weight:800;font-size:22px;letter-spacing:4px;color:var(--coral);border:3px solid var(--coral);padding:6px 14px}}
.count{{font-weight:700;font-size:24px;color:#8a8178}}
.fit{{flex:1;display:flex;flex-direction:column;justify-content:center;overflow:hidden;position:relative}}
.serif{{font-family:var(--serif),var(--f),serif}}
.hl{{background:linear-gradient(transparent 52%,var(--hl) 52%,var(--hl) 92%,transparent 92%);padding:0 6px;margin:0 -6px;
     border-radius:3px;-webkit-box-decoration-break:clone;box-decoration-break:clone}}
.hook{{font-weight:900;font-size:96px;line-height:1.08;letter-spacing:-1.5px}}
.hookq{{font-weight:900;font-size:96px;line-height:1.08;color:var(--coral);margin-top:28px;font-style:italic}}
.brk{{font-family:Caveat,var(--f);font-weight:700;font-size:54px;color:var(--coral);transform:rotate(-3deg);margin-top:40px}}
.big{{font-family:Fraunces;font-weight:900;font-size:190px;line-height:.8;color:transparent;-webkit-text-stroke:4px var(--coral);margin-bottom:26px}}
.title{{font-weight:800;font-size:76px;line-height:1.12;letter-spacing:-1px;margin-bottom:34px}}
.body{{font-weight:500;font-size:41px;line-height:1.5;color:var(--soft)}}
ul{{list-style:none}}
li{{font-weight:500;font-size:39px;line-height:1.38;color:var(--soft);padding:18px 0 18px 54px;position:relative;border-top:2px dashed var(--line)}}
li:last-child{{border-bottom:2px dashed var(--line)}}
li:before{{content:"✓";position:absolute;left:0;top:14px;font-family:Caveat;font-weight:700;font-size:52px;color:var(--coral)}}
.tl{{position:relative;padding-left:70px;margin-top:6px}}
.tl:before{{content:"";position:absolute;left:22px;top:18px;bottom:18px;width:6px;background:var(--ink);border-radius:3px}}
.ev{{position:relative;margin-bottom:46px}}
.ev:before{{content:"";position:absolute;left:-62px;top:10px;width:30px;height:30px;border-radius:50%;background:var(--coral);border:6px solid var(--paper);box-shadow:0 0 0 3px var(--ink)}}
.ev .d{{font-family:var(--serif),serif;font-weight:900;font-size:56px;line-height:1.1}}
.ev .t{{font-weight:500;font-size:38px;line-height:1.42;color:var(--soft);margin-top:8px}}
.note{{font-family:Caveat,var(--f);font-weight:700;font-size:52px;color:var(--coral);transform:rotate(-4deg);margin-top:30px;display:flex;align-items:center;gap:12px}}
.clip{{align-self:flex-start;position:relative;background:#fff;padding:22px 30px 30px;transform:rotate(-1.6deg);
      box-shadow:0 6px 18px rgba(0,0,0,.12);clip-path:polygon(0 0,100% 0,100% 88%,96% 100%,92% 90%,88% 100%,84% 90%,80% 100%,76% 90%,72% 100%,68% 90%,64% 100%,60% 90%,56% 100%,52% 90%,48% 100%,44% 90%,40% 100%,36% 90%,32% 100%,28% 90%,24% 100%,20% 90%,16% 100%,12% 90%,8% 100%,4% 90%,0 100%)}}
.clip small{{display:block;font-family:Inter;font-weight:800;font-size:18px;letter-spacing:3px;color:#8a8178;margin-bottom:6px}}
.clip span{{font-family:Inter,var(--f);font-weight:800;font-size:28px;color:var(--ink)}}
.tape{{position:absolute;width:150px;height:40px;background:rgba(232,82,58,.25);top:-16px;left:40%;transform:rotate(3deg)}}
.sticker{{position:absolute;right:-26px;bottom:0;width:390px;height:500px;transform:scaleX(-1);
          filter:drop-shadow(0 0 0 #fff) drop-shadow(5px 0 0 #fff) drop-shadow(-5px 0 0 #fff) drop-shadow(0 5px 0 #fff) drop-shadow(0 -5px 0 #fff) drop-shadow(0 8px 10px rgba(0,0,0,.18))}}
.sticker svg{{width:100%;height:100%}}
.hookpage .fit{{justify-content:flex-start;padding-top:90px;padding-bottom:300px}}
.hookpage .hook,.hookpage .hookq{{max-width:900px}}
.end h3{{font-family:Inter,var(--f);font-weight:800;font-size:24px;letter-spacing:4px;color:var(--coral);margin-bottom:18px}}
.end .src{{font-weight:600;font-size:31px;line-height:1.4;margin-bottom:10px}}
.end .disc{{font-weight:500;font-size:27px;line-height:1.5;color:#6d655c;margin-top:28px;padding-top:24px;border-top:2px dashed var(--line);max-width:860px}}
.end .clip{{max-width:880px}}
.follow{{display:flex;align-items:center;gap:20px;margin:0 0 26px;max-width:640px}}
.follow b{{display:block;font-family:var(--serif),serif;font-weight:900;font-size:46px;line-height:1.15}}
.follow span{{display:block;font-weight:500;font-size:27px;color:#6d655c;margin-top:4px}}
.cta{{background:var(--ink);color:#fff;padding:36px 42px;max-width:640px;transform:rotate(-1deg);box-shadow:8px 8px 0 var(--coral)}}
.cta p{{font-weight:500;font-size:30px;opacity:.85;margin-bottom:6px}}
.cta strong{{display:block;font-family:var(--serif),serif;font-weight:900;font-size:54px;line-height:1.15}}
.cta em{{font-style:normal;font-family:Inter;font-weight:800;font-size:36px;color:var(--coral);display:block;margin-top:10px}}
.end .sticker{{width:320px;height:410px}}
:lang(hi) .hl,:lang(mr) .hl{{background:linear-gradient(transparent 38%,var(--hl) 38%,var(--hl) 80%,transparent 80%)}}
:lang(hi) .kick,:lang(mr) .kick,:lang(hi) .clip small,:lang(mr) .clip small,:lang(hi) .end h3,:lang(mr) .end h3{{letter-spacing:0;font-size:24px}}
.foot{{position:absolute;left:90px;bottom:56px;display:flex;align-items:center;gap:12px;font-family:Inter,var(--f);font-size:22px;color:#6d655c}}
.foot svg{{width:30px;height:30px}}
.foot b{{font-weight:800;color:var(--ink)}} .foot b i{{font-style:normal;color:var(--coral)}}
.foot em{{font-style:normal;font-weight:700;color:var(--coral)}}
.foot .dot{{width:5px;height:5px;border-radius:50%;background:#b8ad9f}}
"""


def mark(text):
    """Escape, then turn **words** into highlighter spans."""
    return re.sub(r"\*\*(.+?)\*\*", r"<span class='hl'>\1</span>", E(text))


def plain(text):
    return text.replace("**", "")


def footer(lang):
    return (f"<div class='foot'>{render.LOGO}<b>Adalat<i>IQ</i></b><span class='dot'></span>"
            f"<span>{E(TAGLINE.get(lang, TAGLINE['en']))}</span><span class='dot'></span><em>adalatiq.com</em></div>")


def page(inner, lang, cls=""):
    f = render.UI[lang]["font"]
    return (f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><style>{CSS}</style></head>"
            f"<body style='--f:{f};--serif:{SERIF.get(lang, f)}'><div class='s {cls}'>{inner}{footer(lang)}</div></body></html>")


def top(i, n, lang):
    return (f"<div class='top'><div class='brand'>{render.LOGO}<span>Adalat<b>IQ</b></span></div>"
            f"<div class='kick'>{E(KICKER.get(lang, 'EXPLAINED'))}</div><div class='count'>{i}/{n}</div></div>")


def clip(ref, label="THE LAW"):
    return f"<div class='clip'><div class='tape'></div><small>{label}</small><span>{E(ref)}</span></div>"


def build(spec):
    lang, ui, slides = spec["lang"], render.UI[spec["lang"]], spec["slides"]
    n = len(slides) + 2
    pages = [page(top(1, n, lang) +
                  f"<div class='fit'><div class='hook serif'>{mark(spec['hook'])}</div>"
                  f"<div class='hookq serif'>{mark(spec['hook_q'])}</div>"
                  f"<div class='brk'>{E(BREAK.get(lang, BREAK['en']))}</div></div>"
                  f"<div class='sticker'>{nyaya.nyaya('think')}</div>", lang, "hookpage")]
    for k, s in enumerate(slides, start=1):
        c = f"<div class='big'>{k:02d}</div><div class='title serif'>{mark(s['title'])}</div>"
        if "body" in s:
            c += f"<div class='body'>{mark(s['body'])}</div>"
        if "list" in s:
            c += "<ul>" + "".join(f"<li>{mark(x)}</li>" for x in s["list"]) + "</ul>"
        if "timeline" in s:
            c += "<div class='tl'>" + "".join(f"<div class='ev'><div class='d'>{E(ev['date'])}</div>"
                                              f"<div class='t'>{mark(ev['text'])}</div></div>" for ev in s["timeline"]) + "</div>"
        if s.get("note"):
            c += f"<div class='note'>↳ {E(s['note'])}</div>"
        pages.append(page(top(k + 1, n, lang) + f"<div class='fit'>{c}</div>" + clip(s["ref"], LAW.get(lang, LAW["en"])), lang))
    srcs = "".join(f"<div class='src'>{E(x)}</div>" for x in spec["sources"])
    pages.append(page(
        top(n, n, lang) +
        f"<div class='fit'><div class='clip'><div class='tape'></div><h3>{E(ui['sources'])}</h3>{srcs}</div>"
        f"<div class='disc'>{E(ui['disclaimer'])}</div></div>"
        f"<div class='follow'>{render.HEART}<div><b>{E(ui['follow'])}</b><span>{E(ui['follow2'])}</span></div></div>"
        f"<div class='cta'><p>{E(ui['cta'])}</p><strong>{E(ui['cta2'])}</strong><em>adalatiq.com →</em></div>"
        f"<div class='sticker'>{nyaya.nyaya('wave')}</div>", lang, "end"))
    return pages


def render_folders(folders):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=render.chrome_path(), args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        tmp = Path(tempfile.mkdtemp())
        for folder in map(Path, folders):
            spec = json.loads((folder / "post.json").read_text(encoding="utf-8"))
            check = json.loads(json.dumps(spec))
            for s in check["slides"]:          # timeline slides have no body/list; validation only needs the ref
                s.setdefault("body", "")
            render.validate(check)
            for old in folder.glob("slide-*.jpg"):
                old.unlink()
            for i, h in enumerate(build(spec), start=1):
                f = tmp / f"s{i}.html"; f.write_text(h, encoding="utf-8")
                pg.goto(f.as_uri()); pg.evaluate("document.fonts.ready"); pg.evaluate(render.FIT_JS)
                pg.screenshot(path=str(folder / f"slide-{i:02d}.jpg"), type="jpeg", quality=92)
            (folder / "caption.txt").write_text(plain(spec["caption"]), encoding="utf-8")
            print("rendered (explainer)", folder)
        shutil.rmtree(tmp); b.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    render_folders(sys.argv[1:])
