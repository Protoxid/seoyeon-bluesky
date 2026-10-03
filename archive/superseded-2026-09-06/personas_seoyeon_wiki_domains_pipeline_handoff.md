# SEOYEON — HANDOFF
Last updated **Sunday 31 August 2026, evening.** Read this, then `CLAUDE.md`.

If you are a model picking this up cold: **`CLAUDE.md` is the operative
document** — it loads automatically and carries the absolute rules plus a
149-line index. The reasoning behind each line is
[`playbook.md`](playbook.md), ~2,600 lines, read on demand. Every rule was paid
for by a failure that cost money or a post. Do not re-derive them and do not
assume any is arbitrary.

---

## 1. WHAT THIS IS

An AI persona, **Seo-yeon Han** (`@syeon.hn`), run as an Instagram account
intended to convert to a paid Fanvue subscription. The operator is **Shade**,
in Italy, working on **Windows** in PowerShell. The persona is a 25-year-old
woman living alone in Seoul. Every image and clip is generated.

**Rule one, in the operator's words: if the photorealism misses, the whole
thing closes.**

## 2. THE OPERATOR'S STANDING RULES — verbatim, non-negotiable

> "nothing based on assumption. research, get informed, evaluate, apply.
>  i want your 100% honesty."

> "make sure all your informations come from reliable sources and not from
>  random people stating stuff on reddit"

> "you can't make errors and fix them AFTER i tell you. we're wasting credits"

> "always double check what you have, i don't want to tell you again"

> "if people look at the pictures and see it looks too artificial and
>  unrealistic, or that blatantly screams 'AI', our mission fails."

> "I'm investing money here and I expect earnings and a return."

Hard constraints: **no local LoRA training. No men anywhere in her life. Do not
host anything — it works locally.** Minimal video spend until revenue.
**Seedream is retired and must never be reintroduced.** Seedance works but is
not the default, on cost.

## 3. WHERE THINGS RUN — read this before trying anything

| | |
|---|---|
| **Generations** | The operator's PowerShell. **Not** the assistant's shells. |
| `device_bash` | The operator's machine, **no network at all**. Edit and inspect files here; never generate. |
| cloud `Bash` | The assistant's container. Reaches PyPI only — no Kie, no ElevenLabs, no HuggingFace. |
| API keys | `kie_key.txt`, `elevenlabs_key.txt`, `fal_key.txt`, `voice_id.txt`. **They never leave the machine.** |
| ffmpeg | Resolved by `ffbin.py` — PATH, winget, scoop, choco, `C:\ffmpeg`, imageio-ffmpeg. Survives a missing `ffprobe`. |

Two whole classes of bug came from ignoring this: every ffmpeg script worked in
development and died in PowerShell, first because `ffprobe` was not on PATH and
then because a Windows drive-letter colon splits an ffmpeg filtergraph.
`ffbin.filter_path()` handles the second.

## 4. CURRENT STATE — 31 Aug 2026

| | |
|---|---|
| Instagram | `@syeon.hn`, **0 followers** |
| Week 1 | 12-shot grid, published |
| Week 2 | 11 stills generated, captioned, **posting Mon 31 → Sun 6** |
| **Mon 31 published** | `w2_subway_am` (feed) + **R1 text version** (reel) |
| **R1 result** | **118 views · 6s average watch on 23.5s · 0 likes, saves, shares, profile visits** |
| R4 the fit check | **NOT BUILT.** Scheduled Sat 5. See §7. |
| Subscriber Exclusive (Plan B) | 21 shots defined in `exclusive_shots.py`, 2 generated (`ex_bed_shirt`, `ex_towel_mirror`), 100% audit pass |

### What R1's numbers mean, precisely
6s on 23.5s is **26% retention**. The first caption ran 0.3s→6.5s, so the
average viewer left exactly when the first tip was about to appear. **This says
nothing about whether the tips are good** — almost nobody reached them. Fixed
in `fix_r1_timing.py` (first tip at 0.2s, count folded into the cards, reel
trimmed to ~19s). **Not reposted, deliberately**: recycled content is
down-ranked and a re-run could not be attributed.

## 5. THE STACK

Everything through **Kie.ai** except the voice, which is **ElevenLabs direct**.

| role | model | notes |
|---|---|---|
| **stills, default** | `gpt-image-2-image-to-image` | ref field **`input_urls`** · **$0.09 flat** |
| no-person stills | `gpt-image-2-text-to-image` | ratio enum only `1:1 3:4 2:3 9:16` — narrower than i2i |
| video, her face | `minimax-h3/reference-to-video` | `reference_image_urls` ≤9 · 4–15s · 768P/2K · ~$0.08/s |
| video, first frame | `minimax-h3/image-to-video` | `first_frame_url` · **never send `end_image_url`** |
| video, no face | `bytedance/seedance-2-5` | `reference_image_urls` ≤2 · **720p = $0.315/s no-video-input** |
| voice | `eleven_multilingual_v2` | `POST /v1/text-to-speech/{voice_id}`, `xi-api-key`, raw audio back |
| retired | Seedream · fal · `make_fit_clip.py` (i2v) · `make_voice_design.py` (MiniMax) | |

**A field name belongs to the PROVIDER AND THE VERSION, never to the family.**
The playbook's note that "Seedance takes `image_urls`" was true of an older
Seedance elsewhere and is false here. Print the payload against the published
schema before spending.

**Seedance costs 3.7× H3** for the same clips: 24s is $2.04 on H3 and $7.56 on
Seedance 720p. Its two published rates are not interchangeable — "with video
input" is cheaper only when you supply a reference VIDEO. A plate is an image.

**Three providers refuse her face** (Seedance ref2v, Omni Flash, one other).
H3 is the only route for her in motion — single-supplier risk, and providers
are tightening likeness policy, not loosening it. Anything without her face has
many options, including free local ComfyUI.

### ComfyUI
The operator runs ComfyUI locally and it has produced the best results twice.
It is **free** and it has a **real negative-conditioning field**, which the Kie
API does not — so negatives move out of the prompt and into their own box.
`wiki/domains/publishing/reel-r4-comfyui.md` and `reel-r1-voiceover.md` carry
the positive/negative splits.

## 6. THE VOICE — unresolved, and the most likely next task

Failed QC on **all three counts at once**: accent not Korean, not natural,
robotic. That is the voice itself, not the settings — `stab-040` was the least
bad of nine matrix rows, which is not the same as good.

Three things went wrong and all three are mine:

1. **The brief asked for the robot.** "Relaxed and slightly uneven, some words
   run together, some trail off" — a TTS told to be uneven produces artefacts.
   See playbook 148.
2. **A designed voice is synthesised from a description; a library voice is a
   real human recording.** For accent authenticity that is not close.
   `find_voice.py` lists and auditions real Korean voices from the ElevenLabs
   library, and `--add` writes `voice_id.txt`.
3. **Three rounds of tuning by argument** before building a grid. Playbook 146:
   if the next step is "try X and tell me" and X is one value from a continuous
   range, the grid is cheaper than the conversation — on the FIRST round.

`eleven_v3` **is available on this account** (it rendered in the matrix) and has
delivery tags. Untried on a real script.

Delivery settings in `make_voice_el.py` are canon **for the old voice** and must
be re-auditioned against any new one.

## 7. WHAT IS OPEN, in the order it matters

1. **R4 is not built and it goes out Saturday.** The only fit-check file on
   disk is `r4_fit_door_raw.mp4`, the *bad* Kie i2v version. The good ComfyUI
   render is not in the project folder. Finish with
   `python make_reel_text.py --video <the good one> --out clips\r4_fit_door.mp4 --fit`
   — beats are written and width-checked.
2. **The voice.** §6.
3. **"seven in the morning, Tuesdays and Thursdays, Seongsu"** still appears in
   four files. It is an invitation to a class that does not exist. Playbook
   149. Proposed replacement: "honestly, you'll be fine".
4. **`clips/r1_five_things.mp4` is the SLIDESHOW** — the format rejected at the
   start of the project — sitting next to the real files with a similar name.
   Move to `_trash/`.
5. **Plan B SFW Pivot**: Retired `fanvue_shots.py` and established
   `exclusive_shots.py`. Fanvue is an adult-dominated ecosystem where SFW content
   causes subscriber churn. All 21 private/intimate shots (`ex_bed_shirt` through
   `ex_banner`) now route to Instagram Subscriptions / Patreon as SFW exclusive drops.
6. Standing debt: 44 prompts predating NAME THE PLACE (outside 37/54, week 5/6,
   reel_frames 2/4). The exclusive pool is 100% clean (0/21 debt, 21/21 premises).

## 8. FILE MAP — what is live

    CLAUDE.md            operative layer, 149-rule index. Mirrored to C:\AI-Project\
    AGENTS.md            how an agent works here
    wiki/                index, overview, log, domains/, archive/

    outside.py           the generator. --grid --week --week2 --w2reel --plates
                         --exclusive (alias --fanvue) --reel-frames · --only --all --dry-run
    week2_shots.py       11 feed shots + REEL (w2r_fit_door)
    grid_shots.py week_shots.py exclusive_shots.py reel_frames.py    other pools
    pov.py               PLATES (5) + POV clips. plate_path() resolves ids
    masters.py           master frames
    kie_api.py           Kie client: generate, video, ref_video, seedance,
                         upload, download, cost functions
    ffbin.py             finds ffmpeg/ffprobe; filter_path() for filtergraphs
    audit.py             FREE pre-flight on every still pool. Run before spending
    audit_video.py       the same rules against VIDEO prompts
    drift_gate.py bone_gate.py    identity gates
    publish_prep.py      -> 1080x1440 3:4 sRGB JPEG

    make_clip1.py        R1 clip 1 — her, silent, H3 ref2v
    make_clips234.py     R1 clips 2-4 — POV. --engine h3|seedance
    build_r1.py          assembles R1. --check (free) · --no-voice
    make_reel_text.py    burn beats onto a clip. --fit rescales to real duration
    make_reel_r1.py make_reel_r2.py reel_build.py    older reel builders
    phone_audio.py       puts a TTS voice in a room. --preset dry|studio|room|hall
    make_voice.py        SCRIPT + SPEECH, the words she says
    make_voice_el.py     ElevenLabs TTS, canon delivery settings
    design_voice_el.py   ElevenLabs Voice Design, two-step: design then --save
    find_voice.py        audition REAL library voices. --add writes voice_id.txt
    voice_matrix.py      one line, nine settings, listen and pick
    console.py           local control panel, stdlib only, port 8765

    master/a face · master/c body (carries the TATTOO) · master/h back
    content/{grid,week2,week2_reel,plates,outside} · locations/ · publish/ · clips/
    _trash/ spent scripts · _to_delete/ files device_bash cannot remove

## 9. THE FIVE THINGS THAT GO WRONG MOST

**Say only the delta.** Text describing what a reference already shows competes
with the pixels, and the pixels should win. But *delta* means what is NOT in
the reference — a still cannot carry photographic texture into a VIDEO, so
cutting "flat contrast, visible sensor noise" from a clip prompt produced
footage that looked like a render. Cut what the reference shows, not until it
is short.

**Name the place, never the category.** "A market" renders Western. Unless a
plate is attached, in which case the place arrives as pixels and naming it
again is re-description.

**The camera is not an object in the scene.** "Held in one hand" and "the
person holding the phone is not visible" both put a phone in frame — a denial
still names the thing. But **"handheld" is fine**: it describes motion, and
banning it produced glide-cam footage that read as a render. Describe the
viewpoint and the framing errors it causes.

**A number in a prompt is a claim about the world.** "Three reformers" rendered
three, in a corridor, reading as somebody's spare room. A typical class is
8–12 people.

**Verify the artefact, not the exit code.** And when a sweep edits many files,
grep for the REPLACEMENT text: a mechanical edit once replaced every duration
check with `0.0`, and a guard that always passes is invisible.

## 10. VERIFIED EXTERNAL FACTS

**Instagram.** The feed does not show posts to non-followers — Reels and
Explore are the discovery surfaces, the grid is a conversion surface. Sends per
reach worth 3–5× likes. Trial Reels are shown ONLY to non-followers. Recycled
content is down-ranked. Hashtags capped at 5 and are a search signal, not
reach — **caption keywords do the discovery work**. Grid 3:4, 1080×1440 sRGB
JPEG, "Original" crop. Creator account, not Business.

**Pilates, for the teaching content.** A typical group class is 8–12 people and
a mid-size studio runs 10–12 reformers. Grip socks required at most studios.
Fewer springs is often harder. DOMS lands in inner thighs and between the
shoulder blades, settling around class four. **"Sitting shortens the hip
flexors" is unsupported** and "imprint vs neutral" is a live disagreement
between schools — both were in an early draft and both were cut.

**Fanvue.** 80/20. $10–30 performs best. Earnings pend 7 days. 20+ posts before
launch.

**Seoul.** Late August to 38°C. Winter wardrobe not before November.

**Still assumptions:** follower-to-sub conversion, how long a reel takes to
find an audience cold, whether this positioning beats fitness, churn.

## 11. THE META-FAILURE

**Writing a rule and then breaking it in the same session.** It has happened
with overhead light, camera logic, prompt length, the would-she-post test, the
camera-as-object rule, and say-only-the-delta. Twice a checker was written that
encoded the over-correction and made the mistake permanent while looking
principled.

**Re-read the relevant playbook section before writing prompts. Do not trust
memory of it.** And when a check fires, decide whether the prompt or the
checker is wrong before changing either — six of the first eight audit flags
were the checker's fault, and the same run missed a real fault I already knew
about.

---

## Publishing (added 4 Sep 2026)

**Instagram posts from this machine now, without a browser.** Meta's own
Content Publishing API — not an unofficial tool, which is what would put a
clean account status at risk.

### The chain

    a finished file in clips/ or content/
      -> publish_prep.py   sRGB, sizing, the per-shot CROP ANCHOR
      -> FTP upload to register.it's static space
      -> Meta cURLs the public URL ONCE
      -> the remote file is deleted, including when publishing failed
      -> media id returned

Meta will not accept bytes; the file has to be publicly fetchable at the moment
of the attempt. That is the only reason hosting is involved at all, and it is
public for the length of one fetch.

**DNS lives at Cloudflare, not register.it.** The domain's nameservers are
Cloudflare's and register.it's DNS panel is not authoritative for it. `www` is
a CNAME to `onstatic-it.setupdns.net`, proxied, with SSL mode Flexible —
register.it's static space has no certificate for the domain, so Cloudflare
terminates HTTPS. If the site ever stops resolving, look there, not at
register.it.

### The two commands

    python ig_publish.py --video <file> --caption-file <file> --dry-run
    python publish_queue.py --add <file> --at "2026-09-05 18:40" --caption-file <file>

The dry run costs nothing and proves the token, the account and the scope with
a plain GET. Run it first, always.

### THE QUEUE IS THE CONSENT

Nothing in this project publishes by itself. A file is posted because a human
opened it and put it in `queue.jsonl`; the hourly scheduled task decides WHEN,
never WHETHER. **Do not point a scheduler at a folder** — 82% of what this
pipeline generates is discarded, and a folder-watcher publishes the discards.

### The gate, and why each check exists

`ig_publish.py` refuses to publish when:

* **a shot has more than one render** and nobody has said which. On 4 Sep two
  stills existed for `w2_studio_mirror` and the arbitrary one went out. The
  operator had been told in prose to check first. **Prose is not a check.**
  `--i-picked-this` is a human confirming, not a formality.
* **the render predates its current prompt.** This is the check that would have
  caught the black phone: `outside.py` has carried a shared white-iPhone
  `PHONE` block since 30 Aug, and the published still predated it. The canon
  was never missing. **When a render disagrees with canon, suspect the
  render's age before rewriting the canon.**

`--force` overrides both. It is currently needed more often than it should be —
see the open item below.

### Reels vs stills

A reel is `media_type=REELS` + `video_url`; a still is `image_url` and **no
media_type at all**. Meta accepts **JPEG only**, and every render here is PNG,
so conversion is not optional. Trial reels (`trial_params`, graduation
`SS_PERFORMANCE`) are a reel-only feature and are forced off for stills — a
trial on a photo is an invalid container, not a smaller request.

### OPEN, and it matters

**The two machines disagree on prompt hashes.** Windows reports a different
current hash for `w2_studio_mirror` than the mounted filesystem does, and the
one on disk is the one the operator confirmed correct. `console.pool_facts`
caches on the mtimes of both the shots file and `outside.py`, which looks
right, so the cause is not yet known. **Until it is, treat every staleness
verdict as advisory.** That gate is the thing standing between this pipeline
and publishing the wrong file again, so it is worth twenty minutes.
