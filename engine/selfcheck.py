"""Body self-check: the astronaut clicks where it hurts.

The challenge suggests "a human figure where each part of the body is clickable" and a
tool that helps astronauts "assess their own health". On the body figure the astronaut
clicks a body system, ticks what he feels and how strong it is, and gets an answer at
once, in English or Arabic:

  * the status: ACT now (emergency symptom, or a strong one that must not wait),
    WATCH (log it, follow the steps, check again), or NORMAL;
  * for each symptom: what it may mean in space, what to do now, when to call;
  * the NASA HRP hazard page it is based on.

Symptoms marked `act` are always ACT now (the same list as the check-in's severe symptoms,
plus a few). The answer never names a medicine or a dose, and it does not diagnose.
"""

from .guidance import SRC, MEDICINE_NOTE, MEDICINE_NOTE_AR

# id: (EN name, AR name, act_always, means EN, means AR, do_now EN, do_now AR, call EN, call AR, source)
_S = {
    "brain": [
        ("headache", "Headache", "صداع", False,
         "Common in space: fluids shift toward the head, and high cabin CO2 also causes headaches.",
         "شائع في الفضاء: السوائل تتجه للرأس، وارتفاع CO2 في المقصورة يسبب الصداع أيضًا.",
         ["Check the cabin CO2 reading.", "Drink water and rest away from screens for 20 minutes."],
         ["افحص قراءة CO2 في المقصورة.", "اشرب ماء واسترح بعيدًا عن الشاشات 20 دقيقة."],
         "Call if it is severe, sudden, or comes with vision change, confusion or a stiff neck.",
         "تواصل مع الطبيب لو شديد أو مفاجئ أو معه تغيّر في النظر أو تشوش أو تيبس في الرقبة.", "closed"),
        ("severe headache", "Severe or sudden headache", "صداع شديد أو مفاجئ", True,
         "A severe or sudden headache must be checked at once.", "الصداع الشديد أو المفاجئ لازم يتفحص فورًا.",
         ["Stop work and tell a crewmate.", "Follow the mission emergency medical procedure."],
         ["أوقف العمل وبلّغ زميلًا.", "اتبع إجراء الطوارئ الطبي للمهمة."],
         "Contact the flight surgeon now.", "تواصل مع طبيب الرحلة الآن.", "distance"),
        ("vision changes", "Blurred or changed vision", "زغللة أو تغيّر في النظر", True,
         "In weightlessness fluids shift toward the head and can press on the eyes (NASA HRP, gravity fields).",
         "في انعدام الجاذبية السوائل تتجه للرأس وممكن تضغط على العينين (NASA HRP، الجاذبية).",
         ["Stop precision work.", "Note which eye and what changed; do the eye check in the medical kit if trained."],
         ["أوقف أي عمل دقيق.", "سجّل أي عين وإيه اللي اتغيّر، واعمل فحص العين من حقيبة الإسعاف لو متدرّب."],
         "Contact the flight surgeon now.", "تواصل مع طبيب الرحلة الآن.", "gravity"),
        ("confusion", "Confusion or trouble thinking", "تشوش أو صعوبة في التفكير", True,
         "Confusion can come from bad air (CO2, low oxygen), low blood sugar or illness.",
         "التشوش ممكن يكون من هواء سيئ (CO2 أو أكسجين قليل) أو سكر منخفض أو مرض.",
         ["A crewmate checks blood oxygen and blood sugar now.", "Check the cabin air."],
         ["زميل يقيس الأكسجين والسكر الآن.", "افحص هواء المقصورة."],
         "Emergency procedure and flight surgeon now.", "إجراء الطوارئ وطبيب الرحلة الآن.", "closed"),
        ("dizziness", "Dizziness", "دوخة", False,
         "Changing gravity affects balance and the inner ear; dizziness is common after gravity transitions.",
         "تغيّر الجاذبية يأثر على التوازن والأذن الداخلية، والدوخة شائعة بعد الانتقال بين الجاذبيات.",
         ["Stop moving, hold on, and keep the head still.", "Measure heart rate and blood pressure."],
         ["توقف عن الحركة وامسك في حاجة وثبّت رأسك.", "قِس النبض والضغط."],
         "Call if you faint, or it lasts more than an hour.", "تواصل لو أغمي عليك أو استمرت أكتر من ساعة.", "gravity"),
        ("sleep problems", "Trouble sleeping", "صعوبة في النوم", False,
         "Light cycles, noise and workload disturb sleep in space (NASA HRP, isolation and confinement).",
         "دورات الضوء والضوضاء والعمل بتلخبط النوم في الفضاء (NASA HRP، العزلة).",
         ["Keep a fixed sleep time; dim light for the last hour.", "Use the eye mask and earplugs."],
         ["ثبّت موعد النوم، وضوء خافت آخر ساعة.", "استخدم قناع العين وسدادات الأذن."],
         "Call if it lasts a week or affects your work.", "تواصل لو استمرت أسبوعًا أو أثّرت على شغلك.", "isolation"),
        ("low mood", "Low mood, anxiety or feeling alone", "مزاج منخفض أو قلق أو وحدة", False,
         "Isolation and confinement affect mood; it is common and early support works best.",
         "العزلة بتأثر على المزاج، وده شائع، والدعم المبكر هو الأفضل.",
         ["Talk with a crewmate you trust.", "Write in your journal; schedule a call with family."],
         ["اتكلم مع زميل تثق فيه.", "اكتب في يومياتك، واحجز مكالمة مع العائلة."],
         "Call the flight psychologist if it lasts days, or now if you think of harming yourself.",
         "تواصل مع الطبيب النفسي لو استمر أيامًا، أو الآن لو عندك أفكار بإيذاء نفسك.", "isolation"),
    ],
    "heart": [
        ("chest pain", "Chest pain or pressure", "ألم أو ضغط في الصدر", True,
         "Chest pain must be treated as an emergency until proven otherwise.",
         "ألم الصدر يتعامل معه كطوارئ لحد ما يثبت العكس.",
         ["Stop all activity and sit or strap in.", "Follow the mission emergency medical procedure."],
         ["أوقف أي نشاط واقعد أو اربط نفسك.", "اتبع إجراء الطوارئ الطبي للمهمة."],
         "Contact the flight surgeon now.", "تواصل مع طبيب الرحلة الآن.", "distance"),
        ("palpitations", "Racing or irregular heartbeat", "خفقان أو نبض غير منتظم", False,
         "Stress, caffeine, poor sleep and dehydration can cause it; fluid shifts also change how the heart works.",
         "الضغط النفسي والكافيين وقلة النوم والجفاف ممكن يسببوه، وانتقال السوائل بيغيّر شغل القلب.",
         ["Sit still, breathe slowly, and measure your pulse for 60 seconds.", "Note the time and the pulse value."],
         ["اقعد ثابت واتنفس ببطء وقِس النبض 60 ثانية.", "سجّل الوقت وقيمة النبض."],
         "Call if the pulse is above 130, irregular for more than a few minutes, or with chest pain or fainting.",
         "تواصل لو النبض فوق 130 أو غير منتظم لأكتر من دقايق، أو مع ألم صدر أو إغماء.", "gravity"),
        ("fainting", "Fainting or nearly fainting", "إغماء أو قرب الإغماء", True,
         "NASA notes light-headedness and fainting when moving between gravity fields.",
         "تذكر NASA الدوخة والإغماء عند الانتقال بين الجاذبيات.",
         ["Lie down with legs raised if gravity allows; a crewmate stays with you.", "Measure pulse and blood pressure."],
         ["استلقِ ورجليك مرفوعة لو الجاذبية تسمح، وزميل يفضل معاك.", "قِس النبض والضغط."],
         "Contact the flight surgeon now.", "تواصل مع طبيب الرحلة الآن.", "gravity"),
        ("swelling", "Puffy face or swollen legs", "انتفاخ الوجه أو تورم الرجلين", False,
         "A puffy face is common in weightlessness (fluids shift up). Swollen legs after landing can also happen.",
         "انتفاخ الوجه شائع في انعدام الجاذبية (السوائل تطلع لفوق)، وتورم الرجلين ممكن بعد الهبوط.",
         ["Measure blood pressure.", "Keep the planned water and salt intake."],
         ["قِس الضغط.", "التزم بكمية الماء والملح المخططة."],
         "Call if one leg is swollen and painful, or with shortness of breath.",
         "تواصل لو رجل واحدة متورمة وبتوجع، أو مع ضيق تنفس.", "gravity"),
    ],
    "lungs": [
        ("shortness of breath", "Shortness of breath", "ضيق تنفس", True,
         "Can come from cabin air (CO2, low oxygen) or from the lungs or heart.",
         "ممكن يكون من هواء المقصورة (CO2 أو أكسجين قليل) أو من الرئة أو القلب.",
         ["Measure blood oxygen now.", "Check the cabin air; follow the emergency procedure."],
         ["قِس الأكسجين الآن.", "افحص هواء المقصورة، واتبع إجراء الطوارئ."],
         "Contact the flight surgeon now.", "تواصل مع طبيب الرحلة الآن.", "closed"),
        ("cough", "Cough", "كحة", False,
         "Dry cabin air, dust or an infection passed between crew in a closed habitat.",
         "هواء المقصورة الجاف أو الغبار أو عدوى بتنتقل بين الطاقم في المكان المغلق.",
         ["Measure temperature and blood oxygen.", "Drink water; cover coughs and clean shared surfaces."],
         ["قِس الحرارة والأكسجين.", "اشرب ماء، وغطّي الكحة ونظّف الأسطح المشتركة."],
         "Call if you have fever, blood in the cough, or oxygen below 94%.",
         "تواصل لو عندك حرارة أو دم مع الكحة أو أكسجين أقل من 94%.", "closed"),
        ("blocked nose", "Blocked nose or sinus pressure", "انسداد الأنف أو ضغط الجيوب", False,
         "Very common in space: fluids shift toward the head.", "شائع جدًا في الفضاء: السوائل بتتجه للرأس.",
         ["Drink water; rest with the head up if gravity allows.", "Measure temperature."],
         ["اشرب ماء، واسترح ورأسك مرفوع لو الجاذبية تسمح.", "قِس الحرارة."],
         "Call if you have fever or face pain for more than 3 days.", "تواصل لو عندك حرارة أو ألم في الوجه أكتر من 3 أيام.", "gravity"),
    ],
    "metabolism": [
        ("nausea", "Nausea or motion sickness", "غثيان أو دوار الحركة", False,
         "Space motion sickness is common in the first days and after gravity changes.",
         "دوار الفضاء شائع في الأيام الأولى وبعد تغيّر الجاذبية.",
         ["Keep the head still and look at a fixed point.", "Small sips of water; eat light."],
         ["ثبّت رأسك وبص على نقطة ثابتة.", "رشفات ماء صغيرة وأكل خفيف."],
         "Call if you vomit many times or cannot keep water down.", "تواصل لو رجّعت كتير أو مش قادر تشرب ماء.", "gravity"),
        ("shaky", "Shaky, sweaty or very hungry", "رعشة أو عرق أو جوع شديد", False,
         "Can be low blood sugar.", "ممكن يكون سكر منخفض.",
         ["Measure blood sugar now.", "If below 70 mg/dL: eat a fast-sugar snack and re-check in 15 minutes."],
         ["قِس السكر الآن.", "لو أقل من 70: كُل حاجة سريعة السكر وأعد القياس بعد 15 دقيقة."],
         "Call if below 54 mg/dL or you feel confused.", "تواصل لو أقل من 54 أو حاسس بتشوش.", "distance"),
        ("thirst", "Very thirsty or dark urine", "عطش شديد أو بول غامق", False,
         "Dehydration is common in space and raises the risk of kidney stones (NASA HRP, gravity fields).",
         "الجفاف شائع في الفضاء ويزوّد خطر حصوات الكلى (NASA HRP، الجاذبية).",
         ["Drink water now and follow the daily water plan.", "Measure blood sugar."],
         ["اشرب ماء الآن والتزم بخطة الماء اليومية.", "قِس السكر."],
         "Call if you have side or back pain, or blood in the urine.", "تواصل لو عندك ألم في الجنب أو الظهر أو دم في البول.", "gravity"),
    ],
    "immune": [
        ("fever", "Fever or chills", "حرارة أو قشعريرة", False,
         "Germs pass easily between crew in a closed habitat, and the immune system can change in space.",
         "الجراثيم بتنتقل بسهولة في المسكن المغلق، والمناعة ممكن تتغير في الفضاء.",
         ["Measure temperature with the thermometer.", "Rest, drink fluids and keep distance from the crew."],
         ["قِس الحرارة بالترمومتر.", "استرح واشرب سوائل وابتعد عن الطاقم."],
         "Call if 38.0 °C or more, or with breathing difficulty or a stiff neck.",
         "تواصل لو 38 درجة أو أكتر، أو مع صعوبة تنفس أو تيبس في الرقبة.", "closed"),
        ("sore throat", "Sore throat", "التهاب الحلق", False,
         "Often a minor infection passed between crew.", "غالبًا عدوى بسيطة بين الطاقم.",
         ["Measure temperature.", "Drink warm water; clean shared surfaces."],
         ["قِس الحرارة.", "اشرب ماء دافئ، ونظّف الأسطح المشتركة."],
         "Call if you have fever or trouble swallowing.", "تواصل لو عندك حرارة أو صعوبة في البلع.", "closed"),
        ("skin", "Rash, itch or a wound that is slow to heal", "طفح أو حكة أو جرح بطيء الالتئام", False,
         "Skin and wound healing can change in space; microbes behave differently in closed habitats.",
         "الجلد والتئام الجروح ممكن يتغيروا في الفضاء، والميكروبات بتتصرف بشكل مختلف في الأماكن المغلقة.",
         ["Take a photo with the laptop camera to compare tomorrow.", "Keep it clean and dry."],
         ["صوّرها بكاميرا اللابتوب عشان تقارن بكرة.", "خلّيها نظيفة وناشفة."],
         "Call if it spreads, is hot or red, or you have fever.", "تواصل لو بتنتشر أو سخنة أو حمرا، أو عندك حرارة.", "closed"),
    ],
    "bones": [
        ("back pain", "Back pain", "ألم في الظهر", False,
         "Common in space: the spine lengthens without gravity (NASA HRP, gravity fields).",
         "شائع في الفضاء: العمود الفقري بيطول بدون جاذبية (NASA HRP، الجاذبية).",
         ["Gentle stretching; curl into a ball position for a few minutes.", "Keep the daily exercise, lighter today."],
         ["إطالة خفيفة، واتكوّر كام دقيقة.", "حافظ على التمرين اليومي بس أخف النهارده."],
         "Call if you have numbness, weakness in a leg, or the pain is severe.",
         "تواصل لو عندك تنميل أو ضعف في رجل أو الألم شديد.", "gravity"),
        ("muscle pain", "Muscle or joint pain", "ألم في العضلات أو المفاصل", False,
         "Bones and muscles weaken in weightlessness; exercise loads them again.",
         "العظام والعضلات بتضعف في انعدام الجاذبية، والتمرين بيرجّع الحمل عليها.",
         ["Rest the sore area; keep the rest of the exercise plan.", "Note what movement started it."],
         ["ريّح المكان اللي بيوجع، وكمّل باقي خطة التمرين.", "سجّل الحركة اللي بدأته."],
         "Call if there is swelling, you cannot move it, or after a fall or impact.",
         "تواصل لو فيه تورم أو مش قادر تحركه، أو بعد وقعة أو خبطة.", "gravity"),
        ("injury", "Injury, fall or impact", "إصابة أو وقعة أو خبطة", False,
         "Bones lose 1-1.5% of mineral density per month in space, so an injury needs checking.",
         "العظام بتفقد 1–1.5% من كثافتها كل شهر في الفضاء، فالإصابة لازم تتفحص.",
         ["Stop and do not load the injured part.", "Take a photo with the laptop camera."],
         ["وقّف ومتحمّلش على المكان المصاب.", "صوّره بكاميرا اللابتوب."],
         "Call the flight surgeon today; now if it is deformed, very painful, or you hit your head.",
         "تواصل مع طبيب الرحلة النهارده، والآن لو فيه تشوه أو ألم شديد أو خبطت راسك.", "gravity"),
    ],
}

SYSTEM_SYMPTOMS = {sys: [s[0] for s in items] for sys, items in _S.items()}
_BY_ID = {s[0]: (sys, s) for sys, items in _S.items() for s in items}


def catalogue(lang="en"):
    """The symptoms offered for each body system (for the clickable figure)."""
    i = 1 if lang == "en" else 2
    return {sys: [{"id": s[0], "name": s[i], "act": s[3]} for s in items] for sys, items in _S.items()}


def assess(symptoms, lang="en"):
    """symptoms: [{"id": ..., "severity": "mild" | "strong"}]. Returns the status and one card per symptom."""
    en = lang != "ar"
    cards = []
    for item in symptoms:
        sid = item["id"] if isinstance(item, dict) else item
        severity = (item.get("severity") if isinstance(item, dict) else None) or "mild"
        if sid not in _BY_ID:
            raise ValueError(f"Unknown symptom: {sid}")
        system, s = _BY_ID[sid]
        act = s[3] or (severity == "strong" and sid in ("headache", "palpitations", "fever", "injury"))
        level = "ACT" if act else "WATCH"
        cards.append({"id": sid, "system": system, "name": s[1 if en else 2], "level": level,
                      "means": s[4 if en else 5], "do_now": s[6 if en else 7],
                      "call_if": s[8 if en else 9], "source": SRC[s[10]],
                      "medicine": MEDICINE_NOTE if en else MEDICINE_NOTE_AR})
    cards.sort(key=lambda c: c["level"] != "ACT")
    state = "ACT" if any(c["level"] == "ACT" for c in cards) else ("WATCH" if cards else "NORMAL")
    if not symptoms:
        note = "Nothing ticked: no symptom to assess." if en else "لم تختر أي عَرَض."
    elif state == "ACT":
        note = ("ACT now: follow the emergency procedure and contact the flight surgeon."
                if en else "تصرّف الآن: اتبع إجراء الطوارئ وتواصل مع طبيب الرحلة.")
    else:
        note = ("WATCH: follow the steps below, add it to today's check-in, and check again in a few hours."
                if en else "مراقبة: اتبع الخطوات، وسجّلها في التسجيل اليومي، وراجعها بعد كام ساعة.")
    severe = [c["id"] for c in cards if c["level"] == "ACT"]
    return {"state": state, "note": note, "cards": cards, "severe_for_checkin": severe}
