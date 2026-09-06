"""
outside_shots.py — 29 individually written prompts.

No blocks, no field assembly. Each prompt is one authored description, so
nothing can contradict anything else: the coat cannot appear in a scene without
one, a selfie cannot have folded arms, a wall cannot carry writing that the
lens is meant to blur. Every element is woven — action, expression, clothes,
hair, place, camera, lens — the way you would describe a photograph you had
actually seen.

`tier` is per shot: 2k where she is small in the frame and the face needs the
pixels, 1k otherwise. `aspect` defaults to 3:4 for the feed; 9:16 shots are
for Stories and Reel covers, which is where profile visits and link taps
actually come from.

NEVER generate text. Overlays like "first snow in seoul" are typed in the
editor afterwards — free, perfectly legible, and the opposite of the gibberish
the models produce.
"""

SHOTS = [
# ---------------------------------------------------------------- park
dict(id="park_walk", tier="2k", body=True, text=
 "Walking a wooded path in Seoul Forest on a cold afternoon, bare plane trees "
 "and damp dark ground around her, the light flat and grey. Her free hand is "
 "up pushing her hair out of her face and she is half-smiling at nothing, "
 "looking past the lens at something off to one side. Long charcoal wool coat "
 "over a cream knit, dark jeans. Hair down in soft waves, centre-parted with "
 "curtain bangs, moving in the wind. She is holding the phone herself at arm's "
 "length on the front camera: a 23mm-equivalent lens close to her face, so the "
 "trees fall away behind her and her features stretch very slightly, her "
 "extended arm cutting into the bottom corner, the horizon a few degrees off "
 "level. Softer and noisier than the rear camera, flat HDR contrast, low "
 "saturation, pores and small unevenness in her skin. Nothing behind her but "
 "bark, earth and sky."),

dict(id="park_bench", tier="2k", text=
 "Sitting on a wooden bench in Seoul Forest with a paper cup in her free hand, "
 "coat open over a black roll-neck, dark jeans, cheeks cold-flushed. "
 "Hair half-up in a claw clip with the lengths loose below it. She is looking "
 "into the lens with the small unbothered expression of somebody taking a "
 "photograph for herself rather than for anyone. Front camera at arm's length, "
 "23mm equivalent, the bare trees and grey sky soft behind her, her extended "
 "arm cutting into one corner, the cup held low in the other. Slight "
 "perspective stretch, softer and noisier than the rear lens, flat contrast, "
 "low saturation, real skin texture. Only bark, bench slats and sky behind."),

dict(id="park_tree", tier="2k", body=True, text=
 "Standing under a bare plane tree looking up into the branches, chin lifted, "
 "mouth slightly open, entirely absorbed. Cream knit jumper under a light "
 "windbreaker, dark leggings, hair down and tucked behind both ears. Taken by somebody "
 "she asked, standing further back than she would have chosen, so "
 "a lot of the wood is in frame around her and she sits small and off-centre "
 "against the grey sky. Shot on an iPhone 16 Pro, flat HDR contrast, low "
 "saturation, deep focus, fine shadow noise, the framing a degree off level. "
 "Bark, branches and overcast sky fill the rest of the frame."),

dict(id="park_close", tier="2k", text=
 "Very close, three-quarter, cold-flushed cheeks and the ends of her hair "
 "moving across her face, eyes narrowed against the wind, the beginning of a "
 "laugh. Long charcoal wool coat with the collar up over a cream knit. Hair "
 "down in soft waves, centre-parted with curtain bangs. Front camera at arm's "
 "length, 23mm equivalent so her features stretch very slightly and the woods "
 "dissolve to grey and brown behind her, her extended arm just in the corner. "
 "Softer and noisier than the rear lens, flat HDR contrast, low saturation, "
 "visible pores, one strand stuck to her lip."),

# ---------------------------------------------------------------- restaurant
dict(id="rest_talking", tier="2k", text=
 "Sitting at a steel table in a small Seoul noodle restaurant mid-sentence, "
 "one hand raised slightly, talking to somebody across from her who is out of "
 "frame. Oversized grey blazer over a white shirt, dark jeans. Hair half-up in "
 "a claw clip. Behind her a plain white-tiled wall with a wall fan mounted "
 "above it, strip lighting overhead, other diners at the far tables out of "
 "focus. Taken by whoever she is eating with, from across the table, slightly "
 "off-centre and a degree off level. Shot on an iPhone 16 Pro, flat HDR "
 "contrast, low saturation, deep focus, fine shadow noise, real skin texture. "
 "Bare tile, brushed steel and painted metal, every surface plain."),

dict(id="rest_bowl", tier="2k", text=
 "Leaning over a steaming bowl of noodles at a steel table, chopsticks in her "
 "free hand, pleased with herself, looking straight into the lens. Black "
 "roll-neck tucked into dark jeans, hair up in a low bun with a few pieces "
 "escaping at the nape. A plain white-tiled wall directly behind her, a wall "
 "fan above it, strip lighting, the room warm and busy. Front camera at arm's "
 "length: 23mm equivalent, her features stretching very slightly, her extended "
 "arm cutting into one corner and holding the only phone in the picture. "
 "Softer and noisier than the rear lens, flat contrast, low saturation, steam "
 "catching the light, pores visible. Tile, steel and ceramic, nothing printed."),

dict(id="rest_lean", tier="2k", text=
 "Leaning back after eating with one shoulder against the tiled wall, warm and "
 "slightly sleepy, giving the lens a flat look. Oat knit sweater over a white "
 "shirt with the collar out, dark jeans. Hair half-up in a claw clip, pieces "
 "come loose around her face. Steel table in front of her, wall fan above, "
 "strip lighting, other diners far behind and out of focus. Front camera at "
 "arm's length, 23mm equivalent, her extended arm in the corner, her other "
 "hand resting on the table. Softer and noisier than the rear camera, flat HDR "
 "contrast, low saturation, skin showing pores and small unevenness. Plain "
 "white tile behind her and nothing on it."),

dict(id="gym_bench", tier="2k", text=
 "Sitting on a bench between sets in a small neighbourhood gym, red-faced and "
 "unimpressed, hair stuck to her temple, looking straight into the lens. Matte "
 "black cropped long-sleeve top and black leggings, hair in a low bun coming "
 "apart. Rubber floor, black weight racks and plain painted walls behind her. "
 "Front camera at arm's length, 23mm equivalent, her extended arm cutting into "
 "the corner, her other forearm on her knee. Softer and noisier than the rear "
 "lens, flat contrast, low saturation, sweat on her hairline, pores and "
 "flushed skin. Painted wall, rubber and black steel, nothing else."),

dict(id="gym_mirror", tier="2k", text=
 "Her reflection in the mirrors of a small gym, phone held at chest height in "
 "one hand and visible in the shot, her other hand up in her hair, checking "
 "the frame rather than posing. Matte sage ribbed two-piece activewear set, "
 "hair in a low bun. The room reversed behind her: rubber floor, black racks, "
 "plain painted walls, strip lighting. Slightly rolled, her head near the top "
 "edge. Shot on an iPhone 16 Pro through the glass, flat HDR contrast, low "
 "saturation, faint smears on the mirror, fine noise, skin showing pores. "
 "Mirror, painted wall and black steel, every surface plain."),

dict(id="gym_after", tier="2k", text=
 "Face still red after training, hair coming loose from a high ponytail, "
 "giving the lens a flat look with her eyebrows slightly up. Matte sage ribbed "
 "two-piece activewear set. Plain painted gym wall and a black rack behind "
 "her, strip lighting overhead. Front camera at arm's length, 23mm equivalent, "
 "her features stretching very slightly, her extended arm cutting into a "
 "corner. Softer and noisier than the rear camera, flat contrast, low "
 "saturation, damp hairline, real pores and blotchy colour in her cheeks."),

# ---------------------------------------------------------------- street
dict(id="street_glance", tier="2k", body=True, text=
 "Walking away down a Seongsu-dong side street in the late afternoon and "
 "glancing back over her shoulder, coat swinging, caught mid-step. Long "
 "charcoal wool coat over a black roll-neck, dark jeans, white trainers. Hair "
 "down in soft waves. Red brick close behind her, roller shutters down on the "
 "units, scooters parked at angles, long shadows across the pavement. Taken by "
 "somebody walking with her, from a few steps back, so she is off-centre and "
 "the framing is a degree off level. Shot on an iPhone 16 Pro, flat HDR "
 "contrast, low saturation, deep focus, fine shadow noise. Brick, painted "
 "shutter and worn asphalt, all of it plain."),

dict(id="street_crossing", tier="2k", body=True, text=
 "Waiting at a crossing with traffic moving behind her, tired and patient, "
 "looking past the lens rather than into it, barely bothering with the shot. "
 "Black puffer jacket over a grey sweatshirt, dark jeans. Hair pulled through "
 "the back of a plain black cap with the ends loose. Late afternoon on a "
 "Seongsu-dong street, brick and shuttered units behind, strangers around her "
 "out of focus. Front camera at arm's length, 23mm equivalent, the street "
 "falling away behind her, her extended arm in the corner, horizon off level. "
 "Softer and noisier than the rear lens, flat contrast, low saturation."),

dict(id="street_window", tier="2k", text=
 "Caught in a shopfront window as she passes, the street doubled in the "
 "glass, one hand shifting the strap of her bag, phone held at chest height "
 "and visible in the reflection, her weight already moving to the next step. "
 "Oat knit sweater over a white shirt with the collar out, dark jeans. Hair "
 "down and tucked behind both ears. Brick and shuttered units reversed "
 "behind her, low sun across the pavement, framing slightly rolled. Shot on "
 "an iPhone 16 Pro through glass, flat HDR contrast, low saturation, "
 "reflections doubling, fine noise, real skin texture. Glass, brick and "
 "painted metal, every surface plain."),
dict(id="street_backlit", tier="2k", text=
 "Backlit by the low sun on a Seongsu-dong street, squinting into it and "
 "laughing, the brick behind her bright and half blown out. Long charcoal wool "
 "coat over a cream knit. Hair down in soft waves, lit at the edges. Front "
 "camera at arm's length, 23mm equivalent, her features stretching very "
 "slightly, her extended arm cutting into the frame, the horizon tilted. "
 "Softer and noisier than the rear camera, flat HDR contrast that lifts the "
 "shadows, low saturation, lens flare across one corner, pores and fine hair "
 "visible against the light."),

dict(id="street_step", tier="2k", text=
 "Sitting on a low step with a paper coffee cup, legs stretched out in front "
 "of her, chin down, expression flat and content, looking off to the side "
 "rather than at the lens. Oversized grey sweatshirt and wide linen trousers, "
 "white trainers. Hair half-up in a claw clip. The Seongsu-dong street over "
 "her shoulder, brick, shuttered units, long shadows. Front camera at arm's "
 "length held slightly above her, 23mm equivalent, her extended arm in the "
 "corner, more empty step on one side than she needs. Softer and noisier than "
 "the rear lens, flat contrast, low saturation."),

# ---------------------------------------------------------------- cafe
dict(id="cafe_listen", tier="2k", text=
 "Both elbows on a cafe table with a cup in front of her, listening to someone "
 "across from her who is out of frame, faintly amused. Oat knit sweater over a "
 "white shirt with the collar out. Hair half-up in a claw clip. Warm wood and "
 "brass, trailing plants along a plain painted back wall, other customers "
 "thrown out of focus, window light from the left. Taken by the person she is "
 "sitting with, from across the table, slightly off-centre. Shot on an iPhone "
 "16 Pro, flat HDR contrast, low saturation, deep focus, fine noise, skin "
 "showing pores. Painted wall, wood, brass and leaves, nothing printed."),

dict(id="cafe_laugh", tier="2k", text=
 "Mid-laugh at a cafe table, head tipped back, eyes almost shut, one hand near "
 "her mouth. Black roll-neck tucked into dark jeans. Hair half-up in a claw "
 "clip with pieces falling loose. Warm wood and brass, plants on a plain "
 "painted wall, window light from the left, the room busy and out of focus "
 "behind her. Taken by whoever made her laugh, from across the table, caught a "
 "beat late so the framing is loose and a degree off level. Shot on an iPhone "
 "16 Pro, flat HDR contrast, low saturation, deep focus, real skin texture."),

dict(id="cafe_chin", tier="2k", text=
 "Chin on her hand at a cafe table, just turning back toward the lens with "
 "her eyes half on it and half still somewhere else, the room warm and busy "
 "behind her. Oversized grey blazer over a white shirt. Hair down in soft "
 "waves, centre-parted with curtain bangs. Warm wood and brass, trailing "
 "plants on a plain painted wall, window light from the left. "
 "Front camera at arm's length, 23mm equivalent, the cafe falling away behind "
 "her, her extended arm cutting into a corner and her other hand under her "
 "chin. Softer and noisier than the rear lens, flat contrast, low saturation, "
 "pores and fine hair visible."),

dict(id="cafe_reach", tier="2k", text=
 "Reaching for her cup mid-conversation, eyes still on the "
 "person opposite, mouth slightly open. Oversized grey sweatshirt and wide "
 "linen trousers. Hair down in soft waves. A cafe table in warm wood, brass "
 "fittings, plants on a plain painted wall, window light from the left, other "
 "customers blurred behind. Taken by the person across from her, catching her "
 "mid-movement so one hand is soft with motion. Shot on an iPhone 16 Pro, flat "
 "HDR contrast, low saturation, deep focus, fine shadow noise."),

# ---------------------------------------------------------------- market
dict(id="market_peach", tier="2k", text=
 "Holding a peach up to look at it in a covered Seoul market, head slightly "
 "tilted, deciding, looking at the fruit rather than the lens. Black puffer "
 "jacket over a grey sweatshirt, dark jeans. Hair pulled through the back of a "
 "plain black cap. Loose produce heaped in shallow baskets around her, hanging "
 "bulbs, plastic sheeting overhead, a plain painted wall beside her, the aisle "
 "falling out of focus behind. Front camera at arm's length, 23mm equivalent, "
 "her extended arm in the corner and the peach in her free hand. Softer and "
 "noisier than the rear lens, flat contrast, low saturation, warm bulb light "
 "on her face."),

dict(id="market_aisle", tier="2k", body=True, aspect="3:4", text=
 "Standing in a market aisle with a canvas tote over one shoulder, half turned "
 "back toward the lens as somebody says her name, the crowd moving around her. "
 "Long charcoal wool coat over a cream knit, dark jeans. Hair pulled through a "
 "plain black cap with the ends loose at her shoulders. Heaped produce in "
 "shallow baskets, hanging bulbs, plastic sheeting overhead, warm and crowded. "
 "Taken by somebody a few steps behind her, framing loose and a degree off "
 "level. Shot on an iPhone 16 Pro, flat HDR contrast, low saturation, deep "
 "focus, fine noise, natural head-to-body proportion."),

dict(id="river_grass", tier="2k", text=
 "Sitting on the grass by the Han river with her arms around her knees and the "
 "last light on her face, quiet, barely smiling into the lens. Cream knit "
 "jumper under a light windbreaker, dark leggings. Hair down in soft waves, "
 "centre-parted. Wide dusk sky, apartment towers soft on the far bank, the "
 "water flat. Front camera at arm's length held low, 23mm equivalent, so the "
 "sky opens out behind her and her extended arm cuts into the bottom corner. "
 "Softer and noisier than the rear lens, flat HDR contrast, low saturation, "
 "warm light on one side of her face and cool sky fill on the other."),

dict(id="river_rail", tier="2k", text=
 "Standing at the river rail with her back to the camera, hair moving in the "
 "wind, the water and the far bank beyond her. Long charcoal wool coat over a "
 "black roll-neck, dark jeans. Hair in a high ponytail lifting off her "
 "shoulders. Dusk, wide sky, apartment towers muted behind, joggers passing "
 "out of focus. The phone has been set down on the rail and left running, so "
 "the framing is low and loose with more sky than she needs. Shot on an iPhone "
 "16 Pro, flat HDR contrast, low saturation, deep focus, fine noise."),

dict(id="river_laugh", tier="2k", text=
 "Mid-laugh with the last light behind her, hair lit at the edges, the river "
 "out of focus beyond. Long charcoal wool coat over a cream knit. Hair down in "
 "soft waves, centre-parted with curtain bangs. Dusk on the Han path, wide sky "
 "going orange low down, towers dark on the far bank. Front camera at arm's "
 "length, 23mm equivalent, the light flaring slightly into the lens, her "
 "extended arm cutting into a corner, horizon a few degrees off. Softer and "
 "noisier than the rear camera, flat contrast that lifts the shadows, low "
 "saturation, backlit fine hair, pores visible."),

dict(id="river_walk", tier="2k", body=True, text=
 "Walking the river path at dusk with a convenience-store coffee, seen from a "
 "distance so she is small in the frame with the wide sky above her and the "
 "path running away behind. Oversized grey sweatshirt and wide linen trousers, "
 "white trainers. Hair pulled through a plain black cap. Apartment towers "
 "muted on the far bank, joggers passing. Taken by somebody who has walked on "
 "ahead and turned round, framing loose and off-centre. Shot on an iPhone 16 "
 "Pro, flat HDR contrast, low saturation, deep focus, fine noise in the "
 "shadows."),
# ---- added after studying real fitness/lifestyle grids -------------------
# What those accounts do that we were not doing:
#   * full body dominates; a fitness feed shows the BODY, not the face
#   * backgrounds are far plainer than I was writing — a bare wall and a wooden
#     floor is the actual format, and it is also the lowest-risk one for text
#   * walking away and from-behind shots are common and read as unposed
#   * athleisure is the default wardrobe, not the exception
#   * expressions are much bigger than our uniformly quiet register
dict(id="room_full", tier="2k", body=True, text=
 "Standing in the middle of an empty room against a bare white wall, wooden "
 "floor, weight on one hip, one hand loose at her side, looking straight into "
 "the lens with a flat unbothered expression. Matte black cropped long-sleeve "
 "top and black cycling shorts, bare feet, hair in a low bun. The room is "
 "almost empty: white wall, skirting, floorboards, a door frame at the edge. "
 "The phone has been set down across the room and left running, so she is "
 "small and centred badly with too much floor at the bottom. Shot on an iPhone "
 "16 Pro, flat HDR contrast, low saturation, deep focus, fine noise, real skin "
 "texture and the light entirely from one window out of frame."),

dict(id="park_run", tier="2k", body=True, text=
 "Running away from the camera along a paved park path under green trees, seen "
 "from behind, mid-stride, ponytail swinging, small in the frame with the path "
 "running away ahead of her. Black cropped top and black running shorts, white "
 "socks and trainers, hair in a high ponytail through a plain black cap. Dappled "
 "green light, empty path, plain tarmac and grass. Taken by somebody standing "
 "still as she went on ahead. Shot on an iPhone 16 Pro, flat HDR contrast, low "
 "saturation with the greens muted rather than vivid, deep focus, fine noise."),

dict(id="street_bus", tier="2k", body=True, text=
 "Standing at a Seoul bus stop waiting, weight on one leg, looking down the "
 "road away from the lens, entirely unposed and slightly bored. Oversized grey "
 "sweatshirt over black cycling shorts, white socks and trainers, hair through "
 "a plain black cap. Grey shelter frame, kerb, a plain painted wall behind, "
 "the road out of focus. Taken by somebody standing a few metres off, so she "
 "sits small and off-centre with a lot of pavement in frame. Shot on an iPhone "
 "16 Pro, flat HDR contrast, low saturation, deep focus, fine shadow noise."),

dict(id="gym_full", tier="2k", body=True, text=
 "Standing full length in front of the gym mirrors with the phone held at hip "
 "height in one hand and visible in the reflection, weight on one leg, giving "
 "the mirror a completely flat look. Matte black sports bra and black cycling "
 "shorts, hair in a high ponytail. The room reversed behind her: rubber floor, "
 "black racks, plain painted walls, strip lighting overhead. Framing loose and "
 "slightly rolled with her head near the top edge. Shot on an iPhone 16 Pro "
 "through the glass, flat HDR contrast, low saturation, faint smears on the "
 "mirror, harsh overhead light, fine noise, skin showing pores and texture."),

dict(id="cafe_openmouth", tier="2k", text=
 "Caught mid-word with her mouth open and one eyebrow up, mock-outraged at "
 "something said across the table, hand half-raised. Black roll-neck, hair "
 "half-up in a claw clip. Warm wood and brass, plants on a plain painted wall, "
 "window light from the left, the room busy and out of focus. Taken by the "
 "person opposite, a beat too late so the framing is loose and her hand is "
 "soft with motion. Shot on an iPhone 16 Pro, flat HDR contrast, low "
 "saturation, deep focus, fine noise, unflattering and completely alive."),

dict(id="river_stairs", tier="2k", body=True, text=
 "Walking up concrete steps from the river path, seen from below and behind, "
 "mid-stride, one hand on the rail, small in the frame with the wide dusk sky "
 "above her. Cream knit jumper under a light windbreaker, dark leggings, hair "
 "in a high ponytail. Plain concrete, metal rail, muted towers on the far "
 "bank. The phone has been set down at the bottom of the steps and left "
 "running, so the angle is low with too much sky. Shot on an iPhone 16 Pro, "
 "flat HDR contrast, low saturation, deep focus, fine noise in the shadows."),
# ---- added for the FUNNEL, not the format --------------------------------
# The account converts on parasocial intimacy: a stranger has to want her, not
# her routine. Direct eye contact is the strongest lever we have and we were
# underusing it. These are the frames that carry pull rather than information.
dict(id="rooftop_night", tier="2k", text=
 "On a rooftop at night with the city lit behind her, close, looking straight "
 "into the lens with a small private smile, as though she has just said "
 "something quietly to whoever is watching. An oversized grey knit slipping "
 "off one shoulder over a thin strap, bare collarbone, hair down and messy "
 "from the wind. Warm window lights soft and out of focus far behind, cool "
 "dark sky. Front camera at arm's length, 23mm equivalent so her face fills "
 "much of the frame and the city falls away, her extended arm cutting into a "
 "corner, horizon tilted. Softer and noisier than the rear lens, high ISO "
 "grain in the shadows, flat contrast, low saturation, real skin texture."),

dict(id="stairwell_late", tier="2k", text=
 "In a dim apartment stairwell late at night, leaning back against the wall on "
 "the landing, head tipped back against the tile, still getting her breath "
 "after the stairs, one eyebrow up at the lens. Long charcoal coat open over a plain white tee and dark jeans, hair "
 "down and falling forward. Plain painted wall, a metal handrail, one bare "
 "bulb above throwing hard light down her face. Front camera at arm's length, "
 "23mm equivalent, her extended arm in the corner, framing crooked. Softer and "
 "noisier than the rear lens, heavy grain in the dark, flat contrast, low "
 "saturation, skin uneven and alive under the hard light."),

dict(id="beach_walk", tier="2k", body=True, text=
 "Walking at the edge of the water on a grey off-season beach, seen from a way "
 "back so she is small against the sand and the flat sea, holding her shoes in "
 "one hand, looking down at the water. Cream knit jumper and rolled dark "
 "jeans, bare feet, hair loose and moving. Empty sand, pale sky, a long line "
 "of surf. Taken by somebody who has stopped walking to let her go on ahead. "
 "Shot on an iPhone 16 Pro, flat HDR contrast, low saturation with the greys "
 "and sand muted, deep focus, fine noise, the horizon a degree off level."),
# ---- vertical, warm, seasonal -------------------------------------------
# From studying real Seoul lifestyle accounts. Three things they do that we
# were not: they shoot VERTICAL for stories and reels, they are openly warm
# looking down the lens, and they use the season as a reason to post.
# The warmth is not a break from her character — she is dry in public and warm
# when she is looking straight at you, and that asymmetry IS the parasocial
# mechanism the funnel runs on.
dict(id="wink_close", tier="2k", aspect="9:16", text=
 "Very close, head slightly tipped, one eye closed in a small deliberate wink "
 "and the other bright on the lens, a real open smile, one hand up near her "
 "jaw. A soft black V-neck knit with the collarbone showing, hair down and "
 "straight over one shoulder. Behind her a plain white-tiled wall and a pale "
 "door frame, soft even daylight from the front so the shadows are gentle. "
 "Front camera at arm's length, 23mm equivalent, her face filling most of the "
 "tall frame, her extended arm just in the corner. Softer and noisier than the "
 "rear lens, flat contrast, low saturation, real pores and the fine hairs at "
 "her temple catching the light."),

dict(id="snow_street", tier="2k", aspect="9:16", text=
 "Standing on a Seoul street on the first snow of the year, snow falling "
 "visibly through the streetlight, laughing openly at the lens with her "
 "shoulders up, both delighted and cold. Cream shearling coat over a black "
 "roll-neck, a soft white knitted beanie, hair down over her shoulders with "
 "snow caught in it. Warm shop lights and traffic far behind her, thrown "
 "completely out of focus into round bokeh. Front camera at arm's length, 23mm "
 "equivalent, the street falling away behind her, framing tilted, her extended "
 "arm in the corner. Softer and noisier than the rear lens, high ISO grain in "
 "the dark, warm light on her face against the cold blue night."),

dict(id="night_walk", tier="2k", aspect="9:16", text=
 "Walking a Seoul street at night with the city lit behind her, half turned "
 "back toward the lens, warm and unguarded, hands pushed into her coat "
 "pockets. Long charcoal wool coat over a cream knit, dark jeans, hair down "
 "and moving. Shopfront lights and traffic thrown far out of focus into warm "
 "round bokeh, wet tarmac holding the reflections. Taken by somebody walking "
 "with her, from a step behind, framing loose and off level. Shot on an iPhone "
 "16 Pro at night, flat HDR contrast that lifts the shadows, low saturation, "
 "visible grain, motion softness in one hand."),

dict(id="vlog_coffee", tier="2k", aspect="9:16", text=
 "Mid-walk on a Seoul side street holding a takeaway coffee up beside her "
 "face as if presenting evidence of it, eyebrows raised at the lens, mouth "
 "pressed shut against saying anything. Olive utility jacket over a black top and black shorts, bare legs, "
 "hair down. Red-painted bike lane, a brick wall and a low kerb behind her, "
 "flat overcast daylight. Front camera at arm's length held slightly above "
 "her, 23mm equivalent, her extended arm cutting into the bottom corner, the "
 "street tilting away. Softer and noisier than the rear lens, flat contrast, "
 "low saturation, real skin texture. Every surface plain brick and painted "
 "tarmac."),

dict(id="cafe_window_night", tier="2k", aspect="9:16", text=
 "Sitting by a cafe window after dark with one hand around a warm cup, "
 "leaning in toward the lens with a soft direct smile, as though she is "
 "listening to you rather than talking. Oversized oat knit slipping off one "
 "shoulder over a white strap, hair down and tucked behind one ear. Warm "
 "interior lamps, the black window beside her holding a faint reflection, a "
 "plain painted wall behind. Front camera at arm's length, 23mm equivalent, "
 "her face high in the tall frame. Softer and noisier than the rear lens, warm "
 "low light with grain in the shadows, flat contrast, low saturation, pores "
 "and small unevenness visible."),
# ---- profile picture -----------------------------------------------------
# The highest-stakes single image on the account, and it is judged in 100ms.
# Willis & Todorov (2006): a 100ms exposure is enough to form a trait
# inference, and TRUSTWORTHINESS correlates most strongly with unconstrained
# judgement (r=.73) — ahead of attractiveness (r=.69). Both are decided before
# anyone reads a word of the bio.
# What the evidence says to do:
#   * SMILE. The Airbnb study in J. Consumer Research found smiling raised
#     warmth AND competence — there is no serious-equals-credible tradeoff.
#   * SHOW TEETH. Hinge data: women showing teeth were 76% more likely to be
#     liked than closed-mouth. The first version of this prompt got that wrong.
#   * MAKE IT DUCHENNE. A real smile involves the eyes — cheeks raised, lower
#     lids pushed up, crow's feet. Without those it reads pasted on, which
#     costs trust instead of building it.
#   * DO NOT MAKE IT A HEADSHOT. An evenly lit face on a seamless wall reads as
#     corporate stock photography, which signals brand rather than person.
#     A real room, thrown out of focus, keeps the background simple in TONE
#     while staying somewhere she actually is.
# And it still has to survive the crop: Instagram renders it as a circle at
# 110px on the profile and ~32px beside every comment and DM. Face large, head
# centred with headroom, hair off the face, background simple in tone.
dict(id="profile_pic", tier="2k", aspect="1:1", text=
 "Head and shoulders, her face large and centred with a little space above her "
 "head, caught in the middle of a real laugh at something just said off "
 "camera — teeth showing, cheeks pushed up, eyes narrowed to creases with "
 "fine lines at the outer corners, looking into the lens. Behind her the "
 "corner of a bright room thrown out of focus into soft pale shapes, a window "
 "to one side. Warm daylight across her face from the front and slightly to "
 "one side, brighter on one cheek, the shadows open. A black scoop-neck top, "
 "one small gold hoop. Hair down and pushed back off her face and behind her "
 "shoulders, centre-parted with the curtain bangs swept aside. Taken by a "
 "friend a couple of metres away on an iPhone 16 Pro at 2x, flat HDR "
 "contrast, low saturation, framing slightly off level. Skin shows pores, "
 "the small pale freckles across her nose and inner cheeks, fine hairs at "
 "her temple, and the faint flush of actually laughing."),

# The quieter alternative. Generate both and judge them SHRUNK to 40px — the
# one that still reads as a specific person wins, and it will not be the one
# that looks best full size.
dict(id="profile_pic_soft", tier="2k", aspect="1:1", text=
 "Head and shoulders, her face large and centred with a little space above her "
 "head, a warm open smile with her teeth just showing and her eyes creased at "
 "the corners, looking straight into the lens as though she has recognised "
 "whoever is looking. Behind her the corner of a bright room completely out of "
 "focus, pale and simple, a window off to one side. Soft daylight from the "
 "front and slightly above, warmer on one side of her face, shadows open. A "
 "cream ribbed knit with the collarbone showing, one small gold hoop. Hair "
 "down and pushed back off her face and behind her shoulders, centre-parted "
 "with the curtain bangs swept to the sides. Taken by somebody standing close "
 "on an iPhone 16 Pro at 2x, flat HDR contrast, low saturation, the framing a "
 "degree off level. Skin shows pores, the small pale freckles across her nose "
 "and inner cheeks, and fine hairs catching the light at her temple."),
# ---- SUMMER. Late August in Seoul reaches 38C. --------------------------
# The wool coats, puffers, shearling and roll-necks above are a late-November
# to February wardrobe. They are not lost — they are the winter bank — but
# nothing in a coat can launch in August. These are the frames that can.
# Wardrobe here is what people actually wear in that heat: linen, cotton,
# tanks, shorts, sandals, a cap for the sun. Sweat is a realism asset.
dict(id="s_han_evening", tier="2k", body=True, aspect="3:4", text=
 "Sitting on the grass by the Han river in the evening heat, knees up, hair "
 "stuck to her neck, looking into the lens with a tired warm smile. A white "
 "ribbed cotton tank and loose black linen shorts, bare legs, sandals off "
 "beside her. Hair in a low bun with pieces escaping. Wide sky going orange, "
 "towers hazy on the far bank, people on picnic mats out of focus. Front "
 "camera at arm's length held low, 23mm equivalent, the sky opening out behind "
 "her, her extended arm cutting into the bottom corner. Softer and noisier "
 "than the rear lens, flat HDR contrast, low saturation, the heat haze soft, "
 "damp skin with pores and small unevenness."),

dict(id="s_seongsu_iced", tier="2k", body=True, aspect="3:4", text=
 "On a Seongsu-dong street in hard afternoon sun, holding an iced americano "
 "gone watery, one eye almost shut against the glare and her mouth open "
 "blowing hair off her face, eyebrows up, visibly done with the heat. A thin "
 "white cotton t-shirt tucked into faded denim shorts, bare legs. Hair pulled "
 "through a plain black cap with the ends damp at her neck. Red brick close "
 "behind her, shutters down, heat shimmer off the pavement, hard shadows. "
 "Front camera at arm's length, 23mm equivalent, the street falling away, her "
 "extended arm in the corner, framing tilted. Softer and noisier than the rear "
 "lens, blown highlights on the brick, flat contrast, low saturation, sweat at "
 "her hairline and real skin texture."),

dict(id="s_convenience", tier="2k", aspect="3:4", text=
 "Sitting on a plastic stool at the counter outside a convenience store late "
 "at night, one bare foot up on the rung, eating something straight from the "
 "container, caught looking up at the lens mid-bite with her eyebrows raised. "
 "An oversized grey cotton t-shirt and black cycling shorts. Hair in a messy "
 "low bun. Plain painted shopfront and a dark street behind her, the light "
 "coming entirely from the strip lighting above, flat and slightly green. "
 "Taken by whoever is sitting with her, from the next stool, framing loose and "
 "off level. Shot on an iPhone 16 Pro at night, flat HDR contrast, low "
 "saturation, visible grain, unflattering overhead light, skin real."),

dict(id="s_park_green", tier="2k", body=True, aspect="3:4", text=
 "Caught between steps on a shaded path in Seoul Forest in deep summer, weight "
 "still on the back foot, one hand halfway up to lift her hair off her neck "
 "and her mouth open on the start of a word, looking at the person with the "
 "phone rather than at the phone. A pale blue cotton sundress, bare shoulders, "
 "white trainers. Hair down and loose, damp underneath, one piece stuck to her "
 "jaw. Heavy green overhead, dappled light falling in patches so half her face "
 "is in shade. A branch of leaves crosses the near foreground on one side, "
 "close to the lens and thrown right out of focus. Taken by somebody walking "
 "with her who turned round mid-stride: she sits low and to one side with too "
 "much empty path along the bottom, the horizon a few degrees off, one arm "
 "soft with movement. Shot on an iPhone "
 "16 Pro, flat HDR contrast, low saturation with the greens muted rather than "
 "vivid, deep focus on her, fine noise, natural head-to-body proportion."),

dict(id="s_rooftop_dusk", tier="2k", aspect="3:4", text=
 "On a rooftop at dusk in the last of the heat, hip leaned against the "
 "parapet, her free hand up tucking hair behind her ear, half turned toward "
 "the lens with a slow private smile. A black cotton vest and loose cream "
 "linen trousers, bare shoulders, one thin gold chain. Hair down and lifting "
 "slightly in the first cool air. City hazy behind her, windows starting to "
 "light, sky still pale at the horizon. Front camera at arm's length, 23mm "
 "equivalent, the city falling away, her extended arm cutting into a corner, "
 "horizon tilted. Softer and noisier than the rear lens, flat HDR contrast, "
 "low saturation, visible pores."),

dict(id="s_market_summer", tier="2k", body=True, aspect="3:4", text=
 "In a covered market in the heat, holding a peach up to look at it, head "
 "tilted, deciding, entirely unaware of the lens. A cropped white cotton "
 "t-shirt and loose black linen trousers. Hair through a plain black cap. "
 "Loose produce heaped in shallow baskets, hanging bulbs, plastic sheeting "
 "overhead, a plain painted wall beside her, the aisle out of focus behind. "
 "Taken by somebody standing a little back. Shot on an iPhone 16 Pro, flat HDR "
 "contrast, low saturation, warm bulb light, fine noise, damp skin."),

dict(id="s_bus_window", tier="2k", aspect="3:4", text=
 "On a bus in the afternoon, head tipping against the window with the "
 "movement of it, half asleep and just opening her eyes as the city slides "
 "past out of focus behind the glass. A thin "
 "white cotton tank, bare shoulders, a canvas tote in her lap. Hair in a low "
 "bun coming apart. Plain grey seat back and a metal rail beside her. Front "
 "camera at arm's length held low and close, 23mm equivalent, her extended arm "
 "in the corner, framing crooked. Softer and noisier than the rear lens, flat "
 "contrast, low saturation, hard afternoon light through glass, real skin."),

dict(id="s_stairs_sweat", tier="2k", body=True, aspect="3:4", text=
 "Sitting on outdoor concrete steps after walking uphill in the heat, elbows "
 "on her knees, red-faced and openly laughing at herself, hair stuck to her "
 "forehead. A matte black sports bra and loose grey shorts, trainers, a water "
 "bottle beside her. Hair in a high ponytail coming loose. Plain concrete, a "
 "metal handrail, green overgrowth behind, hard midday light. The phone has "
 "been set down on the step below and left running, so the angle is low with "
 "too much sky. Shot on an iPhone 16 Pro, flat HDR contrast, low saturation, "
 "deep focus, fine noise, sweat and flushed uneven skin."),

dict(id="s_cafe_iced", tier="2k", aspect="9:16", text=
 "At a cafe table in the afternoon with an iced drink sweating onto the wood, "
 "leaning in toward the lens with a warm open smile, teeth showing and her "
 "eyes creased. A white linen shirt worn open over a black cotton vest, sleeves "
 "pushed up. Hair down and tucked behind one ear. Warm wood, a plain painted "
 "wall, trailing plants, bright window light from the left, the room out of "
 "focus. Front camera at arm's length, 23mm equivalent, her face high in the "
 "tall frame. Softer and noisier than the rear lens, flat contrast, low "
 "saturation, pores and fine hairs at her temple."),

dict(id="s_night_walk", tier="2k", body=True, aspect="9:16", text=
 "Walking a Seoul street on a warm night, half turned back toward the lens, "
 "unguarded and pleased, one hand holding a plastic cup. A loose black cotton "
 "vest and pale linen shorts, bare legs, sandals. Hair down and damp at the "
 "neck. Shopfront lights and traffic far out of focus into warm round bokeh, "
 "the pavement still holding the day's heat. Taken by somebody walking with "
 "her, from a step behind, framing loose and off level. Shot on an iPhone 16 "
 "Pro at night, flat HDR contrast that lifts the shadows, low saturation, "
 "visible grain, motion softness in one hand."),
# ---- AT HOME, ALONE, HOLDING THE PHONE HERSELF --------------------------
# The session bank has no selfies. Every home frame inherits its camera from
# the hero, which was propped on furniture — and a close crop against bed linen
# reads as neither propped nor held, so nobody is taking the photograph.
# That is backwards: a woman alone in her flat photographs herself at arm's
# length more than anywhere else, and these are the most intimate frames the
# account has. Written as their own prompts rather than session edits, because
# a close frame shows almost no room and does not need the hero to hold one.
dict(id="h_bed_morning", tier="2k", aspect="3:4", text=
 "Lying on her side in bed just after waking, cheek half into the pillow, hair "
 "down and flattened on one side across her face, one eye still half shut, "
 "giving the lens a flat unimpressed look. A thin white cotton strap top, bare "
 "shoulder, white linen duvet pushed down around her. Pale morning light from "
 "a window out of frame on one side, the wall behind plain and out of focus. "
 "Front camera held above her at arm's length: a 23mm-equivalent lens close to "
 "her face, so her features stretch very slightly and the bed falls away "
 "below, her extended arm cutting into a corner, the frame tilted well off "
 "level. Softer and noisier than the rear lens, flat HDR contrast, low "
 "saturation, pillow creases on her cheek, real pores and unbrushed hair."),

dict(id="h_sofa_evening", tier="2k", aspect="3:4", text=
 "Sitting slumped sideways into the corner of an armchair in the evening, "
 "knees up, head against the wing of it, halfway through saying something "
 "to the lens with her eyebrows raised. An oversized grey cotton t-shirt, "
 "bare legs, hair in a bun coming apart. A plain wall behind her, a linen "
 "curtain drawn at the edge of frame, one warm lamp out of shot doing all "
 "the lighting. "
 "Front camera at arm's length held low and close, 23mm equivalent, her free "
 "hand tucked under her cheek, her extended arm in the bottom corner, framing "
 "crooked. Softer and noisier than the rear lens, warm low light with grain in "
 "the shadows, flat contrast, low saturation, real skin texture."),

dict(id="h_kitchen_night", tier="2k", aspect="3:4", text=
 "Standing at the kitchen counter late at night eating something out of the "
 "container, caught mid-bite looking straight into the lens with her eyebrows "
 "up, entirely unbothered. A white ribbed tank and loose linen trousers, hair "
 "in a low bun. Pale wood worktop, ceramic bowls on an open shelf behind her, "
 "the window dark and the strip light under the shelf the only source. Front "
 "camera at arm's length, 23mm equivalent, the kitchen falling away behind "
 "her, her extended arm cutting into a corner, horizon a few degrees off. "
 "Softer and noisier than the rear lens, flat HDR contrast that lifts the "
 "shadows, low saturation, harsh underlighting, real skin texture."),
]
