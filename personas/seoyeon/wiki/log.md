# Decision log

Append-only. Newest last. Corrections stay visible — they are the most valuable
content in the project.

## 2026-08-30 · reorganised as an LLM Wiki
Documents into `wiki/domains/{persona,pipeline,publishing}`, superseded into
`wiki/archive/`, nineteen spent one-shot scripts into `_trash/`. Code stayed at
the root: 58 modules import by bare name and every documented command says
`python outside.py`. The convention is for knowledge, not for code.

## 2026-08-30 · back to Kie.ai from fal.ai
fal bills output tokens AND input tokens per reference frame: $0.3106 a
referenced image against Kie's flat $0.09, and $0.5304 a plate against $0.09.
Spent $1.52 on fal, which bought all four room plates plus two week images —
permanent assets, not a loss. Kept `fal_api.py` unused.

## 2026-08-30 · seedream stays retired
Reintroduced it as a plate renderer because Kie's gpt text-to-image enum lacks
4:3. Wrong: it is retired for "pulls editorial", the exact failure this project
exists to avoid, and the constraint did not apply — every plate was already
generated. `--model seedream` is no longer a valid choice.

## 2026-08-30 · the flat is a one-room, not an apartment
The first flat plates showed a double-vanity bathroom and a separate bedroom.
Her live grid and captions say a small one-room on three months of savings.
Regenerated. The old set is in `locations/_superseded_rich_flat/` for a later
chapter.

## 2026-08-30 · her phone is a white iPhone 15 Pro
It rendered differently every frame because nothing in the canon said what it
was. As the CAMERA it stays invisible; as a PROP it is pinned with `phone=True`.

## 2026-08-30 · reels rebuilt around why anyone watches one
A photo-dump slideshow is a mood board and earns nothing at zero followers.
Every reel now does exactly one of: teaches, beautiful, relatable, funny, or
shows her off. Gemini Omni 1.1 Flash is free in Google Flow on AI Plus, so all
video attempts go there first and paid video is the exception.

## 2026-08-30 · first reel built under the new rules
R2, the washing machine. Two stills, four burned-in text beats, a push-in and a
hard cut on the punchline. $0. Two defects caught in build: ffmpeg drawtext does
NOT wrap, so a 38-character line was drawn off the right edge and a clipped line
still looks like a line; and the frame-check sheet sorted its samples wrongly,
which nearly hid it. Text is now pre-wrapped with a hard 30-character check that
raises, and drawtext reads from textfile= so nothing has to survive two layers
of escaping.

## 2026-08-30 · washing-machine reel pulled, not published
Operator: nobody cares, they skip it. Right. Relatable content needs an
existing relationship — a stranger has no reason to care that an appliance
broke, and she is not even in the frame. Reel order at zero followers is HER,
then beauty, then teaching, then relatable. Reel 01 is now her moving in the
studio, generated in Flow, which doubles as the free identity test.

## 2026-08-30 · Omni Flash refuses her; H3 is the only route for her face
Third provider to refuse a photorealistic human reference. The free Flow tier
is not lost, it is SCOPED: everything without her face still generates there at
no cost. Her face in motion goes to H3 on Kie, first-frame conditioned, about
$0.68 for eight seconds. Noted as a single-supplier risk — providers are
tightening likeness policy, not loosening it.

## 2026-08-30 · the fit check, and Seedance re-enters for no-face shots only
R4 built in ComfyUI after Kie i2v came back with a push-in, no tattoo and floaty
motion — the API has no negative field, so "no zoom" sat in the positive prompt
and summoned a zoom. ComfyUI has a real negative box. Seedance had been ruled
out for REFUSING HER FACE; a POV clip has no face, which is the operator's own
observation and reopens it. It produced the acceptable studio clip, and is not
the default: 24s costs $2.04 on H3 and $7.56 on Seedance 720p, and the plate is
an image so the cheaper "with video input" rate does not apply.

## 2026-08-30 · R1 restructured to voice-over, which removes the hardest problem
Her voice runs across the whole reel; only clip 1 shows her and she does not
speak in it. Nothing has to sync, so the mouth can never make the wrong shapes,
and clips 2-4 have no face at all — no refusal risk, no identity drift. The
studio plate was regenerated first because `locations/studio.png` turned out to
be a DOMESTIC LIVING ROOM with one reformer in it, and every POV clip references
the studio.

## 2026-08-30 · the voice, three rounds of tuning by argument
Sleepy, then a YouTube presenter, then robotic — each round one adjective or one
number changed on a hunch. `voice_matrix.py` then rendered the same line nine
ways for two-thirds of a cent and the answer was the middle of the stability
range, the one place never tried. Rule 146. The deeper fault: the brief asked
for imperfection ("uneven, words running together, trailing off"), and a TTS
told to be uneven produces artefacts. Rule 148.

## 2026-08-31 · R1 published as text-only. 118 views, 6s watch, zero engagement
The voice failed QC on all three counts at once — accent not Korean, unnatural,
robotic — so R1 went out as captions over the clips with no voice, and R1 was
unscheduled rather than moved to a new date.
6s on 23.5s is 26% retention, and the first caption ran 0.3s to 6.5s: the
average viewer left exactly when the first tip was about to appear. A TITLE CARD
is free on a voiced cut, where the hook is spoken while the picture moves, and
is six seconds of dead air without one. Rule 147. **Zero saves is not evidence
the tips are bad** — almost nobody reached them.
Not reposted: recycled content is down-ranked and a re-run could not be
attributed. The re-cut waits for a slot where its numbers mean something.

## 2026-08-31 · the persona cannot make an offer a viewer could act on
"Seven in the morning, Tuesdays and Thursdays, Seongsu" reached four files
before the operator asked what it was. It is an invitation to a class that does
not exist. "The 7am slot is the one nobody wants" is a story about her; a class
time is an appointment. Rule 149, and it binds everything downstream including
Fanvue.

## 2026-08-31 · documentation brought current for handoff
`handoff.md` rewritten from scratch — the previous one was dated 24 Aug, cited
CLAUDE.md as 1,305 lines when it is 345, listed Qwen and Seedream as live, and
pointed at a HANDOFF.md that no longer exists at root. Four superseded reel
documents moved to `wiki/archive/` with banners saying what replaced them.
Index and overview rebuilt.

## 2026-08-31 · Higgsfield MCP connected, and the first spend went to the wrong clip
The Higgsfield connector is an MCP server on the account, not a REST API: it
lives only in the chat session, `kie_api.py` cannot reach it, and nothing was
added to the project folder.

VERIFIED BY SPENDING, not by reading:
  * `minimax_h3` is in the catalog with `image_references` — real ref2v, 9:16,
    4-15s, **2K only** (no 768P), `batch_size` 1-4.
  * Cost is **2 credits per second**, not per generation: 5s = 10 credits,
    7s = 14. Preflight with `get_cost: true` before every call.
  * The MCP INTERCEPTS PROMPTS. The first call generated nothing — it returned
    a `preset_recommendation` proposing the "IN THE DARK" template instead.
    Every call from this project must pass `declined_preset_id` and render
    literally, or the audited prompt is silently replaced by a template.
  * Neither the cloud container nor `device_bash` can reach S3 or CloudFront.
    Uploads go through `media_import_url` off a live Kie URL; downloads happen
    in the operator's PowerShell. The MCP does not remove that round trip.
  * The subscription's headline "UNLIMITED" models are **web-only** — not
    available over MCP. Plus is EUR 49/mo (EUR 29 annual) at the endpoint, not
    the EUR 35 in the offer screenshot.

THE ERROR, AND IT COST THE WHOLE BALANCE. Asked for "a next clip", the agent
read `build_r1.py`, saw slot 4 holding a duplicate of `r1_c1`, and filled it —
r1_c4_socks, cut from 7s to 5s to fit 10 credits. But R1's picture had ALREADY
PUBLISHED that morning as `r1_text.mp4`. Voicing footage that is already up is
a repost, and 118 views says the footage was not the thing worth buying. The
unbuilt scheduled item was R4, Sat 5. **Rule: pick the next shot from the
schedule, never from a gap in a build script.** A missing entry in a CLIPS list
is a code smell, not a priority.

Balance now 0. The clip renders fine and survives as studio stock.

## 2026-09-01 · w2_desk_rain killed, R3 unheld and moved, the river loses its plate
THREE SHOTS CHANGED AND ONE RULE CAME OUT OF IT.

`w2_desk_rain` was `n_desk_late` in different weather — both a table from
above, a laptop, a fan on the floor, one bare knee at the bottom edge, no face,
mid-afternoon. The two used different plates, so the same flat rendered as two
flats. **A continuity break costs more than a repeat: it un-teaches the room
the grid has been building.** THE TEST IS NOT "is the story different", IT IS
"would a scrolling stranger see a photograph they have already seen".
Replaced by `w2_rain_awning` — she is caught in the first rain since June
outside the convenience store, laughing, wet. Tuesday afternoon was already
specced as *errands, convenience store*; the structure was right and the shot
was ignoring it. It also puts a face in Tuesday, which otherwise had two
no-face object shots and no person in it at all.

`pov_river_walk` released from hold. The gate was "build it only if the studio
POV performs" and it did not — R1 got 118 views and nothing after them. Built
because it was asked for, with the objection recorded rather than swallowed: a
faceless beauty clip is the most oversupplied thing on the platform. So her
SHADOW and her SHOES are in it. **A walking POV where the walker never appears
is drone stock.**

NO PLATE FOR THE RIVER, and the operator was right. A plate exists so a place
can be THE SAME place every time — the studio has to be recognisable or the
account stops being one person's life. The Han path is forty kilometres long.
**A plate is for recurrence, not for realism**, and applying the studio's rule
to a place that does not have it cost a plate entry and a refusal to run.
The price of dropping it is that the text carries the place: say only the delta
means cut what the REFERENCES show, and with no reference the river IS the
delta. Prompt now 2,337 chars, and that is correct rather than bloated.

R3 moved Fri 4 -> Thu 3. Friday already carried `w2_river_steps` in the feed —
the same river at the same hour. Thursday evening is *"Han river path, walking"*
in week-structure.md, which is the shot, and the clip's story line already said
THU 19:00.

TOOLING, all three the same class of bug — a value hardcoded when there was
only one case:
  * `kie_api.text_video()` added. H3 had no plateless path: `ref_video()`
    raises on zero references and `video()` requires a first frame. That was
    the real reason the clip was held. **`H3_T2V` is INFERRED from the other
    two ids and is NOT verified** — Kie documents the mode but not the string.
    A wrong id fails at createTask before generating, so it costs a round trip.
  * `audit_video.py` had `n_refs=1` hardcoded for every POV clip and duly
    demanded a job for an Image 1 that is never sent. Now read off the clip.
  * `audit_video.NO_PERSON` only recognised empty rooms, so it wanted a skin
    block for a clip with no skin and a framing error for a clip with no face.
    Widened to accept an avoid list that excludes the body AND the face —
    narrow on purpose: hiding the face while showing bare arms still trips it.
  * `make_reel_text.py --set fit|pilates|river`. BEATS was one global holding
    the fit check's captions, so pointing it at any other clip silently burned
    "seoul in august is not a joke" over it. **An error that publishes rather
    than one that raises.** And `--fit` is WRONG for a one-card cut: it would
    stretch R3's single card from 3.2s across the whole 7s reel.

## 2026-09-02 · 2K did not fix the plastic look, which is the useful half
R3 rendered on H3 text-to-video at 2K, $0.91 against $0.56 at 768P. Operator's
verdict: "still looks kinda bad". Paused, to resume tomorrow.

WHAT THAT BUYS. The plastic look had two candidate causes and they needed
different money spent on them:
  1. THE UPSCALE. Every clip until today was 768P stretched into a 1080x1920
     reel — about 40% up, and upscaling smooths exactly the pore texture and
     edge noise whose absence reads as plastic.
  2. THE MODEL PRIOR. Already written down here: a video model re-renders skin
     every frame and its own prior is glossy.
2K is a direct test of (1) and it did not fix it, so (1) is largely out and the
weight moves to (2). **A negative result that eliminates a cause is worth its
price** — this one narrows the engine grid before it is run rather than after.

CONSEQUENCE FOR THE GRID. The planned four arms were H3@768P, H3@2K,
seedance_2_0_mini, wan3_0. Drop the H3@2K arm — it has now been run and
answered. Spend the arm somewhere else: gemini_omni_flash_1_1 or kling3_0,
both reference-capable in the Higgsfield catalog.

PRICES, PREFLIGHTED FREE ON HIGGSFIELD (5s, 9:16, credits):
    minimax_h3 10 · seedance_2_0_mini 12.5 · wan3_0 12.5 ·
    seedance_2_0 22.5 · seedance_2_5 32.5
**The Seedance cost objection was priced on the wrong Seedance.** "Too
expensive" was formed on 2.5 at $0.315/s on Kie, 3.7x H3. The reference-capable
budget variant is 1.25x. And Higgsfield is NOT cheaper than Kie for H3 itself —
about EUR 0.49 per 5s at Plus rates against $0.40 on Kie. Its value is model
access and batch_size, not price.

ALSO: this was the first clip run through `kie_api.text_video()`, whose model
id `minimax-h3/text-to-video` was INFERRED from the other two. A video came
back, so the id appears correct — CONFIRM IT EXPLICITLY next session rather
than inheriting this sentence as fact.

## 2026-09-03 · R4 attempted four times on Higgsfield. H3 is the plastic.
FOUR RENDERS, 39 CREDITS SPENT, NO KEEPER — but the failures were different
each time, which is the only reason the night was worth anything.

1. seedance_2_5, 6s 720p, 3 refs — NEVER RAN. `get_cost` quoted 39 credits
   happily and submit returned "Requires plus plan or higher."
   **`get_cost` IS A PRICE CHECK, NOT AN ENTITLEMENT CHECK.** A successful
   preflight does not mean a runnable call. Virality Predictor is gated the
   same way ("requires basic plan"). THE CREDITS ARE NOT THE PRODUCT, THE PLAN
   IS — that belongs in the subscription maths.
2. minimax_h3_max, 6s 768p, 3 refs, 15 credits — "it's not her". The refs WERE
   attached; the API echoed all three ids back. H3 Max is the FAST variant and
   fast variants are distilled, which is what you lose identity to first.
   Also: the catalog LISTING showed only start_image/end_image for this model
   and the model RECORD showed image_references. **`models_explore list` is a
   summary; only `get` is the contract.**
3. minimax_h3, 6s 2K, 3 refs, 12 credits — dark, noisy throughout, skin tone
   pushed darker. MY ERROR, AND IT WAS ALREADY WRITTEN DOWN. The prompt carried
   "flat contrast, low saturation, visible sensor noise in the shadows" from
   make_fit_clip's LENS block. make_clip1.py had cut those exact words for that
   exact symptom and its docstring says the fix is deletion, not brightening
   adjectives. I read that docstring the same session and shipped the clause
   anyway. "in the shadows" limited nothing; the noise came out global.
   Now removed from make_fit_clip.py. NOT removed from make_clips234.py —
   those are rooms with no face, the texture line earned itself there, and
   nobody has called them dark. **Same words, opposite verdicts, because the
   shots are not the same shot.**
4. minimax_h3, 6s 2K, 3 refs, 12 credits, prompt cut 2051 -> 960 chars — clean
   exposure, still plastic skin. CONFOUNDED, AND SAY SO: simplifying dropped
   the skin block, which is not description but the documented exception —
   a video model re-renders skin every frame and its prior is glossy, so the
   still's matte skin is NOT inherited. Asked for "only attire and movement",
   I cut the one line written to fight this.

THE VERDICT ON H3 STANDS ANYWAY. Plastic at 768P with a plate, at 2K text-only,
and at 2K ref2v — with the skin block and without it. 2K already eliminated the
upscale. Prompting has not beaten the prior. **It is the model, and the next
lever is a different engine, not another sentence.**

BLOCKED THERE TONIGHT: 1 credit left, Seedance 2.5 needs Plus, and wan3_0 /
gemini_omni_flash_1_1 / kling3_0 are untested and may be gated too.

ALSO LEARNED: the `.url` sidecars are NOT a durable upload path — the Kie
tempfile links for a1_front and w2r_fit_door both 404 now. Anything older than
a few days has to go up from disk through the Higgsfield widget.

CANON TO SET: the phone in mirror shots is a WHITE IPHONE 15 PRO. It is visible
in every mirror shot she will ever post and a phone that changes model between
reels is the same continuity break as a flat that changes rooms. Not yet
written into w2r_fit_door or body_block.txt.

## 2026-09-03 · Kling 3.0 wired but not run. Out of credits both sides.
`kie_api.kling_video()` written against Kie's published contract, plus
`make_fit_clip.py --engine kling`. NOT YET RUN — no credits. Everything below
is verified from docs or from a real 422, not inferred.

THE CONTRACT, AND IT IS NOT H3'S:
    model        kling-3.0/video
    first frame  image_urls   -- an ARRAY (first + last), NOT H3's
                 first_frame_url string
    duration 3-15 · aspect 16:9|9:16|1:1 · mode std|pro|4K · sound bool
    multi_shots  REQUIRED. Omitting it returns 422 "multi_shots cannot be
                 empty". Kie's doc lists it as a true/false field like the
                 others, which reads as "omit for the default". IT HAS NO
                 DEFAULT. **A documented field with a stated type is still not
                 an optional field — the doc describes the shape, the API
                 enforces it, and only one of those is the contract.**
                 It also selects the prompt field: false -> `prompt`,
                 true -> `multi_prompt` [{prompt, duration}]. Pinned false, so
                 nobody can set it true and have multi_prompt silently dropped.
    NO negative_prompt field at all.
    NO PUBLISHED PRICE — not on the model page, not in the docs. The kling
    path therefore REFUSES to run without an explicit --budget: a cap computed
    from a rate nobody knows is a decoration, not a guard.

THE PROMPT WAS REBUILT TO KLING'S OWN PUBLISHED FORMULA:
    Subject + Subject Description + Subject Movement + Scene
    (+ Camera Language + Lighting + Atmosphere)
  * SUBJECT LEADS. The draft opened on the scene with the person arriving late.
  * **THE AVOID LIST IS DELETED.** H3 has a designated elements-to-avoid
    section its guide tells you to use. Kling documents no negative handling
    and Kie exposes no field for it. Pasting H3's nineteen negatives across a
    model boundary is the same error class as assuming a field name transfers
    within a family. THE FAILURE MODES CHANGED GRAMMAR INSTEAD: for a model
    with no negative handling a negative must be restated as a POSITIVE FACT —
    not "avoid a second person" but "she is the only person in the room,
    holding one phone, and her reflection is the only place she appears".
    **A model can render a fact. It cannot render an absence.**
  * NO [0-2 SECONDS] BRACKETS. The guide says movement should be
    "straightforward" and warns the models "are not sensitive to numbers".
    Tension noted honestly: Kling's own 3.0 guide shows an example that DOES
    time camera moves to the second. Beats are not forbidden, just not what
    the prompt guide asks for, and this shot is three small actions.
  * Kling says keep visual content "as simple as possible" — say only the
    delta, arriving from the other direction. 866 chars vs H3's 2,051.

TWO BUGS FOUND WHILE WIRING, BOTH WOULD HAVE PUBLISHED RATHER THAN RAISED:
  * `make_fit_clip.py` picked the still with `sorted(glob)[-1]`. The names
    carry a HEX HASH, not a counter, so sorting them sorts noise: the
    regenerated w2r_fit_door_279a0c sorts BEFORE the superseded _36013e, and
    the script would have animated the old frame — the cropped tank with the
    bare ribcage. Now sorted by mtime. **A "latest" that is alphabetical is
    not a latest.**
  * The tattoo. Canon puts it on the LEFT RIBCAGE below the bra line, and
    Kling takes a first frame and NO body reference, so the clip can only show
    what the frame shows. The outfit decision therefore happens at the STILL
    stage, not in the video prompt. w2r_fit_door's top changed from a cropped
    ribbed tank to a plain white t-shirt tucked into the shorts. Still
    regenerated as w2r_fit_door_279a0c_1.png.

CANON SET: the phone in mirror shots is a WHITE IPHONE 15 PRO, now in
w2r_fit_door's text. Not yet in body_block.txt.

STATE: R4 unbuilt. Kling ready to run the moment there is Kie credit.

## 2026-09-04 · publishing automated end to end, and four ways it went wrong
Instagram now posts from this machine without a browser. Meta's own Content
Publishing API, not a bot: the account status is clean and that is what an
unofficial tool would risk.

THE CHAIN, all of it verified live:
    register.it "Spazio Web" (STATICO) + FTP user syeonpub
      -> Cloudflare CNAME www -> onstatic-it.setupdns.net, PROXIED, SSL Flexible
      -> ig_publish.py uploads, Meta cURLs it once, the file is deleted
    Meta app "syeon-publisher-IG", use case "Gestisci i messaggi e i contenuti
    su Instagram", permission instagram_business_content_publish added BY HAND
    (it is optional for that use case and the "add all required" button does
    NOT include it), @syeon.hn added as Instagram tester.
    token check: GET /{ig-user-id} -> @syeon.hn (MEDIA_CREATOR)
NO APP REVIEW NEEDED: review is only required for apps used by people without
a role on the app. Confirmed in Meta's own app-creation doc.
DNS WAS THE REAL BLOCKER, not hosting: the domain's nameservers are Cloudflare
and the zone was EMPTY -- protoxiderpg.it did not resolve at all. register.it's
own DNS panel is not authoritative for it and could never have fixed it.

FOUR FAILURES, ALL MINE, ALL NOW GATED:
  1. PUBLISHED THE WRONG RENDER. Two stills existed for w2_studio_mirror and I
     picked one arbitrarily while telling the operator in prose to "check
     first". PROSE IS NOT A CHECK. ig_publish.py now REFUSES when a shot has
     more than one render until --i-picked-this says a human chose.
  2. THE BLACK PHONE WAS NOT A CANON GAP. I concluded the white iPhone needed
     writing into 22 shots at ~$2 of re-renders, and wrote that into CLAUDE.md.
     WRONG: outside.py has carried a shared PHONE block since 30 Aug. I had
     read the shot lists and not the assembler. The black phone came from
     publishing the STALE render, which predates that block.
     **When a render disagrees with canon, suspect the render's age before
     rewriting the canon.**
  3. THE DRY RUN CHECKED THE EASY HALF. FTP config was read before the dry-run
     return, the Instagram token only after the upload -- so a bad token passed
     the dry run and would have failed with 13 MB already public. The dry run
     now does a free GET that proves the token, the account and the scope.
  4. "publish_prep failed" WHEN IT HAD SUCCEEDED. It writes to _prep/feed/ with
     a pool prefix; my glob looked for a flat name. **An error message that
     blames the wrong component is worse than none** -- it sends you to debug a
     working script.
  Also: my first converter was a naive PIL call that threw away the per-shot
  CROP ANCHOR. publish_prep.py already did sRGB, sizing and the anchor. The
  plan says in writing that the mirror selfie needs 0.35 or it loses the top of
  her head. The pipeline knew; the publisher did not ask.

UNRESOLVED, AND FLAGGED RATHER THAN GUESSED: the two machines disagree on the
current prompt hash for w2_studio_mirror -- Windows says 04576e, the mounted
filesystem says 1b34a6, and 1b34a6 is what is on disk and what the operator
confirmed is correct. console.pool_facts caches on the mtimes of both the shots
file and outside.py, which looks sound. Until this is understood **treat every
staleness verdict as advisory** and expect to use --force. Worth twenty minutes
fresh: that gate is what stands between us and publishing the wrong file again.

CORRECTION TO MY OWN CLAIM: I said Instagram's feed minimum is 4:5 and that the
3:4 renders would be cropped. publish_prep.py says the opposite in writing --
3:4 is taller in feed and takes more screen, do not export 4:5 -- and the post
went through untouched. The claim was mine and unverified. Disregard it.

SCHEDULED TASKS NOW LIVE (both bound to the operator's machine):
  * Sun 18:00  weekly_prep.py -> contact sheet + plan.md. SPENDS NOTHING.
  * hourly :31 publish_queue.py --due. Posts only what is already in the queue.
    THE QUEUE IS THE CONSENT: an item is there because a human looked at the
    render and added it. The schedule decides WHEN, never WHETHER. A scheduler
    pointed at clips/ would publish the 82% that get discarded.

## 2026-09-04 · prompt hash divergence resolved, pipeline hardened, R4 assembled

THE HASH DIVERGENCE ROOT CAUSE AND FIX. The mystery where Windows reported hash
04576e while the mounted filesystem and disk file showed 1b34a6 for
w2_studio_mirror was diagnosed and resolved.
  * CAUSE: `console._dry_run` shells out to `outside.py --dry-run` and reads
    stdout. On Windows without forced UTF-8 mode, Python subprocess stdout
    defaults to the Windows ANSI codepage (cp1252). Prompt blocks carry Unicode
    em-dashes (`—` / U+2014, byte 0x97 in cp1252), which decoded with
    `errors="replace"` into `\ufffd`. The corrupted prompt string yielded hash
    04576e. Meanwhile, `outside.py` generation in memory encodes natively as
    UTF-8, producing 1b34a6. Four other week 2 prompts carrying em-dashes
    were similarly misreported as stale.
  * FIX: `outside.py` now reconfigures `sys.stdout` and `sys.stderr` to UTF-8
    on startup. `console.py` passes `-Xutf8`, `PYTHONUTF8=1`, and UTF-8 encoding
    in `_dry_run` and `Run.start`.
  * CONSEQUENCE: `w2_studio_mirror` prompt hash is consistently 1b34a6.
    `ig_publish.py --dry-run` passes the staleness gate immediately without
    needing `--force`.

LOCKED SHOT CONTINUITY IN WEEKLY_PREP.
  * `w2_kitchen_sun` and `w2_broken_machine` were documented in outside.py as
    passed QC and accepted without re-render, but lacked `locked=True`.
  * `n_mirror_dress` in `grid_shots.py` (published week 1) was also missing
    `locked=True`.
  * `weekly_prep.py survey()` was checking hashes without respecting
    `locked`. Updated to match `console.py` ("locked beats stale"). Stale count
    across all pools is now cleanly 0.

STALE CLASS INVITATION CUT.
  * `make_voice.py` line 71: replaced "Seven in the morning, Tuesdays and
    Thursdays, Seongsu." with "Honestly, you'll be fine." per Playbook 149.

AUDIT SCRIPTS HARDENED.
  * `audit.py`: removed obsolete attempt to import retired `make_clip`.
  * `audit_video.py`: removed conflicting duplicate check on `make_fit_clip.PROMPT`,
    aligned Kling rules (no H3 bracketed timestamp requirement), and updated
    `make_fit_clip.py` mirror eyeline and framing. `audit_video.py` now reports
    0 issues.

PIPELINE RESILIENCE & SUBPROCESS DECODING.
  * `kie_api.py`: `Kie.__init__` now assigns `self.key = api_key` so `upload()`
    does not fail when `KIE_API_KEY` is not in `os.environ`.
  * `ffbin.py`: hardened all subprocess decode calls with `encoding="utf-8", errors="replace"`.
  * `publish_queue.py`: added delegation for `--anchor`, `--i-picked-this`, and
    `--force` flags to `ig_publish.py`.
  * `make_reel_text.py`: uses `tempfile.TemporaryDirectory` for clean scratch
    cleanup, and guarantees a silent stereo AAC audio track when the source clip
    has no audio, preventing Meta container rejection.

ASSETS.
  * Rejected slideshow artifact `clips/r1_five_things.mp4` moved to `_trash/`.
  * `clips/r4_fit_door.mp4` assembled from candidate raw render
    `clips/r4_fit_door_v3_phonemoved.mp4` (6.04s, 595 KB, audio track included).
    Verified with `ig_publish.py --dry-run` as valid Trial Reel.

## 2026-09-04 · Fanvue prompts overhauled to canon, audit cleared

All 21 prompts in `fanvue_shots.py` (`fv_bed_shirt` through `fv_banner`) brought
into full compliance with project realism and canon rules:
  * **NAME THE PLACE**: Grounded all interior/flat shots in "her flat in Seongsu,
    Seoul", balcony shot in "the small balcony of her flat in Seongsu, Seoul",
    and pool shots in "a rooftop pool in Seoul". Cleared all 21 `[NO PLACE NAMED]`
    violations reported by `audit.py`.
  * **Story premises**: Authored grounded `story=` premise strings answering
    the 4 core questions (time/place, who/camera, mood, why this photo exists)
    for all 21 shots. `audit.py` now reports `fanvue/story: 21/21 have a premise`.
  * **Canon camera spec**: Replaced obsolete "Shot on an iPhone 16 Pro" with
    "Shot on an iPhone 15 Pro" (or front camera).
  * **Prop pinning**: Added `phone=True` on `fv_towel_mirror` and `fv_mirror_set`
    where the handset is visible in the reflection, ensuring the canonical white
    iPhone 15 Pro with scuffed clear case is attached via `outside.PHONE`.
  * **Audits**: Total standing audit debt dropped from 65 to 44 issues (Fanvue
    debt reduced to 0). Verified with `python outside.py --fanvue --list` (21 shots, ~$1.89)
    and `--dry-run`.
  * **Test generation**: Rendered `fv_bed_shirt` (`5d52f9`, 6.9 MB) and
    `fv_towel_mirror` (`4382f8`, 7.9 MB) via Kie (`gpt-image-2-image-to-image`,
    2K tier, $0.18 total spend). Both passed `bone_gate.py` structural checks.
    Visual QC confirmed: canonical white iPhone 15 Pro with clear case faithfully
    rendered in the fogged mirror, natural matte skin, correct freckling and
    Seongsu flat lighting.

## 2026-09-04 · Plan B executed: SFW Exclusive Pool established, Fanvue retired

Strategic pivot away from adult-dominated platforms (Fanvue) to protect persona
canon and conversion efficiency:
  * **The Friction**: Fanvue is an adult subscription platform where paying
    subscribers expect explicit nudity. Publishing SFW suggestive content (towel,
    lingerie, loungewear) triggers high churn, refund disputes, and credit-card
    adult billing stigma.
  * **The Pivot**: Preserves Seoyeon's SFW/intimate canon ("mostly alone, mostly fine",
    pilates instructor in Seoul) by routing exclusive content to native
    **Instagram Subscriptions** (primary, 1-tap in-app billing) and aesthetic
    **Patreon** supporter tiers.
  * **Codebase Transition**:
    - Created `exclusive_shots.py` holding all 21 private shots (`ex_bed_shirt`
      through `ex_banner`) with full canon compliance.
    - Marked `fanvue_shots.py` as `RETIRED = True`.
    - Updated `outside.py` to support `--exclusive` (with `--fanvue` as alias),
      routing to `content/exclusive`.
    - Migrated test renders to `content/exclusive/ex_bed_shirt_5d52f9_1.png` and
      `content/exclusive/ex_towel_mirror_4382f8_1.png`.
    - Updated `profile.md`, `handoff.md`, and `playbook.md` to reflect Plan B.
    - Audits verified: `exclusive/story: 21/21 have a premise`, 0 duplicate IDs,
      standing debt holds cleanly at 44 legacy items.
## 2026-09-05 · Concept 2 built: 7am studio unlock (continuous motion POV reel)

Built full-motion handheld studio walkthrough replacing still slideshows:
- **Footage**: `clips/rC_studio_7am.mp4` (9.0s, 1080x1920, 24 fps, 7.4 MB). Continuous handheld walking POV down the center aisle of Seongsu studio in morning light. Categorised under Rule 129 as **Beautiful / Atmosphere**.
- **Visual QC**: Verified mirror reflections (Rule 109) — camera angle keeps phone and operator outside the mirror view. No face in frame (Rule 107), eliminating likeness refusal and identity drift risk.
- **Narrative Hooks**:
  - Beat 1 (0.2–2.8s): *"the 7am slot is the one / nobody wants"* (Rule 147: hook fires at 0.2s, no dead air / title card).
  - Beat 2 (3.0–5.8s): *"so it is the one they / give the trainee"*
  - Beat 3 (6.0–8.8s): *"i have the whole room / for forty minutes"*
  - Typography: Segoe UI Bold (56pt), centered, y=240/315 in Instagram UI safe zone, black 55% background pillbox for high contrast.
- **Audio & Caption**: Ambient stereo AAC track attached. Caption in `caps/rC_studio.txt` grounded in Seoyeon's actual life (Rule 149), capped at exactly 5 hashtags (Rule 56).
- **Gate Check**: Passed `ig_publish.py --dry-run` targeting `@syeon.hn` as a Trial Reel (`SS_PERFORMANCE`).

