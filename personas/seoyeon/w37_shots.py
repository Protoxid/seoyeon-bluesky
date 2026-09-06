"""
w37_shots.py — Mon 7 to Sun 13 September 2026 (ISO 2026-W37), posted in week.

THE WEEK IS ALREADY WRITTEN. The thread, the day-by-day, the captions and the
plate decisions live in content/w37_2026-09-07/WEEK.md; the handoff to Echo is
content/w37_2026-09-07/handoff.json. This file only carries the shot prompts so
`outside.py --week3` can render them. Do not redesign the week here — if a shot
will not render, fix the image or block it.

Season: the heat came BACK after the week-2 turn. The fan is on again and the
window is shut, which is the reversal of last week's story and the thread that
runs under Tuesday, Thursday and Sunday.

MIX (rebalanced 7 Sep, owner ruling — 3 face frames, not 1): 1 selfie (class_bad) · 1 friend-taken (jieun_roof — Jieun holds the camera, is never rendered, exactly the shipped n_cafe_jieun precedent) · 1 selfie (table_sunday) · 4 noface. Caption age 25 (CANON §2, birthday 23 Oct).
No men in any frame, including backgrounds. Clothedy torso shots set NEITHER
body=True NOR limb=True, so master/c/c5_relax_front.png never attaches and the
word "tattoo" never appears in the prompt.

PLATE IDs (verified against pov.plate_path, which resolves <id>_<hash>_1.png):
  plate_room        -> content/plates/plate_room_ecc050_1.png
  plate_studio_wide -> content/plates/plate_studio_wide_4e68ba_1.png
  plate_rooftop     -> locations/rooftop.png
Bare `plate_studio`, `plate_kitchen` and `plate_window` do NOT resolve.

BATCH 1 (generated first): w37_class_bad, w37_fan, w37_gimbap.
BATCH 2: the Wednesday-to-Sunday four.
"""

SHOTS = [

# ---- MON 7 SEP · 07:55 --------------------------------------------- selfie --
dict(id="w37_class_bad", day="mon", tier="2k", aspect="3:4", selfie=True,
     plate="plate_studio_wide", safe=True,
 story="MON 07:55. The 7am beginner class, and she teaches it badly. She "
       "loses the count on the second set, says 'again' when she means "
       "'wait', and one regular corrects her in front of the other four. "
       "Everyone has gone. She sits on the floor and takes one before she "
       "leaves, still thinking about the count.",
 text=
 "A woman takes a front-camera selfie at arm's length sitting on the floor of "
 "a pilates studio in Seongsu, Seoul, just after seven in the morning. She is "
 "in a black sports bra and black leggings, her knees drawn up a little to "
 "one side, hair coming out of a low bun with pieces loose at the nape, "
 "flushed and slightly damp at the hairline. Her mouth is closed and pushed "
 "to one side, one eyebrow marginally higher than the other, eyes straight "
 "into the lens — the face of someone telling you about something that just "
 "happened, not posing. Behind her the room is empty: two rows of reformer "
 "frames, blue mats stacked along the wall, a water cooler, tall windows down "
 "one side letting in early light, a full-height mirror on the other. Nobody "
 "else in the room. Front camera at arm's length, her extended arm cutting "
 "into the lower corner of the frame, the room stretching a little wide at "
 "the edges. Everything sharp. Cool morning daylight mixed with the room's "
 "overhead lights, flat, fine noise in the shadows."),

# ---- TUE 8 SEP · 15:10 --------------------------------------------- noface --
dict(id="w37_fan", day="tue", tier="2k", aspect="3:4", noface=True,
     plate="plate_room",
 story="TUE 15:10. No class. Course reading at the table she cannot "
       "concentrate on and the fan achieving nothing in a flat that is 29 "
       "degrees. She has started shutting the window as though it were the "
       "fan's fault. She photographs the room, not herself.",
 # REROLL 1. The first render drew the curtains across the window, which made
 # a 15:10 frame read as dusk AND took the room off its own plate, where the
 # curtains sit bunched at either side. The heat is now carried by the light on
 # the glass and the band on the floor, not by closing the room down.
 text=
 "The inside of a small one-room flat in Seongsu, Seoul, in the middle of a "
 "hot mid-afternoon, photographed standing near the door with the phone held "
 "at chest height. Nobody is in the frame and the room is untidied exactly as "
 "it stands. A white standing fan on the floor is switched on and angled at "
 "the bed, its blades spun into a soft blur, the cage tilted slightly down. "
 "The big window at the far end is shut with the glass down and the grey "
 "curtains pushed back to either side of it, so the afternoon lies flat and "
 "bright on the glass and in a pale band across the floorboards. The bed is "
 "unmade. At the table in the near half of the room one chair is pulled out: "
 "an open laptop turned sideways to the lens with its screen unreadable, a "
 "page of notes pushed aside untouched, a tall glass of water on the wood. "
 "Everything sharp except the fan. Hot still air, bright flat daylight off "
 "the window, low contrast, fine noise, the frame a few degrees off level."),

# ---- TUE 8 SEP · 13:20 --------------------------------------------- noface --
dict(id="w37_gimbap", day="tue", tier="2k", aspect="3:4", noface=True,
 story="TUE 13:20. Lunch because it is lunchtime. She worked out on Monday "
       "exactly how much is left, so she stands at the counter doing the "
       "division on a 2,500 won gimbap and does not enjoy it. Rear camera, "
       "close, one item of food and a drink on a counter.",
 text=
 "A close photograph taken on the rear camera of a phone, held crooked and "
 "slightly above, of lunch resting on the pale counter beside the till of a "
 "small corner shop in Seoul in the early afternoon: a short log of gimbap "
 "cut into six pieces in a shallow clear plastic tray with plain film laid "
 "loose over it, and a small bottle of barley tea standing next to it. The "
 "tray and the bottle are plain and unmarked, the generic pale packaging that "
 "sits in photographs, printed with nothing large enough to read, the labels "
 "turned partly away. The counter around them is empty and the frame holds "
 "only those two things: the food and the surface under it, the shop falling "
 "soft behind. Everything past the tray is out of focus — the edge of a shelf "
 "of snacks, a cooler door, warm-white fluorescent strip light, a pale floor. "
 "Sharp on the tray and the film over it. Flat colour, slight noise in the "
 "shadows, nothing arranged."),

# ---- WED 9 SEP · 08:05 --------------------------------------------- noface --
dict(id="w37_studio_after", day="wed", tier="2k", aspect="3:4", noface=True,
     plate="plate_studio_wide",
 story="WED 09. Second 7am class, taught properly. The reward is a fourth "
       "slot next month — money, and more hours. She stays in the empty room "
       "afterwards and takes the room as it is, her towel and bottle still on "
       "the near machine.",
 text=
 "An empty pilates studio in Seongsu, Seoul, in the morning after a class has "
 "finished and everyone has left. Nobody is in the frame. Two rows of "
 "reformer machines stand lined up and unused, blue mats stacked along one "
 "wall, a water cooler in the corner, tall windows down one side with low "
 "early sun coming through and lying in bright bands across the floor, a "
 "full-height mirror along the other wall reflecting the empty room back. On "
 "the nearest machine a small grey towel is left draped over the shoulder "
 "rest and a plain metal water bottle stands on the carriage beside it, both "
 "of them hers. Taken standing in the doorway with the phone held loosely at "
 "chest height, slightly crooked, nothing tidied for the camera. Everything "
 "sharp. Warm morning light mixed with cool shade, low contrast, fine noise."),

# ---- THU 10 SEP · 20:40 ---------------------------------------------- face --
# REBALANCED 7 Sep (owner 3-faces ruling). Was noface (cups only) — that render
# (w37_jieun_roof_bd67ba_1.png) was deleted as spec-superseded: it cannot carry
# her face. Jieun is the CAMERA, never a face in frame — the n_cafe_jieun
# precedent, where the second glass nearest the lens is where Jieun sits.
# Do not describe her, do not name her in the text; the second cup is her.
dict(id="w37_jieun_roof", day="thu", tier="2k", aspect="3:4", safe=True,
     # PLATE RESOLVED AS ONE-OFF (batch 5, by eye). There is NO valid empty
     # rooftop plate anywhere in this repo. plate_rooftop -> locations/rooftop.png
     # is an interior living room, AND locations/rooftop/rooftop_0[123].png are
     # ALSO interior living rooms — the batch-4 claim that they are the real
     # roofs is FALSE (verified by eye on all four). The account's real roof
     # only exists in published grid shots WITH her in them (n_roof_posed,
     # n_rooftop_posed), which cannot serve as an empty Image-1 room (ROLE_PLATE
     # forbids a person in Image 1, and her dress/pose would bleed into the
     # frame). So this renders plate-less, exactly like market_peaches and
     # w37_gimbap, with the dusk roof carried fully by the text below (gravel
     # underfoot, low concrete parapet, water tanks, metal stairwell door,
     # washing line, skyline at dusk) so it matches the grid roof. No shared
     # code edited. Latent bug flagged to the owner: a real empty roof plate
     # must be generated before any future week uses plate_rooftop.
     plate=None,
 story="THU 10. Jieun brings something her mother made. They eat it at the "
       "table, then carry it up to the roof because the flat is warmer than "
       "outside. While they are up there, Seoyeon telling her about the "
       "fourth slot, Jieun picks up the phone without warning — the n_cafe_jieun "
       "move. Jieun leaves before nine for work. Two cups come back down.",
 text=
 "A woman sitting sideways on the low concrete parapet wall of a residential "
 "rooftop in Seoul at dusk, photographed from a step or two away with the "
 "phone held low at chest height, slightly off-centre and a degree off "
 "level. She is mid-turn back toward the camera, having just been looking "
 "out at the skyline, mouth closed with the last of a smile going, eyes "
 "coming back to the lens, one hand resting flat on the wall beside her. An "
 "oversized grey cotton t-shirt, her hair clipped up off her neck with "
 "strands loose at the sides, moving a little in the evening air. On the "
 "wall near her: a round plastic food container with the lid off and "
 "chopsticks laid across it, a crumpled napkin, and two paper cups — hers, "
 "and a second one close to the camera, low and half out of focus along the "
 "bottom edge of the frame. Beyond the wall the rooftops and low blocks of "
 "the neighbourhood, a water tower on the neighbouring roof, a few windows "
 "lit, the sky going from pale warm at the horizon to grey-blue above. "
 "Nobody else on the roof. Rooftop clutter kept honest: a washing line "
 "with nothing on it, water tanks, a metal stairwell door, gravel "
 "underfoot. Late evening light, soft, no flash, a little flat and "
 "slightly underexposed, fine grain, the horizon a few degrees off level."),

# ---- SAT 12 SEP · 10:15 --------------------------------------------- noface --
dict(id="w37_market_peaches", day="sat", tier="2k", aspect="3:4", noface=True,
 story="SAT 10:15. Market, not a department store, because that is how she "
       "shops. Peaches going cheap at the end of the season. She photographs "
       "the tray standing in the queue, holding the phone low.",
 text=
 "A market fruit stall in Seoul in the mid-morning, photographed standing in "
 "the queue with the phone held low and close, the frame crooked and blocked "
 "along one edge by the corner of the stall. The tray in front is late-season "
 "peaches in shallow cardboard, some wrapped in pale foam netting, a few soft "
 "at the shoulder, one open box with the fruit loose in it. The cardboard is "
 "plain and unmarked, the printed writing on it turned away and out of focus "
 "so nothing on it can be read. Behind the tray more crates stacked at "
 "angles and a small handwritten Korean price card on a clothespin line, "
 "turned edge-on to the lens so only its blank back shows, a plastic bag "
 "hanging ready, the awning above throwing flat shade. Two women further "
 "along the row of stalls, seen from behind, both with long dark hair and "
 "light summer dresses, out of focus. Nothing in the foreground is held or "
 "touched. Daylight under the awning, warm and flat, deep shadows behind, "
 "fine noise."),

# ---- SUN 13 SEP · 21:05 ---------------------------------------------- face --
# REBALANCED 7 Sep (owner 3-faces ruling): the week's payoff ends on her face.
# NOT studio_after — a second studio face in the same week as class_bad is the
# content-account tell. Gates are absolute and must be checked by eye before
# approval: laptop screen turned away from the lens (only its back and a thin
# glow in frame), the single pencil line too faint to read, no readable
# numerals anywhere, lamp on, night outside the window.
dict(id="w37_table_sunday", day="sun", tier="2k", aspect="3:4", selfie=True,
     safe=True, plate="plate_room",
 story="SUN 21:05. The money post. She sits at the table with the laptop and "
       "the bank app and writes down the date the savings run out, which she "
       "has known since June. She does not post the number. She takes one of "
       "herself first — flat, not sad — because she is about to say yes to the "
       "fourth slot and wants it recorded without saying it.",
 text=
 "A woman takes a front-camera selfie at arm's length, sitting at the small "
 "table in her one-room flat in Seongsu, Seoul, late at night: her extended "
 "arm cuts into the lower corner of the frame and is holding the only phone "
 "in the picture. She has just stopped writing: mouth closed, eyes level and "
 "straight into the lens, the flat look of someone who has just written a "
 "date down and is not going to say it out loud. An oversized grey t-shirt, "
 "hair down and gone flat with the day, tucked behind one ear. A lamp on at "
 "one end of the table throwing warm light across the wood and across her "
 "face, the rest of the room behind her in shade: the standing fan still "
 "running at the bed, the window black with night. Low in the frame between "
 "the camera and her, the back of her open laptop standing on the table, "
 "its screen facing her and turned away from the lens with only a thin pale "
 "glow at its edge, and beside it an open notebook with a pen lying loose, "
 "the single short pencil line in it angled away and too faint to read at "
 "this distance. A glass of water and a coaster. Warm lamp light against "
 "cold dark, low contrast, heavy fine noise in the shadows, the frame "
 "slightly off level."),
]
