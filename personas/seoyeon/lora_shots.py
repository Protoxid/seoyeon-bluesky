#!/usr/bin/env python3
"""
lora_shots.py — the training set for a Krea 2 identity LoRA. 30 shots.

    python outside.py --lora --dry-run
    python outside.py --lora --all              ~$2.70 at $0.09 each

BUILT TO A PUBLISHED RECIPE, NOT TO INTUITION. The composition below follows a
community-calibrated Krea-2 LoRA workflow for face and character training on
Ostris AI-Toolkit (github.com/chengyansen-ai/krea2-lora-training). It is a
community source, not an official one — but it is specific to THIS model, and
it overruled two things this file originally did on my own reasoning.

WHAT IT OVERRULED, both worth remembering:

  1. FRAMING MIX. The first version was ~70% head-and-shoulders, on the theory
     that a face LoRA should mostly see a face. The recipe calls for
     **40% close / 30% half-body / 30% full-body** — and this file is now
     12 / 9 / 9. Full-body shots teach PROPORTION, and a set without them
     produces a model that only knows how to crop.
  2. BACKGROUNDS. The first version held every background to the same plain
     pale wall, so that exactly one variable moved per image. That is the
     intuitive design and the recipe explicitly warns against it: repetitive
     plain backgrounds cause **background and composition bleeding**, where
     the LoRA learns the wall as part of her. Every shot below has a
     DIFFERENT setting.

OTHER RULES TAKEN FROM THE RECIPE:
  * The head never fills the frame (recipe: head <= 20% of frame). Even the
    close shots are head-and-shoulders, not face-fills-frame.
  * Full-body shots ALWAYS show the shoes. Cropped feet teach cropped feet.
  * Captions follow the recipe's own schema:
        [trigger], single person, [framing], [angle], [expression], [hair],
        [light], [background], [focus]
    with a FICTIONAL trigger word — here `sy3nh`. Each shot carries its
    caption in a `caption` field, ready for the training folder.

DELIBERATELY ABSENT:
  * the turntable sheet — one light, one backdrop, twelve times. Excellent as
    a generation-time reference, poison as training data.
  * the word "phone", anywhere. This project has already learned that naming
    the device summons it, and a phone in a seventh of the images teaches the
    LoRA to draw one.
  * the existing masters. Those are the canonical set drift_gate scores
    against; training on the exam paper is not a test.

TRAIN ON KREA 2 **RAW**, VERIFY ON **TURBO**. Raw previews look flat on
purpose — the recipe says so, and "plastic on Raw" is listed as expected
behaviour rather than a fault. Judge on Turbo at 8 steps, CFG 0, LoRA weight
1.0, mu 1.15.
"""

SHOTS = [
    dict(id='lx_c01', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 1/12. The anchor: dead front, neutral, soft light. Everything else is measured against this one.',
         text='A head-and-shoulders photograph of a woman facing the camera straight on, mouth closed and no particular expression. Soft daylight reaches her from a window to one side. Behind her is a lived-in room, visible but out of the way. She is wearing a plain white cotton t-shirt, her hair loose down her back. Everything sharp.',
         caption='sy3nh, white t-shirt, hair down loose, standing facing camera, neutral, mouth closed, lived-in room, soft window light, eye level, front'),
    dict(id='lx_c02', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 2/12. Three-quarter left. The angle a LoRA meets most often in real posts.',
         text='A head-and-shoulders photograph of a woman turned about thirty degrees to her left, with a small closed-mouth smile. Flat grey light from an overcast sky. A brick wall and a bare tree stand behind her. She is wearing a grey marl sweatshirt, her hair in a low bun with a few strands loose. Everything sharp.',
         caption='sy3nh, grey sweatshirt, low bun, standing turned left, small closed-mouth smile, brick wall and bare tree, flat overcast light, eye level, three-quarter left'),
    dict(id='lx_c03', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 3/12. Three-quarter right with a real laugh — angle and expression moving together, warm light.',
         text='A head-and-shoulders photograph of a woman turned about thirty degrees to her right, laughing with her mouth open and her eyes half shut. A lamp lights her warm and low. Behind her a dim room and an open doorway. She is wearing a black ribbed vest, her hair down and tucked behind one ear. Everything sharp.',
         caption='sy3nh, black ribbed vest, hair tucked behind one ear, standing turned right, laughing, eyes half shut, dim room, open doorway, warm lamp at night, eye level, three-quarter right'),
    dict(id='lx_c04', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 4/12. Full left profile. Profiles are where weak LoRAs collapse, under unflattering strip light.',
         text='A head-and-shoulders photograph of a woman in full left profile, mouth closed, looking ahead. Hard white strip lighting from overhead. A corridor and a lift door behind her. She is wearing a navy zip-up jacket, zipped halfway, her hair in a high ponytail. Everything sharp.',
         caption='sy3nh, navy zip-up jacket, high ponytail, standing in profile, neutral, looking ahead, corridor with a lift door, hard overhead strip light, eye level, left profile'),
    dict(id='lx_c05', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 5/12. Full right profile, mid-word. Both profiles are needed; a set with one teaches a mirror.',
         text='A head-and-shoulders photograph of a woman in full right profile, caught mid-sentence with her mouth open on a word. Bright open shade outdoors. A sunlit street runs away behind her. She is wearing a cream knitted jumper, her hair down and pushed back off her face. Everything sharp.',
         caption='sy3nh, cream knit jumper, hair pushed back, standing in profile, talking, mouth open, sunlit street, bright open shade, eye level, right profile'),
    dict(id='lx_c06', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 6/12. Low camera, chin up. Covers the angle a phone held below eye level produces.',
         text='A head-and-shoulders photograph of a woman with her chin lifted, taken from slightly below her eye line, eyebrows up and mildly surprised. Overcast daylight. Sky and the top of a building behind her. She is wearing a black puffer jacket with the collar up, her hair loose and moving in the wind. Everything sharp.',
         caption='sy3nh, black puffer jacket, hair loose in wind, chin lifted, eyebrows up, surprised, sky and rooftop, overcast daylight, low angle'),
    dict(id='lx_c07', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 7/12. High camera, eyes down. The other half of the vertical range, at night.',
         text='A head-and-shoulders photograph of a woman looking down and away, taken from slightly above her eye line, her face relaxed. One warm lamp lights her from the side at night. A bed and a rumpled duvet behind her. She is wearing an oversized grey t-shirt with a stretched collar, her hair damp and pushed back as if just washed. Everything sharp.',
         caption='sy3nh, oversized grey tee, damp hair pushed back, head turned down and away, eyes lowered, relaxed, bed and rumpled duvet, warm lamp at night, high angle'),
    dict(id='lx_c08', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 8/12. Eyes closed. Identity has to survive a face doing nothing.',
         text='A head-and-shoulders photograph of a woman facing the camera with her eyes closed and her face relaxed. Soft daylight comes through a curtain. A window and a radiator behind her. She is wearing a soft pink pyjama top, her hair in a loose plait over one shoulder. Everything sharp.',
         caption='sy3nh, pink pyjama top, loose plait, standing facing camera, eyes closed, relaxed, window and radiator, diffused daylight through a curtain, eye level, front'),
    dict(id='lx_c09', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 9/12. Looking back over the shoulder under fluorescent light — the ugliest lighting she will meet.',
         text='A head-and-shoulders photograph of a woman turned slightly away and looking back at the camera, unimpressed, her mouth pushed to one side. Cool fluorescent light. Convenience store shelves behind her. She is wearing a black hoodie with the hood down, her hair clipped up off her neck. Everything sharp.',
         caption='sy3nh, black hoodie, clipped up, turned away, looking back, unimpressed, convenience store shelves, cool fluorescent light, eye level, over the shoulder'),
    dict(id='lx_c10', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 10/12. Direct flash at night. A LoRA that has never seen flash cannot make a night photo.',
         text='A head-and-shoulders photograph of a woman facing the camera in a wide open laugh with her head tipped back, lit by a direct camera flash at night. The background falls away dark behind her. She is wearing a black slip top with thin straps, her hair down and slightly messy. Everything sharp.',
         caption='sy3nh, black slip top, hair down messy, standing facing camera, head tipped back, wide open laugh, dark falling-away background, direct camera flash at night, eye level, front'),
    dict(id='lx_c11', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 11/12. Low evening sun from behind the camera. The most flattering light, for balance.',
         text='A head-and-shoulders photograph of a woman turned three-quarters to her left and looking at the camera with a small smile. Late evening sun comes from behind the camera. A river and a bridge lie far behind her. She is wearing a pale blue striped shirt with the collar open, her hair half up in a clip. Everything sharp.',
         caption='sy3nh, pale blue striped shirt, half up in a clip, standing turned left, small smile, river and bridge far behind, low evening sun from behind camera, eye level, three-quarter left'),
    dict(id='lx_c12', tier='2k', aspect='3:4', framing='close',
         story='CLOSE 12/12. Mixed colour temperature, warm indoors against blue outside. Hardest case for skin tone.',
         text='A head-and-shoulders photograph of a woman facing the camera, mouth closed, eyebrows slightly raised. Warm indoor light mixes with blue evening light from a window. A kitchen counter behind her. She is wearing a mustard cardigan over a white top, her hair in a low bun. Everything sharp.',
         caption='sy3nh, mustard cardigan over a white top, low bun, standing facing camera, neutral, eyebrows slightly raised, kitchen counter, warm indoor light mixed with blue window light, eye level, front'),
    dict(id='lx_h01', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 1/9. Standing front, neutral. The half-body anchor.',
         text='A photograph of a woman from the waist up, standing and facing the camera with her arms relaxed, mouth closed. Soft daylight from a window. A plain room with a chair and a lamp behind her. She is wearing a white t-shirt tucked into wide black trousers, her hair loose. Everything sharp.',
         caption='sy3nh, white tee tucked into wide black trousers, hair down loose, standing, arms relaxed, neutral, plain room with a chair and a lamp, soft window light, eye level, front'),
    dict(id='lx_h02', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 2/9. Outdoors on a Seoul street — the environment the account actually posts from.',
         text='A photograph of a woman from the waist up, standing turned to her left and looking at the camera with a small smile. Overcast daylight outdoors. A residential street with Korean shop signage behind her. She is wearing an oversized denim jacket over a black top, her hair down under a small beanie. Everything sharp.',
         caption='sy3nh, oversized denim jacket over a black top, hair down under a beanie, standing turned left, small smile, Seoul residential street with shop signage, overcast daylight, eye level, three-quarter'),
    dict(id='lx_h03', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 3/9. Seated at a table, talking. Covers seated posture, which standing shots never teach.',
         text='A photograph of a woman from the waist up, sitting at a table and turned towards the camera, talking with her mouth open. Warm cafe lighting. A cafe interior with other tables behind her. She is wearing a beige oversized shirt with the sleeves pushed up, her hair in a messy bun. Everything sharp.',
         caption='sy3nh, beige oversized shirt, sleeves pushed up, messy bun, seated at a table, turned to camera, talking, mouth open, cafe interior with other tables, warm cafe lighting, eye level, seated'),
    dict(id='lx_h04', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 4/9. Weight shifted, laughing outdoors. Body language plus expression at once.',
         text='A photograph of a woman from the waist up, standing with her weight on one leg and one hand at her side, laughing. Bright open shade. A park path and grass behind her. She is wearing a green windbreaker over a white t-shirt, her hair in a high ponytail. Everything sharp.',
         caption='sy3nh, green windbreaker over a white tee, high ponytail, standing, weight on one leg, hand at side, laughing, park path and grass, bright open shade, eye level, front'),
    dict(id='lx_h05', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 5/9. Turned away, looking back, in the studio. The pose half her real posts use.',
         text='A photograph of a woman from the waist up, standing turned three-quarters away and looking back at the camera without smiling. Hard overhead light. A pilates studio in Seongsu, Seoul with reformers behind her. She is wearing a black sports bra and black leggings, her hair in a tight low bun. Everything sharp.',
         caption='sy3nh, black sports bra and black leggings, tight low bun, standing turned away, looking back, neutral, pilates studio with reformers, hard overhead light, eye level, over the shoulder'),
    dict(id='lx_h06', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 6/9. On the floor, leaning back. A low posture nothing else in the set covers.',
         text='A photograph of a woman from the waist up, sitting on the floor and leaning back on one hand, relaxed and half smiling. Low warm lamp light at night. A rug and a low table behind her. She is wearing a grey sweatshirt and shorts, her hair loose and falling forward. Everything sharp.',
         caption='sy3nh, grey sweatshirt and shorts, hair loose falling forward, sitting on the floor, leaning back on one hand, relaxed half smile, rug and low table, low warm lamp at night, slightly high angle'),
    dict(id='lx_h07', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 7/9. At a window in grey light. Backlit-adjacent, where cheap LoRAs blow the face out.',
         text='A photograph of a woman from the waist up, standing at a window and turned towards the camera, looking at the lens. Grey daylight comes through the glass. Rooftops and low buildings outside behind her. She is wearing a long camel coat over a black polo neck, her hair down and straight. Everything sharp.',
         caption='sy3nh, long camel coat over a black polo neck, hair down straight, standing at a window, turned to camera, neutral, rooftops and low buildings outside, grey daylight through glass, eye level, front'),
    dict(id='lx_h08', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 8/9. Arms crossed under fluorescent light. Occluded torso plus bad light.',
         text='A photograph of a woman from the waist up, standing with her arms loosely crossed, unimpressed. Cool fluorescent light. A laundromat with washing machines behind her. She is wearing a washed-out band t-shirt and pyjama shorts, her hair in a claw clip. Everything sharp.',
         caption='sy3nh, band tee and pyjama shorts, claw clip, standing, arms loosely crossed, unimpressed, laundromat with washing machines, cool fluorescent light, eye level, front'),
    dict(id='lx_h09', tier='2k', aspect='3:4', framing='half', body=True,
         story='HALF 9/9. Leaning on a wall, one shoulder forward. Asymmetric stance, warm low sun.',
         text='A photograph of a woman from the waist up, leaning against a wall with one shoulder to the camera, a small tired smile. Late evening sun. A brick wall and a doorway behind her. She is wearing a cropped black leather jacket, her hair down and windblown. Everything sharp.',
         caption='sy3nh, cropped black leather jacket, hair windblown, leaning on a wall, one shoulder forward, small tired smile, brick wall and doorway, late evening sun, eye level, three-quarter'),
    dict(id='lx_f01', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 1/9. Straight on, arms down, hallway. The full-body anchor and the cleanest proportion reference.',
         text='A full-length photograph of a woman, head to feet, standing straight on with her arms at her sides, mouth closed. Soft daylight from a window. A hallway with a door and a shoe rack behind her. White low sneakers on her feet, fully in frame. She is wearing a white t-shirt and high-waisted denim shorts, her hair loose. Everything sharp.',
         caption='sy3nh, white tee and high-waisted denim shorts, white low sneakers, hair down loose, standing straight on, arms at sides, neutral, hallway with a door and a shoe rack, soft window light, eye level, front, full length'),
    dict(id='lx_f02', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 2/9. Weight on one leg outdoors. Contrapposto — the stance almost every real photo has.',
         text='A full-length photograph of a woman, head to feet, standing with her weight on one leg and a small smile. Overcast daylight outdoors. A quiet street in Seoul behind her. Trainers on her feet, fully in frame. She is wearing a long grey trench coat over a white top and jeans, her hair in a low ponytail. Everything sharp.',
         caption='sy3nh, long grey trench coat over a white top and jeans, trainers, low ponytail, standing, weight on one leg, small smile, quiet Seoul street, overcast daylight, eye level, front, full length'),
    dict(id='lx_f03', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 3/9. Walking, mid-step. Motion, and legs in an unbalanced position.',
         text='A full-length photograph of a woman, head to feet, walking towards the camera mid-step and looking ahead. Bright open shade. A park path behind her. Trainers on her feet, fully in frame. She is wearing black leggings and a loose lilac t-shirt, her hair in a high ponytail. Everything sharp.',
         caption='sy3nh, black leggings and a loose lilac tee, trainers, high ponytail, walking towards camera, mid-step, neutral, looking ahead, park path, bright open shade, eye level, front, full length'),
    dict(id='lx_f04', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 4/9. Turned, laughing, low sun. Full body with the face still doing something.',
         text='A full-length photograph of a woman, head to feet, standing turned to her right and looking at the camera, laughing. Late evening sun from the side. A riverside path and a bridge behind her. Trainers on her feet, fully in frame. She is wearing a cream summer dress, her hair down and moving. Everything sharp.',
         caption='sy3nh, cream summer dress, trainers, hair down moving, standing turned right, looking at camera, laughing, riverside path and a bridge, late evening sun from the side, eye level, three-quarter, full length'),
    dict(id='lx_f05', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 5/9. Seated on steps, legs extended. Seated full-length, which standing shots cannot teach.',
         text='A full-length photograph of a woman, head to feet, sitting on wide concrete steps with her legs out in front of her, talking mid-word. Warm dusk going blue. The Han river in Seoul and a lit bridge behind her. Trainers on her feet, fully in frame. She is wearing a navy hoodie and wide jeans, her hair in a plait over one shoulder. Everything sharp.',
         caption='sy3nh, navy hoodie and wide jeans, trainers, plait over one shoulder, sitting on wide steps, legs extended, talking mid-word, Han river and a lit bridge, warm dusk going blue, eye level, seated, full length'),
    dict(id='lx_f06', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 6/9. In a doorway, looking back, bare feet. Frames her body and covers feet without shoes.',
         text='A full-length photograph of a woman, head to feet, standing in a doorway with one hand on the frame, looking back over her shoulder. Warm lamp light at night. A dim flat behind her. Bare feet, fully in frame. She is wearing an oversized white shirt worn open over a black vest and shorts, her hair damp and loose. Everything sharp.',
         caption='sy3nh, oversized white shirt open over a black vest and shorts, bare feet, damp hair loose, standing in a doorway, hand on the frame, looking back, neutral, dim flat, warm lamp light at night, eye level, over the shoulder, full length'),
    dict(id='lx_f07', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 7/9. Crouching to tie a lace, looking up. Extreme compression of the body, hardest pose here.',
         text='A full-length photograph of a woman, head to feet, crouching down to tie a shoelace and looking up at the camera with a small smile. Flat overcast light. A pavement and a low wall behind her. Trainers on her feet, fully in frame. She is wearing a khaki utility jacket and straight black trousers, her hair in a low bun. Everything sharp.',
         caption='sy3nh, khaki utility jacket and straight black trousers, trainers, low bun, crouching to tie a shoelace, looking up, small smile, pavement and a low wall, flat overcast light, low angle, full length'),
    dict(id='lx_f08', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 8/9. Straight on in the studio, grip socks. Proportion under hard overhead light.',
         text='A full-length photograph of a woman, head to feet, standing straight on, mouth closed. Hard overhead light. A pilates studio in Seongsu, Seoul with reformers behind her. Grip socks on her feet, fully in frame. She is wearing a dark green sports bra and black leggings, her hair in a tight low bun. Everything sharp.',
         caption='sy3nh, dark green sports bra and black leggings, grip socks, tight low bun, standing straight on, neutral, pilates studio with reformers, hard overhead light, eye level, front, full length'),
    dict(id='lx_f09', tier='2k', aspect='3:4', framing='full', body=True,
         story='FULL 9/9. Turned away, looking back, subway platform. Covers her back, which nothing else does.',
         text='A full-length photograph of a woman, head to feet, standing turned away and looking back at the camera with her eyebrows raised. Cool daylight. A subway platform behind her. Trainers on her feet, fully in frame. She is wearing a black wool coat over a grey jumper and jeans, her hair down inside the collar. Everything sharp.',
         caption='sy3nh, black wool coat over a grey jumper and jeans, trainers, hair down inside the collar, standing turned away, looking back, eyebrows raised, subway platform, cool daylight, eye level, over the shoulder, full length'),
]
