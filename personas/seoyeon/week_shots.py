"""
week_shots.py — the first shots written from week.md instead of from a mood.

Each carries a `story=` premise answering the four questions: where she went,
who she was with, what mood she was in, and why the photo exists at all.
THE PREMISE IS NOT SENT. Naming an emotion produces a performance of it. It is
there to generate the physical details, and only those go in `text`.

Every premise names a SLOT from week.md — day and time of day, not just day.
If a premise cannot be placed in that week, the shot is wrong.

Constraints applied throughout:
  * late August, Seoul, mid-thirties. Summer only. The winter bank waits.
  * no men anywhere — in frame, in the premise, or implied
  * friends appear as EVIDENCE, never as a stable face
  * rooms are USED: something out of place, one hard light source with a
    direction, one object breaking the colour harmony, nothing tidied for
    the photograph

    python outside.py --week --all --budget 0.4
"""

SHOTS = [

dict(id="w_studio_early", day="mon", tier="2k", aspect="3:4",
 story=("MON MORNING, practice hours, just after seven. Trainees get the slot "
        "nobody wants. Alone, first class two hours off, has not washed her "
        "face. SELFIE, because the reason is an impulse: she got up at six for "
        "this and wants someone to know. Phone out, arm out, thirty seconds, "
        "back to it. She is not posing and does not need her whole body, so "
        "there is nothing to prop for."),
 text=
 "Sitting on the floor of an empty pilates studio just after seven in the "
 "morning with her back against a plain wall, one knee up and her free hand "
 "resting on it. Black leggings and a loose grey training top with the sleeves "
 "pushed up, her hair in a low bun with pieces escaping at the nape, her face "
 "bare. A water bottle on the floor beside her, her bag dumped with a towel "
 "half out of it, a mat unrolled at the far end of the room and rollers along "
 "the wall, the floor scuffed. Hard low morning sun coming in almost level "
 "from a window behind the camera, hitting her straight in the face so she is "
 "squinting a little, the wall beside her bleached flat and her own shadow "
 "thrown hard onto it. Front camera at arm's length, a 23mm-equivalent lens "
 "close to her face so the studio falls away behind her and her features "
 "stretch very slightly, her extended arm cutting into the bottom corner, "
 "framing crooked. "
 "Shot on an iPhone 16 Pro front camera: flat HDR contrast, low saturation, "
 "softer and noisier than the rear lens."),

dict(id="w_cafe_jieun", day="tue", tier="2k", aspect="3:4", selfie=False,
 story=("TUE EVENING, cafe with Jieun. They have been there since eight "
        "because Jieun is avoiding going home. Seoyeon has just said something "
        "she thinks is funny and Jieun picked up her phone to photograph her "
        "mid-sentence. She posts it because she likes how she looks when she "
        "is not the one holding the camera, and because it is proof she still "
        "sees people."),
 text=
 "Sitting at a small cafe table in the evening with one hand still raised "
 "mid-sentence, looking slightly past the lens at the woman sitting "
 "opposite her, her mouth open on a word. A plain black t-shirt under an "
 "open cream overshirt, her hair down, centre-parted with curtain bangs "
 "and pushed behind one ear on one side. A tall glass in front of her and "
 "a second one close to the camera and half out of frame, a canvas tote "
 "slumped on the chair beside it. Hard overhead LED spots in the ceiling "
 "doing most of the lighting, slightly cool, with the service counter "
 "behind her lit brighter than she is and the window beside it black with "
 "evening. Taken from directly across the small table by the woman sitting "
 "opposite, from about a metre away and a little below her eyeline, off- "
 "centre and a degree off level. Shot on an iPhone 16 Pro: flat HDR "
 "contrast, low saturation, fine noise in the shadows, real skin texture."),

dict(id="w_street_heat", day="thu", tier="2k", aspect="3:4",
 story=("THU AFTERNOON, errands. Thirty-four degrees. She walked to the market "
        "because the delivery minimum costs more than she wants to spend, and "
        "now she is carrying it up her own street with the bag cutting into "
        "her hand. She is not enjoying it. She photographs it because she is "
        "sweating through her shirt on a residential street and the absurdity "
        "is funny to her, and because she posts the unglamorous ones too."),
 text=
 "Standing halfway up a narrow residential street in Seoul in the "
 "afternoon heat with a heavy plastic bag of shopping in one hand, her "
 "weight on one leg. Damp hair stuck at her temples and along her "
 "hairline, a white cotton t-shirt with a sweat mark at the collarbone, "
 "loose black shorts, her hair scraped up into a high ponytail. Low brick "
 "walls and parked scooters behind her, air-conditioning units on the "
 "wall, the street going up and away behind her. Hard overhead afternoon "
 "sun making short black shadows, the sky above her blown to white. Front "
 "camera at arm's length, a 23mm-equivalent lens close to her face so the "
 "street falls away behind her and her features stretch very slightly, her "
 "extended arm cutting into a corner and her other hand holding the "
 "shopping bag down at her side, horizon a few degrees off level. Shot on "
 "an iPhone 16 Pro front camera: flat HDR contrast, low saturation, softer "
 "and noisier than the rear lens."),

dict(id="w_home_sunday", day="sun", tier="2k", aspect="3:4", selfie=True,
 story=("SUN EVENING, the reset. She cooks properly once a week because the "
        "rest of the week is convenience store food. Laundry on, week planned, "
        "something actually on the stove. Alone, and it does not bother her. "
        "She photographs it because the food came out well and she wants "
        "credit for it, and because Sunday night is the one she does not mind "
        "people seeing. THIS IS THE ANSWER TO THE ARMCHAIR: same room type, "
        "same solitude, opposite production value."),
 text=
 "Standing at the kitchen counter on a Sunday evening with a finished bowl "
 "of food on the counter in the near foreground beside her, looking into "
 "the lens with her chin down and her eyebrows raised. A washed-out navy "
 "t-shirt with a mark near the hem and grey cotton shorts, her hair half- "
 "up in a claw clip with the lengths loose below it. The counter covered: "
 "a chopping board still out with peel on it, two used bowls, a bright "
 "yellow plastic carrier bag crumpled at the edge, a drying rack full of "
 "clean dishes, and a laundry rack with clothes on it just visible through "
 "the doorway behind her. A broad flat ceiling panel overhead and a strip "
 "light under the wall cupboard, both switched on, so the whole kitchen is "
 "evenly lit, slightly cool and flat. Front camera at arm's length held a "
 "little above her, a 23mm-equivalent lens, her extended arm cutting into "
 "the top corner and her other hand down at her side, framing crooked. "
 "Shot on an iPhone 16 Pro front camera: flat HDR contrast, low "
 "saturation, softer and noisier than the rear lens."),

dict(id="w_desk_afternoon", day="mon", tier="2k", aspect="3:4",
 story=("MON AFTERNOON. A deck due Wednesday for the agency she used to work "
        "at full-time. Sat down at one, it is now four, the coffee she made at "
        "two is cold. SELFIE: she has been on the same slide for forty minutes "
        "and wants to complain to someone. One shot, back to it. Nobody props "
        "a phone to procrastinate for thirty seconds."),
 text=
 "Sitting at a table at four in the afternoon, slumped back in the chair, "
 "her mouth pressed flat and her eyebrows up. A white t-shirt, her hair "
 "half-up in a claw clip. A laptop and a mug of cold coffee beside her. "
 "The window behind her blown to white so her face sits dark and lifted "
 "unevenly. Front camera at arm's length held a little low, her arm "
 "cutting into the bottom corner, framing off level. Phone front camera: "
 "soft, noisy, flat."),

dict(id="w_mon_late", day="mon", tier="2k", aspect="3:4",
 story=("MON EVENING. Studio at seven this morning, table until six. Sunday is "
        "the cooking night, so tonight is instant noodles on the floor and bed "
        "before ten. Alone. She photographs it because she looks completely "
        "destroyed and finds that funny, and because the account is not only "
        "the good days. CONTINUITY: the mat by the door is the one she carried "
        "to the studio this morning."),
 text=
 "Sitting on the kitchen floor with her back against a cupboard late on a "
 "weekday evening, a small pot on the floor beside her that she has been "
 "eating out of, the chopsticks left standing in it, looking into the lens "
 "with her eyes half shut. An oversized washed grey t-shirt over black "
 "shorts, her hair mostly escaped from a bun and stuck to her neck, her "
 "face bare. A tote and a rolled exercise mat dumped by the door behind "
 "her, one shoe on its side, a used pan still on the hob. A broad flat LED "
 "ceiling panel overhead doing all the lighting, even and slightly cool "
 "and faintly green, flattening everything, with only soft shadow under "
 "her eyes and chin. Front camera at arm's length held low and close, a "
 "23mm-equivalent lens, her extended arm cutting into the bottom corner "
 "and her other hand resting on her knee, framing crooked. Shot on an "
 "iPhone 16 Pro front camera: flat HDR contrast, low saturation, softer "
 "and noisier than the rear lens."),
]
