"""
week2_shots.py — Mon 24 to Sun 30 August 2026, posted from Mon 31.

Her week runs one week behind the posting, as it has since the first grid. The
week that just ended is the week that gets posted.

THE THREAD THIS WEEK IS THE HEAT BREAKING. Seoul's late-August turn is real,
it is the only thing anyone there talks about when it happens, and it earns a
whole set of changes for free: the fan goes off, the window opens, it rains
once, and she stops looking like someone who has been too hot for a month. A
season doing something is the cheapest source of variety there is, and it is
the one kind of change nobody reads as a content decision.

MIX, counted before writing rather than after: 4 no-face · 2 selfie · 1 mirror
· 1 friend-taken. Four of eight show her face. Zero propped — she propped the
phone last week and it must stay rare or it stops meaning anything.

Every shot names Seoul and, where week.md fixes one, the neighbourhood.
"""

SHOTS = [

# ---- MON 24 AUG · 07:35 -------------------------------------------- noface --
dict(id="w2_subway_am", day="mon", tier="2k", aspect="3:4", noface=True,
 story="MON 07:35. First morning in five weeks she has not been sweating "
       "before she got out of the building. She is early for the seven "
       "o'clock and the platform is nearly empty, and the light down there is "
       "doing something it does not usually do. She photographs the platform. "
       "She is not in it.",
 text=
 "A subway platform at Seongsu station in Seoul early on a weekday morning: "
 "the glass screen doors closed along the platform edge, tiled wall, a row of "
 "empty metal seats, Korean station signage and a lit route map, two or three "
 "people standing far down the platform, a train not yet in. Taken standing, "
 "phone held at chest height, slightly crooked, nothing arranged. Everything "
 "sharp. Cool fluorescent cast, flat, faint reflection in the screen doors."),

# ---- MON 24 AUG · 08:50 -------------------------------------------- mirror --
dict(id="w2_studio_mirror", phone=True, safe=True, day="mon", tier="2k", aspect="3:4",
 selfie=False,
 story="MON 08:50. The class is over and the changing room is empty. She is "
       "not checking whether she looks good, she is checking whether the "
       "leggings have gone see-through at the back, which is the actual "
       "reason anyone takes this photograph.",
 text=
 "A mirror selfie in the small changing room of a pilates studio in Seongsu, "
 "Seoul, after an early class. The phone held at chest height and clearly "
 "visible, partly covering her. Black leggings and a black sports bra, a "
 "zip-up over one arm, hair still up and coming loose. Her head is turned "
 "slightly to look past the phone at her own reflection, mouth closed. Around "
 "her: open lockers, a bench with a bag on it, a folded towel, a hairdryer on "
 "a shelf, a bin, clothes hooks. Everything sharp. Warm-white overhead cast, "
 "slightly underexposed, grainy."),

# ---- TUE 25 AUG · 15:20 -------------------------------------------- selfie --
# REPLACED w2_desk_rain, WHICH WAS w1's n_desk_late WEARING DIFFERENT WEATHER.
# Both were: a table shot from above, an open laptop, a fan on the floor, one
# bare knee at the bottom edge, no face, mid-afternoon. The only differences
# were the rain and whether the fan was on. Worse, the two used different
# plates, so the same flat rendered as two flats — a continuity break is more
# expensive than a repeat, because it un-teaches the room the grid has been
# building. THE TEST A SHOT HAS TO PASS IS NOT "is the story different", it is
# "would a scrolling stranger see a photograph they have already seen".
#
# TUESDAY AFTERNOON IS ALREADY SPECCED AS "errands, convenience store", and the
# structure was right and the shot was ignoring it. The rain beat survives — it
# is a real Seoul seasonal turn and the best thing in the original — it just
# happens to her outside instead of to her furniture.
#
# AND IT PUTS HER FACE IN TUESDAY. w2_broken_machine at 09:15 is also a no-face
# domestic object shot; two of those in one day is a day with no person in it.
dict(id="w2_rain_awning", day="tue", tier="2k", aspect="3:4", selfie=True,
 story="TUE 15:20. She goes down for milk and washing-up liquid and it starts "
       "while she is inside. She stands under the awning working out whether "
       "it will pass, decides it will not, and walks home wet — it is thirty "
       "metres. First rain since June, and the first time in two months she "
       "has been cold. The photograph is taken under the awning, during the "
       "part where she is pretending to decide.",
 text=
 "A woman takes a front-camera selfie at arm's length under the awning "
 "outside the convenience store on her own residential street in Seoul, in "
 "heavy afternoon rain. Her hair is damp at the temples with a few strands "
 "stuck to her forehead and one cheek, and the shoulders of her grey t-shirt "
 "are darker where the rain has gone through. A thin plastic shopping bag "
 "hangs from her other hand, low at the bottom of the frame. She is laughing "
 "with her mouth open and her eyes half shut, not posing. Behind her the rain "
 "comes down hard on a wet road that is reflecting the shop light, parked "
 "scooters, a low brick building opposite with Korean shop signage and an "
 "air-conditioning unit bracketed to the wall. Nobody else is in the frame. "
 "The frame is off centre and off level, taken from slightly above her eye "
 "line with her face towards one edge. Everything sharp front to back. Flat "
 "grey afternoon daylight, low contrast, fine noise."),

# ---- WED 26 AUG · 14:40 -------------------------------------------- selfie --
dict(id="w2_class_two", day="wed", tier="2k", aspect="3:4", selfie=True,
 story="WED 14:40. Second class. The first one was terror and the photograph "
       "of it was a blank face. This one was just a Wednesday — she got "
       "through it, someone asked a question she could answer, and it was "
       "fine. The story of the second time is that it is boring, and that is "
       "the interesting part.",
 text=
 "A woman takes a front-camera selfie at arm's length sitting on the floor of "
 "a pilates studio in Seongsu, Seoul, after teaching. She is in a black sports "
 "bra and black leggings, hair coming out of a low bun, flushed, a little "
 "damp at the hairline. Her mouth is closed and pushed slightly to one side "
 "and one eyebrow is marginally higher than the other, the face of someone "
 "who has just finished something ordinary. Behind her the studio: reformer "
 "frames, mats rolled against the wall, a water bottle on the floor, a mirror "
 "along one wall, another woman putting her shoes on by the door. Everything "
 "sharp. Cool daylight from a high window, flat."),

# ---- WED 26 AUG · 21:30 -------------------------------------------- noface --
dict(id="w2_laundromat", day="wed", tier="2k", aspect="3:4", noface=True,
 story="WED 21:30. The machine in the flat has been making a noise for a "
       "month so she takes the sheets to the coin laundry two streets over "
       "and sits there for forty minutes doing nothing. It is the least "
       "curated thing that happened all week, which is exactly why it goes in.",
 text=
 "The inside of a small coin laundry in Seoul late at night: a row of front-"
 "loading washing machines and dryers, one running, a plastic basket on a "
 "folding counter with a paperback and a phone charger on top of it, a "
 "vending machine for detergent, Korean instruction signs on the wall, a "
 "moulded plastic chair. Nobody else in the room. Taken from the chair, phone "
 "held low, crooked, nothing tidied. Everything sharp. Hard fluorescent cast, "
 "overexposed at the ceiling, faint reflection in the machine doors."),

# ---- THU 27 AUG · 17:10 -------------------------------------------- noface --
dict(id="w2_bakery", day="thu", tier="2k", aspect="3:4", noface=True,
 story="THU 17:10. Jieun's birthday dinner is Friday and Seoyeon is bringing "
       "something, so she stops at the bakery near the station and stands in "
       "front of the tray for longer than a person should. She photographs "
       "the bread, not herself in front of the bread.",
 text=
 "The counter of a small neighbourhood bakery in Seoul in the late afternoon: "
 "trays of bread and pastries under warm light, metal tongs resting on a "
 "tray, small handwritten Korean price cards, a stack of shallow trays and a "
 "pair of tongs by the door, a glass case at the till. A hand is not in the "
 "picture. Taken standing in the queue, phone held low and close, crooked, "
 "slightly blocked at one edge by a shelf. Everything sharp. Warm tungsten "
 "cast, flat."),

# ---- FRI 28 AUG · 19:40 ---------------------------------------- friend-taken --
dict(id="w2_river_steps", day="fri", tier="2k", aspect="3:4", selfie=False,
 story="FRI 19:40. Jieun's birthday, and instead of a restaurant they buy "
       "beer and snacks at the convenience store and sit on the steps at the "
       "river like students. Somebody has to be holding the camera and it is "
       "not Seoyeon — she is the one being photographed, mid-sentence again, "
       "which is the only way anyone gets a real photograph of her.",
 text=
 "A woman sitting on the wide concrete steps beside the Han river in Seoul in "
 "the evening, photographed from a step below by someone sitting next to her. "
 "She is turned to talk, one hand out mid-gesture, looking off past the "
 "camera, not at it. A can and an open bag of snacks on the step beside her, "
 "a plastic convenience-store bag. Behind her the river, a bridge with its "
 "lights on, the far bank, other people sitting further along the steps. She "
 "is in a plain t-shirt with a cardigan pushed up her forearms because the "
 "evening has gone cool. Everything sharp. Warm dusk light going blue, "
 "slightly underexposed, grainy."),

# ---- SUN 30 AUG · 11:00 -------------------------------------------- selfie --
dict(id="w2_kitchen_sun", plate="plate_room", day="sun", tier="2k", aspect="3:4", selfie=True, locked=True,
 story="SUN 11:00. No course module this weekend, so Sunday is the reset: "
       "laundry on, something cooking, the week ahead written down. She has "
       "not brushed her hair and she takes one anyway, because for the first "
       "time in weeks the flat is a nice temperature and she is in a good "
       "mood about a Sunday, which almost never happens.",
 text=
 "A woman takes a front-camera selfie at arm's length standing in the tiny "
 "kitchen of a Seoul flat late on a Sunday morning. Hair unbrushed and pushed "
 "back, an oversized washed-out t-shirt, no makeup. Her eyes are half shut "
 "against the window light and her mouth is open slightly in the middle of "
 "saying something to nobody. Behind her: a pot on a small gas hob with the "
 "lid tipped, a drying rack of clean dishes, a laundry rack with clothes on "
 "it just visible through the doorway, jars and a rice cooker on the counter, "
 "a window with the building opposite behind it. Everything sharp. Bright "
 "flat daylight through the window, slightly overexposed at the window."),

# ---- SAT 29 AUG · 16:20 -------------------------------------------- noface --
# ONE image, four Reel beats: reel_build pushes in and the crops do the rest,
# so a five-item haul costs one generation instead of five.
dict(id="w2_daiso_haul", day="sat", tier="2k", aspect="3:4", noface=True,
 story="SAT 16:20. She went in for one thing. The strawberry sponge is the "
       "joke and she knows it is the joke, which is why it is in the middle of "
       "the picture.",
 text=
 "A flat lay on a pale wood floor in a Seoul flat of things just bought from "
 "a Daiso: a pair of grey grip socks still joined by their tag, two black "
 "hair claws, three small square plastic containers stacked, a roll of "
 "freezer bags, a kitchen sponge shaped like a strawberry, and a thin paper "
 "receipt curling at one end with Korean text on it. The white plastic "
 "shopping bag they came in pushed to one edge of the frame, still creased. "
 "Taken from directly above, standing, slightly crooked, nothing arranged "
 "neatly. Everything sharp. Flat daylight, low contrast, fine noise."),

# ---- TUE 25 AUG · 09:15 -------------------------------------------- noface --
dict(id="w2_broken_machine", plate="plate_room", day="tue", tier="2k",
 aspect="3:4", noface=True, locked=True,
 story="TUE 09:15. The washing machine has been making the noise for a month "
       "and this is the morning it stops pretending. This is why she is in a "
       "coin laundry on Wednesday — the thread was already there, it just "
       "never had a picture.",
 text=
 "A small washing machine in the corner of a Seoul one-room flat with the "
 "door open and wet washing still inside it, a puddle spread across the vinyl "
 "floor in front of it, a towel thrown down at the edge of the puddle to soak "
 "it up, a bottle of detergent knocked over on its side. Taken standing, "
 "looking down, phone held in one hand, crooked and a bit too close. "
 "Everything sharp. Flat morning daylight, low contrast."),

# ---- THU 27 AUG · 12:40 -------------------------------------------- noface --
dict(id="w2_bad_coffee", phone=True, day="thu", tier="2k", aspect="3:4", noface=True,
 story="THU 12:40. Six thousand won for an iced americano that tastes of "
       "nothing, in a cafe she will not go back to. A small, funny, "
       "universally understood disappointment.",
 text=
 "An iced americano in a tall plastic cup on a small marble table in a cafe "
 "in Seoul, the ice already melted into a pale layer at the top, a paper "
 "straw going soft, a wet ring on the table beside it and a crumpled napkin. "
 "A phone face down and a set of keys next to it. Through the window behind, "
 "a narrow street. Taken sitting, phone held low over the table, crooked. "
 "Everything sharp. Flat daylight, low contrast."),
]


# 9:16 frames, generated ONLY if the H3 reference-to-video test is run. A reel
# still is not a feed still: it is the FIRST FRAME of a clip, so it has to have
# somewhere to move to. Do not generate these speculatively.
# THE WEEK-2 REEL: R4, the showoff slot the plan already had.
#
# R4 was written as "the mirror — free if Flow holds her face". Flow does not:
# Omni Flash refuses her as a real person, and so do two other providers. The
# slot did not need a new concept, it needed a supplier — H3 on Kie, $0.52.
#
# w2r_mat_after is retired with the pilates reel it was the first frame of.
# That concept died on its own merits: nothing happens in it, the hook was
# mundane relatability, and it did not show her off. This does exactly one
# thing from the six-reason list, which is the one that works at zero
# followers, because it is the only reason that needs no relationship with the
# viewer: a good-looking person and a good outfit. The payoff is a PROFILE
# VISIT, and that is the metric that compounds from nothing.
#
# It is the reel FIRST FRAME, so it is 9:16 and lives in content/week2_reel.
# The mirror is the camera position, which is why there is no camera sentence
# in it: the phone in frame is the format, not the failure it is everywhere
# else. plate_hallway keeps the flat the same flat it has been all week.
REEL = [
    {
        "id": "w2r_fit_door",
        "day": "sat",
        "tier": "2k",
        "aspect": "9:16",
        "plate": "plate_hallway",
        "phone": True,
        "body": True,              # full length: the outfit IS the content
        "selfie": False,           # a mirror shot, not an arm's-length one
        "safe": True,
        "story": ("SAT 18:40. She is meeting Jieun at eight and she has "
                  "changed twice. This is the photograph you take to decide, "
                  "not the one you take because you have decided — she is "
                  "looking at the shorts, not at her face."),
        "text": (
            "A full-length mirror selfie by the front door of a small one-room "
            "flat in Seongsu, Seoul, early evening in late August. The whole "
            "frame is the mirror and she is her own reflection. A white iPhone 15 Pro held "
            "low at her hip and clearly visible, so her face is not covered. "
            # THE TOP COVERS THE RIBCAGE NOW, AND IT IS A PIPELINE FACT NOT A STYLING
            # ONE. Canon puts her tattoo on the LEFT RIBCAGE below the bra line
            # (body_block.txt). A cropped tank leaves that skin bare, and any
            # engine that takes a FIRST FRAME and no body reference -- Kling 3.0
            # takes image_urls and nothing else -- can only render what the frame
            # shows. A bare ribcage with no tattoo in it is a continuity break
            # against every c5-anchored still. Covering it removes the question.
            "A plain white cotton t-shirt tucked into the front of the "
            "shorts, an oversized pale blue striped "
            "cotton shirt worn open over it with the sleeves pushed up, "
            "high-waisted washed denim shorts, a small black shoulder bag on a "
            "short strap, plain white low sneakers. Hair down and slightly "
            "damp at the ends from the heat, one side tucked behind her ear. "
            "She is standing with her weight on one leg, head tipped a little, "
            "looking at the shorts in the reflection rather than at the lens, "
            "mouth closed. Around her: the shoe rack by the door with two "
            "other pairs on it, a coat hook, a light switch, the door frame. "
            "Everything sharp. Warm-white overhead cast mixed with low evening "
            "daylight from the room behind her, slightly underexposed, grainy."
        ),
    },
]
