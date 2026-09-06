"""
reel_frames.py — 9:16 first frames for the day-214 Reel.

WHY THIS FILE EXISTS. Take 1 and take 2 both went reference-to-video: the model
re-derived her face and body from the master stack every frame. That is how the
ribcage tattoo ended up mirrored and how shot 5 stopped being her. Nothing we
learned in the stills pipeline survives that route, because none of it is in
the pixels the video model starts from.

First-frame conditioning keeps it. Frame 1 IS a still we generated, looked at,
and accepted. The video model only has to move it.

A first frame determines the output frame, so these are authored at 9:16 — our
locked bank is 3:4 and would give a 3:4 video.

COST. $0.07 each, $0.28 for the set, and the photorealism verdict happens here
rather than after a video generation. Reject and rewrite for 7 cents.

WHAT CHANGED FROM reel_day214:
  * the floor/sofa shot is gone — it is the one that came back with the wrong
    light behind her, and it was the shot with the least motion in it.
  * five shots became four, three seconds each. Overlay 5 folds into shot 4.
  * her ribcage is covered in all four. It is her only tattoo, it sits on the
    LEFT, and a video model with nothing but text to go on will mirror it.
  * every frame has her face legible. A first frame the model cannot read her
    from is a first frame that drifts.

    python outside.py --reel-frames --all --budget 0.4
"""

# Each entry is one authored description, same shape and same rules as
# outside_shots.py: written as a single thought, nothing negated, the device
# never named, the surface named instead of any signage on it.
SHOTS = [

dict(id="rf_bed", tier="2k", aspect="9:16", selfie=False, text=
 "Lying on her side in bed in a small Seoul apartment early in the morning, "
 "one arm folded under the pillow and the duvet pushed down to her waist. Her "
 "eyes are open and she is looking straight into the lens, awake but not yet "
 "moving. A washed grey cotton t-shirt, her hair down and spread across the "
 "pillow, flattened on one side from sleeping. White linen, a pale wall, one "
 "window out of frame to her left giving thin early light across the bed. "
 "The camera is resting on the mattress just beyond the pillow, at pillow "
 "height, slightly below her eyeline and a few degrees off level, with more "
 "empty bed along the bottom of the frame than she would have chosen. "
 "Shot on an iPhone 16 Pro: flat HDR contrast, low saturation, fine noise in "
 "the shadows, pillow creases on her cheek and real skin texture."),

dict(id="rf_window", tier="2k", aspect="9:16", body=True, text=
 "Standing at the window of a small apartment in the morning holding a mug in "
 "both hands, her weight settled on one hip, looking out rather than at the "
 "lens. An oversized cream knit and loose grey shorts, her hair half-up in a "
 "claw clip with the lengths loose below it. A low sill with one plant on it, "
 "a linen curtain pushed to one side, the flat white of an overcast Seoul sky "
 "filling the window and doing all of the lighting. The camera is set down on "
 "a table behind her and left running, low and a little wrong, with the corner "
 "of a chair in the near foreground. "
 "Shot on an iPhone 16 Pro: flat HDR contrast, low saturation, deep focus so "
 "the room stays legible, fine noise in the shadows. Skin shows pores and "
 "small unevenness."),

dict(id="rf_mat", tier="2k", aspect="9:16", body=True, text=
 "Sitting on a thin exercise mat on a pale wood floor against a plain white "
 "wall, one leg extended in front of her and the other folded in, both hands "
 "resting on her shin partway into a stretch, her head turned toward the lens "
 "with a small tired half-smile. A fitted matte black long-sleeve top and "
 "black leggings, her hair in a low bun with a few pieces escaping at the "
 "nape. A tall window out of frame to one side giving flat overcast daylight, "
 "a folded towel and a water bottle at the edge of the mat. The camera is on "
 "the floor a few steps away, propped against something at mat height so the "
 "frame sits low and tilts up very slightly, one corner of the mat cut off. "
 "Shot on an iPhone 16 Pro: flat HDR contrast, low saturation, deep focus, "
 "fine noise in the shadows. Skin shows pores and small unevenness."),

dict(id="rf_rooftop", tier="2k", aspect="9:16", text=
 "Close to the lens on a rooftop at dusk, her head and shoulders filling the "
 "frame, the wind moving a few strands of hair across her cheek. A black "
 "ribbed tank under an open oversized shirt, her hair down in soft natural "
 "waves, centre-parted with curtain bangs. The city behind her falling away "
 "into soft out-of-focus lights, the last warm band of sky on one side of her "
 "face and cool blue on the other. She is looking into the lens, her face "
 "still. Front camera at arm's length, a 23mm-equivalent lens close to her "
 "face so the background falls away and her features stretch very slightly, "
 "her extended arm cutting into the bottom corner and her other hand down at "
 "her side, horizon a few degrees off level. "
 "Shot on an iPhone 16 Pro front camera: flat HDR contrast, low saturation, "
 "softer and noisier than the rear lens, real skin texture."),
]

# The motion each frame performs. REWRITTEN AFTER TAKE 3 CAME BACK FLOATY.
#
# The first version said "blinks slowly", "very slightly", "a little further",
# "the smallest amount". That was "keep the motion small" written as adverbs —
# and diminutives are exactly what produces float. These models default to
# sluggish pacing because slow motion is the easiest thing to keep temporally
# consistent frame to frame, so a hedged verb is read as permission to pick the
# slowest possible interpretation. Four seconds is also the DURATION FLOOR, and
# a movement too small to fill four seconds gets the remainder filled with
# drift.
#
# So: two beats with timestamps, each a discrete action that starts and
# finishes, at ordinary speed. H3 accepts timestamped action ranges and the
# published guidance is one scene, one action, one camera move.
MOTION = {
 "rf_bed":     "0-2s: she blinks twice and draws in a breath, her shoulder "
               "rising under the duvet. "
               "2-4s: she pulls the duvet up over her shoulder in one movement "
               "and presses her cheek into the pillow, her eyes staying on the "
               "lens.",
 # "beside her" named no side and "still facing the window" re-asserted an
 # orientation the model had to re-derive. Both removed after the clip flipped
 # to its mirror partway through. A first attempt at the fix said "her back
 # staying to the camera" — wrong, and only caught by LOOKING at the frame:
 # she stands in profile with her face visible. See ANCHOR below.
 "rf_window":  "0-2s: she raises the mug to her mouth with both hands and "
               "drinks. "
               "2-4s: she lowers it to chest height and swallows, staying in "
               "profile and still looking out through the window.",
 "rf_mat":     "0-2s: she folds forward over the extended leg until her chest "
               "is close to her thigh and breathes out. "
               "2-4s: she comes back up to sitting and rolls her shoulders "
               "back once.",
 "rf_rooftop": "0-2s: she looks into the lens and blinks once as the wind "
               "lifts the hair off her cheek. "
               "2-4s: her mouth moves into a small closed smile and she tips "
               "her head a few degrees toward her shoulder.",
}

# WHERE THINGS ARE, read off the generated frame itself rather than guessed.
# rf_window flipped to its mirror partway through, and a generic "do not
# mirror" instruction leaves the model nothing to hold onto. Naming fixed
# landmarks on named sides makes a flip contradict the prompt.
# ONLY write an anchor for a frame you have actually looked at. An anchor that
# disagrees with its own first frame is worse than no anchor at all.
ANCHOR = {
 "rf_window": "The window fills the left of the frame with the potted plant on "
              "its sill at the bottom left, the linen curtain hangs down the "
              "right side, and the corner of the table and the chair stay in "
              "the bottom right. She stands in profile facing left toward the "
              "window throughout.",
}

# rf_window IS DROPPED FROM THE CUT.
# It mirrored partway through, twice-diagnosed: she is the only subject standing
# side-on, so her face gives the weakest orientation signal of the four, and a
# window-curtain-sill frame is close to left-right symmetric, which makes the
# mirror nearly as plausible a continuation as the original. The still and its
# ANCHOR are kept here because both are sound and the frame may be worth
# animating later with her turned a few degrees toward the lens.
# Dropping it cost the reel nothing: the overlays are typed in the editor, and
# three 4-second shots hold six two-second beats exactly as well as four did.
DROPPED = {"rf_window": "mirrored mid-clip; weakest orientation anchor"}

# THE CUT — 12s, three shots, six overlay beats. Typed, never generated.
#   rf_bed      0-2s   i quit my job 214 days ago
#               2-4s   i had ten months of savings
#   rf_mat      4-6s   i have four left
#               6-8s   i'm retraining as a pilates instructor
#   rf_rooftop  8-10s  everyone told me it was a mistake
#              10-12s  would you have done it?
