"""Nyaya v2 — AdalatIQ's mascot: a bold, confident young Indian woman in a tailored blazer and pencil skirt.

Original character (flat vector). Black wavy hair over one shoulder, coral accents (scarf knot, button,
earrings, lips). Poses: point (other hand on hip), wave, think, confident (both hands on hips).

python3 mascot/nyaya.py  -> mascot/nyaya2-<pose>.svg  (viewBox 0 0 700 900)
She points to image-right; mirror with transform="scale(-1,1)" when placed on the right of a slide.
"""
from pathlib import Path

SKIN, SKIN_SHADE, SKIN_DARK = "#C98F6B", "#B07450", "#8F5638"
HAIR, HAIR_HI = "#1C1717", "#463838"
INK, INK2, SKIRT = "#161616", "#272222", "#1E1B1B"
CORAL, CORAL_DARK = "#E8523A", "#C43E29"
WHITE, LIP, LIP2 = "#FBF7F2", "#B8402C", "#D24B34"


def limb(points, w=44, color=INK):
    d = "M" + " L".join(f"{x} {y}" for x, y in points)
    return f'<path d="{d}" stroke="{color}" stroke-width="{w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


def hand_fist(x, y, r=21):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{SKIN}"/>'


def hand_point(x, y):
    return (f'<ellipse cx="{x}" cy="{y}" rx="23" ry="20" fill="{SKIN}"/>'
            f'<rect x="{x+4}" y="{y-16}" width="58" height="15" rx="7.5" fill="{SKIN}"/>'
            f'<rect x="{x-8}" y="{y-36}" width="14" height="28" rx="7" fill="{SKIN}" transform="rotate(-25 {x-1} {y-22})"/>')


def hand_open(x, y):
    fingers = "".join(f'<rect x="{x-24+i*13}" y="{y-56-(6 if i in (1, 2) else 0)}" width="12" height="44" rx="6" fill="{SKIN}"/>'
                      for i in range(4))
    return (f'<ellipse cx="{x}" cy="{y-12}" rx="30" ry="30" fill="{SKIN}"/>{fingers}'
            f'<rect x="{x-46}" y="{y-14}" width="34" height="13" rx="6.5" fill="{SKIN}" transform="rotate(-30 {x-29} {y-8})"/>')


def head(expr):
    # face shape, ears, neck
    out = (f'<rect x="278" y="330" width="44" height="110" rx="20" fill="{SKIN_SHADE}"/>'
           f'<ellipse cx="202" cy="258" rx="15" ry="22" fill="{SKIN}"/><ellipse cx="398" cy="258" rx="15" ry="22" fill="{SKIN}"/>'
           f'<path d="M204 246 Q202 140 300 138 Q398 140 396 246 Q394 324 346 356 Q300 380 254 356 Q206 324 204 246Z" fill="{SKIN}"/>')

    def eye(cx, wink=False):
        side = 1 if cx > 300 else -1
        if wink:
            return f'<path d="M{cx-16} 262 Q{cx} 250 {cx+16} 262" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>'
        return (f'<path d="M{cx-17} 258 Q{cx} 244 {cx+17} 256 Q{cx} 272 {cx-17} 258Z" fill="#fff"/>'
                f'<circle cx="{cx+side}" cy="258" r="9.5" fill="#4A2A1A"/><circle cx="{cx+side}" cy="258" r="5" fill="{INK}"/>'
                f'<circle cx="{cx+side+3}" cy="254" r="2.8" fill="#fff"/>'
                f'<path d="M{cx-18} 257 Q{cx} 241 {cx+18} 255" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/>'
                f'<path d="M{cx+side*17} 255 L{cx+side*29} 246" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>')

    brows = {
        "confident": ("M236 228 Q258 214 282 222", "M318 220 Q342 208 364 222"),   # one brow arched higher
        "wink": ("M236 228 Q258 216 282 224", "M318 218 Q342 206 364 220"),
        "think": ("M236 224 Q258 214 282 220", "M318 230 Q342 224 364 230"),
    }[expr]
    mouth = {
        "confident": (f'<path d="M280 316 Q306 336 326 310 Q306 324 280 316Z" fill="{LIP2}"/>'
                      f'<path d="M280 316 Q292 308 302 312 Q314 304 326 310 Q306 320 280 316Z" fill="{LIP}"/>'),
        "wink": (f'<path d="M278 312 Q304 342 326 310 Q302 322 278 312Z" fill="{LIP2}"/>'
                 f'<path d="M278 312 Q290 304 302 309 Q314 302 326 310 Q302 318 278 312Z" fill="{LIP}"/>'),
        "think": f'<path d="M288 322 Q302 316 316 323" stroke="{LIP}" stroke-width="7" fill="none" stroke-linecap="round"/>',
    }[expr]
    out += (eye(262) + eye(338, wink=(expr == "wink")) +
            "".join(f'<path d="{b}" stroke="{HAIR}" stroke-width="8" fill="none" stroke-linecap="round"/>' for b in brows) +
            f'<path d="M300 266 Q293 290 307 293" stroke="{SKIN_DARK}" stroke-width="4" fill="none" stroke-linecap="round"/>'
            f'<circle cx="240" cy="296" r="15" fill="{CORAL}" opacity=".18"/><circle cx="360" cy="296" r="15" fill="{CORAL}" opacity=".18"/>'
            + mouth)
    # coral drop earrings
    out += "".join(f'<circle cx="{x}" cy="284" r="5" fill="{CORAL}"/><path d="M{x-8} 292 Q{x} 312 {x+8} 292Z" fill="{CORAL}"/>' for x in (202, 398))
    return out


HAIR_BACK = (f'<path d="M196 250 Q178 120 304 108 Q438 116 414 262 Q432 330 418 396 Q436 452 410 492 '
             f'Q380 470 372 430 L232 430 Q216 470 192 480 Q170 440 186 400 Q164 330 196 250Z" fill="{HAIR}"/>')
HAIR_FRONT = (f'<path d="M200 270 Q190 128 304 124 Q408 130 402 236 Q374 196 338 168 Q306 222 200 270Z" fill="{HAIR}"/>'
              f'<path d="M238 186 Q266 150 304 142" stroke="{HAIR_HI}" stroke-width="8" fill="none" stroke-linecap="round"/>')
# wavy lock swept forward over her right shoulder (image left), drawn on top of the blazer
HAIR_LOCK = (f'<path d="M206 262 Q186 350 206 420 Q224 480 196 540 Q186 566 206 584 Q236 560 244 500 '
             f'Q250 440 234 390 Q226 330 236 284Z" fill="{HAIR}"/>'
             f'<path d="M214 350 Q206 420 226 470" stroke="{HAIR_HI}" stroke-width="6" fill="none" stroke-linecap="round"/>')


def body():
    return (
        # pencil skirt (to the knees)
        f'<path d="M210 640 Q190 720 206 800 Q214 860 226 900 L374 900 Q386 860 394 800 Q410 720 390 640Z" fill="{SKIRT}"/>'
        f'<path d="M300 760 L300 900" stroke="#000" stroke-width="3" opacity=".35"/>'
        # tailored blazer: shoulders, cinched waist, flared peplum hem
        f'<path d="M160 520 Q166 452 232 436 L300 428 L368 436 Q434 452 440 520 Q414 560 384 600 '
        f'Q404 640 412 676 Q300 700 188 676 Q196 640 216 600 Q186 560 160 520Z" fill="{INK}"/>'
        # white collared shirt
        f'<path d="M262 432 L300 520 L338 432Z" fill="{WHITE}"/>'
        f'<path d="M262 432 L284 470 L300 446Z M338 432 L316 470 L300 446Z" fill="#E9E2D8"/>'
        # lapels
        f'<path d="M232 436 L300 556 L292 676 L246 676 Q256 620 238 590 Q252 520 232 436Z" fill="{INK2}"/>'
        f'<path d="M368 436 L300 556 L308 676 L354 676 Q344 620 362 590 Q348 520 368 436Z" fill="{INK2}"/>'
        # coral neck-scarf knot + tails
        f'<path d="M270 432 Q300 452 330 432 L334 446 Q300 470 266 446Z" fill="{CORAL}"/>'
        f'<path d="M292 450 L282 512 L298 506 L304 456Z" fill="{CORAL}"/><path d="M306 452 L318 506 L302 512 L298 456Z" fill="{CORAL_DARK}"/>'
        # waist button + seam
        f'<circle cx="300" cy="606" r="8" fill="{CORAL}"/>'
        f'<path d="M216 600 Q300 616 384 600" stroke="#000" stroke-width="3" fill="none" opacity=".3"/>'
    )


def arms(pose):
    hip_l = limb([(196, 478), (132, 584), (208, 632)]) + hand_fist(214, 630, 20)       # her right hand on hip
    if pose == "point":
        return hip_l + limb([(404, 478), (500, 486), (574, 452)]) + hand_point(590, 446)
    if pose == "wave":
        return hip_l + limb([(404, 478), (512, 520), (552, 396)]) + hand_open(556, 382)
    if pose == "think":
        return hip_l + limb([(404, 480), (436, 600), (338, 392)]) + hand_fist(330, 372, 23)
    # confident: both hands on hips
    return hip_l + limb([(404, 478), (468, 584), (392, 632)]) + hand_fist(386, 630, 20)


POSES = {"point": "confident", "wave": "wink", "think": "think", "confident": "confident"}


def nyaya(pose="point"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 900">'
            f'{HAIR_BACK}{body()}{head(POSES[pose])}{HAIR_FRONT}{HAIR_LOCK}{arms(pose)}</svg>')


if __name__ == "__main__":
    out = Path(__file__).parent
    for pose in POSES:
        (out / f"nyaya2-{pose}.svg").write_text(nyaya(pose))
    print("written")
