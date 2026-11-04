"""Animated 9:16 Reel with the Nyaya mascot, built from a post.json.

Usage: python3 scripts/animate_reel.py queue/<folder> [--music track.mp3]
Writes <folder>/reel.mp4 (1080x1920, 30 fps, H.264 + AAC, faststart).

The page is rendered frame by frame in headless Chrome (deterministic: every frame is drawn from time t),
so nothing depends on real-time playback. Without --music, an original ambient pad plus soft "pop" cues
at each scene change is generated, so there are no licensing issues.
"""
import argparse, html, json, math, shutil, subprocess, sys, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mascot"))
sys.path.insert(0, str(ROOT / "scripts"))
import nyaya          # noqa: E402
import render         # noqa: E402  (fonts, UI strings)

FPS = 30
HOOK, SCENE, END = 4.0, 4.4, 5.0


def timeline(spec):
    scenes, t = [], 0.0
    scenes.append(("hook", t, HOOK)); t += HOOK
    for i in range(len(spec["slides"])):
        scenes.append((f"s{i}", t, SCENE)); t += SCENE
    scenes.append(("end", t, END)); t += END
    return scenes, t


def page_html(spec):
    e = html.escape
    ui = render.UI[spec["lang"]]
    words = lambda s, cls: "".join(f'<span class="w {cls}">{e(w)}</span> ' for w in s.split())
    scenes = [f'<section id="hook" class="sc"><div class="q">Q.</div><h1>{words(spec["hook"], "")}</h1>'
              f'<h1 class="coral">{words(spec["hook_q"], "late")}</h1></section>']
    for i, s in enumerate(spec["slides"]):
        body = f'<p class="body">{e(s["body"])}</p>' if "body" in s else ""
        lst = ("<ul>" + "".join(f'<li>{e(x)}</li>' for x in s["list"]) + "</ul>") if "list" in s else ""
        scenes.append(f'<section id="s{i}" class="sc"><div class="num">{i+1:02d}</div>'
                      f'<h2>{words(s["title"], "")}</h2>{body}{lst}<div class="ref">{e(s["ref"])}</div></section>')
    srcs = "".join(f"<div class='src'>{e(x)}</div>" for x in spec["sources"])
    scenes.append(f'<section id="end" class="sc"><h3>{e(ui["sources"])}</h3>{srcs}'
                  f'<div class="disc">{e(ui["disclaimer"])}</div>'
                  f'<div class="cta"><p>{e(ui["cta"])}</p><strong>{e(ui["cta2"])}</strong><em>adalatiq.com →</em></div></section>')
    poses = "".join(f'<div class="pose" id="p-{p}">{nyaya.nyaya(p)}</div>' for p in ("think", "point", "confident", "wave"))
    css = render.FACES + f"""
:root{{--paper:#FBF7F2;--ink:#161616;--soft:#4a4540;--coral:#E8523A;--coral-soft:#FBE3DD;--line:#E9E0D5}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:1080px;height:1920px;overflow:hidden;background:var(--paper);font-family:{ui['font']},Inter,sans-serif;color:var(--ink)}}
#dark{{position:absolute;inset:0;background:var(--ink);clip-path:circle(0% at 85% 80%)}}
.top{{position:absolute;left:80px;right:80px;top:110px;display:flex;align-items:center;justify-content:space-between;font-family:Inter;font-weight:800;font-size:40px}}
.top b{{color:var(--coral)}}
#bar{{position:absolute;left:80px;right:80px;top:190px;height:8px;border-radius:4px;background:var(--line)}}
#bar i{{display:block;height:100%;width:0;border-radius:4px;background:var(--coral)}}
.sc{{position:absolute;left:80px;right:80px;top:300px;opacity:0}}
.q{{font-family:Inter;font-weight:900;font-size:170px;color:var(--coral);line-height:1;margin-bottom:30px}}
h1{{font-weight:800;font-size:100px;line-height:1.1;letter-spacing:-2px;margin-bottom:24px}}
h1.coral{{color:var(--coral)}}
.num{{font-family:Inter;font-weight:900;font-size:56px;color:#fff;background:var(--coral);width:110px;height:110px;border-radius:30px;display:grid;place-items:center;margin-bottom:40px}}
h2{{font-weight:800;font-size:84px;line-height:1.12;letter-spacing:-1.5px;margin-bottom:36px}}
.body{{font-weight:500;font-size:46px;line-height:1.45;color:var(--soft);max-width:900px}}
ul{{list-style:none;max-width:920px}}
li{{font-weight:500;font-size:42px;line-height:1.35;color:var(--soft);padding:20px 0 20px 54px;border-top:2px solid var(--line);position:relative}}
li:before{{content:"";position:absolute;left:4px;top:36px;width:20px;height:20px;border-radius:50%;background:var(--coral)}}
.ref{{display:inline-block;margin-top:40px;font-family:Inter,{ui['font']};font-weight:700;font-size:30px;color:var(--coral);background:var(--coral-soft);padding:16px 26px;border-radius:999px}}
.w{{display:inline-block}}
#end{{color:var(--paper)}}
#end h3{{font-weight:700;font-size:34px;letter-spacing:3px;text-transform:uppercase;color:var(--coral);margin-bottom:24px}}
#end .src{{font-weight:500;font-size:40px;line-height:1.4;margin-bottom:14px}}
#end .disc{{font-weight:500;font-size:34px;line-height:1.5;color:#bdb4aa;border-top:2px solid #333;padding-top:36px;margin-top:36px;max-width:620px}}
.cta{{position:absolute;left:0;top:760px;width:560px;background:var(--coral);color:#fff;border-radius:32px;padding:44px 48px}}
.cta p{{font-weight:500;font-size:36px;margin-bottom:8px}} .cta strong{{display:block;font-weight:800;font-size:58px;line-height:1.15}}
.cta em{{font-style:normal;font-family:Inter;font-weight:800;font-size:42px;display:block;margin-top:14px}}
#nyaya{{position:absolute;right:-70px;bottom:-70px;width:660px;height:850px}}
.pose{{position:absolute;inset:0;opacity:0;transform:scaleX(-1)}}
.pose svg{{width:100%;height:100%}}
.arm{{transform-box:view-box;transform-origin:404px 478px}}
.eyes{{transform-box:fill-box;transform-origin:center}}
"""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>"
            f"<div id='dark'></div><div class='top'><span>Adalat<b>IQ</b></span></div><div id='bar'><i></i></div>"
            f"{''.join(scenes)}<div id='nyaya'>{poses}</div></body></html>")


ANIM_JS = r"""
(() => {
  const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x));
  const ease = x => 1 - Math.pow(1 - clamp(x), 3);
  const back = x => { x = clamp(x); const c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const P = window.PLAN;
  window.draw = (t) => {
    const total = P.total;
    document.querySelector('#bar i').style.width = (100 * clamp(t / total)) + '%';
    let current = null;
    for (const [id, s, d] of P.scenes) {
      const el = document.getElementById(id), lt = t - s;
      if (lt < 0 || lt > d) { el.style.opacity = 0; continue; }
      current = [id, lt, d];
      const inn = ease(lt / 0.5), out = id === 'end' ? 0 : clamp((lt - (d - 0.35)) / 0.35);
      el.style.opacity = Math.min(inn, 1 - out);
      el.style.transform = `translateX(${(1 - inn) * 140 - out * 140}px)`;
      el.querySelectorAll('.w').forEach((w, k) => {
        const st = (w.classList.contains('late') ? 1.1 : 0.15) + k * 0.07;
        const p = back((lt - st) / 0.35);
        w.style.opacity = clamp((lt - st) / 0.2); w.style.transform = `translateY(${(1 - p) * 40}px)`;
      });
      const q = el.querySelector('.q'); if (q) q.style.transform = `scale(${back(lt / 0.45)})`;
      const num = el.querySelector('.num'); if (num) num.style.transform = `scale(${back((lt - 0.05) / 0.4)}) rotate(${(1 - ease((lt - 0.05) / 0.4)) * -20}deg)`;
      const body = el.querySelector('.body'); if (body) { const p = ease((lt - 0.8) / 0.5); body.style.opacity = p; body.style.transform = `translateY(${(1 - p) * 30}px)`; }
      el.querySelectorAll('li').forEach((li, k) => { const p = ease((lt - 0.8 - k * 0.22) / 0.4); li.style.opacity = p; li.style.transform = `translateX(${(1 - p) * 60}px)`; });
      const ref = el.querySelector('.ref'); if (ref) { const p = back((lt - 1.4) / 0.4); ref.style.opacity = clamp((lt - 1.4) / 0.2); ref.style.transform = `scale(${0.6 + 0.4 * p})`; }
      if (id === 'end') {
        el.querySelectorAll('h3,.src,.disc').forEach((x, k) => { const p = ease((lt - 0.6 - k * 0.15) / 0.4); x.style.opacity = p; });
        const cta = el.querySelector('.cta'); const p = back((lt - 1.4) / 0.5);
        cta.style.opacity = clamp((lt - 1.4) / 0.2); cta.style.transform = `translateY(${(1 - p) * 120}px)`;
      }
    }
    // dark background wipe for the closing scene
    const endS = P.scenes[P.scenes.length - 1][1];
    document.getElementById('dark').style.clipPath = `circle(${ease((t - endS) / 0.7) * 150}% at 85% 80%)`;
    document.querySelector('.top').style.color = t > endS + 0.3 ? '#FBF7F2' : '#161616';
    document.getElementById('nyaya').style.filter = t > endS + 0.3 ? 'drop-shadow(0 0 2px #FBF7F2) drop-shadow(0 0 2px #FBF7F2)' : 'none';
    // Nyaya: pose per scene, slide-in, idle bob, blink, arm jab / wave
    const id = current ? current[0] : 'hook', lt = current ? current[1] : 0;
    const pose = id === 'hook' ? 'think' : id === 'end' ? 'wave' : (P.confident.includes(id) ? 'confident' : 'point');
    const ny = document.getElementById('nyaya');
    const enter = back((t - 0.2) / 0.8);
    const bob = Math.sin(t * Math.PI * 1.1) * 7;
    const squash = 1 - 0.04 * Math.max(0, 1 - lt / 0.18);
    ny.style.transform = `translateX(${(1 - enter) * 700}px) translateY(${bob}px) scaleY(${squash})`;
    ny.style.transformOrigin = 'bottom center';
    document.querySelectorAll('.pose').forEach(p => { p.style.opacity = p.id === 'p-' + pose ? 1 : 0; });
    const arm = document.querySelector('#p-' + pose + ' .arm');
    let rot = 0;
    if (pose === 'point') rot = -10 * Math.max(0, Math.sin(clamp((lt - 0.3) / 0.6) * Math.PI));        // a jab toward the new point
    if (pose === 'wave') rot = Math.sin(lt * Math.PI * 3.2) * 14;
    if (pose === 'think') rot = Math.sin(lt * Math.PI * 0.8) * 3;
    arm.style.transform = `rotate(${rot}deg)`;
    const blink = ((t + 0.4) % 3.3) < 0.12 ? 0.1 : 1;
    document.querySelectorAll('.eyes').forEach(eg => eg.style.transform = `scaleY(${blink})`);
  };
})();
"""


def audio(tmp, scenes, total, music):
    out = tmp / "audio.m4a"
    if music:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(music), "-t", f"{total}",
                        "-af", f"afade=t=in:d=1,afade=t=out:st={total-2}:d=2", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(out)], check=True)
        return out
    pad = ("0.05*sin(2*PI*130.81*t)+0.035*sin(2*PI*196.00*t)+0.03*sin(2*PI*261.63*t)"
           "+0.025*sin(2*PI*329.63*t)*(0.6+0.4*sin(2*PI*0.15*t))")
    pop = "0.35*sin(2*PI*(700+500*exp(-30*t))*t)*exp(-22*t)"
    inputs = ["-f", "lavfi", "-t", f"{total}", "-i", f"aevalsrc={pad}:s=48000"]
    delays = [int(s * 1000) + 60 for _, s, _ in scenes]
    for _ in delays:
        inputs += ["-f", "lavfi", "-t", "0.3", "-i", f"aevalsrc={pop}:s=48000"]
    chains = [f"[{k+1}:a]adelay={d}|{d}[p{k}]" for k, d in enumerate(delays)]
    mix = "[0:a]" + "".join(f"[p{k}]" for k in range(len(delays)))
    chains.append(f"{mix}amix=inputs={len(delays)+1}:normalize=0,afade=t=in:d=1,afade=t=out:st={total-2}:d=2,"
                  f"aformat=channel_layouts=stereo[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains), "-map", "[a]",
                    "-t", f"{total}", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", str(out)], check=True)
    return out


def build(folder, music=None):
    folder = Path(folder)
    spec = json.loads((folder / "post.json").read_text(encoding="utf-8"))
    scenes, total = timeline(spec)
    tmp = Path(tempfile.mkdtemp())
    page = tmp / "reel.html"
    page.write_text(page_html(spec), encoding="utf-8")
    plan = {"scenes": scenes, "total": total, "confident": [f"s{len(spec['slides'])//2}"]}
    frames = tmp / "frames"; frames.mkdir()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=render.chrome_path(), args=["--allow-file-access-from-files"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(page.as_uri())
        pg.evaluate("document.fonts.ready")
        pg.evaluate(f"window.PLAN = {json.dumps(plan)};")
        pg.evaluate(ANIM_JS)
        n = math.ceil(total * FPS)
        for i in range(n):
            pg.evaluate(f"draw({i / FPS})")
            pg.screenshot(path=str(frames / f"{i:05d}.jpg"), type="jpeg", quality=88)
        b.close()
    a = audio(tmp, scenes, total, music)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "%05d.jpg"), "-i", str(a),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
                    "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(folder / "reel.mp4")], check=True)
    shutil.rmtree(tmp)
    print(f"reel: {folder / 'reel.mp4'} ({total:.1f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("--music")
    a = ap.parse_args()
    build(a.folder, a.music)
