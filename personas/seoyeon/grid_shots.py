"""
grid_shots.py — the twelve, written from grid_stories.md.

Each one is a dated moment in one real week, Mon 17 to Sun 23 August 2026.
Read grid_stories.md first: it holds the why, and the why is what produced
every physical detail below.

WHAT THE REFERENCE ALREADY CARRIES — so none of it is written here:
her face, her features, the freckles, her build, her hair colour, her skin.
Describing any of that again competes with the pixels. The prompt says the
PLACE, the MOMENT, the CAMERA and the EXPRESSION, because a1 contains none
of those.

TWELVE DIFFERENT EXPRESSIONS, described physically, no two alike. She has had
two faces for most of this project — neutral, or a soft smile.

FOUR OF TWELVE HAVE NO FACE. A real feed is photographs of a life, not
portraits of a person.

A DIFFERENT COLOUR CAST EACH. A real feed is inconsistent because it is
different hours, apps and phones — not one tasteful grade.

    python outside.py --grid --all --budget 1.2      (gpt-image-2, $1.08)
"""

SHOTS = [

# ---- MON 17 AUG · 07:04 ---------------------------------------- no face --
dict(id="n_studio_dawn", day="mon", tier="2k", aspect="3:4", noface=True,
 story="MON 07:04. Trainees get the slot nobody wants. She has the room for "
       "two hours. She photographs the floor because the light across it is "
       "the only good part of the arrangement.",
 text=
 "An empty pilates studio in Seongsu, Seoul, just after seven in the "
 "morning. One mat unrolled with a towel and a water bottle dropped on it, "
 "a bag on its side, rolled mats and foam rollers along the wall, a "
 "radiator, a bin, scuffed pale wood. A hard band of low sun lying across "
 "the boards. Taken standing, looking straight down, crooked. Everything "
 "sharp. Cold blue-white cast, contrasty, grainy."),

# ---- MON 17 AUG · 16:20 ---------------------------------------- no face --
dict(id="n_desk_late", limb=True, day="mon", tier="2k", aspect="3:4", noface=True,
 story="MON 16:20. Freelance afternoon, deck due Wednesday. Sat down at one. "
       "The table looks better than anything she did on it.",
 text=
 "A small dining table in a Seoul flat at the end of a working afternoon: "
 "a closed laptop, a mug with a dried coffee ring inside it, a charger "
 "cable running off the edge, an electric fan on the floor, a chair pushed "
 "back, a bare knee and a foot at the bottom edge of the frame. Low sun "
 "laid across the table. Taken looking down from a seated position, "
 "crooked. Everything sharp. Natural orange cast, blown out along the "
 "window edge."),

# ---- TUE 18 AUG · 21:15 ----------------------------------- taken by Jieun --
dict(id="n_cafe_jieun", day="tue", tier="2k", aspect="3:4", selfie=False,
 story="TUE 21:15. Jieun is avoiding going home. Seoyeon is talking herself "
       "into teaching tomorrow. She says something she finds funny and Jieun "
       "picks up her phone without warning.",
 text=
 "Sitting at a small table in a cafe in Euljiro, Seoul, in the evening, "
 "caught mid-word with her mouth open on a consonant, eyebrows up, one "
 "hand still raised in the middle of a gesture, looking just past the "
 "lens. A plain black t-shirt, her hair down and gone flat and slightly "
 "tangled after the day, pushed behind one ear. A tall glass close to the "
 "camera and half out of frame, the marble table edge large in the near "
 "foreground, bentwood chairs, other occupied tables, a service counter, a "
 "window black with evening. Taken from across the small table about a "
 "metre away with the phone held low at chest height, angled slightly up "
 "at her; she sits off-centre and the frame cuts her shoulder. Everything "
 "sharp. Cool flat cast, uneven, the counter brighter than she is."),

# ---- WED 19 AUG · 14:30 ------------------------------------------ selfie --
dict(id="n_studio_taught", day="wed", tier="2k", aspect="3:4", selfie=True,
 story="WED 14:30. She taught a practice class for the first time. It went "
       "fine. She wants it recorded that she did it, and what comes back is "
       "not triumph, it is an empty face.",
 text=
 "Sitting on a mat in a busy pilates studio in Seongsu, Seoul, in the "
 "afternoon, flushed, chin down, mouth closed, eyes level and completely "
 "blank, sweat at her hairline and temples. A black sports bra and "
 "leggings, hair in a low bun coming apart. Two other women on mats "
 "further back mid-class not looking at her, a towel dropped on the mat "
 "behind her, bags and bottles along the wall, a mirrored wall at the far "
 "end. Front camera at arm's length: her forearm fills the bottom third, "
 "much larger than her head and stretched by the lens, hand past the edge, "
 "her other hand flat on the mat beside her. Framing crooked, her head "
 "near the top. Everything sharp. Flat grey cast, slightly overexposed."),

# ---- WED 19 AUG · 23:10 ------------------------------------------ selfie --
dict(id="n_conv_yawn", day="wed", tier="2k", aspect="3:4", selfie=True,
 story="WED 23:10. Eleven hours after the class she goes down for something to "
       "eat. She catches herself in the freezer glass and thinks, against "
       "expectation, that she looks fine. One photo, deadpan, back upstairs. "
       "NOT a yawn: you cannot see yourself yawn, it happens after the button, "
       "and it gets deleted.",
 text=
 "Standing in the aisle of a Seoul convenience store late at night, "
       "mouth closed and pushed slightly to one side, one eyebrow marginally "
       "higher than the other, eyes level and unimpressed — the face of "
       "someone who has been awake too long and has decided she looks fine "
       "anyway. An oversized grey t-shirt, hair up in a claw clip with strands "
       "escaping. The aisle and shelves stretching back behind her, a chest "
       "freezer, a bin, the counter at the far end. Front camera at arm's "
       "length held low, her forearm large and close along the bottom edge, "
       "hand past the frame, her other hand down at her side, crooked. "
       "Everything sharp, the whole aisle in focus. Green-white cast, flat."),

# ---- THU 20 AUG · 15:40 ---------------------------------------- no face --
dict(id="n_market", day="thu", tier="2k", aspect="3:4", noface=True,
 story="THU 15:40. Thirty-four degrees. She walked because the delivery "
       "minimum costs more than she wants to spend. The peaches are absurd "
       "this week. She is showing the fruit.",
 text=
 "A fruit stall in a Seoul market in the afternoon: crates of peaches in pink "
 "foam netting and boxes of plums at the front, handwritten price cards, a "
 "green plastic awning overhead, a weighing scale, stacked polystyrene boxes, "
 "shop signage, other stalls and shoppers walking away down the aisle, wet "
 "ground. Taken from standing height looking down into the crates, crooked, a "
 "shoulder cutting the near corner. Everything sharp. Warm green cast from "
 "the awning, flat."),

# ---- THU 20 AUG · 16:05 ------------------------------------------ selfie --
dict(id="n_street_bag", day="thu", tier="2k", aspect="3:4", selfie=True,
 story="THU 16:05, twenty-five minutes later. The bag is cutting into her "
       "fingers on a hill she chose to walk. It is ridiculous and she still "
       "looks fine, which is exactly the picture people post about heat.",
 text=
 "Standing in the shade halfway up a narrow residential back street in "
 "Seoul in the afternoon heat, a heavy shopping bag of fruit in one hand "
 "at her side, her mouth pressed into a flat line and her eyebrows up, "
 "damp hair stuck at her temples. A white cotton t-shirt with a sweat mark "
 "at the collarbone, black shorts, hair scraped into a high ponytail. "
 "Brick walls, air-conditioning units, bins, parked scooters, the sunlit "
 "road beyond her burnt out to white. Front camera at arm's length, her "
 "forearm large and close in the lower frame, hand past the edge, horizon "
 "off level. Everything sharp. Bleached high-contrast cast."),

# ---- THU 20 AUG · 19:30 ------------------------------------------ selfie --
dict(id="n_river_sun", day="thu", tier="2k", aspect="3:4", noface=True,
 story="THU 19:30. The sun goes down behind the bridge and the whole river "
       "turns. It is so obvious, so postcard, so exactly the thing everyone "
       "photographs — and the honest version is that she photographs THE "
       "SUNSET, not herself in front of it. She is not in this one.",
 text=
 "The Han river in Seoul at sunset seen from the riverside park path: the "
 "low sun going down behind a bridge, the water burnt out to white and "
 "glittering under it, cyclists and walkers on the path, a metal railing "
 "across the near foreground, apartment towers on the far bank, a bench. "
 "Taken standing, phone held up into the light, crooked, flare across the "
 "frame. Everything sharp. Warm hazy cast, heavily overexposed toward the "
 "sun."),

# ---- FRI 21 AUG · 20:50 ---------------------------------------- no face --
dict(id="n_noodles", locked=True, limb=True, day="fri", tier="2k", aspect="3:4", noface=True,
 story="FRI 20:50. Course weekend starts tomorrow, so this is the last proper "
       "meal before three long days. She is not letting it go cold for a "
       "photograph.",
 text=
 "A bowl of kalguksu, hand-cut noodle soup, on a steel table in a small "
 "late-night noodle shop in Seoul, steam coming off it, kimchi and pickled "
 "radish in small metal side dishes, a stainless cup of water, a napkin "
 "dispenser, a tray, the shop's empty stools and steel tables behind. One "
 "forearm comes in from the right edge holding steel chopsticks over the "
 "bowl, the hand mid-motion, the rest of her out of frame. Taken looking "
 "down at her own table from where she is sitting, close, crooked. "
 "Everything sharp. Yellow-green fluorescent cast, flat."),

# ---- SAT 22 AUG · 18:40 ------------------------------------------ mirror --
dict(id="n_mirror_dress", phone=True, safe=True, locked=True, day="sat", tier="2k", aspect="3:4", selfie=False,
 story="SAT 18:40. Jieun turns 27 and there is dinner. Seoyeon almost never "
       "dresses up and wants it recorded before the evening ruins it. She is "
       "not smiling at herself, she is checking.",
 text=
 "A full-length mirror selfie in the narrow hallway of a small Seoul flat "
 "in the evening, the phone held up in front of her chest and clearly "
 "visible, partly covering her. Her eyes slightly narrowed and her mouth "
 "closed and neutral, the face someone makes deciding whether an outfit is "
 "working. A short black dress, a small bag on a chain at her shoulder, "
 "hair down. The whole hallway around her: shoes left out by the door, a "
 "coat on a hook, a light switch, a doorway into a dark room, a laundry "
 "rack just visible. Everything sharp. Dim warm cast, underexposed, "
 "grainy."),

# ---- SAT 22 AUG · 23:50 ------------------------------------ propped/posed --
dict(id="n_roof_posed", locked=True, safe=True, day="sat", tier="2k", aspect="3:4", body=True,
 selfie=False,
 story="SAT 23:50. Home before midnight because of practice hours, not ready "
       "to go inside. She sets the phone on a ledge and walks into frame — "
       "wanting the whole outfit in it is the only reason worth that effort.",
 text=
 "Standing full length on the roof of an apartment building in Seoul near "
 "midnight, waiting for the timer to go, arms hanging at her sides, weight "
 "even on both feet, mouth closed. The same short black dress and small "
 "shoulder bag. Water tanks, a satellite dish, ducting, a drying rack with "
 "washing still on it, the open lit stairwell doorway behind her, the "
 "windows of low buildings below the parapet. The phone has been set down "
 "on a ledge a few steps away and left running: the frame sits too low and "
 "off level, and she stands off to one side of it with more roof around "
 "her than she wanted. The roof clutter and the buildings behind are as "
 "much in focus as she is. Dark and underexposed, heavy noise in the "
 "shadows, a little soft on her because it is midnight."),

# ---- SUN 23 AUG · 17:20 ------------------------------------------ selfie --
dict(id="n_grass_laugh", day="sun", tier="2k", aspect="3:4", selfie=True,
 story="SUN 17:20. An hour on the grass doing very little. Jieun says "
       "something about the exam and she laughs properly. She keeps the frame "
       "where she looks terrible because it is the only one this week where "
       "she looks happy.",
 text=
 "Sitting on the grass at Seoul Forest park in Seoul in the late "
 "afternoon, caught in the middle of a real laugh: upper teeth showing, "
 "eyes creased shut, head tipped back, chin softened, cheeks lifted. Knees "
 "up with one arm around them. A black vest top and loose jeans, worn "
 "white trainers, hair down and messy. Grass, a path, trees, a parked car "
 "and an apartment block behind her. Front camera at arm's length held "
 "low, her forearm close along the bottom, hand past the edge, tilted. "
 "Everything sharp. Golden-green cast, hazy, low contrast."),
]

REEL = []   # rebuilt after the grid lands
