"""Explainer-style animated Reel with voiceover (9:16, 1080x1920).

Usage: python3 scripts/explainer_reel.py <folder-with-reel.json> [--out reel.mp4]

reel.json:
{
  "lang": "en",
  "scenes": [
    {"kind": "hook", "kicker": "THE QUESTION", "head": "Can ... **joint family property?**", "say": "...", "pose": "think"},
    {"kind": "text", "kicker": "THE RULE", "head": "Daughters are **coparceners by birth.**", "sub": "...", "ref": "...", "say": "..."},
    {"kind": "timeline", "kicker": "THE CATCH", "head": "...", "events": [{"date": "...", "text": "..."}], "ref": "...", "say": "..."},
    {"kind": "end", "head": "Know your **rights.**", "say": "...", "pose": "wave"}
  ]
}
Each scene lasts as long as its narration line (+ a short beat). Narration only covers the crux; the
on-screen text carries the detail. Voice: Piper "lessac" (voice A), music: original track from compose_music.py.
"""
import argparse, html, json, math, re, shutil, subprocess, sys, tempfile, urllib.request, wave
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mascot")); sys.path.insert(0, str(ROOT / "scripts"))
import nyaya             # noqa: E402
import render            # noqa: E402
import render_explainer  # noqa: E402

FPS, BEAT, LEAD = 30, 0.55, 0.35
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz"
VOICE_DIR = Path.home() / ".cache" / "adalatiq" / "voice-en-us-lessac-medium"
E = html.escape


def voice_model():
    onnx = VOICE_DIR / "en-us-lessac-medium.onnx"
    if not onnx.exists():
        VOICE_DIR.mkdir(parents=True, exist_ok=True)
        tgz = VOICE_DIR / "voice.tar.gz"
        urllib.request.urlretrieve(VOICE_URL, tgz)
        subprocess.run(["tar", "-xzf", str(tgz), "-C", str(VOICE_DIR)], check=True)
        tgz.unlink()
    return onnx


def narrate(scenes, tmp):
    from piper import PiperVoice, SynthesisConfig
    v = PiperVoice.load(str(voice_model()))
    cfg = SynthesisConfig(length_scale=1.0, noise_scale=0.667, noise_w_scale=0.8)
    durs = []
    for i, sc in enumerate(scenes):
        p = tmp / f"line{i}.wav"
        with wave.open(str(p), "wb") as w:
            v.synthesize_wav(sc["say"], w, syn_config=cfg)
        with wave.open(str(p)) as w:
            durs.append(w.getnframes() / w.getframerate())
    return durs


def mark(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<span class='hl'>\1</span>", E(t))


def words(t):
    """Wrap each word for the pop-in, keeping highlighter spans intact."""
    out, parts = [], re.split(r"(\*\*.+?\*\*)", t)
    for part in parts:
        if part.startswith("**"):
            inner = " ".join(f"<span class='w'>{E(x)}</span>" for x in part[2:-2].split())
            out.append(f"<span class='hl'>{inner}</span>")
        else:
            out.extend(f"<span class='w'>{E(x)}</span>" for x in part.split())
    return " ".join(out)


CSS = render.FACES + render_explainer.EXTRA_FACES + f"""
:root{{--paper:#F5EFE3;--ink:#171514;--soft:#45403a;--coral:#E8523A;--hl:rgba(232,82,58,.40);--line:#E2D8C8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1920px;overflow:hidden;background:var(--paper);color:var(--ink);font-family:Inter,sans-serif}}
#bg{{position:absolute;inset:-40px;background-image:{render_explainer.PAPER}}}
.frame{{position:absolute;inset:40px;border:2px solid rgba(23,21,20,.12)}}
.top{{position:absolute;left:84px;right:84px;top:96px;display:flex;align-items:center;justify-content:space-between}}
.brand{{display:flex;align-items:center;gap:14px;font-weight:800;font-size:40px}} .brand b{{color:var(--coral)}}
.dots{{display:flex;gap:10px}} .dots i{{width:16px;height:16px;border-radius:50%;border:3px solid var(--ink);display:block}}
.dots i.on{{background:var(--coral);border-color:var(--coral)}}
.sc{{position:absolute;left:84px;right:84px;top:260px;opacity:0}}
.kick{{display:inline-block;font-weight:800;font-size:28px;letter-spacing:5px;color:var(--coral);border:4px solid var(--coral);padding:8px 18px;margin-bottom:46px}}
.q{{font-family:Fraunces;font-weight:900;font-size:200px;line-height:.8;color:var(--coral);margin-bottom:30px}}
.head{{font-family:Fraunces,serif;font-weight:900;font-size:104px;line-height:1.08;letter-spacing:-1.5px}}
.hook .head{{font-size:112px}}
.w{{display:inline-block}}
.hl{{background-image:linear-gradient(transparent 55%,var(--hl) 55%,var(--hl) 92%,transparent 92%);background-repeat:no-repeat;
     background-size:0% 100%;padding:0 6px;margin:0 -6px;-webkit-box-decoration-break:clone;box-decoration-break:clone}}
.sub{{font-weight:500;font-size:48px;line-height:1.42;color:var(--soft);margin-top:44px;max-width:880px}}
.clip{{display:inline-block;position:relative;background:#fff;padding:26px 34px 36px;margin-top:60px;transform:rotate(-1.6deg);
      box-shadow:0 8px 22px rgba(0,0,0,.12);clip-path:polygon(0 0,100% 0,100% 86%,96% 100%,92% 88%,88% 100%,84% 88%,80% 100%,76% 88%,72% 100%,68% 88%,64% 100%,60% 88%,56% 100%,52% 88%,48% 100%,44% 88%,40% 100%,36% 88%,32% 100%,28% 88%,24% 100%,20% 88%,16% 100%,12% 88%,8% 100%,4% 88%,0 100%)}}
.clip small{{display:block;font-weight:800;font-size:22px;letter-spacing:4px;color:#8a8178;margin-bottom:8px}}
.clip span{{font-weight:800;font-size:34px}}
.tape{{position:absolute;width:170px;height:44px;background:rgba(232,82,58,.28);top:-18px;left:40%;transform:rotate(3deg)}}
.tl{{position:relative;margin-top:56px;padding-left:84px}}
.tl .bar{{position:absolute;left:26px;top:20px;width:8px;height:0;background:var(--ink);border-radius:4px}}
.ev{{position:relative;margin-bottom:56px;opacity:0}}
.ev:before{{content:"";position:absolute;left:-74px;top:12px;width:36px;height:36px;border-radius:50%;background:var(--coral);border:7px solid var(--paper);box-shadow:0 0 0 4px var(--ink)}}
.ev .d{{font-family:Fraunces;font-weight:900;font-size:70px;line-height:1.05}}
.ev .t{{font-weight:500;font-size:44px;line-height:1.4;color:var(--soft);margin-top:10px;max-width:820px}}
.end .follow{{display:flex;align-items:center;gap:24px;margin-top:60px;max-width:680px}}
.end .follow svg{{width:90px;height:90px;flex:none}}
.end .follow b{{display:block;font-family:Fraunces;font-weight:900;font-size:58px;line-height:1.1}}
.end .follow span{{display:block;font-size:34px;color:#6d655c;margin-top:6px}}
.end .cta{{display:inline-block;margin-top:60px;background:var(--ink);color:#fff;padding:40px 46px;transform:rotate(-1deg);box-shadow:10px 10px 0 var(--coral)}}
.end .cta p{{font-size:34px;opacity:.85}} .end .cta strong{{display:block;font-family:Fraunces;font-weight:900;font-size:62px}}
.end .cta em{{font-style:normal;font-weight:800;font-size:42px;color:var(--coral);display:block;margin-top:8px}}
#ny{{position:absolute;right:-40px;bottom:-30px;width:600px;height:770px;transform-origin:bottom center}}
.pose{{position:absolute;inset:0;opacity:0;transform:scaleX(-1);
      filter:drop-shadow(5px 0 0 #fff) drop-shadow(-5px 0 0 #fff) drop-shadow(0 5px 0 #fff) drop-shadow(0 -5px 0 #fff) drop-shadow(0 10px 12px rgba(0,0,0,.18))}}
.pose svg{{width:100%;height:100%}}
.arm{{transform-box:view-box;transform-origin:404px 478px}} .eyes{{transform-box:fill-box;transform-origin:center}}
.foot{{position:absolute;left:84px;top:1830px;display:flex;align-items:center;gap:12px;font-size:26px;color:#6d655c}}
.foot b{{color:var(--ink);font-weight:800}} .foot b i{{font-style:normal;color:var(--coral)}} .foot em{{font-style:normal;font-weight:700;color:var(--coral)}}
"""


def scene_html(i, sc):
    kind = sc.get("kind", "text")
    h = f"<section class='sc {kind}' id='s{i}'>"
    if sc.get("kicker"):
        h += f"<div class='kick'>{E(sc['kicker'])}</div>"
    if kind == "hook":
        h += "<div class='q'>Q.</div>"
    h += f"<div class='head'>{words(sc['head'])}</div>"
    if sc.get("sub"):
        h += f"<div class='sub'>{mark(sc['sub'])}</div>"
    if kind == "timeline":
        h += "<div class='tl'><div class='bar'></div>" + "".join(
            f"<div class='ev'><div class='d'>{E(ev['date'])}</div><div class='t'>{mark(ev['text'])}</div></div>"
            for ev in sc["events"]) + "</div>"
    if sc.get("ref"):
        h += f"<div><div class='clip'><div class='tape'></div><small>THE LAW</small><span>{E(sc['ref'])}</span></div></div>"
    if kind == "end":
        ui = render.UI["en"]
        h += (f"<div class='follow'>{render.HEART}<div><b>{E(ui['follow'])}</b><span>{E(ui['follow2'])}</span></div></div>"
              f"<div class='cta'><p>{E(ui['cta'])}</p><strong>{E(ui['cta2'])}</strong><em>adalatiq.com →</em></div>")
    return h + "</section>"


def page_html(scenes):
    dots = "".join("<i></i>" for _ in scenes)
    poses = "".join(f"<div class='pose' id='p-{p}'>{nyaya.nyaya(p)}</div>" for p in ("think", "point", "confident", "wave"))
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>"
            f"<div id='bg'></div><div class='frame'></div>"
            f"<div class='top'><div class='brand'>{render.LOGO}<span>Adalat<b>IQ</b></span></div><div class='dots'>{dots}</div></div>"
            + "".join(scene_html(i, s) for i, s in enumerate(scenes)) +
            f"<div id='ny'>{poses}</div>"
            f"<div class='foot'><b>Adalat<i>IQ</i></b> · Legal Made Simple · <em>adalatiq.com</em></div></body></html>")


ANIM = r"""
(() => {
  const C = (x, a=0, b=1) => Math.max(a, Math.min(b, x));
  const ease = x => 1 - Math.pow(1 - C(x), 3);
  const back = x => { x = C(x); const c = 1.6; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const P = window.PLAN;
  window.draw = t => {
    let cur = 0;
    P.scenes.forEach((s, i) => { if (t >= s.start) cur = i; });
    document.querySelectorAll('.dots i').forEach((d, i) => d.classList.toggle('on', i <= cur));
    document.getElementById('bg').style.transform = `scale(${1 + 0.02 * Math.sin(t * 0.25)})`;
    P.scenes.forEach((s, i) => {
      const el = document.getElementById('s' + i), lt = t - s.start, d = s.dur, last = i === P.scenes.length - 1;
      if (lt < 0 || lt > d) { el.style.opacity = 0; return; }
      const inn = ease(lt / 0.4), out = last ? 0 : C((lt - (d - 0.3)) / 0.3);
      el.style.opacity = Math.min(inn, 1 - out);
      el.style.transform = `translateY(${(1 - inn) * 50 - out * 40}px)`;
      const k = el.querySelector('.kick'); if (k) k.style.transform = `scale(${back(lt / 0.35)})`;
      const q = el.querySelector('.q'); if (q) q.style.transform = `scale(${back((lt - 0.05) / 0.4)}) rotate(${(1 - ease(lt / 0.4)) * -12}deg)`;
      el.querySelectorAll('.head .w').forEach((w, n) => {
        const st = 0.12 + n * 0.055, p = back((lt - st) / 0.32);
        w.style.opacity = C((lt - st) / 0.18); w.style.transform = `translateY(${(1 - p) * 46}px)`;
      });
      const nWords = el.querySelectorAll('.head .w').length;
      el.querySelectorAll('.hl').forEach((h, n) => {
        const st = 0.25 + nWords * 0.055 + n * 0.25;
        h.style.backgroundSize = `${ease((lt - st) / 0.5) * 100}% 100%`;
      });
      const sub = el.querySelector('.sub'); if (sub) { const p = ease((lt - 0.9) / 0.5); sub.style.opacity = p; sub.style.transform = `translateY(${(1 - p) * 30}px)`; }
      const clip = el.querySelector('.clip');
      if (clip) { const p = back((lt - 1.2) / 0.5); clip.style.opacity = C((lt - 1.2) / 0.15); clip.style.transform = `translateY(${(1 - p) * 90}px) rotate(${-1.6 - (1 - ease((lt - 1.2) / 0.5)) * 6}deg)`; }
      const bar = el.querySelector('.tl .bar');
      if (bar) {
        const evs = el.querySelectorAll('.ev'), full = el.querySelector('.tl').offsetHeight - 40;
        const p = ease((lt - 0.8) / 1.6); bar.style.height = (p * full) + 'px';
        evs.forEach((ev, n) => { const st = 0.9 + n * (1.6 / evs.length); const q = back((lt - st) / 0.4);
          ev.style.opacity = C((lt - st) / 0.2); ev.style.transform = `translateX(${(1 - q) * 60}px)`; });
      }
      if (s.kind === 'end') {
        const f = el.querySelector('.follow'), c = el.querySelector('.cta');
        const pf = back((lt - 0.8) / 0.5), pc = back((lt - 1.3) / 0.5);
        f.style.opacity = C((lt - 0.8) / 0.2); f.style.transform = `translateX(${(1 - pf) * -80}px)`;
        c.style.opacity = C((lt - 1.3) / 0.2); c.style.transform = `translateY(${(1 - pc) * 100}px) rotate(-1deg)`;
        const heart = f.querySelector('svg'); heart.style.transform = `scale(${1 + 0.14 * Math.max(0, Math.sin(Math.max(0, lt - 1.2) * Math.PI * 2.4))})`;
      }
    });
    const s = P.scenes[cur], lt = t - s.start, pose = s.pose;
    const ny = document.getElementById('ny');
    const enter = back((t - 0.15) / 0.8), bob = Math.sin(t * Math.PI * 1.1) * 8, sq = 1 - 0.04 * Math.max(0, 1 - lt / 0.18);
    ny.style.transform = `translateX(${(1 - enter) * 760}px) translateY(${bob}px) scaleY(${sq})`;
    document.querySelectorAll('.pose').forEach(p => p.style.opacity = p.id === 'p-' + pose ? 1 : 0);
    const arm = document.querySelector('#p-' + pose + ' .arm');
    let rot = 0;
    if (pose === 'point') rot = -11 * Math.max(0, Math.sin(C((lt - 0.25) / 0.6) * Math.PI));
    if (pose === 'wave') rot = Math.sin(lt * Math.PI * 3.2) * 14;
    if (pose === 'think') rot = Math.sin(lt * Math.PI * 0.8) * 3;
    if (pose === 'confident') rot = Math.sin(lt * Math.PI * 1.2) * 2;
    arm.style.transform = `rotate(${rot}deg)`;
    const blink = ((t + 0.6) % 3.1) < 0.12 ? 0.1 : 1;
    document.querySelectorAll('.eyes').forEach(e => e.style.transform = `scaleY(${blink})`);
  };
})();
"""


def build(folder, out=None):
    folder = Path(folder)
    spec = json.loads((folder / "reel.json").read_text(encoding="utf-8"))
    scenes = spec["scenes"]
    tmp = Path(tempfile.mkdtemp())
    durs = narrate(scenes, tmp)
    t = 0.0
    for sc, d in zip(scenes, durs):
        sc.setdefault("pose", "point")
        sc["start"], sc["voice"] = t, t + LEAD
        sc["dur"] = LEAD + d + BEAT + (1.2 if sc.get("kind") == "end" else 0)
        t += sc["dur"]
    total = t
    page = tmp / "reel.html"; page.write_text(page_html(scenes), encoding="utf-8")
    plan = {"scenes": [{k: sc[k] for k in ("start", "dur", "pose")} | {"kind": sc.get("kind", "text")} for sc in scenes]}
    frames = tmp / "frames"; frames.mkdir()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=render.chrome_path(), args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(page.as_uri()); pg.evaluate("document.fonts.ready")
        pg.evaluate(f"window.PLAN = {json.dumps(plan)};"); pg.evaluate(ANIM)
        for i in range(math.ceil(total * FPS)):
            pg.evaluate(f"draw({i / FPS})")
            pg.screenshot(path=str(frames / f"{i:05d}.jpg"), type="jpeg", quality=88)
        b.close()
    # audio: narration lines at their offsets over the original music bed, which ducks under the voice
    music = tmp / "music.wav"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "compose_music.py"), str(music), "--seconds", f"{total + 1}",
                    "--seed", str(sum(map(ord, folder.name)) % 97)], check=True, capture_output=True)
    ins, chains = ["-i", str(music)], []
    for i, sc in enumerate(scenes):
        ins += ["-i", str(tmp / f"line{i}.wav")]
        ms = int(sc["voice"] * 1000)
        chains.append(f"[{i+1}:a]aresample=48000,highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,"
                      f"volume=1.6,adelay={ms}|{ms}[l{i}]")
    chains.append("".join(f"[l{i}]" for i in range(len(scenes))) + f"amix=inputs={len(scenes)}:normalize=0,apad,atrim=0:{total},asplit=2[vo1][vo2]")
    chains.append(f"[0:a]atrim=0:{total},volume=0.20[mus]")
    chains.append("[mus][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[duck]")
    chains.append(f"[duck][vo2]amix=inputs=2:normalize=0,afade=t=in:d=0.4,afade=t=out:st={total-1.5:.2f}:d=1.5,aformat=channel_layouts=stereo[a]")
    audio = tmp / "audio.m4a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(chains), "-map", "[a]",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(audio)], check=True)
    out = Path(out) if out else folder / "reel.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "%05d.jpg"), "-i", str(audio),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
                    "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    shutil.rmtree(tmp)
    print(f"reel: {out} ({total:.1f}s, {len(scenes)} scenes)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("folder"); ap.add_argument("--out")
    a = ap.parse_args(); build(a.folder, a.out)
