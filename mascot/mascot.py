"""AdalatIQ mascot "Nyaya" — original flat vector character, generated as SVG.

python3 mascot/mascot.py   -> writes mascot/nyaya-<variant>-<pose>.svg  (viewBox 700x700)
Variants differ in hairstyle and outfit. Poses (point / wave / think) are reused by slide and Reel templates.
She faces the viewer and points to her left (image right); mirror with transform when she stands on the right.
"""
from pathlib import Path

SKIN, SKIN_SHADE, SKIN_DARK = "#C98F6B", "#B07450", "#9A6040"
HAIR, INK, INK2 = "#1F1A1A", "#161616", "#262222"
CORAL, CORAL_DARK = "#E8523A", "#C43E29"
WHITE, LIP = "#FBF7F2", "#B8402C"


def face(expr):
    def eye(cx, wink=False):
        if wink:
            return f'<path d="M{cx-14} {266} Q{cx} {254} {cx+14} {266}" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>'
        return (f'<ellipse cx="{cx}" cy="262" rx="12" ry="15" fill="{INK}"/>'
                f'<circle cx="{cx+4}" cy="256" r="4" fill="#fff"/>'
                # winged liner on the outer corner
                + (f'<path d="M{cx+10} 254 L{cx+22} 246" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>' if cx > 300
                   else f'<path d="M{cx-10} 254 L{cx-22} 246" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'))
    brows = {"smile": ("M240 230 Q262 218 282 226", "M318 226 Q338 218 360 230"),
             "wink": ("M240 232 Q262 222 282 228", "M318 224 Q338 212 360 226"),
             "think": ("M240 226 Q262 216 282 222", "M318 232 Q338 226 360 232")}[expr]
    mouth = {"smile": f'<path d="M276 314 Q300 340 324 314 Q300 324 276 314Z" fill="{LIP}"/>',
             "wink": f'<path d="M272 312 Q302 344 328 310 Q300 324 272 312Z" fill="{LIP}"/>',
             "think": f'<path d="M288 324 Q302 318 316 326" stroke="{LIP}" stroke-width="6" fill="none" stroke-linecap="round"/>'}[expr]
    return (eye(262) + eye(338, wink=(expr == "wink")) +
            "".join(f'<path d="{b}" stroke="{HAIR}" stroke-width="8" fill="none" stroke-linecap="round"/>' for b in brows) +
            f'<path d="M300 270 Q294 292 306 296" stroke="{SKIN_DARK}" stroke-width="4" fill="none" stroke-linecap="round"/>'
            f'<circle cx="236" cy="300" r="16" fill="{CORAL}" opacity=".2"/><circle cx="364" cy="300" r="16" fill="{CORAL}" opacity=".2"/>'
            + mouth)


def hair_back(style):
    return {
        "long": f'<path d="M188 250 Q182 120 300 116 Q418 120 412 250 L430 480 Q300 506 170 480Z" fill="{HAIR}"/>',
        "bob": f'<path d="M186 256 Q180 120 300 116 Q420 120 414 256 L418 366 Q392 390 368 374 L232 374 Q208 390 182 366Z" fill="{HAIR}"/>',
        "bun": f'<circle cx="300" cy="112" r="54" fill="{HAIR}"/><path d="M196 250 Q190 132 300 128 Q410 132 404 250 L398 300 L202 300Z" fill="{HAIR}"/>',
    }[style]


def hair_front(style):
    return {
        "long": f'<path d="M198 268 Q190 134 300 130 Q408 134 404 246 Q372 206 336 176 Q300 224 198 268Z" fill="{HAIR}"/>',
        "bob": f'<path d="M196 276 Q188 132 300 128 Q412 132 404 276 Q390 222 372 196 Q300 218 228 196 Q210 226 196 276Z" fill="{HAIR}"/>',
        "bun": f'<path d="M204 246 Q206 142 300 138 Q394 142 396 246 Q362 190 300 180 Q238 190 204 246Z" fill="{HAIR}"/>',
    }[style]


def torso(outfit):
    top = CORAL if outfit == "kurta" else WHITE
    t = (f'<path d="M110 700 L124 530 Q136 452 222 434 L300 426 L378 434 Q464 452 476 530 L490 700Z" fill="{INK}"/>'
         f'<path d="M260 430 L300 512 L340 430Z" fill="{top}"/>'
         f'<path d="M222 434 L300 540 L286 700 L236 700 Q248 560 222 434Z" fill="{INK2}"/>'
         f'<path d="M378 434 L300 540 L314 700 L364 700 Q352 560 378 434Z" fill="{INK2}"/>'
         # resting arm on her right (image left)
         f'<path d="M132 520 Q112 610 120 700 L168 700 Q162 612 180 540Z" fill="{INK}"/>')
    if outfit == "scarf":
        t += (f'<path d="M238 424 Q300 470 362 424 L370 446 Q300 498 230 446Z" fill="{CORAL}"/>'
              f'<path d="M332 456 L360 626 L334 616 L318 468Z" fill="{CORAL}"/>'
              f'<path d="M344 458 L380 610 L360 620 L334 470Z" fill="{CORAL_DARK}"/>')
    elif outfit == "kurta":
        t += f'<path d="M260 430 L300 512 L340 430" stroke="{CORAL_DARK}" stroke-width="6" fill="none"/>'
    else:  # coral pocket square
        t += f'<path d="M386 520 L430 520 L418 498 L406 512 L396 496Z" fill="{CORAL}"/><path d="M382 520 h52" stroke="{INK2}" stroke-width="4"/>'
    return t


def arm(pose):
    if pose == "point":   # arm out to the side, index finger pointing right
        return (f'<path d="M446 470 Q530 468 574 440 L588 470 Q536 512 456 528Z" fill="{INK}"/>'
                f'<ellipse cx="600" cy="452" rx="24" ry="20" fill="{SKIN}"/>'
                f'<rect x="604" y="436" width="56" height="15" rx="7.5" fill="{SKIN}"/>'
                f'<rect x="588" y="418" width="14" height="28" rx="7" fill="{SKIN}" transform="rotate(-20 595 432)"/>')
    if pose == "wave":    # forearm up, open palm
        return (f'<path d="M446 470 Q532 452 552 352 L584 360 Q576 480 458 528Z" fill="{INK}"/>'
                f'<ellipse cx="570" cy="326" rx="30" ry="32" fill="{SKIN}"/>'
                + "".join(f'<rect x="{546+i*13}" y="{272 - (6 if i in (1, 2) else 0)}" width="12" height="44" rx="6" fill="{SKIN}"/>' for i in range(4))
                + f'<rect x="530" y="318" width="34" height="13" rx="6.5" fill="{SKIN}" transform="rotate(-30 547 324)"/>')
    # think: hand under the chin
    return (f'<path d="M446 700 L496 700 Q470 560 352 382 L326 402 Q430 560 446 700Z" fill="{INK}"/>'
            f'<ellipse cx="334" cy="372" rx="28" ry="24" fill="{SKIN}"/>'
            f'<rect x="306" y="352" width="44" height="14" rx="7" fill="{SKIN_SHADE}"/>')


def nyaya(hair="long", outfit="scarf", pose="point", expr="smile"):
    jhumka = "".join(f'<circle cx="{x}" cy="290" r="5" fill="{CORAL}"/><path d="M{x-9} 300 Q{x} 316 {x+9} 300Z" fill="{CORAL}"/>'
                     for x in (200, 400))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 700">'
            f'{hair_back(hair)}{torso(outfit)}'
            f'<rect x="274" y="340" width="52" height="96" rx="22" fill="{SKIN_SHADE}"/>'
            f'<ellipse cx="200" cy="266" rx="16" ry="24" fill="{SKIN}"/><ellipse cx="400" cy="266" rx="16" ry="24" fill="{SKIN}"/>'
            f'<ellipse cx="300" cy="256" rx="100" ry="114" fill="{SKIN}"/>'
            f'{hair_front(hair)}{jhumka}{face(expr)}{arm(pose)}</svg>')


VARIANTS = {"a": ("long", "scarf"), "b": ("bob", "kurta"), "c": ("bun", "pocket")}
POSES = [("point", "smile"), ("wave", "wink"), ("think", "think")]

if __name__ == "__main__":
    out = Path(__file__).parent
    for v, (h, o) in VARIANTS.items():
        for pose, expr in POSES:
            (out / f"nyaya-{v}-{pose}.svg").write_text(nyaya(h, o, pose, expr))
    print("written")
