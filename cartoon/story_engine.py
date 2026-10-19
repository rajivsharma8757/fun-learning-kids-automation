"""
story_engine.py
---------------
Content & Story Engine for the 3rd Daily Cartoon Video in "Fun Learning Kids".
Features:
1. Curated, original, child-safe story repository (6 scenes per story).
2. Variety Pool:
   - Diverse Characters: Chintu Bunny, Koko Squirrel, Bholu Puppy, Leo Lion Cub,
     Mimi Kitten, Bantu Robot, Aarav Explorer, Tara Kitten.
   - Diverse Backgrounds: Forest Meadow, Sunny Farm, Treehouse Canopy, Pond Park,
     Cozy Playroom, Little Science Lab, Starry Space.
3. Strict 1:1 Alternation & Anti-Repetition Rules powered by VarietyManager:
   - Day 1 = V1, Day 2 = V4, Day 3 = V1, Day 4 = V4...
   - Equal 50/50 priority.
   - No same character on consecutive days.
   - Mimi cooldown (at least 3-4 other cartoon productions).
   - No same background or location on consecutive days.
   - No same visual theme on consecutive days.
   - No duplicate video hash.
4. Complete YouTube metadata generation (Title, Description, Tags, Category 27, Made for Kids).
5. Multi-attribute persistent history tracking.
"""

import os
import sys
import json
import logging
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, r"C:\kids_automation")
from cartoon.config import CARTOON_HISTORY_FILE, CHANNEL_NAME, CHANNEL_NAME_HI
from cartoon.variety_manager import VarietyManager

logger = logging.getLogger("kids_automation")

STORY_BANK = [
    # =========================================================================
    # STYLE A: VERSION 4 STORIES (Multi-Plane Parallax / 1080p Polish)
    # =========================================================================
    {
        "story_id": "v4_bantu_science_lab",
        "style": "V4",
        "main_character": "bantu",
        "characters": ["bantu", "aarav"],
        "location": "science_lab",
        "background": "science_lab",
        "visual_theme": "inventions_and_curiosity",
        "title_hi": "बंटू रोबोट और रंगीन प्रयोग",
        "title_en": "Bantu the Robot Color Experiment",
        "short_title": "बंटू रोबोट",
        "moral_hi": "जिज्ञासा और नया सीखने की चाह हमें समझदार बनाती है।",
        "moral_en": "Curiosity and a passion for learning lead to amazing discoveries.",
        "tags": [
            "Bantu Robot", "Robot Cartoon Hindi", "Science for Kids",
            "Fun Learning Kids", "Hindi Animation", "Kids Learning",
            "Kids Cartoon Hindi", "Educational Cartoons"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "हमारी छोटी विज्ञान प्रयोगशाला में, प्यारा रोबोट बंटू खुशी से घूम रहा था!",
                "text_en": "In our little science lab, the cute robot Bantu was happily rolling around!",
                "emotion": "excited",
                "action": "inspect_beakers"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "बंटू ने मेज पर रखी दो रंगीन बोतलें देखीं - एक नीली और एक पीली!",
                "text_en": "Bantu spotted two colorful bottles on the table - one blue and one yellow!",
                "emotion": "curious",
                "action": "look_at_flasks"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "उसने दोनों रंगों को धीरे से एक बीकर में मिलाया। अरे वाह! यह तो हरा रंग बन गया!",
                "text_en": "He gently mixed the colors into a beaker. Wow! It turned into bright green!",
                "emotion": "amazed",
                "action": "mix_colors"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "बंटू की स्क्रीन पर हरी बत्तियाँ चमकने लगीं और वह खुशी से नाचने लगा!",
                "text_en": "Green lights sparkled on Bantu's screen, and he started dancing with joy!",
                "emotion": "celebrate",
                "action": "spin_and_beep"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "विज्ञान का जादू कितना मजेदार होता है! नए रंग बनाना कितना आसान है!",
                "text_en": "The magic of science is so wonderful! Making new colors is so simple and fun!",
                "emotion": "happy",
                "action": "show_color_green"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "रोज कुछ नया सीखिए और फन लर्निंग किड्स के साथ हमेशा मुस्कुराते रहिए!",
                "text_en": "Learn something new every day and keep smiling with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v4_aarav_space_rocket",
        "style": "V4",
        "main_character": "aarav",
        "characters": ["aarav", "bantu"],
        "location": "space",
        "background": "starry_space",
        "visual_theme": "space_adventure_and_dreams",
        "title_hi": "आरव की जादुई अंतरिक्ष यात्रा",
        "title_en": "Aarav Magical Space Rocket Mission",
        "short_title": "अंतरिक्ष यात्रा",
        "moral_hi": "बड़े सपने देखो और ज्ञान पाने के लिए हमेशा तत्पर रहो।",
        "moral_en": "Dream big and always stay curious to learn about the universe.",
        "tags": [
            "Aarav Space Story", "Rocket Cartoon Hindi", "Space for Kids",
            "Hindi Moral Stories", "Fun Learning Kids", "Kids Animation Hindi",
            "Solar System for Kids", "Children Cartoon"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "नन्हे खोजी आरव ने रात के आसमान में टिमटिमाते तारे देखे और एक सुंदर सपना देखा!",
                "text_en": "Little explorer Aarav gazed at the twinkling stars in the night sky and had a dream!",
                "emotion": "wonder",
                "action": "look_at_stars"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "उसने अपने चमकदार खिलौना रॉकेट को तैयार किया। तीन, दो, एक... उड़ान शुरू!",
                "text_en": "He readied his shiny toy rocket. Three, two, one... Blast off!",
                "emotion": "excited",
                "action": "launch_rocket"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "रॉकेट बादलों से ऊपर निकल गया और चारों ओर खूबसूरत नीले ग्रह दिखने लगे!",
                "text_en": "The rocket soared above the clouds, revealing beautiful planets all around!",
                "emotion": "happy",
                "action": "orbit_planets"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "चाँद मामा ने मुस्कुराकर आरव का स्वागत किया। चाँद पर कितना सुकून था!",
                "text_en": "The friendly Moon smiled and welcomed Aarav with gentle silver light!",
                "emotion": "peaceful",
                "action": "salute_moon"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "आरव ने एक चमकता सितारा उठाया और अंतरिक्ष की सुंदरता को महसूस किया!",
                "text_en": "Aarav touched a glowing star and marvelled at the beauty of the cosmos!",
                "emotion": "inspired",
                "action": "hold_star"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "सपने सच होते हैं जब हम मेहनत करते हैं! फन लर्निंग किड्स को सब्सक्राइब करना न भूलें!",
                "text_en": "Dreams come true when we work hard! Don't forget to subscribe to Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v4_mimi_magic_train",
        "style": "V4",
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "playroom",
        "background": "cozy_playroom",
        "visual_theme": "toys_and_care",
        "title_hi": "मीमी और जादुई रेलगाड़ी",
        "title_en": "Mimi and the Magic Toy Train",
        "short_title": "जादुई रेलगाड़ी",
        "moral_hi": "खिलौनों की देखभाल करना और सावधानी से खेलना अच्छी आदत है।",
        "moral_en": "Playing carefully and taking care of toys is a good habit.",
        "tags": [
            "Mimi Cartoon", "Kids Cartoon Hindi", "Toy Train Story",
            "Mimi and Train", "Hindi Moral Stories for Kids", "Fun Learning Kids",
            "Kids Animation Hindi", "Good Habits for Kids", "Children Cartoon"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "मीमी अपने प्यारे कमरे में खेल रही थी, तभी उसे एक सुंदर छोटी रेलगाड़ी दिखी!",
                "text_en": "Mimi was playing in her lovely room, when she spotted a cute little toy train!",
                "emotion": "curious",
                "action": "playing_with_blocks"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "मीमी ने झुककर रेलगाड़ी को उठाया। वाह! कितने प्यारे पहिए और घंटी!",
                "text_en": "Mimi gently picked up the train. Wow! Such cute wheels and a little bell!",
                "emotion": "happy",
                "action": "crouch_and_inspect"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "उसने रेलगाड़ी को लकड़ी की पटरी पर रखा। अब शुरू होगा असली मज़ा!",
                "text_en": "She placed the train on the wooden track. Now the real fun begins!",
                "emotion": "excited",
                "action": "place_on_track"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "छुक-छुक, चूं-चूं! रेलगाड़ी दौड़ने लगी! मीमी खुशी से तालियाँ बजाने लगी!",
                "text_en": "Chug-chug, choo-choo! The train started rolling! Mimi clapped with delight!",
                "emotion": "cheering",
                "action": "clap_hands"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "रेलगाड़ी पुल से गुजरी और मीमी हँसते हुए उसके पीछे चलने लगी!",
                "text_en": "The train crossed the bridge and Mimi happily followed behind it!",
                "emotion": "playful",
                "action": "follow_train"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "सावधानी से खेलने से खिलौने खुश रहते हैं! फन लर्निंग किड्स के साथ सीखते रहिए!",
                "text_en": "Playing with care keeps toys happy! Keep learning with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v4_mimi_garden_adventure",
        "style": "V4",
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "garden",
        "background": "cozy_playroom",
        "visual_theme": "nature_and_play",
        "title_hi": "मीमी का नन्हा बगीचा",
        "title_en": "Mimi's Little Garden Adventure",
        "short_title": "नन्हा बगीचा",
        "moral_hi": "पेड़-पौधों को पानी देना और प्रकृति से प्यार करना बहुत जरूरी है।",
        "moral_en": "Watering plants and loving nature makes our world green and happy.",
        "tags": [
            "Mimi Cartoon", "Kids Garden Story", "Hindi Kids Animation",
            "Mimi Cat", "Fun Learning Kids", "Moral Stories Hindi"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "मीमी सुबह-सुबह बालकनी के बगीचे में टहलने निकली। सूरज की मीठी धूप खिली थी!",
                "text_en": "Mimi stepped into the balcony garden early in the morning. Sweet sunshine smiled upon her!",
                "emotion": "cheerful",
                "action": "walk_in_garden"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "तभी उसने देखा कि एक छोटे पौधे की पत्तियाँ थोड़ी उदास और सूखी थीं।",
                "text_en": "Then she noticed that a little plant's leaves looked slightly droopy and thirsty.",
                "emotion": "caring",
                "action": "look_at_flowerpot"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "मीमी ने तुरंत नन्हा फव्वारा उठाया और पौधे की जड़ों में प्यार से पानी दिया।",
                "text_en": "Mimi quickly picked up the little watering can and gently watered the plant's roots.",
                "emotion": "helpful",
                "action": "water_plant"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "अरे वाह! पानी पीते ही नन्हीं कली मुस्कुराई और एक सुंदर लाल फूल खिल गया!",
                "text_en": "Wow! Drinking fresh water, the little bud smiled and bloomed into a red flower!",
                "emotion": "delighted",
                "action": "flower_blooms"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "एक रंग-बिरंगी तितली उड़कर फूल पर आई और मीमी खुशी से खिलखिला उठी!",
                "text_en": "A colorful butterfly fluttered onto the flower and Mimi giggled with sheer delight!",
                "emotion": "excited",
                "action": "butterfly_flutter"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "प्रकृति की देखभाल करना सबसे अच्छी आदत है! फन लर्निंग किड्स से जुड़े रहिए!",
                "text_en": "Caring for nature is the best habit! Stay connected with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v4_mimi_clean_room",
        "style": "V4",
        "main_character": "mimi",
        "characters": ["mimi"],
        "location": "playroom",
        "background": "cozy_playroom",
        "visual_theme": "cleanliness_and_responsibility",
        "title_hi": "मीमी का स्वच्छ कमरा अभियान",
        "title_en": "Mimi Clean Room Mission",
        "short_title": "स्वच्छ कमरा",
        "moral_hi": "खेलने के बाद खिलौनों को सही जगह रखना अच्छी आदत है।",
        "moral_en": "Putting toys back in their place after playing is a wonderful habit.",
        "tags": [
            "Mimi Cartoon", "Clean Room for Kids", "Good Habits",
            "Hindi Animation Kids", "Fun Learning Kids", "Kids Moral Story"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "मीमी ने खूब मजे से खेल खेला, लेकिन कमरे में रंगीन खिलौने यहाँ-वहाँ फैले थे!",
                "text_en": "Mimi had so much fun playing, but colorful toys were scattered across the floor!",
                "emotion": "thoughtful",
                "action": "look_at_mess"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "मीमी ने सोचा, एक अच्छा बच्चा वही है जो अपने कमरे को साफ और सुंदर रखे!",
                "text_en": "Mimi thought: a good kid always keeps their room neat, clean, and organized!",
                "emotion": "resolved",
                "action": "nod_head"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "उसने बड़ी सी खिलौना टोकरी उठाई और एक-एक करके सारे खिलौने उसमें रखे।",
                "text_en": "She brought the big toy basket and placed all the toys into it one by one.",
                "emotion": "focused",
                "action": "pick_up_toys"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "किताबें शेल्फ पर रखीं, तकिया ठीक किया, और कमरा चमकने लगा!",
                "text_en": "Books neatly placed on shelves, pillow straightened, and the room sparkled!",
                "emotion": "happy",
                "action": "align_books"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "साफ कमरा देखकर मीमी की माँ बहुत खुश हुईं और उन्होंने मीमी को शाबाशी दी!",
                "text_en": "Seeing the spotless room, Mimi's mother was so proud and gave her warm praise!",
                "emotion": "proud",
                "action": "smile_and_bow"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "सफाई से स्वास्थ्य और खुशी दोनों मिलते हैं! फन लर्निंग किड्स के संग सीखते रहिए!",
                "text_en": "Cleanliness brings health and happiness! Keep learning with Fun Learning Kids!",
                "emotion": "cheerful",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v4_tara_magic_library",
        "style": "V4",
        "main_character": "tara",
        "characters": ["tara", "aarav"],
        "location": "library",
        "background": "magic_library",
        "visual_theme": "reading_and_wisdom",
        "title_hi": "तारा बिल्ली और जादुई किताब",
        "title_en": "Tara the Kitten and the Magic Book",
        "short_title": "जादुई किताब",
        "moral_hi": "किताबें पढ़ने से हमारी बुद्धि और ज्ञान का विस्तार होता है।",
        "moral_en": "Reading books expands our knowledge, wisdom, and imagination.",
        "tags": [
            "Tara Cartoon", "Magic Book Story", "Reading for Kids",
            "Hindi Animation Kids", "Fun Learning Kids", "Kids Moral Story"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "शांत पुस्तकालय में प्यारी तारा बिल्ली किताबों की खुशबू का आनंद ले रही थी!",
                "text_en": "In the quiet library, sweet Tara the kitten was enjoying the fragrance of books!",
                "emotion": "peaceful",
                "action": "walk_among_shelves"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "तभी शेल्फ पर एक सुनहरे पन्नों वाली बड़ी जादुई किताब चमकी!",
                "text_en": "Just then, a grand book with golden pages glowed softly on the shelf!",
                "emotion": "curious",
                "action": "discover_book"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "तारा ने जैसे ही पन्ना पलटा, किताब से सुंदर परियाँ और तितलियाँ निकल आईं!",
                "text_en": "As Tara gently opened a page, magical butterflies and fairies fluttered out!",
                "emotion": "delighted",
                "action": "turn_page"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "किताब ने बताया कि हर कहानी हमें कुछ नया और अच्छा सिखाती है!",
                "text_en": "The story revealed that every book teaches us kindness, courage, and wisdom!",
                "emotion": "inspired",
                "action": "read_story"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "तारा ने किताब को सीने से लगाया और रोज पढ़ने का प्यारा वादा किया!",
                "text_en": "Tara hugged the book warmly and promised to read every single day!",
                "emotion": "happy",
                "action": "hug_book"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "किताबें हमारी सबसे सच्ची दोस्त हैं! फन लर्निंग किड्स के साथ पढ़ते रहिए!",
                "text_en": "Books are our truest best friends! Keep reading with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },

    # =========================================================================
    # STYLE B: VERSION 1 STORIES (Kinematic Vector Animation)
    # =========================================================================
    {
        "story_id": "v1_koko_nut_harvest",
        "style": "V1",
        "main_character": "koko",
        "characters": ["koko", "piku"],
        "location": "treehouse",
        "background": "treehouse_canopy",
        "visual_theme": "hard_work_and_teamwork",
        "title_hi": "कोको गिलहरी का जादुई पेड़",
        "title_en": "Koko Squirrel and the Magic Treehouse",
        "short_title": "कोको गिलहरी",
        "moral_hi": "मेहनत और मिलकर काम करने से हर काम आसान हो जाता है।",
        "moral_en": "Hard work and teamwork turn challenging tasks into joyous success.",
        "tags": [
            "Koko Squirrel", "Squirrel Cartoon Hindi", "Treehouse Story",
            "Fun Learning Kids", "Hindi Moral Stories", "Kids Animation",
            "Children Cartoon Hindi"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "हरे-भरे ऊंचे पेड़ की छांव में, चुलबुली कोको गिलहरी खुशी से उछल-कूद कर रही थी!",
                "text_en": "In the shade of a lush treehouse canopy, lively Koko the squirrel was happily hopping!",
                "emotion": "cheerful",
                "action": "hop_on_branches"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "कोको को एक बड़ा, स्वादिष्ट सुनहरा नट मिला। वाह! कितना मीठा और कुरकुरा!",
                "text_en": "Koko found a large, golden delicious acorn. Wow! So sweet and crunchy!",
                "emotion": "excited",
                "action": "pick_up_nut"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "तभी उसका नन्हा साथी पीकू चिड़िया भूखा और थका हुआ वहाँ आया।",
                "text_en": "Just then, little bird Piku arrived, looking hungry and tired after a long flight.",
                "emotion": "sympathetic",
                "action": "look_at_friend"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "कोको ने बिना सोचे अपना आधा नट पीकू को प्यार से दे दिया!",
                "text_en": "Without a second thought, Koko lovingly shared half of the nut with Piku!",
                "emotion": "giving",
                "action": "share_nut"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "दोनों दोस्तों ने मिलकर खाया और पेड़ की डालियों पर खुशी का गीत गाया!",
                "text_en": "Both friends enjoyed the meal together and sang a happy song on the canopy!",
                "emotion": "celebrate",
                "action": "sing_together"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "सच्चे दोस्त हमेशा एक-दूसरे का ख्याल रखते हैं! फन लर्निंग किड्स देखते रहिए!",
                "text_en": "True friends always care for one another! Keep watching Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v1_bholu_puppy_farm",
        "style": "V1",
        "main_character": "bholu",
        "characters": ["bholu", "sheru"],
        "location": "farm",
        "background": "sunny_farm",
        "visual_theme": "helping_and_honesty",
        "title_hi": "भोलू पिल्लू की प्यारी खेती",
        "title_en": "Bholu Puppy's Sunny Farm Day",
        "short_title": "भोलू पिल्लू",
        "moral_hi": "दूसरों की मदद करना और ईमानदार रहना सबसे अच्छा गुण है।",
        "moral_en": "Helping others and being honest makes our hearts peaceful and happy.",
        "tags": [
            "Bholu Puppy", "Puppy Cartoon Hindi", "Sunny Farm Kids",
            "Farm Animals for Kids", "Fun Learning Kids", "Hindi Kids Animation"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "धूप खिले सुंदर खेत में, नन्हा भोलू पिल्लू अपनी लाल घंटी बजाता हुआ दौड़ रहा था!",
                "text_en": "In the sunny farm, cute little puppy Bholu was running with his shiny red collar!",
                "emotion": "playful",
                "action": "run_in_farm"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "उसने देखा कि खेत की प्यारी बकरियाँ बाड़े से थोड़ा दूर चली गई थीं।",
                "text_en": "He noticed that the little farm goats had wandered slightly far from the barn.",
                "emotion": "concerned",
                "action": "bark_gently"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "भोलू ने प्यार से पूंछ हिलाई और सबको सुरक्षित बाड़े की ओर चलने का रास्ता दिखाया।",
                "text_en": "Bholu gently wagged his tail and guided everyone safely back toward the green pasture.",
                "emotion": "guiding",
                "action": "guide_flock"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "किसान चाचा ने भोलू की समझदारी देखकर उसे प्यार से थपथपाया और मीठा दूध दिया!",
                "text_en": "The farmer uncle saw Bholu's responsibility, gently patted him, and offered fresh milk!",
                "emotion": "happy",
                "action": "receive_reward"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "भोलू ने खुशी से छलांग लगाई और खेत के सभी जानवरों के साथ खेलने लगा!",
                "text_en": "Bholu jumped with happiness and played merrily with all his barnyard pals!",
                "emotion": "joyful",
                "action": "jump_and_play"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "मददगार बनने से सबको प्यार मिलता है! फन लर्निंग किड्स के साथ सीखते रहिए!",
                "text_en": "Being helpful brings love and warmth from everyone! Keep learning with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v1_leo_pond_crossing",
        "style": "V1",
        "main_character": "leo",
        "characters": ["leo", "meenu"],
        "location": "pond",
        "background": "pond_park",
        "visual_theme": "courage_and_kindness",
        "title_hi": "छोटे शेर लियो का साहस",
        "title_en": "Little Leo Brave Pond Journey",
        "short_title": "साहसी लियो",
        "moral_hi": "धैर्य और साहस से हम हर मुश्किल पार कर सकते हैं।",
        "moral_en": "Patience, courage, and kindness help us cross every river of difficulty.",
        "tags": [
            "Leo Lion Cub", "Lion Cartoon Hindi", "Pond Adventure Kids",
            "Courage for Kids", "Fun Learning Kids", "Hindi Kids Animation"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "झील किनारे छोटे लियो शेर का बच्चा रंग-बिरंगे पत्थरों पर खेल रहा था!",
                "text_en": "By the tranquil pond, little lion cub Leo was playing along the stepping stones!",
                "emotion": "cheerful",
                "action": "walk_by_pond"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "पानी में सुंदर कमल खिले थे और नन्हीं बत्तखें तैर रही थीं।",
                "text_en": "Lovely lotuses bloomed in the pond, and cute ducklings swam gracefully.",
                "emotion": "amazed",
                "action": "watch_ducks"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "तभी एक छोटी गेंद पानी में गिर गई। लियो ने साहस जुटाया और लकड़ी की मदद से गेंद निकाली!",
                "text_en": "A little ball rolled into the water. Leo stayed calm and carefully retrieved it with a twig!",
                "emotion": "brave",
                "action": "rescue_ball"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "बत्तखों ने खुश होकर क्वैक-क्वैक किया और लियो को धन्यवाद दिया!",
                "text_en": "The ducklings quacked with joy and thanked brave little Leo with big smiles!",
                "emotion": "relieved",
                "action": "bow_kindly"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "लियो की समझदारी और हिम्मत ने सबका दिल जीत लिया!",
                "text_en": "Leo's quick thinking and gentle courage won the hearts of everyone at the pond!",
                "emotion": "happy",
                "action": "roar_gently"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "साहसी बनो और दूसरों के काम आओ! फन लर्निंग किड्स को सब्सक्राइब करना मत भूलिए!",
                "text_en": "Be brave and always lend a hand! Don't forget to subscribe to Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    },
    {
        "story_id": "v1_chintu_shares",
        "style": "V1",
        "main_character": "chintu",
        "characters": ["chintu", "golu"],
        "location": "forest",
        "background": "forest_meadow",
        "visual_theme": "sharing_and_caring",
        "title_hi": "चिंटू ने सीखा बाँटना",
        "title_en": "Chintu Learns to Share",
        "short_title": "चिंटू ने सीखा बाँटना",
        "moral_hi": "बाँटने से खुशियाँ और दोस्ती दोनों बढ़ती हैं।",
        "moral_en": "Sharing brings double joy and strengthens true friendship.",
        "tags": [
            "Chintu Cartoon", "Chintu and Golu", "Hindi Moral Story",
            "Sharing is Caring", "Fun Learning Kids", "Kids Animation Hindi",
            "Chintu Rabbit", "Golu Bear", "Children Cartoon"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "हरे-भरे जंगल में प्यारा खरगोश चिंटू उछल-कूद कर रहा था। सुबह की ताजी हवा में कितना मज़ा आ रहा था!",
                "text_en": "In the lush green forest, cute bunny Chintu was happily hopping around. The morning breeze felt so refreshing!",
                "emotion": "happy",
                "action": "hop_entrance"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "तभी चिंटू को एक बड़े पेड़ के नीचे एक रसीला लाल सेब मिला। वाह! इतना बड़ा और मीठा सेब!",
                "text_en": "Then Chintu spotted a juicy red apple under a big tree. Wow! Such a big and sweet apple!",
                "emotion": "excited",
                "action": "discover_apple"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "तभी उसका दोस्त गोलू भालू वहाँ आया। गोलू बहुत भूखा और उदास लग रहा था।",
                "text_en": "Just then, his friend Golu Bear arrived. Golu looked very hungry and sad.",
                "emotion": "concerned",
                "action": "golu_enters_sad"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "चिंटू ने एक पल सोचा, और मुस्कुराते हुए सेब के दो टुकड़े किए। उसने आधा सेब गोलू को दे दिया!",
                "text_en": "Chintu thought for a moment, then smiled and split the apple into two halves. He gave half to Golu!",
                "emotion": "generous",
                "action": "share_apple"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "गोलू का चेहरा खुशी से खिल उठा! दोनों दोस्तों ने मिलकर मीठा सेब खाया और हँसने लगे।",
                "text_en": "Golu's face lit up with joy! Both friends enjoyed the sweet apple together and giggled with delight.",
                "emotion": "celebrate",
                "action": "munch_and_celebrate"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "बाँटने से खुशियाँ दोगुनी हो जाती हैं! फन लर्निंग किड्स के साथ सीखते रहिए, मुस्कुराते रहिए!",
                "text_en": "Sharing makes joy double! Keep learning and smiling with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_outro"
            }
        ]
    },
    {
        "story_id": "v1_chintu_morning_exercise",
        "style": "V1",
        "main_character": "chintu",
        "characters": ["chintu", "golu"],
        "location": "meadow",
        "background": "forest_meadow",
        "visual_theme": "health_and_fitness",
        "title_hi": "चिंटू और गोलू की सुबह की कसरत",
        "title_en": "Chintu and Golu Morning Exercise",
        "short_title": "सुबह की कसरत",
        "moral_hi": "रोज सुबह कसरत करने से शरीर स्वस्थ और मन खुश रहता है।",
        "moral_en": "Daily morning exercise keeps body fit and mind active.",
        "tags": [
            "Morning Exercise Kids", "Chintu Bunny", "Golu Bear",
            "Health Habits Kids", "Fun Learning Kids", "Hindi Moral Story"
        ],
        "scenes": [
            {
                "scene_id": 1,
                "speaker": "narrator",
                "text_hi": "सूरज उगते ही चिंटू खरगोश ने लंबी सांस ली और गोलू भालू को जगाने पहुंचा!",
                "text_en": "As the sun rose, bunny Chintu took a deep breath and went to wake up Golu Bear!",
                "emotion": "energetic",
                "action": "stretch_body"
            },
            {
                "scene_id": 2,
                "speaker": "narrator",
                "text_hi": "गोलू आलस में था, लेकिन चिंटू ने कहा, चलो दोस्त, थोड़ी कसरत करते हैं!",
                "text_en": "Golu was feeling lazy, but Chintu cheerfully said: Let's do some fun morning exercises!",
                "emotion": "encouraging",
                "action": "wave_hands"
            },
            {
                "scene_id": 3,
                "speaker": "narrator",
                "text_hi": "दोनों ने पहले दोनों हाथ ऊपर उठाए, फिर धीरे-धीरे कमर झुकाई। एक, दो, तीन, चार!",
                "text_en": "Both raised their arms high, then gently stretched their waists. One, two, three, four!",
                "emotion": "focused",
                "action": "do_stretching"
            },
            {
                "scene_id": 4,
                "speaker": "narrator",
                "text_hi": "फिर दोनों ने घास पर हल्की दौड़ लगाई। ताजी हवा से गोलू का आलस छूमंतर हो गया!",
                "text_en": "Then they did a gentle jog on the grass. The fresh breeze blew away all of Golu's laziness!",
                "emotion": "happy",
                "action": "jog_in_circle"
            },
            {
                "scene_id": 5,
                "speaker": "narrator",
                "text_hi": "कसरत पूरी करके दोनों ने मीठा नारियल पानी पिया और ताजगी से भर गए!",
                "text_en": "After the workout, both enjoyed fresh coconut water and felt completely energized!",
                "emotion": "refreshed",
                "action": "drink_water"
            },
            {
                "scene_id": 6,
                "speaker": "narrator",
                "text_hi": "स्वस्थ शरीर में ही स्वस्थ मन रहता है! फन लर्निंग किड्स के साथ फिट रहिए!",
                "text_en": "A healthy mind lives in a healthy body! Stay fit with Fun Learning Kids!",
                "emotion": "proud",
                "action": "wave_to_viewer"
            }
        ]
    }
]


class StoryEngine:
    def __init__(self, history_file=CARTOON_HISTORY_FILE):
        self.history_file = history_file
        self.variety_mgr = VarietyManager(self.history_file)

    def load_history(self):
        """Loads persistent history via VarietyManager."""
        return self.variety_mgr.load_history()

    def determine_next_style(self, forced_style=None):
        """
        Determines the next style using strict 1:1 alternation (Day 1=V1, Day 2=V4...).
        """
        return self.variety_mgr.determine_next_style(forced_style=forced_style)

    def _brand_story(self, story):
        """Dynamically applies active channel branding to story scenes and tags."""
        if not story:
            return story
        branded = dict(story)
        if "scenes" in story:
            branded_scenes = []
            for sc in story["scenes"]:
                sc_copy = dict(sc)
                if "text_hi" in sc_copy:
                    sc_copy["text_hi"] = sc_copy["text_hi"].replace("फन लर्निंग किड्स", CHANNEL_NAME_HI)
                if "text_en" in sc_copy:
                    sc_copy["text_en"] = sc_copy["text_en"].replace("Fun Learning Kids", CHANNEL_NAME)
                branded_scenes.append(sc_copy)
            branded["scenes"] = branded_scenes

        if "tags" in story:
            branded_tags = [
                t.replace("Fun Learning Kids", CHANNEL_NAME).replace("fun learning kids", CHANNEL_NAME.lower())
                for t in story["tags"]
            ]
            if CHANNEL_NAME not in branded_tags:
                branded_tags.append(CHANNEL_NAME)
            branded["tags"] = branded_tags

        return branded

    def get_next_story(self, forced_story_id=None, forced_style=None):
        """
        Selects the next story adhering strictly to 1:1 alternation and anti-repetition rules.
        """
        story = self.variety_mgr.select_next_production_story(
            STORY_BANK,
            forced_style=forced_style,
            forced_story_id=forced_story_id
        )
        return self._brand_story(story)

    def record_run(
        self,
        story_id,
        style,
        title,
        main_character=None,
        characters=None,
        background=None,
        location=None,
        visual_theme=None,
        video_path=None,
        thumb_path=None,
        video_id=None,
        status="completed",
        video_hash=None
    ):
        """Records production in persistent history with full variety attributes."""
        # Find story in bank if attributes not supplied
        if not main_character or not background:
            for s in STORY_BANK:
                if s["story_id"] == story_id:
                    main_character = main_character or s.get("main_character")
                    characters = characters or s.get("characters")
                    background = background or s.get("background")
                    location = location or s.get("location")
                    visual_theme = visual_theme or s.get("visual_theme")
                    break

        self.variety_mgr.record_production(
            story_id=story_id,
            style=style,
            title=title,
            main_character=main_character,
            characters=characters,
            background=background,
            location=location,
            visual_theme=visual_theme,
            video_path=video_path,
            thumbnail_path=thumb_path,
            video_hash=video_hash,
            upload_id=video_id,
            status=status
        )

    def build_youtube_metadata(self, story):
        """Builds YouTube metadata dictionary ready for uploader.py."""
        # Calculate dynamic episode count to ensure 100% unique titles and avoid spam filters
        history = self.load_history()
        completed_runs = [h for h in history if h.get("status") in ("uploaded", "completed")]
        ep_num = len(completed_runs) + 1

        story_runs = [h for h in completed_runs if h.get("story_id") == story["story_id"]]
        story_part = len(story_runs) + 1

        ep_tag = f"Ep {ep_num}"
        part_tag = f" (Part {story_part})" if story_part > 1 else ""

        title = f"{ep_tag}: {story['title_hi']}{part_tag} | {story['short_title']} 🚂 | {CHANNEL_NAME}"
        if len(title) > 100:
            title = f"{ep_tag}: {story['title_hi']} | {story['short_title']} 🚂 | {CHANNEL_NAME}"
            if len(title) > 100:
                title = title[:97] + "..."

        hashtag_clean = CHANNEL_NAME.replace(" ", "")
        desc_parts = [
            f"🌟 Episode {ep_num}: {story['title_hi']} ({story['title_en']})",
            "",
            f"✨ सीख (Moral): {story['moral_hi']}",
            f"✨ Moral: {story['moral_en']}",
            "",
            f"Welcome to {CHANNEL_NAME}! Enjoy this lovely animated Hindi cartoon episode "
            "crafted specially for toddlers, preschoolers, and young learners. "
            "Subscribe for daily educational cartoons, stories, and fun songs!",
            "",
            f"🎭 Main Character: {story.get('main_character', '').title()}",
            f"🎨 Animation Style: {story.get('style')}",
            "",
            f"#{hashtag_clean} #KidsCartoon #HindiAnimation #MoralStories #KidsLearning #CartoonAnimation"
        ]
        description = "\n".join(desc_parts)

        tags = [
            t.replace("Fun Learning Kids", CHANNEL_NAME).replace("fun learning kids", CHANNEL_NAME.lower())
            for t in story.get("tags", [])
        ]
        if CHANNEL_NAME not in tags:
            tags.append(CHANNEL_NAME)

        return {
            "title": title,
            "description": description,
            "tags": tags,
            "topic": "cartoon_animation",
            "style": story["style"],
            "story_id": story["story_id"],
            "moral": story["moral_en"]
        }


if __name__ == "__main__":
    engine = StoryEngine()
    next_s = engine.get_next_story()
    print("Next Selected Story:", next_s["title_hi"], f"({next_s['style']}) - Main Char: {next_s.get('main_character')}")
    meta = engine.build_youtube_metadata(next_s)
    print("Title:", meta["title"])
