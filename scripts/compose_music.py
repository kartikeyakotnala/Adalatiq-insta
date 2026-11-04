"""Compose an original, copyright-free background track for AdalatIQ Reels.

Usage: python3 scripts/compose_music.py out.wav --seconds 40 [--seed 3]

Upbeat, light "explainer" feel at 104 BPM: warm electric-piano chords, soft bassline, gentle kick,
hats and finger snaps, and a simple pentatonic hook. Everything is synthesised here from sine waves
and noise, so the track is entirely original. The seed varies the hook, the chord progression and
the sparkle pattern so each week's Reels don't sound identical.
"""
import argparse
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter

SR = 48000
BPM = 104
BEAT = 60 / BPM
BAR = 4 * BEAT

PROGRESSIONS = [  # (root midi, chord intervals) per bar — common pop progressions
    [(60, (0, 4, 7, 11)), (57, (0, 3, 7, 10)), (53, (0, 4, 7, 11)), (55, (0, 4, 7, 10))],   # Cmaj7 Am7 Fmaj7 G7
    [(53, (0, 4, 7, 11)), (55, (0, 4, 7, 10)), (52, (0, 3, 7, 10)), (57, (0, 3, 7, 10))],   # Fmaj7 G7 Em7 Am7
    [(60, (0, 4, 7, 9)), (55, (0, 4, 7, 10)), (57, (0, 3, 7, 10)), (53, (0, 4, 7, 11))],    # C6 G7 Am7 Fmaj7
]
PENTA = [0, 2, 4, 7, 9]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=0.005, d=0.3, s=0.0, r=0.05):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * (s + (1 - s) * np.exp(-t / max(d, 1e-4)))
    rel = int(r * SR)
    if rel and n > rel:
        e[-rel:] *= np.linspace(1, 0, rel)
    return e


def epiano(m, dur, vel=0.18):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    tone = np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t*6) + 0.12*np.sin(2*np.pi*3*f*t)*np.exp(-t*9)
    trem = 1 + 0.06*np.sin(2*np.pi*4.5*t)
    return vel * tone * trem * env(n, 0.004, 0.9, 0.15, 0.08)


def bass(m, dur, vel=0.32):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m - 24)
    tone = np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*2*f*t)
    return vel * tone * env(n, 0.008, 0.35, 0.4, 0.05)


def kick(vel=0.55):
    n = int(0.28 * SR); t = np.arange(n) / SR
    f = 50 + 90*np.exp(-t*30)
    return vel * np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t*14)


def noise_hit(dur, lo, hi, decay, vel, rng):
    n = int(dur * SR); x = rng.standard_normal(n)
    b, a = butter(2, [lo/(SR/2), hi/(SR/2)], btype="band")
    return vel * lfilter(b, a, x) * np.exp(-np.arange(n)/SR*decay)


def bell(m, dur, vel=0.10):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    return vel * (np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*4.01*f*t)*np.exp(-t*8)) * env(n, 0.002, 0.5, 0, 0.1)


def place(track, clip, start):
    i = int(start * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(clip))
    track[i:j] += clip[: j - i]


def compose(seconds, seed):
    rng = np.random.default_rng(seed)
    prog = PROGRESSIONS[seed % len(PROGRESSIONS)]
    n = int((seconds + 2) * SR)
    keys, low, drums, top = (np.zeros(n) for _ in range(4))
    hook = [int(rng.choice(PENTA)) + 72 for _ in range(8)]          # one-bar-pair motif in C pentatonic
    bars = int(np.ceil(seconds / BAR)) + 1
    for b in range(bars):
        t0 = b * BAR
        root, chord = prog[b % 4]
        intro = b < 1
        # keys: off-beat chord stabs (pushes the groove along)
        for k, beat in enumerate([0, 1.5, 2, 3.5]):
            for iv in chord:
                place(keys, epiano(root + iv, BEAT * (1.4 if k % 2 == 0 else 0.9), 0.07), t0 + beat * BEAT)
        if intro:
            continue
        # bass: root / fifth pattern
        for beat, iv, d in [(0, 0, 0.9), (1.5, 0, 0.4), (2, 7, 0.9), (3.5, 12, 0.4)]:
            place(low, bass(root + iv, BEAT * d), t0 + beat * BEAT)
        # drums: kick on 1 and 3 (+ pickup), snaps on 2 and 4, eighth-note hats
        for beat in (0, 2, 2.75):
            place(drums, kick(0.5 if beat != 2.75 else 0.3), t0 + beat * BEAT)
        for beat in (1, 3):
            place(drums, noise_hit(0.12, 1500, 5000, 40, 0.22, rng), t0 + beat * BEAT)
        for h in range(8):
            place(drums, noise_hit(0.05, 7000, 14000, 90, 0.07 if h % 2 else 0.11, rng), t0 + h * BEAT / 2)
        # hook every other bar pair, sparkle bells otherwise
        if (b // 2) % 2 == 1:
            for k, m in enumerate(hook):
                place(top, bell(m, BEAT * 0.9), t0 + (b % 2) * 0 + k * BEAT / 2)
        elif rng.random() < 0.6:
            place(top, bell(root + chord[-1] + 12, BEAT * 1.5, 0.06), t0 + 3 * BEAT)
    # simple stereo + room: slight delay on keys/top
    def echo(x, ms, fb):
        d = int(ms / 1000 * SR); y = x.copy()
        for k in range(1, 4):
            y[d*k:] += x[:-d*k] * (fb ** k)
        return y
    keys, top = echo(keys, 230, 0.28), echo(top, 345, 0.35)
    left = 0.9*keys + low + drums + 0.7*top
    right = 0.75*keys + low + drums + 0.9*top
    st = np.stack([left, right], 1)[: int(seconds * SR)]
    fade = int(2 * SR); st[-fade:] *= np.linspace(1, 0, fade)[:, None]
    fi = int(0.5 * SR); st[:fi] *= np.linspace(0, 1, fi)[:, None]
    st /= np.max(np.abs(st)) / 0.8
    return st


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--seconds", type=float, default=40); ap.add_argument("--seed", type=int, default=3)
    a = ap.parse_args()
    wavfile.write(a.out, SR, (compose(a.seconds, a.seed) * 32767).astype(np.int16))
    print("music:", a.out)
