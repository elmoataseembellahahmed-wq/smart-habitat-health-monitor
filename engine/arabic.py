"""Arabic version of the daily report.

Built from the same computed results as the English report (flags, rule codes,
patterns, actions), never by translating free text, so both say exactly the same thing.
"""

from .signals import SIGNALS, CABIN_SIGNALS
from .fusion import action_type

TYPE_AR = {"escalate": "تصعيد", "equipment": "أجهزة", "confirm": "تأكيد أولًا",
           "self-care": "عناية ذاتية", "none": "-"}
CONF_AR = {"full": "كاملة", "limited": "محدودة", "low": "منخفضة"}
DEVICE_AR = {"wristband": "السوار", "chest": "حزام الصدر", "bp": "حساس ضغط الدم",
             "glucose": "لاصقة السكر", "camera": "الكاميرا", "voice": "اليوميات"}
FAULT_AR = {"missing": "لم تصل قراءة اليوم (الحساس مفصول أو غير ملبوس)",
            "out_of_range": "القراءة غير ممكنة جسديًا، فاعتُبرت خطأ في الحساس",
            "stuck": "نفس القيمة بالضبط لعدة أيام متتالية: الحساس متجمّد أو منتهي الصلاحية"}
DEVICE_ACTION_AR = {"wristband": "افحص السوار: هل هو ملبوس جيدًا ومشحون ومتصل؟",
                    "chest": "افحص تثبيت حزام الصدر وبطاريته.",
                    "bp": "افحص حساس ضغط الدم وخذ قراءة بجهاز الكُمّ للتأكد.",
                    "glucose": "افحص لاصقة السكر واستبدلها إن انتهت صلاحيتها.",
                    "camera": "افحص كاميرا المقصورة."}

STATE_AR = {"NORMAL": "طبيعي", "WATCH": "مراقبة", "ACT": "تدخّل فوري"}
LEVEL_AR = {"mild": "خفيف", "strong": "قوي", "critical": "حرج"}
AI_LEVEL_AR = {"normal": "طبيعي", "unusual": "غير معتاد", "strong": "غير معتاد بشدة"}
ROLE_AR = {"Commander": "قائدة المهمة", "Flight engineer": "مهندس الطيران",
           "Mission specialist": "أخصائي المهمة"}
NAME_AR = {"Amira": "أميرة", "Ben": "بن", "Chen": "تشين"}

SIGNAL_AR = {
    "heart_rate": ("معدل نبض القلب أثناء الراحة", "نبضة في الدقيقة"),
    "hrv": ("تقلّب نبض القلب (HRV)", "مللي ثانية"),
    "spo2": ("نسبة الأكسجين في الدم", "%"),
    "sleep_hours": ("مدة النوم", "ساعة"),
    "fatigue_score": ("درجة إرهاق الوجه", "من 100"),
    "blink_rate": ("معدل الرمش", "رمشة في الدقيقة"),
    "mood_score": ("درجة المزاج (تقرير ذاتي اختياري)", "من 100"),
    "stress_words": ("كلمات الضغط في اليوميات", "كلمة في اليوم"),
    "body_temp": ("حرارة جلد المعصم (تقدير لحرارة الجسم)", "°م"),
    "breathing_rate": ("معدل التنفس", "نَفَس في الدقيقة"),
    "bp_systolic": ("ضغط الدم الانقباضي", "ملم زئبق"),
    "bp_diastolic": ("ضغط الدم الانبساطي", "ملم زئبق"),
    "glucose": ("سكر الدم (متوسط اليوم)", "ملغ/دسل"),
}
CABIN_AR = {"co2": ("ثاني أكسيد الكربون في المقصورة", "ملم زئبق"),
            "radiation": ("جرعة الإشعاع", "ملّي سيفرت في اليوم")}

PATTERN_AR = {
    "stress_fatigue": ("ضغط جسدي ونفسي معًا",
                       "إشارات الجسم (القلب) والإشارات النفسية (المزاج والإرهاق) خارج المعتاد معًا، مع نوم سيئ."),
    "sleep_debt": ("تراكم نقص النوم", "النوم أقصر من المعتاد لعدة ليالٍ."),
    "mental_strain": ("إجهاد نفسي", "المزاج منخفض وكلمات الضغط في اليوميات مرتفعة."),
    "low_oxygen": ("انخفاض الأكسجين في الدم",
                   "الأكسجين في الدم أقل من المعتاد لهذا الرائد أو أقل من حد الأمان."),
    "high_bp": ("ارتفاع ضغط الدم",
                "ضغط الدم أعلى من المعتاد لهذا الرائد منذ يومين أو أكثر، أو فوق حد الأمان."),
    "glucose": ("سكر الدم خارج المعدل", "متوسط سكر الدم خارج المعدل الطبيعي لهذا الرائد."),
    "fever": ("احتمال حمّى", "حرارة الجسم أعلى من المعتاد بوضوح، وقد تكون أول علامة على عدوى."),
    "cabin_air": ("جودة هواء المقصورة",
                  "ثاني أكسيد الكربون في المقصورة فوق الحد. هذا يؤثر على الطاقم كله وقد يسبب صداعًا وإرهاقًا."),
}

ACTION_AR = {
    "Reduce workload for the next 48 hours and reschedule non-critical tasks.":
        "خفّف عبء العمل خلال الـ 48 ساعة القادمة وأجّل المهام غير الحرجة.",
    "Protect an 8-hour sleep window tonight.": "خصّص 8 ساعات كاملة للنوم الليلة.",
    "Book a private conversation with the flight psychologist at the next contact window.":
        "احجز محادثة خاصة مع الطبيب النفسي للرحلة في نافذة الاتصال القادمة.",
    "Shift the sleep schedule back to the usual time and limit screen light before bed.":
        "أعد موعد النوم إلى وقته المعتاد وقلّل ضوء الشاشات قبل النوم.",
    "Avoid scheduling demanding tasks at the start of the next shift.":
        "تجنّب جدولة مهام صعبة في بداية الوردية القادمة.",
    "Schedule personal time and a call or recorded message from family.":
        "خصّص وقتًا شخصيًا ومكالمة أو رسالة مسجلة من العائلة.",
    "Check in with the crew member in a short private conversation.":
        "تحدّث مع فرد الطاقم في محادثة خاصة قصيرة.",
    "Re-measure blood oxygen and check the sensor fit.":
        "أعد قياس الأكسجين في الدم وتأكد من تثبيت الحساس جيدًا.",
    "Re-measure blood oxygen now and check the sensor fit.":
        "أعد قياس الأكسجين في الدم الآن وتأكد من تثبيت المستشعر.",
    "Check cabin air (CO2 and O2) and notify the flight surgeon.":
        "افحص هواء المقصورة (ثاني أكسيد الكربون والأكسجين) وأبلغ طبيب الرحلة.",
    "Inspect and service the CO2 scrubber.": "افحص جهاز إزالة ثاني أكسيد الكربون وأصلحه.",
    "Treat crew fatigue and headache today as possibly caused by CO2, not only by stress.":
        "تعامل مع إرهاق الطاقم والصداع اليوم على أنه قد يكون بسبب ثاني أكسيد الكربون، وليس الضغط فقط.",
    "Re-check resting heart rate after 10 minutes of rest; hydrate.":
        "أعد قياس النبض بعد 10 دقائق من الراحة، واشرب الماء.",
    "Plan a lighter exercise session and extra recovery time.":
        "خطّط لتمرين أخف ووقت إضافي للتعافي.",
    "Protect tonight's sleep window.": "احمِ وقت النوم الليلة.",
    "Take a short break before the next demanding task.": "خذ استراحة قصيرة قبل المهمة الصعبة القادمة.",
    "Take a screen break and rest the eyes.": "ابتعد عن الشاشة قليلًا وأرح عينيك.",
    "Make time for a short check-in conversation.": "خصّص وقتًا لمحادثة قصيرة للاطمئنان.",
    "Notify the flight surgeon with this report at the next contact window.":
        "أرسل هذا التقرير إلى طبيب الرحلة في نافذة الاتصال القادمة.",
    "No action needed. Keep the normal schedule.": "لا حاجة لأي إجراء. استمر في الجدول المعتاد.",
    "Re-check blood pressure with the cuff to confirm the sensor reading.":
        "أعد قياس ضغط الدم بجهاز الكُمّ للتأكد من قراءة المستشعر.",
    "Cut salt and caffeine today and add a rest break.":
        "قلّل الملح والكافيين اليوم وأضف استراحة.",
    "Confirm with a finger-prick glucose check.": "تأكّد بقياس السكر من وخزة الإصبع.",
    "Review today's meals and snacks against the mission nutrition plan.":
        "راجع وجبات اليوم والوجبات الخفيفة مقارنة بخطة التغذية للمهمة.",
    "Confirm with a core (oral or ear) temperature check.":
        "تأكّد بقياس الحرارة من الفم أو الأذن.",
    "Rest, drink fluids and limit close contact with the crew until checked.":
        "استرح واشرب السوائل وقلّل الاحتكاك القريب بالطاقم حتى يتم التأكد.",
    "Re-check temperature later today.": "أعد قياس الحرارة لاحقًا اليوم.",
    "Rest for 10 minutes and re-check breathing rate; check cabin CO2.":
        "استرح 10 دقائق ثم أعد قياس معدل التنفس، وافحص ثاني أكسيد الكربون في المقصورة.",
    "Check that you are wearing your own wristband (the ID is on the band), then swap back if needed.":
        "تأكّد أنك تلبس سوارك أنت (الرقم التعريفي مكتوب على السوار)، وبدّله إن لزم.",
    "Flight surgeon: review the slow change in this astronaut's normal since the start of the mission "
    "(it is too gradual to show on any single day).":
        "طبيب الرحلة: راجع التغيّر البطيء في المعدل الطبيعي لهذا الرائد منذ بداية المهمة "
        "(تغيّر تدريجي جدًا لا يظهر في أي يوم منفرد).",
}

AI_NOTE_AR = {
    ("agree", True): "نموذج الذكاء الاصطناعي والقواعد متفقان: هذا اليوم غير معتاد لهذا الرائد.",
    ("agree", False): "نموذج الذكاء الاصطناعي والقواعد متفقان: هذا اليوم يبدو طبيعيًا.",
    ("ai_only", True): "النموذج يرى هذا اليوم غير معتاد رغم أن أي إشارة لم تتجاوز قاعدة. يستحق نظرة أقرب: "
                       "قد يكون مزيجًا غير معتاد من تغيّرات صغيرة.",
    ("rules_only", False): "القواعد رصدت إشارة، لكن النموذج يرى اليوم ككل قريبًا من الطبيعي. "
                           "غالبًا تغيّر صغير ومنفرد.",
}


def _fmt(value, decimals):
    return f"{value:.{decimals}f}" if decimals else f"{round(value)}"


def reason_ar(f):
    name, unit = SIGNAL_AR[f["signal"]]
    if f.get("private"):
        return f"{name}: إشارة تقرير ذاتي خاصة خارج المعتاد لهذا الرائد (التفاصيل لطبيب الرحلة فقط)."

    prefix = ""
    if f.get("source") == "wristband":
        name = "تقدير الإرهاق من السوار"
        prefix = (f"لم ترَ الكاميرات هذا الرائد إلا {f.get('camera_minutes', 0)} دقيقة اليوم، "
                  "لذلك قُدّر الإرهاق من السوار (النوم وتباين نبضات القلب والنبض). ")
    d = SIGNALS[f["signal"]]["decimals"]
    base = f["baseline"]
    pct = abs(f["value"] - base) / base * 100 if base else 0
    direction = "أعلى" if f["value"] > base else "أقل"
    text = prefix + (f"{name} = {_fmt(f['value'], d)} {unit}، أي {direction} بنسبة {pct:.0f}% "
            f"من المعتاد لهذا الرائد ({_fmt(base, d)} {unit})")
    if f["streak_days"] >= 2:
        text += f" لمدة {f['streak_days']} أيام متتالية"
    if f.get("limit"):
        side = "تحت" if f["limit"][0] == "below" else "فوق"
        text += f"، و{side} حد الأمان ({f['limit'][1]:g} {unit})"
        if SIGNALS[f["signal"]].get("confirm_first"):
            text += " (قيمة تقديرية: تأكّد بقياس الحرارة من الفم أو الأذن قبل أي إجراء)"
    return text + "."


def rule_ar(c):
    r = c["rule"]
    if r == "safety_limit":
        return "إشارة تحت حد الأمان المطلق."
    if r == "act_score":
        return (f"مجموع الانحراف {c['score']} وصل إلى مستوى التدخّل ({c['limit']})، "
                f"وعدد الإشارات الخارجة عن المعتاد منذ يومين أو أكثر: {c['persistent']}.")
    if r == "stress_3_days":
        return "الضغط الجسدي والنفسي معًا مستمر منذ 3 أيام أو أكثر."
    if r == "cabin_act":
        return "ثاني أكسيد الكربون في المقصورة فوق حد التدخّل."
    if r == "one_day_high":
        return (f"مجموع الانحراف {c['score']} مرتفع، لكنه تغيّر ليوم واحد: مراقبة، "
                "ويصبح تدخّلًا إذا استمر غدًا.")
    if r == "watch_score":
        return f"مجموع الانحراف {c['score']} وصل إلى مستوى المراقبة ({c['limit']})."
    if r == "drift":
        return ("تدهور بطيء: المعدل الطبيعي لهذا الرائد ابتعد كثيرًا عن بداية المهمة في: "
                + "، ".join(SIGNAL_AR[s][0] for s in c["signals"]) + ".")
    if r == "pattern":
        return "تم رصد نمط خطر معروف: " + "، ".join(PATTERN_AR[p][0] for p in c["patterns"]) + "."
    return r


def cabin_reason_ar(c):
    name, unit = CABIN_AR[c["signal"]]
    meta = CABIN_SIGNALS[c["signal"]]
    level_word = "التدخّل" if c["level"] == "act" else "المراقبة"
    return f"{name} = {_fmt(c['value'], meta['decimals'])} {unit}، فوق حد {level_word} ({meta[c['level']]} {unit})."


def build_report_ar(member, day, decision, trend, cabin):
    name = NAME_AR.get(member["name"], member["name"])
    role = ROLE_AR.get(member["role"], member["role"])
    L = []
    L.append(f"التقرير الصحي اليومي  -  اليوم {day} من المهمة")
    L.append(f"فرد الطاقم: {name} ({role})")
    L.append(f"الحالة: [{STATE_AR[decision['state']]}]  (مجموع الانحراف {decision['score']})")
    cov = decision.get("coverage")
    if cov:
        missing = "، ".join(SIGNAL_AR[k][0] for k in cov["unavailable"])
        line = f"اكتمال البيانات: {CONF_AR[cov['confidence']]} - الحالة مبنية على {cov['measured']} من {cov['total']} إشارة"
        if cov["estimated"]:
            line += f" ({len(cov['estimated'])} منها تقديرية)"
        if missing:
            line += f". غير متاح اليوم: {missing}"
        if cov["safety_gap"]:
            line += ". إشارة لها حد أمان غير متاحة، فكلمة «طبيعي» لا تستبعد مشكلة فيها"
        L.append(line + ".")
    L.append("")
    L.append(f"الاتجاه في آخر {len(trend)} أيام: "
             + "  ←  ".join(f"اليوم {t['day']}: {STATE_AR[t['state']]}" for t in trend))
    L.append("")

    if decision["state"] == "NORMAL" and not decision["flags"]:
        L.append("كل الإشارات المراقَبة ضمن المعدل الطبيعي لهذا الرائد.")
    else:
        if decision["patterns"]:
            L.append("ماذا يحدث:")
            for p in decision["patterns"]:
                title, explain = PATTERN_AR[p["id"]]
                L.append(f"  - {title}: {explain}")
            L.append("")
        if decision["flags"]:
            L.append("لماذا (إشارات خارج المعدل الشخصي):")
            for f in decision["flags"]:
                L.append(f"  - [{LEVEL_AR[f['level']]}] {reason_ar(f)}")
            L.append("")
        if decision.get("rule_codes"):
            L.append("القواعد التي انطبقت:")
            for c in decision["rule_codes"]:
                L.append(f"  - {rule_ar(c)}")
            L.append("")

    faults = decision.get("sensor_faults") or []
    if faults or decision.get("self_report_skipped"):
        L.append("فحص الحساسات (أجهزة، وليست صحة):")
        for f in faults:
            for k, code in zip(f["signals"], f["codes"]):
                L.append(f"  - {DEVICE_AR.get(f['device'], f['device'])} ({SIGNAL_AR[k][0]}): {FAULT_AR[code]}.")
            L.append(f"    ← {DEVICE_ACTION_AR.get(f['device'], 'افحص الحساس.')}")
        if decision.get("self_report_skipped"):
            L.append("  - لم تُكتب اليوميات اليوم (وهي اختيارية)، فلم يُقيَّم المزاج. لا مشكلة في ذلك.")
        L.append("")

    band = decision.get("band_check")
    if band:
        other = NAME_AR.get(band["with_name"], band["with_name"])
        L.append("فحص السوار:")
        L.append(f"  - قراءات السوار اليوم تطابق المعدل الطبيعي لـ{other}، وسوار {other} يطابق هذا الرائد. "
                 "الأرجح أن السوارين تبادلا. لا يُطلق إنذار صحي بسببهما: تم تجاهل قراءات السوار لهذا اليوم.")
        L.append("")
    if decision.get("drift"):
        L.append("تغيّر بطيء منذ بداية المهمة (لطبيب الرحلة):")
        for x in decision["drift"]:
            name, unit = SIGNAL_AR[x["signal"]]
            d = SIGNALS[x["signal"]]["decimals"]
            L.append(f"  - {name}: المعدل الطبيعي لهذا الرائد تحرّك ببطء من {_fmt(x['anchor'], d)} "
                     f"إلى {_fmt(x['now'], d)} {unit} منذ بداية المهمة ({x['shift']:.1f} انحراف معياري).")
        L.append("")

    ai = decision.get("ai")
    if ai:
        L.append(f"فحص الذكاء الاصطناعي (Isolation Forest): الدرجة {ai['score']:.2f} "
                 f"(غير معتاد فوق {ai['threshold']:.2f}) ← {AI_LEVEL_AR[ai['level']]}")
        note = AI_NOTE_AR.get((ai["agreement"], ai["level"] != "normal"), ai.get("note", ""))
        L.append(f"  {note}")
        L.append("")

    L.append("بيئة المقصورة:")
    for c in cabin:
        if c["level"]:
            L.append(f"  - {cabin_reason_ar(c)}")
        if c["signal"] == "radiation" and "mission_total" in c:
            L.append(f"  - إجمالي جرعة الإشعاع في المهمة حتى الآن {c['mission_total']:.1f} ملّي سيفرت، أي "
                     f"{c['pct_of_career_limit']:.0f}% من حد ناسا المهني (600 ملّي سيفرت) (مقياس جرعة محاكى).")
        if c["signal"] == "co2" and "avg_7d" in c:
            L.append(f"  - متوسط ثاني أكسيد الكربون في آخر 7 أيام {c['avg_7d']:.1f} ملم زئبق"
                     + ("، أعلى من 2.5 الذي يبقي خطر الصداع منخفضًا." if c["avg_7d"] > 2.5 else "."))
    cw = decision.get("crew_wide") or {}
    if cw.get("environmental"):
        L.append("  - على مستوى الطاقم: تغيّر مشترك مع ارتفاع ثاني أكسيد الكربون في: "
                 + "، ".join(SIGNAL_AR[k][0] for k in cw["environmental"]) + ". الأرجح سبب بيئي: أصلح الهواء أولًا.")
    if cw.get("shared_no_cabin_cause"):
        L.append("  - على مستوى الطاقم: تغيّر مشترك بلا سبب في المقصورة: "
                 + "، ".join(SIGNAL_AR[k][0] for k in cw["shared_no_cabin_cause"])
                 + ". يُعامل كمشكلات فردية؛ افحص الأسباب المشتركة (الجدول، العبء، عدوى).")
    for b in cw.get("beyond_cabin", []):
        L.append(f"  - {NAME_AR.get(b['name'], b['name'])}: تغيّرات أكثر مما يفسّره هواء المقصورة، فهي أيضًا نمط صحي فردي.")
    L.append("")

    L.append("الإجراءات المقترحة (قائمة نموذج أولي؛ اتبع الإجراءات المعتمدة للمهمة وطبيب الرحلة):")
    for i, a in enumerate(decision["actions"], 1):
        L.append(f"  {i}. [{TYPE_AR[action_type(a)]}] {ACTION_AR.get(a, a)}")
    L.append("")

    routine = decision.get("routine")
    if routine:
        L.append("المهام الروتينية:")
        for r in routine["reminders"]:
            due = "مطلوب اليوم" if r["due_in_days"] == 0 else f"بعد {r['due_in_days']} يوم"
            L.append(f"  - {r['task_ar']}: {due}")
        L.append(f"  - أيام متتالية في الحالة الطبيعية: {routine['normal_streak']}")
        L.append("")

    v = decision.get("versions")
    if v:
        L.append(f"الإصدارات: البرنامج {v['software']}، {v['rules']}، {v['thresholds']}، {v['model']}، "
                 f"المعدل الطبيعي {v['personal_normal']} (تعلّمه من الأيام {v['learned_from_days'][0]}-"
                 f"{v['learned_from_days'][1]}، {v['learned_from_days'][2]} يومًا).")
    L.append("أُنشئ على متن المركبة من بيانات محاكاة. الحدود نموذج أولي وليست للقرارات الطبية. "
             "للمساعدة في القرار فقط؛ القرارات الطبية يتخذها طبيب الرحلة.")
    return "\n".join(L)
