"""Festival greeting post (single 1080x1350 image) in AdalatIQ's style, with Nyaya.

Usage: python3 scripts/render_greeting.py queue/<folder>
greeting.json: {"kind": "diwali", "kicker": "...", "title": "Happy **Diwali**", "message": "...", "signoff": "...", "caption": "..."}
Writes slide-01.jpg + caption.txt (a single-image post).
"""
import html, json, math, random, re, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mascot")); sys.path.insert(0, str(ROOT / "scripts"))
import nyaya             # noqa: E402
import render            # noqa: E402
import render_explainer  # noqa: E402

E = html.escape


def diya(x, y, s=1.0):
    """A clay lamp with a glowing flame, centred at (x, y)."""
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<ellipse cx="0" cy="-70" rx="70" ry="90" fill="url(#glow)"/>'
            f'<path d="M-62 0 Q0 58 62 0 Q40 -12 0 -10 Q-40 -12 -62 0Z" fill="#B5542E"/>'
            f'<path d="M-62 0 Q0 22 62 0" stroke="#8C3B1E" stroke-width="5" fill="none"/>'
            f'<path d="M-40 14 Q0 40 40 14" stroke="#F2B544" stroke-width="5" fill="none" stroke-dasharray="2 12" stroke-linecap="round"/>'
            f'<path d="M0 -12 Q-14 -40 0 -78 Q14 -40 0 -12Z" fill="#FFB547"/>'
            f'<path d="M0 -16 Q-7 -36 0 -58 Q7 -36 0 -16Z" fill="#FFF3C4"/></g>')


def rangoli(cx, cy, r):
    """Concentric petal mandala in coral, marigold and cream."""
    out = []
    rings = [(r, 16, "#E8523A", 0), (r * 0.78, 12, "#F2B544", 7.5), (r * 0.56, 10, "#FBF7F2", 0), (r * 0.36, 8, "#E8523A", 11)]
    for rad, n, col, rot in rings:
        for k in range(n):
            a = math.radians(rot + 360 * k / n)
            px, py = cx + rad * 0.62 * math.cos(a), cy + rad * 0.62 * math.sin(a)
            out.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{rad*0.36:.1f}" ry="{rad*0.14:.1f}" fill="{col}" opacity=".9" '
                       f'transform="rotate({math.degrees(a):.1f} {px:.1f} {py:.1f})"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r*0.16:.1f}" fill="#F2B544"/><circle cx="{cx}" cy="{cy}" r="{r*0.07:.1f}" fill="#E8523A"/>')
    for k in range(24):
        a = math.radians(360 * k / 24)
        out.append(f'<circle cx="{cx + r*1.05*math.cos(a):.1f}" cy="{cy + r*1.05*math.sin(a):.1f}" r="6" fill="#FBF7F2" opacity=".8"/>')
    return "".join(out)


def soop(x, y, s=1.0):
    """Bamboo winnowing basket (soop) with thekua, banana, coconut and a diya."""
    weave = "".join(f'<path d="M{-150+k*20} -6 Q{-150+k*20} 40 {-120+k*16} 70" stroke="#9A6A2E" stroke-width="3" fill="none" opacity=".6"/>' for k in range(16))
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<path d="M-170 -10 Q0 -40 170 -10 L120 70 Q0 95 -120 70Z" fill="#D9A55A"/>{weave}'
            f'<path d="M-170 -10 Q0 -40 170 -10" stroke="#8C5A22" stroke-width="10" fill="none" stroke-linecap="round"/>'
            f'<circle cx="-70" cy="-38" r="34" fill="#7A4A1E"/><path d="M-96 -46 q26 -14 52 0" stroke="#5A3412" stroke-width="5" fill="none"/>'
            f'<path d="M-10 -30 Q30 -110 90 -96 Q40 -80 20 -24Z" fill="#F2C94C" stroke="#C99A1E" stroke-width="4"/>'
            f'<ellipse cx="110" cy="-30" rx="34" ry="16" fill="#C9772E"/><ellipse cx="110" cy="-34" rx="22" ry="7" fill="#E8A55A"/>'
            f'<ellipse cx="-12" cy="-26" rx="26" ry="12" fill="#C9772E"/><path d="M-26 -28 h28" stroke="#E8A55A" stroke-width="3"/>'
            f'<ellipse cx="45" cy="-42" rx="16" ry="16" fill="#E8523A"/></g>')


def sugarcane(x, y, h, lean):
    joints = "".join(f'<rect x="-9" y="{-k*70}" width="18" height="5" fill="#2E1A22"/>' for k in range(1, int(h/70)))
    leaves = (f'<path d="M0 {-h} Q-90 {-h-60} -150 {-h+20} Q-70 {-h-30} 0 {-h+10}Z" fill="#3E7A3A"/>'
              f'<path d="M0 {-h} Q80 {-h-90} 140 {-h-10} Q60 {-h-50} 0 {-h+10}Z" fill="#4E8F45"/>'
              f'<path d="M0 {-h+40} Q-60 {-h-20} -110 {-h+90} Q-40 {-h+20} 0 {-h+50}Z" fill="#356B33"/>')
    return (f'<g transform="translate({x} {y}) rotate({lean})">'
            f'<rect x="-9" y="{-h}" width="18" height="{h}" rx="8" fill="#5B2E3C"/>{joints}{leaves}</g>')


def chhath_svg():
    rnd = random.Random(15)
    ripples = "".join(f'<path d="M{x} {y} q{w/2} -6 {w} 0" stroke="#FFB86B" stroke-width="{rnd.uniform(2,4):.1f}" fill="none" '
                      f'opacity="{rnd.uniform(.25,.7):.2f}" stroke-linecap="round"/>'
                      for x, y, w in [(rnd.randint(140, 520), rnd.randint(1010, 1180), rnd.randint(40, 160)) for _ in range(26)])
    reflect = "".join(f'<rect x="{330 - w/2:.0f}" y="{1000 + k*22}" width="{w:.0f}" height="5" rx="2.5" fill="#FFC861" opacity="{.45 - k*.05:.2f}"/>'
                      for k, w in enumerate([260, 220, 200, 150, 130, 90, 70, 40]))
    stars = "".join(f'<circle cx="{rnd.randint(0,1080)}" cy="{rnd.randint(40,420)}" r="{rnd.uniform(1.5,3.5):.1f}" fill="#FFE7C2" opacity="{rnd.uniform(.3,.8):.2f}"/>' for _ in range(40))
    floats = "".join(diya(x, y, s) for x, y, s in [(560, 1080, .45), (700, 1130, .4), (470, 1150, .5)])
    birds = "".join(f'<path d="M{x} {y} q12 -12 24 0 q12 -12 24 0" stroke="#2A1420" stroke-width="4" fill="none"/>' for x, y in [(560, 820), (620, 790), (600, 850)])
    return (f'<svg class="art" viewBox="0 0 1080 1350" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><radialGradient id="glow"><stop offset="0" stop-color="#FFC861" stop-opacity=".75"/>'
            f'<stop offset="1" stop-color="#FFC861" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="sunhalo"><stop offset="0" stop-color="#FFB547" stop-opacity=".8"/><stop offset=".5" stop-color="#E8523A" stop-opacity=".35"/>'
            f'<stop offset="1" stop-color="#E8523A" stop-opacity="0"/></radialGradient>'
            f'<linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE29A"/><stop offset="1" stop-color="#FF8A3D"/></linearGradient>'
            f'<linearGradient id="water" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5A2232"/><stop offset="1" stop-color="#1E1020"/></linearGradient>'
            f'<clipPath id="above"><rect x="0" y="0" width="1080" height="1000"/></clipPath></defs>'
            f'{stars}<circle cx="330" cy="1000" r="420" fill="url(#sunhalo)"/>'
            f'<circle cx="330" cy="1000" r="150" fill="url(#sun)" clip-path="url(#above)"/>{birds}'
            f'<path d="M0 985 Q200 965 420 980 T1080 972 L1080 1000 L0 1000Z" fill="#3A1A2A" opacity=".9"/>'
            f'<rect x="0" y="1000" width="1080" height="350" fill="url(#water)"/>{reflect}{ripples}{floats}'
            f'{sugarcane(62, 1240, 330, -4)}{sugarcane(108, 1248, 290, 5)}'
            f'{soop(270, 1170, .75)}</svg>')


def scene_svg():
    rnd = random.Random(8)
    bokeh = "".join(f'<circle cx="{rnd.randint(0,1080)}" cy="{rnd.randint(0,900)}" r="{rnd.randint(8,34)}" '
                    f'fill="{rnd.choice(["#F2B544","#E8523A","#FFD98A"])}" opacity="{rnd.uniform(.08,.28):.2f}" filter="url(#blur)"/>'
                    for _ in range(46))
    sparks = "".join(f'<path d="M{x} {y} l4 12 l12 4 l-12 4 l-4 12 l-4 -12 l-12 -4 l12 -4z" fill="#FFE7A8" opacity=".85"/>'
                     for x, y in [(1000, 190), (960, 640), (640, 930), (70, 960), (720, 230)])
    diyas = "".join(diya(x, 1175, s) for x, s in [(130, .8), (300, 1.0), (470, .85)])
    return (f'<svg class="art" viewBox="0 0 1080 1350" xmlns="http://www.w3.org/2000/svg">'
            f'<defs><radialGradient id="glow"><stop offset="0" stop-color="#FFC861" stop-opacity=".75"/>'
            f'<stop offset="1" stop-color="#FFC861" stop-opacity="0"/></radialGradient>'
            f'<filter id="blur"><feGaussianBlur stdDeviation="6"/></filter></defs>'
            f'{bokeh}<g opacity=".95">{rangoli(840, 1120, 250)}</g>{sparks}{diyas}</svg>')


CSS = render.FACES + render_explainer.EXTRA_FACES + f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1080px;height:1350px}}
body{{background:radial-gradient(ellipse at 50% 30%,#3a1d17 0%,#1d1210 55%,#120b0a 100%);color:#FBF2E4;font-family:Inter,sans-serif;overflow:hidden}}
.tex{{position:absolute;inset:0;background-image:{render_explainer.PAPER};opacity:.5;mix-blend-mode:overlay}}
.art{{position:absolute;inset:0;width:1080px;height:1350px}}
.frame{{position:absolute;inset:34px;border:2px solid rgba(242,181,68,.35)}}
.top{{position:absolute;left:90px;right:90px;top:80px;display:flex;align-items:center;justify-content:space-between}}
.brand{{display:flex;align-items:center;gap:12px;font-weight:800;font-size:32px;color:#FBF2E4}} .brand b{{color:#E8523A}}
.brand svg g{{stroke:#FBF2E4}}
.kick{{font-weight:800;font-size:22px;letter-spacing:4px;color:#F2B544;border:3px solid #F2B544;padding:6px 14px}}
.txt{{position:absolute;left:90px;right:90px;top:200px}}
h1{{font-family:Fraunces;font-weight:900;font-size:150px;line-height:.95;letter-spacing:-2px}}
h1 .hl{{color:#F2B544;font-style:italic}}
.msg{{font-family:Fraunces;font-weight:600;font-size:46px;line-height:1.3;margin-top:44px;max-width:720px;color:#F6E7D2}}
.sign{{font-family:Caveat;font-weight:700;font-size:58px;color:#F2B544;margin-top:34px;transform:rotate(-3deg);display:inline-block}}
.ny{{position:absolute;right:-30px;bottom:150px;width:430px;height:553px;transform:scaleX(-1);
     filter:drop-shadow(5px 0 0 #FBF2E4) drop-shadow(-5px 0 0 #FBF2E4) drop-shadow(0 5px 0 #FBF2E4) drop-shadow(0 -5px 0 #FBF2E4) drop-shadow(0 0 30px rgba(255,181,71,.45))}}
.ny svg{{width:100%;height:100%}}
.foot{{position:absolute;left:90px;bottom:54px;display:flex;align-items:center;gap:12px;font-size:22px;color:#cdb9a3}}
.foot b{{color:#FBF2E4;font-weight:800}} .foot b i{{font-style:normal;color:#E8523A}} .foot em{{font-style:normal;font-weight:700;color:#F2B544}}
"""


CHHATH_CSS = """body{background:linear-gradient(180deg,#1A0F24 0%,#3B1830 38%,#8A3330 62%,#D9623A 74%,#2A1420 74.2%)}
h1{font-size:132px} .msg{max-width:640px}"""


def build(g):
    title = re.sub(r"\*\*(.+?)\*\*", r"<span class='hl'>\1</span>", E(g["title"]))
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{CHHATH_CSS if g.get('kind') == 'chhath' else ''}</style></head><body>"
            f"<div class='tex'></div>{chhath_svg() if g.get('kind') == 'chhath' else scene_svg()}<div class='frame'></div>"
            f"<div class='top'><div class='brand'>{render.LOGO}<span>Adalat<b>IQ</b></span></div>"
            f"<div class='kick'>{E(g.get('kicker', ''))}</div></div>"
            f"<div class='txt'><h1>{title}</h1><div class='msg'>{E(g['message'])}</div>"
            f"<div class='sign'>{E(g['signoff'])}</div></div>"
            f"<div class='ny'>{nyaya.nyaya('wave')}</div>"
            f"<div class='foot'><b>Adalat<i>IQ</i></b> · Legal Made Simple · <em>adalatiq.com</em></div></body></html>")


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    g = json.loads((folder / "greeting.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp()) / "g.html"; tmp.write_text(build(g), encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=render.chrome_path(), args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(tmp.as_uri()); pg.evaluate("document.fonts.ready")
        pg.screenshot(path=str(folder / "slide-01.jpg"), type="jpeg", quality=93); b.close()
    (folder / "caption.txt").write_text(g["caption"], encoding="utf-8")
    print("rendered greeting", folder)
