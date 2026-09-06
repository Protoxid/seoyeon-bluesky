#!/usr/bin/env python3
"""
ig_publish.py — publish a finished reel to Instagram through Meta's own API.

    python ig_publish.py --video clips/r4_fit_door.mp4 --caption-file caps/r4.txt --dry-run
    python ig_publish.py --video clips/r4_fit_door.mp4 --caption-file caps/r4.txt

WHY THE OFFICIAL API AND NOT A BROWSER BOT. This is Meta's sanctioned
Content Publishing endpoint, not automation pretending to be a person. The
account status is currently clean and that is worth protecting; an unofficial
tool is the thing that puts it at risk, not this.

THE ONE AWKWARD REQUIREMENT: Instagram cURLs the file itself.
    "the media must be hosted on a publicly accessible server at the time of
     the attempt"
There is no byte upload. So the finished mp4 goes up to protoxiderpg.it over
FTP, Instagram fetches it once, and this script deletes it again. It is public
for the length of one fetch. Nothing is hosted permanently and no server runs.

TRIAL REELS ARE ON BY DEFAULT AND THEY COST NOTHING. `trial_params` with
graduation_strategy SS_PERFORMANCE means the reel goes to non-followers only,
stays OFF the profile grid, and Instagram promotes it to the grid by itself if
the numbers are good. At zero followers the reach is identical either way --
100% of views are non-followers regardless -- so the reach argument for trials
is empty. THE REAL BENEFIT IS THAT A FLOP NEVER LANDS ON THE GRID, and with
nine profile visits a week the grid is the conversion surface that matters.
Free, and it needs no decision from anyone. --no-trial turns it off.

SECRETS LIVE IN FILES, NOT IN THIS SCRIPT, and not in the shell history:
    ig_token.txt     long-lived access token
    ig_user_id.txt   the Instagram professional account id
    ftp_host.txt     three lines: host, username, password
    ftp_public.txt   the public URL base that maps to the FTP upload folder
Add all four to .gitignore. This script never prints a token.
"""
from __future__ import annotations
import argparse, ftplib, io, json, pathlib, re, subprocess, sys, time, urllib.error
import urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import ffbin                                            # noqa: E402

GRAPH = "https://graph.instagram.com"
VERSION = "v26.0"          # from Meta's own examples. Bump deliberately.
POLL_EVERY, POLL_MAX = 12, 25       # ~5 minutes, the documented ceiling

# Meta's published reel limits. A reel that violates one is rejected AFTER the
# upload and after the container build, which wastes the slowest part of the
# run, so they are checked here first.
MAX_MB, MIN_SECS, MAX_SECS = 300, 3, 90
MAX_IMG_MB = 8


def read(name: str) -> str:
    p = ROOT / name
    if not p.is_file():
        sys.exit(f"  ! missing {name} — see the docstring at the top of this file")
    return p.read_text(encoding="utf-8").strip()


def api(path: str, params: dict, post: bool = False) -> dict:
    url = f"{GRAPH}/{VERSION}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data if post else None,
                                 method="POST" if post else "GET")
    if not post:
        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read()[:600].decode(errors="replace")
        # NEVER echo the token back. A traceback lands in a log or a chat.
        sys.exit(f"  ! HTTP {e.code} on {path}: {body}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--caption-file", default=None)
    ap.add_argument("--caption", default=None)
    ap.add_argument("--no-trial", action="store_true",
                    help="publish straight to the grid instead of as a trial")
    ap.add_argument("--graduation", default="SS_PERFORMANCE",
                    choices=["SS_PERFORMANCE", "MANUAL"])
    ap.add_argument("--keep-remote", action="store_true",
                    help="do not delete the uploaded file afterwards")
    ap.add_argument("--anchor", type=float, default=0.70,
                    help="vertical crop anchor; the plan lists per-shot values")
    ap.add_argument("--i-picked-this", action="store_true",
                    help="confirm which render, when a shot has several")
    ap.add_argument("--force", action="store_true",
                    help="publish despite the gate")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    vid = ROOT / a.video if not pathlib.Path(a.video).is_absolute() else pathlib.Path(a.video)
    if not vid.is_file():
        print(f"  ! {a.video} not found")
        return 2

    # IMAGES ARE A DIFFERENT MEDIA TYPE AND A DIFFERENT FIELD. A reel is
    # media_type=REELS + video_url; a photo is image_url and NO media_type at
    # all. Sending REELS with a still is not a degraded post, it is a rejected
    # container -- and the first version of this script could only ever post
    # reels, which is half the week's content.
    #
    # AND META TAKES JPEG ONLY. Every render in content/ is a PNG, so a
    # straight upload would be refused after the file was already public. The
    # conversion happens here, to a temp file, at quality 95: this is the
    # publish copy, not the master, and the master stays untouched PNG.
    is_image = vid.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")

    # THE GATE. Every check here exists because something got published that
    # should not have been. None of them can judge whether a picture is GOOD --
    # that stays human -- but each catches a fact a machine can know.
    if is_image and not a.force:
        stop = []
        sid = re.sub(r"_[0-9a-f]{6}_\d+$", "", vid.stem)

        # 1. AMBIGUITY IS NOT A DEFAULT. w2_studio_mirror had two renders and
        #    the operator was told "pick one" in prose; the arbitrary one went
        #    out. A script that guesses between two candidates guesses wrong
        #    half the time, and the half it gets wrong is public.
        sibs = sorted(vid.parent.glob(f"{sid}_*_*.png"))
        if len(sibs) > 1 and not a.i_picked_this:
            stop.append(f"{len(sibs)} renders exist for {sid}: "
                        + ", ".join(q.name for q in sibs)
                        + "\n      Pass --i-picked-this once you have opened "
                        "them and chosen.")

        # 2. STALE MEANS THE PROMPT MOVED ON. The white iPhone 15 Pro became
        #    canon after these renders were made, so they show a black phone --
        #    a continuity break nobody would spot in a thumbnail, and exactly
        #    what a hash comparison catches for free.
        try:
            import weekly_prep as WP
            for pool, (_m, _a, _f, outdir) in __import__("console").POOLS.items():
                if (ROOT / outdir).resolve() != vid.parent.resolve():
                    continue
                hashes, why = WP.prompt_hashes(pool)
                if why:
                    print(f"  (staleness not checked: {why})")
                elif hashes.get(sid) and f"_{hashes[sid]}_" not in vid.name:
                    stop.append(
                        f"{vid.name} was rendered from an OLDER prompt "
                        f"(current is {sid}_{hashes[sid]}_*). Re-render, or "
                        f"--force if the change does not affect this shot.")
        except Exception as e:                           # noqa: BLE001
            print(f"  (staleness not checked: {e})")

        for msg in stop:
            print(f"  ! {msg}")
        if stop:
            print("\n  nothing published")
            return 1

    # Conversion goes through publish_prep.py, which already handles sRGB, the
    # size targets and the per-shot CROP ANCHOR. A naive PIL convert -- which
    # is what this did first -- throws the anchor away, and the plan says in
    # writing that the mirror selfie needs 0.35 or it takes the top of her head
    # off. The pipeline already knew; the publisher did not ask.
    tmp_jpg = None
    if is_image and vid.suffix.lower() != ".jpg":
        tmp_jpg = ROOT / "_prep" / f"_pub_{vid.stem}.jpg"
        tmp_jpg.parent.mkdir(exist_ok=True)
        r = subprocess.run(
            [sys.executable, str(ROOT / "publish_prep.py"), str(vid),
             "--anchor", str(a.anchor), "--out", str(tmp_jpg.parent)],
            capture_output=True, text=True)
        # publish_prep writes into a KIND SUBFOLDER with a POOL PREFIX --
        # _prep/feed/week2__w2_studio_mirror_1b34a6_1.jpg, not the flat name
        # this first looked for. The mismatch reported "publish_prep failed"
        # for a run that had succeeded, which is the worst kind of error
        # message: it blames the wrong component and sends you to debug a
        # script that is working. Search the tree and match on the stem.
        made = sorted((q for q in tmp_jpg.parent.rglob("*.jpg")
                       if vid.stem in q.stem),
                      key=lambda q: q.stat().st_mtime)
        if r.returncode or not made:
            print(f"  ! publish_prep failed: {(r.stderr or r.stdout)[-300:]}")
            return 1
        tmp_jpg = made[-1]
        print(f"  prepared  {tmp_jpg.name}  anchor {a.anchor}")
        vid = tmp_jpg
    mb = vid.stat().st_size / 1e6
    secs = 0.0 if is_image else ffbin.duration(vid)
    cap = a.caption or (pathlib.Path(a.caption_file).read_text(encoding="utf-8")
                        if a.caption_file else "")

    print(f"  file      {vid.name}  {mb:.1f} MB  {secs:.1f}s")
    print(f"  caption   {len(cap)} chars")
    # Trial reels are a REEL feature. Asking for one on a photo is not a
    # smaller request, it is an invalid container, so it is forced off here
    # rather than left to fail at Meta.
    trial = (not a.no_trial) and not is_image
    print(f"  mode      " + ("photo post" if is_image else
                             ("grid post" if not trial
                              else f"TRIAL REEL ({a.graduation})")))

    bad = []
    if is_image:
        if mb > MAX_IMG_MB:
            bad.append(f"{mb:.1f} MB is over Meta's {MAX_IMG_MB} MB image limit")
    else:
        if mb > MAX_MB:
            bad.append(f"{mb:.0f} MB is over Meta's {MAX_MB} MB reel limit")
        if secs and not MIN_SECS <= secs <= MAX_SECS:
            bad.append(f"{secs:.1f}s is outside {MIN_SECS}-{MAX_SECS}s")
    if len(cap) > 2200:
        bad.append(f"caption is {len(cap)} chars, over 2200")
    for b in bad:
        print(f"  ! {b}")
    if bad:
        return 1

    host, user, pw = (read("ftp_host.txt").splitlines() + ["", "", ""])[:3]
    base = read("ftp_public.txt").rstrip("/")
    remote = f"r_{int(time.time())}_{vid.name}"
    public = f"{base}/{remote}"
    print(f"  url       {public}")

    # THE DRY RUN HAS TO CHECK EVERYTHING A DRY RUN CAN CHECK. The first
    # version read ftp_host.txt and ftp_public.txt before this point and the
    # Instagram token and account id only AFTER the upload -- so a missing or
    # expired token passed the dry run and then failed on the real run, with a
    # 13 MB file already sitting on a public URL. A check that stops short of
    # the thing most likely to be wrong is theatre.
    #
    # The token call below is a plain GET. It costs nothing, it is not a
    # publish, and it is the only way to learn BEFORE uploading that the token
    # is live, that it belongs to the right account, and that the app's
    # permissions actually resolved -- which is the step this setup kept
    # failing on.
    have_ig = (ROOT / "ig_token.txt").is_file() and (ROOT / "ig_user_id.txt").is_file()
    if not have_ig:
        print("  ! ig_token.txt / ig_user_id.txt not found yet — the FTP half "
              "is configured, the Instagram half is not")
    if a.dry_run:
        if have_ig:
            ig, tok = read("ig_user_id.txt"), read("ig_token.txt")
            d = api(ig, {"fields": "username,account_type", "access_token": tok})
            print(f"  token OK   @{d.get('username', '?')}  "
                  f"({d.get('account_type', '?')})")
        print("\n  DRY RUN — nothing uploaded, nothing published")
        return 0

    # 1. up to the host, so Meta has something to fetch
    with ftplib.FTP(host, user, pw, timeout=120) as ftp:
        with open(vid, "rb") as fh:
            ftp.storbinary(f"STOR {remote}", fh)
    print("  uploaded")

    try:
        ig, tok = read("ig_user_id.txt"), read("ig_token.txt")
        params = ({"image_url": public, "caption": cap, "access_token": tok}
                  if is_image else
                  {"media_type": "REELS", "video_url": public,
                   "caption": cap, "access_token": tok})
        if trial:
            params["trial_params"] = json.dumps(
                {"graduation_strategy": a.graduation})
        cid = api(f"{ig}/media", params, post=True).get("id")
        if not cid:
            print("  ! no container id returned")
            return 1
        print(f"  container {cid} — encoding")

        # 2. wait for Meta to finish fetching and transcoding. A container that
        #    is not FINISHED cannot be published, and publishing early is the
        #    most common failure in every example of this flow.
        state = ""
        for _i in range(POLL_MAX):
            time.sleep(POLL_EVERY)
            state = api(cid, {"fields": "status_code",
                              "access_token": tok}).get("status_code", "")
            print(f"    {state}")
            if state in ("FINISHED", "ERROR", "EXPIRED"):
                break
        if state != "FINISHED":
            print(f"  ! container ended as {state or 'unknown'} — not published")
            return 1

        # 3. publish
        pid = api(f"{ig}/media_publish",
                  {"creation_id": cid, "access_token": tok}, post=True).get("id")
        print(f"\n  published  media id {pid}")
        if trial:
            print("  Trial reel: non-followers only, not on the grid.")
            print(f"  graduation {a.graduation}"
                  + (" — Instagram promotes it if the 72h numbers are good."
                     if a.graduation == "SS_PERFORMANCE" else
                     " — promote it yourself in the app when you have looked."))
    finally:
        # 4. the file existed to be fetched once. Take it down either way --
        #    including when publishing failed, which is exactly when a stray
        #    public copy would otherwise be left behind and forgotten.
        if not a.keep_remote:
            try:
                with ftplib.FTP(host, user, pw, timeout=60) as ftp:
                    ftp.delete(remote)
                print("  remote file deleted")
            except Exception as e:                       # noqa: BLE001
                print(f"  ! could not delete {remote}: {e}")
                print(f"    Remove it by hand: {public}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
