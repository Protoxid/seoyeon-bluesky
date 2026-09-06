#!/usr/bin/env python3
"""audit.py — read every prompt the pipeline can build and flag known failures.

Cheaper than a generation. Run before any batch.
"""
import importlib, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from content import SCENES, PROP, REF_SETS, ROLE, IPHONE_LEAN, ALLOWED_ASPECTS

from locations import PLACES as ROOMS
import session as S

# things a person picks up / holds — if one appears in BOTH the room line and
# an action, you get two of them (the two-mug bug)
PROPS = ("mug","cup","glass","book","phone","towel","bowl","plate","bottle",
         "brush","kettle","laptop","magazine","blanket","pillow","cushion",
         "matcha","coffee","tea","paperback","board","mat","lamp","spring",
         "block","vase","plant","stool","chair")
NEG   = (" no ","not ","without","never ","n't ")
COND  = ("only when","only if","when she","if she","unless")

# Reviewed false positives: the action takes the object FROM the place the room
# puts it, which is coherent rather than duplicated. Anything not listed here
# has not been reviewed — do not add to this set to silence a real collision.
ALLOW = {
    ("kitchen", "bowl"),    # she takes a bowl FROM the shelf of bowls
    ("studio",  "mat"),     # she rolls up the mat that is against the wall
    ("bedroom", "lamp"),    # she reaches for the bedside lamp
    ("reformer","mat"),     # scene key is 'reformer', place is 'studio'
}

issues = 0
def flag(scene, kind, msg):
    global issues; issues += 1
    print(f"  [{kind}] {scene}: {msg}")

for k, sc in SCENES.items():
    place = sc.get("place")
    room  = ROOMS.get(place, "")
    ward  = sc["wardrobe"]
    acts  = sc["actions"]
    prop  = PROP.get(place, "")

    # 1. prop collision: room line and an action both introduce the same object
    for p in PROPS:
        if re.search(rf"\b{p}s?\b", room, re.I):
            for i, a in enumerate(acts):
                if re.search(rf"\b{p}s?\b", a, re.I) and (k, p) not in ALLOW:
                    flag(k, "DUPLICATE PROP",
                         f"'{p}' is in the room line AND action {i} -> two of them")

    # 2. wardrobe collision: room or action names clothing the wardrobe also sets
    for garment in ("cardigan","top","dress","shirt","robe","jumper","sweater"):
        if re.search(rf"\b{garment}\b", room, re.I):
            flag(k, "WARDROBE IN ROOM", f"room line mentions '{garment}'")

    # 3. negation and conditionals anywhere in the shared blocks
    for label, txt in (("room", room), ("wardrobe", ward), ("camera", prop)):
        low = " " + txt.lower()
        for n in NEG:
            if n in low: flag(k, "NEGATION", f"{label} contains '{n.strip()}'")
        for c in COND:
            if c in low: flag(k, "CONDITIONAL", f"{label} contains '{c}'")

    # 4. two measurements in one sentence
    for label, txt in (("room", room), ("camera", prop)):
        for sent in re.split(r"(?<=[.!?])\s+", txt):
            if len(re.findall(r"\d+\s*(?:cm|mm|m\b|metre)", sent, re.I)) > 1:
                flag(k, "TWO MEASUREMENTS", f"{label}: {sent[:70]}")

    # 5. depth-of-field contradiction against the lens line
    dof = re.search(r"out of focus|blurred|bokeh|shallow depth", prop, re.I)
    if dof and "deep focus" in IPHONE_LEAN:
        flag(k, "DOF CONFLICT", f"camera says '{dof.group()}', lens says deep focus")

    # 6. device named in the camera line
    if re.search(r"\bphone\b|\btripod\b|\bcamera is\b", prop, re.I):
        flag(k, "DEVICE NAMED", "camera line names the device -> it appears in frame")

    # 6b. anything that invites legible text
    import itertools
    for label, txt in (("room", room), ("camera", prop),
                       *(("action %d" % i, x) for i, x in enumerate(acts))):
        m = re.search(r"\bsign\b|signage|menu|hangul|handwriting|written|"
                      r"lettering|label|poster|logo|newspaper", txt, re.I)
        if m:
            flag(k, "INVITES TEXT",
                 f"{label} says '{m.group()}' — models render Korean as broken "
                 f"pseudo-syllables and a native speaker sees it instantly")

    # 7. missing pieces
    if not room:  flag(k, "MISSING", f"no room text for place '{place}'")
    if not prop:  flag(k, "MISSING", f"no camera position for place '{place}'")
    for n in REF_SETS[sc["framing"]]:
        if n not in ROLE: flag(k, "MISSING", f"no role defined for reference {n}")

    # 8. session frames vs their derived KEEP clause
    for i, f in enumerate(S.SESSIONS[k]["frames"]):
        keep = S.keep_for(f)
        low = f.lower()
        if "light" in keep and re.search(r"light|shadow|sun|evening|later in the day", low):
            flag(k, "KEEP CONFLICT", f"frame {i} changes the light but KEEP holds it")
        if "her face" in keep and re.search(r"face not visible|from behind|back to the camera", low):
            flag(k, "KEEP CONFLICT", f"frame {i} hides her face but KEEP holds it")
        if len(f) > 220:
            flag(k, "LONG FRAME", f"frame {i} is {len(f)} chars — edits want one change")

    # 9. prompt length
    hero_len = len("\n\n".join([acts[0], room, ward, prop, IPHONE_LEAN]))
    if hero_len > 1200:
        flag(k, "LONG HERO", f"{hero_len} chars — short beats long with references")


# ---------------------------------------------------------------- outside.py
# Different shape from the room scenes: no hero, no plate, but a camera-mode
# and a hairstyle per shot, both of which can contradict the action.
def check_outside():
    """Checks run on the FINAL authored text, since there are no fields left.

    Every prompt in outside_shots.py is one written description, so field-vs-
    field contradictions cannot happen by construction. What can still go wrong
    is what the words themselves invite.
    """
    from outside_shots import SHOTS
    import outside as O

    for d in SHOTS:
        sid, txt = d["id"], d["text"]
        low = " " + txt.lower()

        for n in NEG:
            if n in low:
                flag(sid, "NEGATION", f"'{n.strip()}' — mentioning summons")
        for c in COND:
            if c in low:
                flag(sid, "CONDITIONAL", f"'{c}'")

        m = re.search(r"\bsign\b|signage|menu|hangul|handwriting|lettering|"
                      r"label|poster|logo|newspaper|written", txt, re.I)
        if m:
            flag(sid, "INVITES TEXT", f"'{m.group()}'")

        m = re.search(r"shelving|shelves|crate|packaging|\bbox(es)?\b|\bcans?\b|"
                      r"magazine|book(shelf|case)|noticeboard|whiteboard|"
                      r"receipt|ticket|carton", txt, re.I)
        if m:
            flag(sid, "PRINT-BEARING OBJECT",
                 f"'{m.group()}' comes back with writing on it")

        # a selfie occupies one hand, and the extended arm holds the only phone
        selfie = "arm's length" in low or "front camera" in low
        if selfie:
            m = re.search(r"arms folded|arms crossed|both hands|forearms|"
                          r"both arms|elbows on|"
                          r"hands in (her )?pockets|hands in (her )?sleeves",
                          txt, re.I)
            if m:
                flag(sid, "SELFIE HANDS", f"'{m.group()}' gives her a third arm")
            if txt.lower().count("phone") > 1:
                flag(sid, "TWO PHONES", "phone named more than once")

        # every prompt must answer: who took this, and on what
        if not re.search(r"arm's length|front camera|taken by|set down|"
                         r"reflection|mirror", txt, re.I):
            flag(sid, "NO CAMERA", "nobody is holding the camera")
        if not re.search(r"iphone|front camera", txt, re.I):
            flag(sid, "NO LENS", "no device or lens stated")
        # "pores and fine hair visible" is not a hairstyle. Demand a style.
        if not re.search(r"hair (down|up|in a|pulled|loose|half-up|coming|"
                         r"stuck|caught)|ponytail|\bbun\b|claw clip|beanie|"
                         r"through (the back of )?a .*cap", txt, re.I):
            flag(sid, "NO HAIR", "hairstyle unstated — it will default forever")
        if not re.search(r"wearing|coat|jumper|sweater|sweatshirt|top|knit|"
                         r"roll-neck|blazer|jacket|shirt|dress|beanie|tank|vest|sundress|cotton|linen|"
                         r"shorts|leggings|set\b", txt, re.I):
            flag(sid, "NO WARDROBE", "clothing unstated")

        if len(txt) > 950:
            flag(sid, "LONG", f"{len(txt)} chars")

    ids = [d["id"] for d in SHOTS]
    if len(set(ids)) != len(ids):
        flag("outside", "DUPLICATE ID", "shot ids are not unique")
    texts = [d["text"] for d in SHOTS]
    if len(set(texts)) != len(texts):
        flag("outside", "DUPLICATE TEXT", "two shots share a prompt")


def check_prompts_deep(SHOTS=None, label="outside"):
    """Classes the keyword checks cannot see: geometry, physics, continuity.

    Takes a pool. It used to import outside_shots and check only that, which
    meant grid_shots, week_shots and reel_frames were generated with NO deep
    checking at all — the newest prompts were the least examined ones.
    """
    if SHOTS is None:
        from outside_shots import SHOTS
    from model_schemas import SCHEMAS
    # Validate each shot against the enum of the model it will ACTUALLY route
    # to, not against whatever model this check was first written for. It said
    # Seedream while the renderer was gpt-image-2. That happened to be harmless
    # -- the two i2i enums are the same eight ratios -- but gpt-image-2's
    # TEXT-to-image sibling only accepts four (1:1 3:4 2:3 9:16), and a no-face
    # shot with no limb goes to text-to-image. A 4:3 no-face shot would have
    # passed this audit and failed at the API, after paying to find out.
    ok_i2i = set(SCHEMAS["gpt-image-2-image-to-image"]["ratios"])
    ok_t2i = set(SCHEMAS["gpt-image-2-text-to-image"]["ratios"])

    for d in SHOTS:
        i, low = d["id"], d["text"].lower()
        # noface with no limb sends zero images, so it goes to text-to-image,
        # which is the narrower enum. See outside.py's `nf` branch.
        # A PLATE IS A REFERENCE, so a plated shot is image-to-image no matter
        # what else is true of it. outside.py prepends the plate and then picks
        # T2I only when the reference list came out empty. Judging a plated
        # shot against the text-to-image enum flags legal aspects as illegal.
        t2i = (d.get("noface") and not d.get("limb") and not d.get("plate"))
        allowed = ok_t2i if t2i else ok_i2i
        # A shot already GENERATED on another provider is not a pending API
        # call, and its aspect and tier were legal where it was made. Checking
        # it against today's provider flags it forever and teaches everyone to
        # skim past the report. Regenerating it would be worse: these four are
        # the continuity anchors and a re-render is a different room.
        if d.get("generated"):
            continue
        if d.get("aspect", "3:4") not in allowed:
            flag(i, "ASPECT", f"{d.get('aspect')} is not accepted by "
                              f"gpt-image-2 {'text' if t2i else 'image'}"
                              f"-to-image")
        if d["tier"] not in ("1k", "2k"):
            flag(i, "TIER", d["tier"])

        selfie = "arm's length" in low
        # A close portrait's action IS its expression, so only demand a body
        # verb from frames that are not close.
        close = re.search(r"very close|much closer|her face fill|^close,", low)
        if not close and not re.search(
                r"walking|running|sitting|standing|leaning|holding|reaching|"
                r"crouch|turning|turned|tipping|eating|laugh|looking|mid-|climbing|wiping|checking|"
                r"passes|shifting|giving|waiting|paying", low):
            # A TRAINING SET IS NOT A POST, AND THE RULES DIFFER. `lx_*` is
            # the LoRA dataset: the angle, expression and light sweeps
            # deliberately hold the pose still so that exactly ONE variable
            # moves per image. A verb there would add the variance the sweep
            # exists to exclude. The rule is right; this pool is not what it
            # was written for.
            if not d.get("noface") and "banner" not in i \
                    and not i.startswith("lx_") \
                    and "mirror" not in low:
                flag(i, "NO ACTION",
                     "no verb — the model defaults to a posed stand")

        if selfie and re.search(r"seen from (a way |a few steps |directly )?"
                                r"(back|behind|below)|small in the frame|"
                                r"full length|from below and behind", low):
            flag(i, "SELFIE REACH", "a selfie cannot show this distance or angle")
        if selfie and re.search(r"walking away|running away|back to the camera", low):
            flag(i, "SELFIE REACH", "selfie but she is facing away")
        if re.search(r"taken by (somebody|the person|whoever)", low) and \
                ("set down" in low or selfie):
            flag(i, "TWO CAMERAS", "two people are holding the phone")
        if re.search(r"her reflection|caught in a shopfront window|in the mirror",
                     low) and not re.search(r"mirror|window|glass", low):
            flag(i, "NO MIRROR", "reflection with nothing to reflect in")
        if re.search(r"empty room|stairwell|gym|restaurant|cafe", low) and \
                re.search(r"\bwind\b|breeze", low):
            flag(i, "INDOOR WIND", "wind indoors")
        if "bare feet" in low and re.search(r"street|park|river|market", low):
            flag(i, "BAREFOOT", "bare feet outdoors")
        # The back of her head does not render well — hair goes to mush.
        if re.search(r"seen from directly behind|from behind so the back of "
                     r"her head|back of her head and shoulders fill", low):
            flag(i, "BACK OF HEAD", "back-facing hair renders badly — turn her")
        if len(re.findall(r"hair (?:down|up|in a|pulled|loose|half-up)", low)) > 1:
            flag(i, "HAIR TWICE", "hairstyle described more than once")
        # The model already defaults to a glass-skin specular sheen; asking
        # for shine on top of it is how every frame got a highlighted face.
        m = re.search(r"shiny|sheen|glow|dewy|glossy|luminous|radiant", low)
        if m and "faint natural sheen" not in low:
            flag(i, "SHINE", f"'{m.group()}' compounds the default glass-skin "
                             f"highlight — outside.SKIN handles this globally")
        for frag in ("flat hdr contrast", "low saturation", "fine noise"):
            if low.count(frag) > 1:
                flag(i, "REPEATED", f"'{frag}' appears twice")


def check_variety():
    from outside_shots import SHOTS
    from collections import Counter
    import re as _re

    def bucket(txt, pats):
        for name, pat in pats:
            if _re.search(pat, txt, _re.I):
                return name
        return "other"

    CAMS = [("selfie", r"arm's length|front camera"),
            ("mirror", r"reflection|mirror"),
            ("friend", r"taken by"),
            ("propped", r"set down")]
    HAIRS = [("bun", r"\bbun\b"), ("ponytail", r"ponytail"),
             ("clip", r"claw clip"), ("cap", r"\bcap\b"),
             ("tucked", r"tucked behind"), ("down", r"hair down|waves")]

    n = len(SHOTS)
    for name, counts, cap, least in (
            ("camera", Counter(bucket(d["text"], CAMS) for d in SHOTS), 0.62, 4),
            ("hair", Counter(bucket(d["text"], HAIRS) for d in SHOTS), 0.45, 5)):
        print(f"\n  outside/{name}: {len(counts)} distinct over {n}")
        for v, c in counts.most_common():
            print(f"    {c:>3}  {'#'*c:<14} {v}")
        top, c = counts.most_common(1)[0]
        if c / n > cap:
            flag(f"outside/{name}", "IMBALANCE",
                 f"'{top}' is {c}/{n} ({c/n:.0%}), over {cap:.0%}")
        if len(counts) < least:
            flag(f"outside/{name}", "TOO FEW", f"{len(counts)} distinct")

    cams = Counter(bucket(d["text"], CAMS) for d in SHOTS)
    selfie = cams.get("selfie", 0) + cams.get("mirror", 0)
    print(f"\n  outside/selfie family: {selfie}/{n} ({selfie/n:.0%})")
    if selfie / n < 0.45:
        flag("outside/camera", "TOO FEW SELFIES",
             f"{selfie}/{n} — the front selfie should be the majority outdoors")


try:
    check_outside()
except Exception as e:                      # outside.py optional
    print(f"  [SKIP] outside.py not checked: {e}")


# ---------------------------------------------------------------- variety
# Two of the three worst defects so far were DISTRIBUTION problems, invisible
# in any single prompt and obvious in a table: six outfits with ten shots in
# the same coat, and two extra frames repeated across all seven rooms.
# A per-prompt checker can never see those, so imbalance is an ISSUE here.
try:
    check_prompts_deep()
except Exception as e:
    print(f'  [SKIP] deep check: {e}')

try:
    check_variety()
except Exception as e:
    print(f"  [SKIP] variety not checked: {e}")

# ---------------------------------------------------------------- story
# Every picture has to answer four questions before it is written: where she
# went, who she was with, what mood she was in, and why this photo exists at
# all. Camera angle, wardrobe, expression and framing are CONSEQUENCES of those
# answers, not independent choices — which is why a shot assembled from fields
# can be plausible in every part and incoherent as a whole.
# The premise is an AUTHORING tool and is NOT sent to the model: naming an
# emotion produces a performance of it. It exists to generate the physical
# details, and those are what go in `text`.
# Coverage is reported rather than flagged while the back catalogue is
# backfilled. Once every shot carries one, make this an issue.
def check_stories():
    # SAME DISCOVERY AS check_all_pools(). This function had its own separate
    # hand-maintained list, and week2 was missing from that one too — one hole
    # per registry, which is what happens when the same list is written twice.
    pools = []
    mods = sorted(q.stem for q in pathlib.Path(__file__).parent.glob("*_shots.py"))
    mods.append("reel_frames")
    for mod in mods:
        try:
            m = importlib.import_module(mod)
        except ImportError:
            continue                     # a pool file that is not there is fine
        except Exception as e:           # anything else is a BUG, not a gap
            print(f"  ! {mod} failed to import: {type(e).__name__}: {e}")
            continue
        if getattr(m, "RETIRED", False):
            continue
        base = mod[:-6] if mod.endswith("_shots") else mod
        for attr, suffix in (("SHOTS", ""), ("REEL", "_reel")):
            pool = getattr(m, attr, [])
            if pool:
                pools.append((base + suffix, pool))

    for name, pool in pools:
        if not pool:
            continue
        missing = [d["id"] for d in pool if not d.get("story")]
        have = len(pool) - len(missing)
        print(f"\n  {name}/story: {have}/{len(pool)} have a premise")
        if missing:
            print("     missing: " + ", ".join(missing[:12])
                  + (f" (+{len(missing)-12} more)" if len(missing) > 12 else ""))


# ------------------------------------------------------------- shared blocks
# `SKIN` carried "no wet highlight on the cheekbones or brow" for the entire
# project. Every authored prompt was checked for negations; the boilerplate
# appended to every one of them was not. A defect in a shared block is worth
# 54 defects in shot text, so it gets checked first and hardest.
def check_blocks():
    import importlib
    NEG = (" no ", " not ", "without", "never", "avoid", "n't", "nothing ")
    OK = {("make_clip", "ORIENT"), ("make_clip", "CAM_LOCK")}   # deliberate, H3
    for mod, names in (("outside", ["SKIN", "ARMS", "ROLES", "ROLES_BODY",
                                    "LENS", "LENS_FRONT", "FRONT"]),
                       ("make_clip", ["SKIN", "HOLD", "TEMPO", "ORIENT"])):
        try:
            m = importlib.import_module(mod)
        except Exception as e:
            print(f"  [SKIP] {mod} blocks: {e}")
            continue
        for n in names:
            v = getattr(m, n, None)
            if not isinstance(v, str) or (mod, n) in OK:
                continue
            for w in NEG:
                if w in v.lower():
                    flag(f"{mod}.{n}", "NEGATION IN SHARED BLOCK",
                         f"'{w.strip()}' — this ships in EVERY prompt")
                    break


# ---------------------------------------------------------------- all pools
# Every pool gets the deep checks, not just the original bank.
def check_all_pools():
    # DISCOVERED, NOT LISTED. The list used to be hardcoded, week2_shots was
    # never added to it, and the eleven shots that were actually generated and
    # queued to publish became the only pool nothing checked. A registry you
    # have to remember to update is a registry that goes stale; the next pool
    # is audited because it exists, not because someone remembered.
    pools = []
    mods = sorted(q.stem for q in pathlib.Path(__file__).parent.glob("*_shots.py"))
    mods.append("reel_frames")            # live pool, does not match the glob
    for mod in mods:
        try:
            m = importlib.import_module(mod)
        except ImportError:
            continue                     # a pool file that is not there is fine
        except Exception as e:           # anything else is a BUG, not a gap
            print(f"  ! {mod} failed to import: {type(e).__name__}: {e}")
            continue
        if getattr(m, "RETIRED", False):
            continue
        base = mod[:-6] if mod.endswith("_shots") else mod
        for attr, suffix in (("SHOTS", ""), ("REEL", "_reel")):
            pool = getattr(m, attr, [])
            if pool:
                pools.append((base + suffix, pool))

    # pov.PLATES IS A POOL AND WAS NEVER CHECKED. plate_studio was written at
    # 4:3 and tier "max" — both legal on fal, where the other four plates were
    # made, and 4:3 is rejected outright by gpt-image-2 TEXT-to-image, which is
    # where a reference-less plate routes on Kie. It passed the audit because
    # the audit was not looking at it. Same shape as week2 missing from the old
    # hardcoded list: the newest thing is the least examined one, every time.
    try:
        import pov as _pov
        if getattr(_pov, "PLATES", None):
            pools.append(("plates", _pov.PLATES))
    except ImportError:
        pass
    except Exception as e:                            # noqa: BLE001
        print(f"  ! pov failed to import: {type(e).__name__}: {e}")

    seen = {}
    for name, pool in pools:
        if name != "outside":
            check_prompts_deep(pool, name)
        for d in pool:
            i = d["id"]
            if i in seen:
                flag(i, "DUPLICATE ID", f"in both {seen[i]} and {name}")
            seen[i] = name
            # NAME THE PLACE. "market" gets a generic global market; "Seoul
            # market" got shop signage, handwritten won price cards and wet
            # ground. The default for any unqualified category is Western.
            import re as _re2
            # SAME EXEMPTION, OPPOSITE REASON. Naming the place stops a
            # published shot rendering as a generic Western market. A LoRA
            # dataset wants the opposite: plain, neutral, interchangeable
            # backgrounds, so the model learns HER FACE rather than welding it
            # to Seoul. The four `lx_env_*` shots that DO sit in the world name
            # their location anyway and are unaffected.
            if not i.startswith("lx_") and not _re2.search(
                               r"\b(Seoul|Seongsu|Euljiro|Hongdae|Gangnam|"
                               r"Itaewon|Han river|Korea|Korean)\b",
                               d["text"], _re2.I):
                flag(i, "NO PLACE NAMED",
                     "category without a location renders as generic Western")

            # noface must actually describe no person, or the model puts her in
            if d.get("noface") and not d.get("limb"):
                # WORD BOUNDARIES. Plain substring matching flagged "chair"
                # as "hair" — the check that exists to catch a person in a
                # no-person shot was firing on the furniture.
                import re as _r
                # "hair" is weak evidence on its own and it now has a THIRD
                # false positive: "hair claws" in a Daiso haul. It already
                # matched "c-hair" once. A person shot practically always says
                # she/her/woman as well, so hair only counts when it is not
                # part of an object.
                # Third and fourth false positives of the same family. The
                # check exists to catch a PERSON in a no-person shot; "hair
                # claws" and "a phone face down" are objects. It already fired
                # on "c-hair" once. Weak words need their object senses
                # excluded, or the check trains you to ignore it — which is
                # worse than not having it.
                HAIR_OBJ = _r.compile(
                    r"\bhair\s?(claw|clip|tie|band|dryer|brush|grip|pin)", _r.I)
                FACE_OBJ = _r.compile(r"\bface\s?(down|up)\b|surface", _r.I)
                for w in ("she", "her", "woman", "hair", "wearing", "face"):
                    if w == "hair" and HAIR_OBJ.search(d["text"]):
                        continue
                    if w == "face" and FACE_OBJ.search(d["text"]):
                        continue
                    if _r.search(rf"\b{w}\b", d["text"], _r.I):
                        flag(i, "NOFACE WITH A PERSON",
                             f"noface=True but text says '{w}'")
                        break
            # HER PHONE IS A PROP when it is visible. A shot that puts a
            # phone in the frame as an object, without phone=True, will get a
            # different handset every render — which is how two week-two shots
            # came back with phones that did not match.
            # The FLAG gates what is sent; this phrase search only nags. That
            # division is deliberate: a phrase search must never decide
            # whether an instruction goes out.
            import re as _r3
            if _r3.search(r"phone[^.]*clearly visible|a phone face (down|up)|"
                          r"phone[^.]*on the (table|counter|bed|floor)",
                          d["text"], _r3.I) and not d.get("phone"):
                flag(i, "PHONE NOT PINNED",
                     "a phone is visible in this frame but phone=True is not "
                     "set — the handset will differ every render")

            # a selfie flag that disagrees with the text is how rf_bed nearly
            # told a sleeping woman to reach for the lens
            phrase = "arm's length" in d["text"].lower()
            if "selfie" in d and d["selfie"] != phrase:
                note = "declared selfie, text lacks the phrase" if d["selfie"] \
                       else "declared not-selfie, text says arm's length"
                print(f"  [note] {i}: {note} — explicit flag wins")
    print(f"\n  pools checked: {', '.join(n for n, _ in pools)}")


try:
    check_all_pools()
except Exception as e:
    print(f"  [SKIP] pools: {e}")

try:
    check_blocks()
except Exception as e:
    print(f"  [SKIP] shared blocks: {e}")

try:
    check_stories()
except Exception as e:
    print(f"  [SKIP] story check: {e}")

print(f"\n  {issues} issue(s).")
