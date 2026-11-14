"""Guidance on treatment and health improvement, for the astronaut.

The challenge asks for a tool that "provides guidance on treatments and health
improvements". For every finding AEGIS gives one card, in English and Arabic:

  means        what the finding means, in plain words
  do_now       first steps the astronaut can take right away (self-care, re-measure)
  improve      what prevents it coming back (the countermeasure)
  call_if      when to contact the flight surgeon or follow the emergency procedure
  hazard/risk  the NASA Human Research Program hazard and risk behind it
  source       the NASA HRP page it is based on (from the challenge's Resources tab)

Safety boundaries, on purpose:
  * AEGIS never names a medicine or a dose. Medicines are given only by the flight
    surgeon's instruction and the mission's approved medical procedures.
  * Every card says when to stop self-care and call for help.
  * The text is general guidance written from the NASA HRP pages, not a diagnosis.
"""

HRP = "https://www.nasa.gov/hrp/"
SRC = {
    "isolation": HRP + "hazard-isolation-and-confinement/",
    "gravity": HRP + "hazard-gravity-fields/",
    "closed": HRP + "hazard-hostile-closed-environments/",
    "distance": HRP + "hazard-distance-from-earth/",
    "radiation": HRP + "hazard-space-radiation/",
    "risks": HRP + "risks/",
}

MEDICINE_NOTE = ("Medicines: only as instructed by the flight surgeon, following the mission's approved "
                 "medical procedures. AEGIS never suggests a medicine or a dose.")
MEDICINE_NOTE_AR = ("الأدوية: فقط بتعليمات طبيب الرحلة ووفق إجراءات المهمة الطبية المعتمدة. "
                    "إيجيس لا يقترح أي دواء أو جرعة أبدًا.")

# One card per pattern (fusion.PATTERNS) and per single signal when no pattern fired.
CARDS = {
    "stress_fatigue": {
        "hazard": "Isolation and confinement", "risk": "Risk of Behavioral Changes and Psychiatric Disorders",
        "source": SRC["isolation"],
        "means": "Body and mind are under strain together: poor sleep, a raised heart rate or blood pressure, "
                 "low mood or fatigue. NASA lists sleep loss, circadian disruption and work overload as the "
                 "main drivers of reduced performance on long missions.",
        "do_now": ["Stop non-critical work for today and tell the commander you need a lighter schedule.",
                   "Keep an 8-hour sleep window tonight, with lights dimmed for an hour before.",
                   "Re-measure heart rate and blood pressure after 10 minutes of rest."],
        "improve": ["Keep a fixed sleep and wake time; use bright light in the morning and dim light at night "
                    "(NASA studies light therapy for circadian alignment).",
                    "Plan the workload with breaks; keep the daily exercise session.",
                    "Keep the daily journal: NASA uses journaling to follow crew wellbeing in isolation."],
        "call_if": ["It is still ACT tomorrow.", "You have thoughts of harming yourself or feel unable to cope: "
                    "contact the flight surgeon or flight psychologist now."],
        "ar": {"means": "الجسم والنفس تحت ضغط معًا: نوم سيئ، ونبض أو ضغط مرتفع، ومزاج منخفض أو إرهاق. تذكر NASA أن "
                        "قلة النوم واضطراب الساعة البيولوجية وكثرة العمل هي أهم أسباب تراجع الأداء في المهمات الطويلة.",
               "do_now": ["أوقف الأعمال غير الحرجة اليوم وأخبر القائد أنك تحتاج جدولًا أخف.",
                          "خصّص 8 ساعات للنوم الليلة، مع إضاءة خافتة قبلها بساعة.",
                          "أعد قياس النبض والضغط بعد 10 دقائق راحة."],
               "improve": ["ثبّت موعد النوم والاستيقاظ؛ ضوء قوي صباحًا وخافت ليلًا (تدرس NASA العلاج بالضوء لضبط الساعة البيولوجية).",
                           "نظّم عبء العمل مع استراحات، وحافظ على التمرين اليومي.",
                           "استمر في كتابة اليوميات: تستخدمها NASA لمتابعة الحالة النفسية في العزلة."],
               "call_if": ["لو الحالة لسه ACT بكرة.", "لو عندك أفكار بإيذاء نفسك أو تشعر أنك لا تستطيع التحمل: "
                           "تواصل مع طبيب الرحلة أو الطبيب النفسي الآن."]},
    },
    "sleep_debt": {
        "hazard": "Isolation and confinement", "risk": "Risk of Inadequate Sleep and Irregular Schedules",
        "source": SRC["isolation"],
        "means": "You have slept less than your normal for several nights. Sleep debt builds up and slows "
                 "reactions and decisions.",
        "do_now": ["Go to bed at your usual time tonight; no screens in the last 30 minutes.",
                   "Use the eye mask and earplugs; keep the sleep station cool and dark.",
                   "Avoid caffeine in the 6 hours before sleep."],
        "improve": ["Keep the same sleep window every day, even on rest days.",
                    "Morning light, evening dim light, to keep the body clock aligned."],
        "call_if": ["Sleep stays short for a week despite these steps.", "You feel unsafe to do a critical task."],
        "ar": {"means": "نمت أقل من معدلك الطبيعي لعدة ليالٍ. نقص النوم يتراكم ويبطئ رد الفعل واتخاذ القرار.",
               "do_now": ["نم في موعدك المعتاد الليلة، وبدون شاشات آخر 30 دقيقة.",
                          "استخدم قناع العين وسدادات الأذن، وخلّي مكان النوم باردًا ومظلمًا.",
                          "تجنّب الكافيين في الـ 6 ساعات قبل النوم."],
               "improve": ["حافظ على نفس موعد النوم كل يوم حتى في أيام الراحة.",
                           "ضوء صباحًا وإضاءة خافتة مساءً لضبط الساعة البيولوجية."],
               "call_if": ["لو النوم فضل قليل أسبوعًا رغم هذه الخطوات.", "لو حاسس إنك مش آمن تعمل مهمة حرجة."]},
    },
    "mental_strain": {
        "hazard": "Isolation and confinement", "risk": "Risk of Behavioral Changes and Psychiatric Disorders",
        "source": SRC["isolation"],
        "means": "Your mood is lower than your normal and your log shows more stress words. In isolation and "
                 "confinement this is common, and early support works best.",
        "do_now": ["Take personal time today; record or listen to a message from family.",
                   "Talk with a crewmate you trust.", "Write a few lines in your journal about what is weighing on you."],
        "improve": ["Plan small things to look forward to (a call, a meal together, a hobby such as plant care: "
                    "NASA studies whether space gardening helps with isolation).",
                    "Keep exercise and sleep regular: both support mood."],
        "call_if": ["Low mood lasts more than a few days.", "You have thoughts of harming yourself: contact the "
                    "flight surgeon or flight psychologist now."],
        "ar": {"means": "مزاجك أقل من معدلك الطبيعي ويومياتك فيها كلمات ضغط أكتر. ده شائع في العزلة، والدعم المبكر هو الأفضل.",
               "do_now": ["خذ وقتًا شخصيًا اليوم، وسجّل أو اسمع رسالة من العائلة.",
                          "اتكلم مع زميل تثق فيه في الطاقم.", "اكتب سطرين في يومياتك عن اللي مضايقك."],
               "improve": ["خطّط لحاجات صغيرة تستناها (مكالمة، وجبة مع الطاقم، هواية زي رعاية النباتات: تدرس NASA "
                           "إن كانت الزراعة في الفضاء تساعد على تحمّل العزلة).",
                           "حافظ على انتظام التمرين والنوم: الاتنين بيدعموا المزاج."],
               "call_if": ["لو المزاج المنخفض استمر أكتر من كام يوم.", "لو عندك أفكار بإيذاء نفسك: تواصل مع طبيب الرحلة "
                           "أو الطبيب النفسي الآن."]},
    },
    "low_oxygen": {
        "hazard": "Hostile/closed environments", "risk": "Risk of Hypoxia",
        "source": SRC["closed"],
        "means": "Blood oxygen is below your normal or below the 92% safety limit. It can come from the cabin "
                 "air or from the lungs.",
        "do_now": ["Re-measure now with the finger pulse oximeter (hand warm and still).",
                   "Stop physical work and rest; tell a crewmate.",
                   "Check the cabin air readings (CO2, O2)."],
        "improve": ["Report any cabin air alarm at once; keep the CO2 scrubber serviced on schedule."],
        "call_if": ["The repeat value is still below 92%: follow the emergency procedure and contact the flight "
                    "surgeon now.", "Shortness of breath, chest pain or confusion: emergency procedure now."],
        "ar": {"means": "الأكسجين في الدم أقل من معدلك أو أقل من حد الأمان 92%. ممكن يكون السبب هواء المقصورة أو الرئتين.",
               "do_now": ["أعد القياس الآن بجهاز الإصبع (اليد دافئة وثابتة).",
                          "أوقف أي مجهود بدني واسترح، وبلّغ زميلًا.", "افحص قراءات هواء المقصورة (CO2 وO2)."],
               "improve": ["بلّغ فورًا عن أي إنذار في هواء المقصورة، وحافظ على صيانة جهاز إزالة CO2 في موعدها."],
               "call_if": ["لو القياس المعاد لسه تحت 92%: اتبع إجراء الطوارئ وتواصل مع طبيب الرحلة الآن.",
                           "ضيق تنفس أو ألم في الصدر أو تشوش: إجراء الطوارئ الآن."]},
    },
    "high_bp": {
        "hazard": "Gravity fields", "risk": "Risk of Cardiovascular Adaptations",
        "source": SRC["gravity"],
        "means": "Blood pressure has been above your normal. In weightlessness fluids shift toward the head, "
                 "and stress raises blood pressure too.",
        "do_now": ["Re-measure after 5 minutes seated, arm at heart level.",
                   "Cut salt and caffeine today; drink water as planned.", "Take a rest break."],
        "improve": ["Keep the daily aerobic and resistance exercise.", "Follow the mission nutrition plan for salt."],
        "call_if": ["It stays high for 3 days.", "Above 180/120, or with headache, vision change or chest pain: "
                    "contact the flight surgeon now."],
        "ar": {"means": "الضغط أعلى من معدلك. في انعدام الجاذبية السوائل تتجه للرأس، والضغط النفسي يرفع الضغط أيضًا.",
               "do_now": ["أعد القياس بعد 5 دقائق جلوس، والذراع في مستوى القلب.",
                          "قلّل الملح والكافيين اليوم، واشرب الماء حسب الخطة.", "خذ استراحة."],
               "improve": ["حافظ على التمرين الهوائي وتمرين المقاومة يوميًا.", "التزم بخطة التغذية بخصوص الملح."],
               "call_if": ["لو فضل مرتفع 3 أيام.", "لو فوق 180/120، أو مع صداع أو تغيّر في النظر أو ألم في الصدر: "
                           "تواصل مع طبيب الرحلة الآن."]},
    },
    "glucose": {
        "hazard": "Distance from Earth", "risk": "Risk of Inadequate Food and Nutrition",
        "source": SRC["distance"],
        "means": "Morning blood sugar is outside your normal. Less activity and a limited diet on long "
                 "missions can upset it.",
        "do_now": ["Repeat the finger-prick check to confirm.",
                   "If it is low (below 70 mg/dL) and you feel shaky: eat a fast-sugar snack from the food "
                   "supply, then re-check in 15 minutes.",
                   "If it is high: drink water and check what you ate since yesterday."],
        "improve": ["Eat the planned meals at regular times; keep the daily exercise."],
        "call_if": ["Below 54 or above 250 mg/dL: contact the flight surgeon now.", "It stays out of range for 3 days."],
        "ar": {"means": "سكر الدم الصباحي خارج معدلك. قلة الحركة ومحدودية الأكل في المهمات الطويلة ممكن تأثر عليه.",
               "do_now": ["أعد قياس السكر من وخزة الإصبع للتأكد.",
                          "لو منخفض (أقل من 70) وحاسس برعشة: كُل وجبة خفيفة سريعة السكر من مخزون الطعام، وأعد القياس بعد 15 دقيقة.",
                          "لو مرتفع: اشرب ماء وراجع أكلك من امبارح."],
               "improve": ["كُل الوجبات المخططة في مواعيد منتظمة، وحافظ على التمرين اليومي."],
               "call_if": ["أقل من 54 أو أكتر من 250: تواصل مع طبيب الرحلة الآن.", "لو فضل خارج المعدل 3 أيام."]},
    },
    "fever": {
        "hazard": "Hostile/closed environments", "risk": "Risk of Altered Immune System Responses",
        "source": SRC["closed"],
        "means": "Your temperature is above normal. In a closed habitat germs pass more easily between crew, "
                 "and NASA notes that the immune system can change in space.",
        "do_now": ["Re-check temperature in 30 minutes, before eating or drinking.",
                   "Rest, drink fluids, and keep distance from the crew; clean shared surfaces you touched.",
                   "Note any other symptoms (cough, sore throat, pain) in the check-in."],
        "improve": ["Hand hygiene and cleaning of shared surfaces; report symptoms early."],
        "call_if": ["38.0 °C or more on the repeat check: contact the flight surgeon today.",
                    "Fever with breathing difficulty, confusion or a stiff neck: emergency procedure now."],
        "ar": {"means": "حرارتك أعلى من الطبيعي. في المسكن المغلق الجراثيم تنتقل بسهولة بين الطاقم، وتذكر NASA أن المناعة ممكن تتغير في الفضاء.",
               "do_now": ["أعد قياس الحرارة بعد 30 دقيقة، قبل الأكل أو الشرب.",
                          "استرح واشرب سوائل وابتعد عن الطاقم، ونظّف الأسطح المشتركة اللي لمستها.",
                          "سجّل أي أعراض تانية (كحة، التهاب حلق، ألم) في التسجيل اليومي."],
               "improve": ["غسل اليدين وتنظيف الأسطح المشتركة، والإبلاغ المبكر عن الأعراض."],
               "call_if": ["38.0 درجة أو أكتر في القياس المعاد: تواصل مع طبيب الرحلة اليوم.",
                           "حرارة مع صعوبة تنفس أو تشوش أو تيبس في الرقبة: إجراء الطوارئ الآن."]},
    },
    "cabin_air": {
        "hazard": "Hostile/closed environments", "risk": "Risk of Hypoxia",
        "source": SRC["closed"],
        "means": "Cabin CO2 is above its limit. It affects the whole crew and can cause headache, fatigue and "
                 "faster breathing. Fix the air first.",
        "do_now": ["Inspect and service the CO2 scrubber.",
                   "Treat headache and fatigue today as possibly caused by CO2, not only by stress.",
                   "Avoid heavy exercise until CO2 is back below the limit."],
        "improve": ["Keep the scrubber maintenance schedule; watch the 7-day CO2 average."],
        "call_if": ["CO2 stays above the ACT limit after servicing.", "Anyone has confusion or severe headache."],
        "ar": {"means": "ثاني أكسيد الكربون في المقصورة فوق الحد. ده بيأثر على الطاقم كله وممكن يسبب صداع وإرهاق وتنفس أسرع. صلّح الهواء الأول.",
               "do_now": ["افحص جهاز إزالة CO2 وصلّحه.",
                          "اعتبر الصداع والإرهاق اليوم ممكن يكونوا بسبب CO2، مش الضغط النفسي بس.",
                          "تجنّب التمرين الشديد لحد ما CO2 يرجع تحت الحد."],
               "improve": ["التزم بجدول صيانة الجهاز، وتابع متوسط CO2 لآخر 7 أيام."],
               "call_if": ["لو CO2 فضل فوق حد ACT بعد الصيانة.", "لو حد في الطاقم عنده تشوش أو صداع شديد."]},
    },
    "symptom": {
        "hazard": "Distance from Earth", "risk": "Risk of Adverse Health Outcomes and Decrements in Performance due to Medical Conditions",
        "source": SRC["distance"],
        "means": "You reported a severe symptom. NASA notes that on deep-space missions the crew must handle "
                 "medical emergencies with minimal support from Earth, so act now.",
        "do_now": ["Stop current work and tell the crew.", "Follow the mission emergency medical procedure.",
                   "Contact the flight surgeon now, without waiting for the next planned contact."],
        "improve": ["Keep reporting symptoms early in the daily check-in."],
        "call_if": ["Now."],
        "ar": {"means": "بلّغت عن عَرَض شديد. تذكر NASA أن الطاقم في رحلات الفضاء العميق لازم يتعامل مع الطوارئ الطبية بأقل دعم من الأرض، فتصرّف الآن.",
               "do_now": ["أوقف العمل الحالي وبلّغ الطاقم.", "اتبع إجراء الطوارئ الطبي للمهمة.",
                          "تواصل مع طبيب الرحلة الآن، بدون انتظار الاتصال المخطط التالي."],
               "improve": ["استمر في الإبلاغ المبكر عن الأعراض في التسجيل اليومي."],
               "call_if": ["الآن."]},
    },
}

# A single signal off with no pattern: point to the closest card.
SIGNAL_CARD = {"heart_rate": "stress_fatigue", "bp_systolic": "high_bp", "bp_diastolic": "high_bp",
               "spo2": "low_oxygen", "body_temp": "fever", "glucose": "glucose", "breathing_rate": "low_oxygen",
               "sleep_hours": "sleep_debt", "mood_score": "mental_strain", "stress_words": "mental_strain",
               "fatigue_score": "sleep_debt", "blink_rate": "sleep_debt"}

TITLES_AR = {"stress_fatigue": "ضغط جسدي ونفسي معًا", "sleep_debt": "نقص النوم", "mental_strain": "إجهاد نفسي",
             "low_oxygen": "انخفاض الأكسجين", "high_bp": "ارتفاع ضغط الدم", "glucose": "سكر الدم خارج المعدل",
             "fever": "احتمال حمّى", "cabin_air": "هواء المقصورة", "symptom": "عَرَض شديد"}
TITLES = {"stress_fatigue": "Combined physical and mental stress", "sleep_debt": "Sleep debt",
          "mental_strain": "Mental strain", "low_oxygen": "Low blood oxygen", "high_bp": "Raised blood pressure",
          "glucose": "Blood sugar out of range", "fever": "Possible fever", "cabin_air": "Cabin air quality",
          "symptom": "Severe symptom reported"}


def _card(key, lang):
    c = CARDS[key]
    base = {"id": key, "hazard": c["hazard"], "risk": c["risk"], "source": c["source"]}
    if lang == "ar":
        return {**base, "title": TITLES_AR[key], **c["ar"], "medicine": MEDICINE_NOTE_AR}
    return {**base, "title": TITLES[key], "means": c["means"], "do_now": c["do_now"],
            "improve": c["improve"], "call_if": c["call_if"], "medicine": MEDICINE_NOTE}


def for_decision(decision, lang="en"):
    """Guidance cards for one day's decision, most urgent first (at most 3)."""
    keys = []
    if decision.get("reported_symptoms"):
        keys.append("symptom")
    for p in decision.get("patterns", []):
        if p["id"] in CARDS and p["id"] not in keys:
            keys.append(p["id"])
    if not keys:
        for f in decision.get("flags", []):
            k = SIGNAL_CARD.get(f["signal"])
            if k and k not in keys:
                keys.append(k)
    return [_card(k, lang) for k in keys[:3]]
