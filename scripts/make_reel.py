"""Turn a rendered carousel folder into a 9:16 Instagram Reel (reel.mp4).

Usage: python3 scripts/make_reel.py queue/<folder> [--music path/to/track.mp3]

Each slide is placed on a 1080x1920 canvas in its own background colour, shown long enough to read,
with soft cross-fades. Without --music, a quiet original ambient tone is generated (no licensing issues).
Output follows Instagram's Reels spec: H.264, AAC 48 kHz, 30 fps, faststart, 9:16.
"""
import argparse, subprocess, tempfile
from pathlib import Path
from PIL import Image

W, H, SLIDE_H = 1080, 1920, 1350
FADE = 0.4


def durations(n):
    # hook 3s, answer slides 4.5s, final slide 4s
    return [3.0] + [4.5] * (n - 2) + [4.0]


def pad_slides(folder, tmp):
    frames = []
    for i, s in enumerate(sorted(folder.glob("slide-*.jpg"))):
        img = Image.open(s).convert("RGB")
        bg = img.getpixel((5, 5))
        canvas = Image.new("RGB", (W, H), bg)
        canvas.paste(img, (0, 220))   # sits a little high so Instagram's caption overlay at the bottom doesn't cover it
        out = tmp / f"f{i:02d}.png"
        canvas.save(out)
        frames.append(out)
    return frames


def build(folder, music=None):
    folder = Path(folder)
    tmp = Path(tempfile.mkdtemp())
    frames = pad_slides(folder, tmp)
    d = durations(len(frames))
    total = sum(d) - FADE * (len(d) - 1)

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f, t in zip(frames, d):
        cmd += ["-loop", "1", "-t", f"{t}", "-i", str(f)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
    else:
        # quiet original pad: a slow, soft C-major chord with gentle movement
        expr = ("0.05*sin(2*PI*130.81*t)+0.04*sin(2*PI*196.00*t)+0.035*sin(2*PI*261.63*t)"
                "+0.03*sin(2*PI*329.63*t)*(0.6+0.4*sin(2*PI*0.15*t))")
        cmd += ["-f", "lavfi", "-t", f"{total}", "-i", f"aevalsrc={expr}:s=48000:c=stereo"]

    chains, prev, offset = [], "[0:v]", 0.0
    for k in range(1, len(frames)):
        offset += d[k - 1] - FADE
        out = f"[v{k}]"
        chains.append(f"{prev}[{k}:v]xfade=transition=fade:duration={FADE}:offset={offset:.2f}{out}")
        prev = out
    chains.append(f"{prev}format=yuv420p,fps=30[vout]")
    a = len(frames)
    chains.append(f"[{a}:a]atrim=0:{total},afade=t=in:d=1,afade=t=out:st={total-1.5:.2f}:d=1.5,"
                  f"aresample=48000[aout]")
    cmd += ["-filter_complex", ";".join(chains), "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart",
            "-t", f"{total}", str(folder / "reel.mp4")]
    subprocess.run(cmd, check=True)
    print(f"reel: {folder / 'reel.mp4'} ({total:.1f}s, {len(frames)} slides)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--music")
    a = ap.parse_args()
    build(a.folder, a.music)
