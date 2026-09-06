"""
exclusive_shots.py — the subscriber & exclusive tier. 20 posts plus a banner.

Plan B (SFW Monetization): Built for Instagram Subscriptions (and SFW creator
platforms like Patreon and Passes). Replaces the old Fanvue destination after
recognizing that SFW/suggestive content cannot convert on adult-dominated platforms.

A different tier from the public grid: warmer, more skin, and private in register —
the sense that this is what she shares only with her close subscriber circle.
Complies 100% with SFW guidelines: lingerie, loungewear, post-shower towel,
swimwear, but strictly no nudity.

Same rules as everywhere else: she holds the camera or it is propped, the free
hand does one thing, expressions come from a physical cause, matte skin, no
text on any surface.
"""

SHOTS = [
# --- morning, bed --------------------------------------------------------
dict(id="ex_bed_shirt", tier="2k", aspect="3:4",
 story="Morning, off-day in her Seongsu flat. Waking up slowly before checking "
       "messages. An impulsive first-thing selfie from bed.",
 text=
 "Sitting up in bed in her flat in Seongsu, Seoul, with the duvet over her "
 "legs, wearing an oversized white cotton shirt with the top buttons undone "
 "and the collar falling off one shoulder, hair loose and slept-on. Looking "
 "into the lens with her chin down and eyebrows slightly up, halfway through "
 "waking. Pale morning light from a window to one side, white linen, a plain "
 "wall behind. Front camera at arm's length, 23mm equivalent, her free hand "
 "pushing hair back, framing off level. Shot on an iPhone 15 Pro front camera, "
 "softer and noisier than the rear lens, flat HDR contrast, low saturation."),

dict(id="ex_bed_stretch", phone=True, tier="2k", aspect="3:4",
 story="Sunday late morning in Seongsu. Nothing scheduled until afternoon. "
       "Stretched out across the mattress, phone set on the bedside table on a timer.",
 text=
 "Lying on her front across the bed on her elbows in her flat in Seongsu, "
 "Seoul, ankles crossed in the air behind her, in a cropped white cotton vest "
 "and plain grey shorts, hair loose over her shoulders, chin on one hand, "
 "giving the lens a flat unhurried look. White linen rucked up around her, "
 "morning light across her back and shoulders. The phone is set down on the "
 "bedside table and left running, so the angle is low and slightly wrong. "
 "Shot on an iPhone 15 Pro, flat HDR contrast, low saturation, fine noise, "
 "real skin texture."),

dict(id="ex_bed_sheet", tier="2k", aspect="3:4",
 story="Mid-morning quiet in her Seongsu flat. Wrapped in the bedsheet before "
       "getting dressed, phone propped on the chest of drawers on a timer.",
 text=
 "Kneeling on the bed in her flat in Seongsu, Seoul, with a white sheet "
 "gathered loosely around her, bare shoulders and collarbone showing above "
 "it, hair down over one shoulder, looking down and away rather than at the "
 "lens. Soft window light from the side, shadow along the far side of her, "
 "plain wall behind. The phone is propped across the room and left running, "
 "framing loose with too much room on one side. Shot on an iPhone 15 Pro, "
 "flat HDR contrast, low saturation, deep focus, fine noise."),

# --- after a shower ------------------------------------------------------
dict(id="ex_towel_mirror", phone=True, tier="2k", aspect="3:4",
 story="Evening in Seongsu after training. Fresh out of a hot shower, bathroom "
       "steamed up. Wiping the glass for a quick mirror check.",
 text=
 "Her reflection in a fogged bathroom mirror in her flat in Seongsu, Seoul, a "
 "white towel wrapped and tucked at the chest, bare shoulders and arms, wet "
 "hair pulled straight back off her face, one hand wiping a clear patch in the "
 "condensation. Phone held at chest height and visible in the reflection. "
 "Warm bulb above the mirror, white tiles. Slightly rolled framing. Shot on "
 "an iPhone 15 Pro through the glass, flat HDR contrast, low saturation, "
 "steam softening the edges, fine noise."),

dict(id="ex_robe_door", tier="2k", aspect="3:4",
 story="Post-shower in her Seongsu flat, making tea before bed. Leaning against "
       "the doorframe, holding a mug and taking a quick front selfie.",
 text=
 "Leaning in a doorway in her flat in Seongsu, Seoul, in a short grey cotton "
 "robe tied loosely, bare legs, damp hair loose over one shoulder, one shoulder "
 "against the frame and her free hand holding a mug, looking into the lens with "
 "a small closed smile. Warm hallway light behind her, plain painted wall. Front "
 "camera at arm's length, 23mm equivalent, framing crooked. Shot on an iPhone "
 "15 Pro front camera, softer and noisier than the rear lens, flat HDR "
 "contrast, low saturation, real skin texture."),

# --- getting dressed -----------------------------------------------------
dict(id="ex_dressing_back", tier="2k", aspect="3:4",
 story="Morning in her Seongsu flat, pulling clothes on before heading out. "
       "Phone propped on the dresser on a self-timer.",
 text=
 "Standing at the end of the bed in her flat in Seongsu, Seoul, half turned "
 "away, pulling a cream knit down over her head so her back and the line of "
 "her shoulders are bare above plain black cotton briefs, face hidden by the "
 "jumper, hair caught up in it. Morning light from a window, white linen, "
 "plain wall. The phone is propped on a chest of drawers and left running, "
 "low and off-centre. Shot on an iPhone 15 Pro, flat HDR contrast, low "
 "saturation, deep focus, fine noise."),

dict(id="ex_mirror_set", phone=True, tier="2k", aspect="3:4",
 story="Afternoon in Seongsu. Trying on a plain cotton underwear set in front "
       "of the full-length mirror, taking a candid progress snap.",
 text=
 "Standing in front of a full-length mirror in her flat in Seongsu, Seoul, in "
 "a plain black cotton bralette and matching briefs, hair down over her "
 "shoulders, weight on one hip, one hand adjusting a strap, giving the mirror "
 "a completely flat unimpressed look, phone held at hip height and visible. "
 "Bedroom reversed behind her, white linen and a plain wall, soft daylight "
 "from one side. Framing loose and slightly rolled. Shot on an iPhone 15 Pro "
 "through the glass, flat HDR contrast, low saturation, fine noise."),

dict(id="ex_shirt_window", tier="2k", aspect="3:4",
 story="Sunny morning in Seongsu. Checking the weather from the window before "
       "showering. Phone propped on a low wooden stool on a timer.",
 text=
 "Standing at a window in her flat in Seongsu, Seoul, in an unbuttoned white "
 "cotton shirt over plain underwear, hair loose down her back, backlit so she "
 "is half in silhouette and the fabric goes translucent at the edges, one hand "
 "on the frame, looking out rather than at the camera. Linen curtain, plain "
 "wall, hard morning light. The phone is propped on a stool and left running, "
 "low with too much floor. Shot on an iPhone 15 Pro, flat HDR contrast that "
 "lifts the shadows, low saturation, fine noise."),

# --- lounging ------------------------------------------------------------
dict(id="ex_sofa_legs", tier="2k", aspect="3:4",
 story="Late evening lounging in her Seongsu flat. Scrolling after dinner, "
       "head hanging back, holding the front camera up for an amused selfie.",
 text=
 "Lying back along an armchair in her flat in Seongsu, Seoul, with her legs "
 "over one arm of it, in a thin grey cotton vest and plain cotton shorts, "
 "bare legs, hair loose spilling over the cushion, head tipped back against "
 "the other arm, looking down the lens upside down and amused at herself. One "
 "warm lamp doing all the lighting, plain wall, linen curtain drawn. Front "
 "camera held above her at arm's length, 23mm equivalent, framing crooked. "
 "Shot on an iPhone 15 Pro front camera, softer and noisier than the rear "
 "lens, grain in the shadows, flat HDR contrast, low saturation."),

dict(id="ex_floor_stretch", phone=True, tier="2k", aspect="3:4",
 story="Post-workout cooldown at home in Seongsu. Stretching on the floor, "
       "phone set down against the sofa on a video timer.",
 text=
 "Sitting on the floor against the sofa after training in her flat in "
 "Seongsu, Seoul, in a matte black sports bra and cycling shorts, one leg "
 "straight and one knee up, reaching toward her foot, hair stuck to her "
 "temple, looking up at the lens mid-stretch with her mouth slightly open. "
 "Wooden floor, plain wall, late afternoon light across her. The phone is set "
 "down on the floor and left running, so the angle is very low. Shot on an "
 "iPhone 15 Pro, flat HDR contrast, low saturation, deep focus, fine noise, "
 "sweat and flushed uneven skin."),

dict(id="ex_kitchen_shirt", tier="2k", aspect="3:4",
 story="Midnight thirst in Seongsu. Drinking water in the dark kitchen, snapping "
       "a sleepy front camera selfie under the cabinet strip light.",
 text=
 "Standing at the kitchen counter late at night in her flat in Seongsu, "
 "Seoul, in an oversized grey t-shirt, bare legs, hair down and unbrushed, "
 "one heel lifted, drinking water straight from the glass and looking sideways "
 "at the lens over the rim. Pale wood worktop, the window dark, the strip "
 "light under the shelf the only source. Front camera at arm's length, 23mm "
 "equivalent, harsh underlighting, framing off level. Shot on an iPhone 15 "
 "Pro front camera, softer and noisier than the rear lens, flat HDR contrast, "
 "low saturation."),

dict(id="ex_bath_edge", tier="2k", aspect="3:4",
 story="End of a long day in Seongsu. Waiting on the tub edge while running "
       "the water, phone propped on the vanity.",
 text=
 "Sitting on the edge of a bath in her flat in Seongsu, Seoul, in a short "
 "white cotton slip, bare legs crossed at the ankle, leaning forward with her "
 "forearms on her knees, hair up in a clip with pieces falling, looking into "
 "the lens with a tired half smile. White tiles, a folded towel, warm bulb "
 "above. The phone is propped on the vanity and left running, framing loose. "
 "Shot on an iPhone 15 Pro, flat HDR contrast, low saturation, fine noise, "
 "real skin texture."),

# --- swimwear ------------------------------------------------------------
dict(id="ex_pool_edge", tier="2k", aspect="3:4",
 story="Sunday afternoon at a rooftop pool in Seoul with a friend. Sitting at "
       "the water's edge chatting, caught mid-sentence.",
 text=
 "Sitting on the edge of a rooftop pool in Seoul with her legs in the water "
 "to the knee, in a plain black one-piece swimsuit, hair up in a high "
 "ponytail, leaning back on one hand, head turned to the lens squinting against "
 "the sun with her mouth open on a word. City hazy behind, hard midday light, "
 "wet concrete. Taken by somebody sitting a couple of metres along the edge. "
 "Shot on an iPhone 15 Pro, flat HDR contrast, low saturation, water spots "
 "on the lens, deep focus, fine noise."),

dict(id="ex_pool_wet", tier="2k", aspect="3:4",
 story="Climbing out of the rooftop pool in Seoul on a hot afternoon. Phone "
       "propped on a sunbed on a timer while she shakes water off.",
 text=
 "Standing at the side of a rooftop pool in Seoul having just got out, "
 "water running off her, in a plain black one-piece, both hands with her wet "
 "hair pulled back off her face and her eyes shut against the water, "
 "mid-movement. Hard sun, wet concrete, the city pale behind. The phone is "
 "propped on a sunbed and left running, low and off-centre. Shot on an "
 "iPhone 15 Pro, flat HDR contrast, blown highlights on the water, low "
 "saturation, fine noise."),

dict(id="ex_towel_balcony", tier="2k", aspect="3:4",
 story="Golden hour in Seongsu. Stepping onto the small balcony after washing "
       "her hair, wrapped in a towel, taking a late sun selfie.",
 text=
 "On the small balcony of her flat in Seongsu, Seoul, in the late sun, "
 "wrapped in a beach towel held closed at the chest, bare shoulders, wet "
 "hair down her back, leaning her hip on the railing and looking back over "
 "her shoulder at the lens. Warm low light, plain concrete and a metal rail, "
 "city soft behind. Front camera at arm's length, 23mm equivalent, framing "
 "tilted. Shot on an iPhone 15 Pro front camera, softer and noisier than the "
 "rear lens, flat HDR contrast, low saturation, visible pores."),

# --- close, warm ---------------------------------------------------------
dict(id="ex_close_collar", tier="2k", aspect="3:4",
 story="Quiet morning in her Seongsu flat. Soft window light on the pale wall, "
       "taking an intimate close-up portrait.",
 text=
 "Very close in her flat in Seongsu, Seoul, head and bare shoulders only "
 "against a plain pale wall, a thin black strap across one shoulder, hair "
 "loose around her shoulders, chin slightly down, looking straight into the "
 "lens with a small closed smile and her eyes creased at the corners. Soft "
 "daylight from the front and one side. Front camera at arm's length, 23mm "
 "equivalent, her face filling most of the frame, her free hand up near her "
 "collarbone. Shot on an iPhone 15 Pro front camera, softer and noisier than "
 "the rear lens, flat HDR contrast, low saturation, pores and the small pale "
 "freckles across her nose."),

dict(id="ex_close_bed", tier="2k", aspect="3:4",
 story="Morning in Seongsu, lingering in bed before getting up. Holding the "
       "front camera directly overhead for a sleepy top-down selfie.",
 text=
 "Lying on her back on white linen in her flat in Seongsu, Seoul, "
 "photographed from directly above, bare shoulders and a thin white strap, "
 "hair loose and spread out around her head, one arm up above her, looking "
 "straight up into the lens with her mouth slightly open. Soft morning light "
 "from one side. Front camera held above her at arm's length, 23mm "
 "equivalent. Shot on an iPhone 15 Pro front camera, softer and noisier than "
 "the rear lens, flat HDR contrast, low saturation, real skin texture and fine "
 "hairs at her temple."),

dict(id="ex_back_line", tier="2k", aspect="3:4",
 story="Early morning in Seongsu. Sitting on the bed edge looking toward the "
       "window light. Phone propped on the low shelf on a timer.",
 text=
 "Sitting on the end of the bed in her flat in Seongsu, Seoul, seen from "
 "behind, bare back with a thin black strap across it, head turned in profile "
 "toward the window, hair pulled over one shoulder so her shoulder blade and "
 "the line of her spine catch the light. Morning light from the side, white "
 "linen, plain wall. The phone is propped on a shelf and left running, "
 "framing loose. Shot on an iPhone 15 Pro, flat HDR contrast, low saturation, "
 "deep focus, fine noise."),

dict(id="ex_window_light", tier="2k", aspect="3:4",
 story="Morning sun breaking into her Seongsu flat. Standing by the window sill "
       "soaking in the light, phone propped on the sill on a timer.",
 text=
 "Standing side-on at a window in her flat in Seongsu, Seoul, in plain black "
 "cotton underwear, arms loose at her sides, head turned down toward the light "
 "with her eyes closed, hair loose. Hard morning light raking across her so "
 "one side is bright and the other falls into open shadow, plain wall behind. "
 "The phone is propped on the sill and left running, framing low and "
 "slightly wrong. Shot on an iPhone 15 Pro, flat HDR contrast, low "
 "saturation, deep focus, fine noise."),

dict(id="ex_lamp_night", tier="2k", aspect="3:4",
 story="Late night in Seongsu before sleeping. Talking to the front camera like "
       "leaving a private video note before turning out the bedside lamp.",
 text=
 "Sitting cross-legged on the bed at night in her flat in Seongsu, Seoul, in "
 "a thin white cotton vest and plain shorts, hair loose over her shoulders, "
 "one lamp beside her doing all the lighting so half of her is in shadow, "
 "leaning toward the lens with her forearms on her knees, saying something to "
 "it. White linen, plain dark wall. Front camera at arm's length, 23mm "
 "equivalent, framing crooked. Shot on an iPhone 15 Pro front camera, softer "
 "and noisier than the rear lens, heavy grain in the dark, flat HDR "
 "contrast, low saturation."),

# --- banner: 1192x335 is 3.56:1, so generate 21:9 and crop -------------
dict(id="ex_banner", tier="2k", aspect="21:9",
 story="Morning header banner for the subscriber profile. Her empty unmade bed in "
       "Seongsu by the window after getting up.",
 text=
 "A wide horizontal photograph of an unmade bed by a window in her flat in "
 "Seongsu, Seoul, in the morning, white linen rucked and creased, a grey "
 "t-shirt left on the sheets, a mug on the sill, a plant, the curtain half "
 "drawn. Nobody in the frame. Soft directional daylight from the left, long "
 "shadows across the linen. Shot on an iPhone 15 Pro, flat HDR contrast, "
 "low saturation, deep focus, fine noise. Every surface plain: linen, painted "
 "wall, wood, glass."),
]
