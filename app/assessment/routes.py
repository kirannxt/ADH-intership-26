from flask import render_template, redirect, url_for, request, session, flash
from flask_login import login_required, current_user

from app.assessment import assessment

# ══════════════════════════════════════════════════════════════════════════
#  REAL ASSESSMENT CATEGORIES
#  Each entry defines:
#    label       – display name
#    icon        – emoji icon
#    color       – card background tint
#    time        – estimated completion time
#    sections    – short section/tag labels for display
#    description – one-sentence summary shown on selection card
#    instructions– paragraph shown before questions begin
#    purpose     – clinical / educational context note
#    questions   – list of dicts, each with:
#                    text   – the question text
#                    type   – "freq4" | "freq5" | "mc" | "yn" | "rate5"
#                    key    – short machine name (e.g. "inattention")
#                    options– list of (label, score) tuples
#    scoring     – dict with bands: list of (min_score, max_score, band, colour, interpretation)
# ══════════════════════════════════════════════════════════════════════════

ASSESSMENT_TYPES = {

    # ── 1. ADHD Screening ─────────────────────────────────────────────────
    "adhd": {
        "label":       "ADHD Screening",
        "icon":        "🎯",
        "color":       "#ede9fe",
        "time":        "~8 min",
        "sections":    ["Inattention", "Hyperactivity", "Impulsivity"],
        "description": "A structured self-report screen for common attention, hyperactivity, and impulsivity traits in adults.",
        "instructions": (
            "The following questions ask about how you have felt and behaved "
            "over the past 6 months. There are no right or wrong answers — "
            "respond as honestly as you can. This is a screening tool only "
            "and cannot diagnose ADHD."
        ),
        "purpose": (
            "Based on the Adult ADHD Self-Report Scale (ASRS) structure. "
            "A positive screen suggests it may be worth discussing with a clinician — "
            "it is not a diagnosis."
        ),
        "questions": [
            {
                "text": "How often do you have trouble wrapping up the final details of a project once the challenging parts have been done?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you have difficulty getting things in order when you have to do a task that requires organisation?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you have problems remembering appointments or obligations?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "When you have a task that requires a lot of thought, how often do you avoid or delay getting started?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you fidget or squirm with your hands or feet when you have to sit down for a long time?",
                "type": "freq5",
                "key":  "hyperactivity",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you feel overly active and compelled to do things, as if driven by a motor?",
                "type": "freq5",
                "key":  "hyperactivity",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you make careless mistakes when you have to work on a boring or difficult project?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you have difficulty keeping your attention when you are doing boring or repetitive work?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you have difficulty concentrating on what people say to you, even when they are speaking to you directly?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "How often do you misplace or have difficulty finding things at home or at work?",
                "type": "freq5",
                "key":  "inattention",
                "options": [
                    ("Never",           0),
                    ("Rarely",          1),
                    ("Sometimes",       2),
                    ("Often",           3),
                    ("Very often",      4),
                ]
            },
        ],
        "scoring": {
            "method": "sum",           # sum all option scores
            "max": 40,
            "bands": [
                (0,  13, "Low",      "success", "Few ADHD-related traits reported. Your responses do not suggest significant attention or hyperactivity difficulties at this time."),
                (14, 23, "Moderate", "warning", "Some ADHD-related traits reported. This does not confirm ADHD but suggests it may be worth discussing these patterns with a GP or specialist."),
                (24, 40, "High",     "danger",  "Several ADHD-related traits reported frequently. A high score on a screening tool like this warrants a conversation with a qualified clinician. This is not a diagnosis."),
            ]
        }
    },

    # ── 2. Anxiety Screening (GAD-7 structure) ────────────────────────────
    "anxiety": {
        "label":       "Anxiety Screening",
        "icon":        "😰",
        "color":       "#dbeafe",
        "time":        "~5 min",
        "sections":    ["Worry", "Nervousness", "Avoidance"],
        "description": "A self-report screen based on the GAD-7 structure for generalised anxiety symptoms over the past two weeks.",
        "instructions": (
            "Over the last two weeks, how often have you been bothered "
            "by the following problems? Choose the response that best "
            "describes your experience. This is a screening tool — "
            "not a clinical diagnosis."
        ),
        "purpose": (
            "Based on the GAD-7 (Generalised Anxiety Disorder 7-item scale) structure, "
            "widely used in primary care. A score of 10+ suggests moderate anxiety "
            "worth discussing with a health professional."
        ),
        "questions": [
            {
                "text": "Feeling nervous, anxious, or on edge.",
                "type": "freq4",
                "key":  "anxiety",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Not being able to stop or control worrying.",
                "type": "freq4",
                "key":  "worry",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Worrying too much about different things.",
                "type": "freq4",
                "key":  "worry",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Trouble relaxing.",
                "type": "freq4",
                "key":  "tension",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Being so restless that it is hard to sit still.",
                "type": "freq4",
                "key":  "tension",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Becoming easily annoyed or irritable.",
                "type": "freq4",
                "key":  "irritability",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Feeling afraid, as if something awful might happen.",
                "type": "freq4",
                "key":  "fear",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Avoiding social situations because of anxiety.",
                "type": "freq4",
                "key":  "avoidance",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Physical symptoms of anxiety (e.g. racing heart, shortness of breath, sweating).",
                "type": "freq4",
                "key":  "physical",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Difficulty concentrating because of worry or anxious thoughts.",
                "type": "freq4",
                "key":  "concentration",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
        ],
        "scoring": {
            "method": "sum",
            "max": 30,
            "bands": [
                (0,   7, "Minimal",  "success", "Few anxiety symptoms reported. Your responses suggest minimal anxiety at this time."),
                (8,  15, "Moderate", "warning",  "Moderate anxiety symptoms reported. Consider speaking with your GP or a mental health professional if this is causing difficulty."),
                (16, 30, "High",     "danger",   "Significant anxiety symptoms reported. This screening tool cannot diagnose an anxiety disorder, but a high score strongly suggests speaking with a qualified clinician."),
            ]
        }
    },

    # ── 3. Depression Screening (PHQ-9 structure) ─────────────────────────
    "depression": {
        "label":       "Depression Screening",
        "icon":        "🌧",
        "color":       "#e0e7ff",
        "time":        "~5 min",
        "sections":    ["Mood", "Energy", "Cognition"],
        "description": "A self-report screen based on the PHQ-9 structure for low mood and depressive symptoms over the past two weeks.",
        "instructions": (
            "Over the last two weeks, how often have you been bothered "
            "by any of the following problems? Answer as honestly as you can. "
            "If you are in crisis, please contact emergency services or a helpline immediately."
        ),
        "purpose": (
            "Based on the PHQ-9 (Patient Health Questionnaire-9), a validated depression "
            "screening tool used in primary care worldwide. A score of 10+ suggests "
            "moderate depression worth discussing with a clinician."
        ),
        "questions": [
            {
                "text": "Little interest or pleasure in doing things.",
                "type": "freq4",
                "key":  "anhedonia",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Feeling down, depressed, or hopeless.",
                "type": "freq4",
                "key":  "mood",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Trouble falling or staying asleep, or sleeping too much.",
                "type": "freq4",
                "key":  "sleep",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Feeling tired or having little energy.",
                "type": "freq4",
                "key":  "energy",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Poor appetite or overeating.",
                "type": "freq4",
                "key":  "appetite",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Feeling bad about yourself — or that you are a failure or have let yourself or your family down.",
                "type": "freq4",
                "key":  "self_worth",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Trouble concentrating on things, such as reading or watching television.",
                "type": "freq4",
                "key":  "concentration",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Moving or speaking so slowly that other people could have noticed — or being so fidgety that you have been moving more than usual.",
                "type": "freq4",
                "key":  "psychomotor",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Thoughts that you would be better off dead, or of hurting yourself.",
                "type": "freq4",
                "key":  "si",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
            {
                "text": "Feeling disconnected or detached from the people and activities around you.",
                "type": "freq4",
                "key":  "detachment",
                "options": [
                    ("Not at all",         0),
                    ("Several days",       1),
                    ("More than half the days", 2),
                    ("Nearly every day",   3),
                ]
            },
        ],
        "scoring": {
            "method": "sum",
            "max": 30,
            "bands": [
                (0,   6, "Minimal",  "success", "Few depressive symptoms reported. Your responses suggest minimal depression at this time."),
                (7,  14, "Moderate", "warning",  "Moderate depressive symptoms reported. If these feelings are affecting your daily life, speaking with a GP or mental health professional is recommended."),
                (15, 30, "High",     "danger",   "Significant depressive symptoms reported. This is a screening tool and cannot diagnose depression, but a high score strongly suggests seeking support from a qualified clinician as soon as possible. If you are in crisis, please contact emergency services."),
            ]
        }
    },

    # ── 4. Perceived Stress Scale (PSS-10 structure) ──────────────────────
    "stress": {
        "label":       "Perceived Stress",
        "icon":        "🧘",
        "color":       "#d1fae5",
        "time":        "~5 min",
        "sections":    ["Control", "Overload", "Coping"],
        "description": "A validated measure of how often you have felt stressed, overloaded, or out of control over the past month.",
        "instructions": (
            "The questions below ask about your feelings and thoughts during "
            "the last month. For each question, choose how often you felt or "
            "thought a certain way. This tool measures perceived stress — "
            "not a medical condition."
        ),
        "purpose": (
            "Based on the PSS-10 (Cohen's Perceived Stress Scale), the most widely "
            "used psychological instrument for measuring stress perception."
        ),
        "questions": [
            {
                "text": "In the last month, how often have you been upset because of something that happened unexpectedly?",
                "type": "freq5",
                "key":  "overload",
                "options": [
                    ("Never",           0),
                    ("Almost never",    1),
                    ("Sometimes",       2),
                    ("Fairly often",    3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "In the last month, how often have you felt that you were unable to control the important things in your life?",
                "type": "freq5",
                "key":  "control",
                "options": [
                    ("Never",           0),
                    ("Almost never",    1),
                    ("Sometimes",       2),
                    ("Fairly often",    3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "In the last month, how often have you felt nervous and stressed?",
                "type": "freq5",
                "key":  "overload",
                "options": [
                    ("Never",           0),
                    ("Almost never",    1),
                    ("Sometimes",       2),
                    ("Fairly often",    3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "In the last month, how often have you felt confident about your ability to handle your personal problems? (Reversed)",
                "type": "freq5",
                "key":  "coping",
                "options": [
                    ("Never",           4),  # reversed scoring
                    ("Almost never",    3),
                    ("Sometimes",       2),
                    ("Fairly often",    1),
                    ("Very often",      0),
                ]
            },
            {
                "text": "In the last month, how often have you felt that things were going your way? (Reversed)",
                "type": "freq5",
                "key":  "coping",
                "options": [
                    ("Never",           4),  # reversed
                    ("Almost never",    3),
                    ("Sometimes",       2),
                    ("Fairly often",    1),
                    ("Very often",      0),
                ]
            },
            {
                "text": "In the last month, how often have you found that you could not cope with all the things that you had to do?",
                "type": "freq5",
                "key":  "overload",
                "options": [
                    ("Never",           0),
                    ("Almost never",    1),
                    ("Sometimes",       2),
                    ("Fairly often",    3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "In the last month, how often have you been able to control irritations in your life? (Reversed)",
                "type": "freq5",
                "key":  "control",
                "options": [
                    ("Never",           4),  # reversed
                    ("Almost never",    3),
                    ("Sometimes",       2),
                    ("Fairly often",    1),
                    ("Very often",      0),
                ]
            },
            {
                "text": "In the last month, how often have you felt that you were on top of things? (Reversed)",
                "type": "freq5",
                "key":  "coping",
                "options": [
                    ("Never",           4),  # reversed
                    ("Almost never",    3),
                    ("Sometimes",       2),
                    ("Fairly often",    1),
                    ("Very often",      0),
                ]
            },
            {
                "text": "In the last month, how often have you been angered because of things that were outside of your control?",
                "type": "freq5",
                "key":  "overload",
                "options": [
                    ("Never",           0),
                    ("Almost never",    1),
                    ("Sometimes",       2),
                    ("Fairly often",    3),
                    ("Very often",      4),
                ]
            },
            {
                "text": "In the last month, how often have you felt difficulties were piling up so high that you could not overcome them?",
                "type": "freq5",
                "key":  "overload",
                "options": [
                    ("Never",           0),
                    ("Almost never",    1),
                    ("Sometimes",       2),
                    ("Fairly often",    3),
                    ("Very often",      4),
                ]
            },
        ],
        "scoring": {
            "method": "sum",
            "max": 40,
            "bands": [
                (0,  13, "Low",      "success", "Low perceived stress. Your responses suggest you are managing pressure well at this time."),
                (14, 26, "Moderate", "warning",  "Moderate perceived stress. This is common, but if sustained it can affect wellbeing. Consider stress-reduction strategies or speaking with someone."),
                (27, 40, "High",     "danger",   "High perceived stress. Your responses suggest significant stress. This is not a diagnosis, but it may be worth discussing with a GP or counsellor, particularly if this has persisted for some time."),
            ]
        }
    },

    # ── 5. Learning Style Inventory (VARK-inspired) ───────────────────────
    "learning": {
        "label":       "Learning Style",
        "icon":        "📚",
        "color":       "#fef3c7",
        "time":        "~6 min",
        "sections":    ["Visual", "Auditory", "Reading/Writing", "Kinaesthetic"],
        "description": "Explore how you prefer to take in and process new information using the VARK framework.",
        "instructions": (
            "For each question, select the option that best describes "
            "how you prefer to learn or process new information. "
            "There are no right or wrong answers — this reflects your "
            "preferred style, not your ability."
        ),
        "purpose": (
            "Based on the VARK model (Visual, Auditory, Read/Write, Kinaesthetic). "
            "Learning styles are preferences — not fixed traits. "
            "Awareness of your style can help you choose study strategies that suit you."
        ),
        "questions": [
            {
                "text": "When learning how to use a new piece of software, you prefer to:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Watch a video tutorial",                    "visual"),
                    ("Have someone explain it to you verbally",   "auditory"),
                    ("Read the manual or written instructions",   "read_write"),
                    ("Try it yourself and learn by doing",        "kinaesthetic"),
                ]
            },
            {
                "text": "When trying to remember a phone number, you are most likely to:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Picture where you saw it written",          "visual"),
                    ("Say it out loud or repeat it to yourself",  "auditory"),
                    ("Write it down",                             "read_write"),
                    ("Dial it repeatedly to remember the pattern","kinaesthetic"),
                ]
            },
            {
                "text": "When you have to give someone directions, you tend to:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Draw a map or show them on a map app",      "visual"),
                    ("Tell them verbally, step by step",          "auditory"),
                    ("Write down the steps for them",             "read_write"),
                    ("Walk or drive the route with them",         "kinaesthetic"),
                ]
            },
            {
                "text": "You find it easiest to understand new concepts when:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("They are shown through diagrams or charts",         "visual"),
                    ("Someone talks through them with examples",          "auditory"),
                    ("You can read about them in depth",                  "read_write"),
                    ("You can apply them to a real situation or problem", "kinaesthetic"),
                ]
            },
            {
                "text": "After attending a lecture or presentation, you are most likely to remember:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Visual aids, slides, or the layout of the room",    "visual"),
                    ("What was said and the tone of the speaker",         "auditory"),
                    ("Notes you wrote or handouts provided",              "read_write"),
                    ("Activities, demonstrations, or examples used",      "kinaesthetic"),
                ]
            },
            {
                "text": "When revising for an exam or preparing for a task, you prefer to:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Use mind maps, colour-coded notes, or diagrams",    "visual"),
                    ("Read notes aloud or discuss with others",           "auditory"),
                    ("Rewrite notes or create detailed summaries",        "read_write"),
                    ("Practise past papers or simulate the task",         "kinaesthetic"),
                ]
            },
            {
                "text": "You are most likely to follow a recipe by:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Looking at pictures of the finished dish",          "visual"),
                    ("Watching a cooking video",                          "auditory"),
                    ("Reading the written instructions carefully",        "read_write"),
                    ("Experimenting with the ingredients as you go",      "kinaesthetic"),
                ]
            },
            {
                "text": "In meetings or classes, you find it most helpful when:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Visual aids and whiteboard diagrams are used",      "visual"),
                    ("There is open discussion and verbal explanation",   "auditory"),
                    ("An agenda or written summary is provided",          "read_write"),
                    ("There are activities, case studies, or exercises",  "kinaesthetic"),
                ]
            },
            {
                "text": "If you are trying to learn a new language, you would most likely:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("Use visual flashcards with images",                 "visual"),
                    ("Listen to audio lessons and repeat phrases",        "auditory"),
                    ("Study grammar books and write vocabulary lists",    "read_write"),
                    ("Travel there or practise in real conversations",    "kinaesthetic"),
                ]
            },
            {
                "text": "You tend to remember information best when:",
                "type": "mc",
                "key":  "vark",
                "options": [
                    ("It is presented visually with colours or layouts",  "visual"),
                    ("You have heard it explained out loud",              "auditory"),
                    ("You have read or written it yourself",              "read_write"),
                    ("You have physically done or practised it",          "kinaesthetic"),
                ]
            },
        ],
        "scoring": {
            "method": "vark",   # special: count category occurrences
            "max": 10,
            "bands": [
                # For VARK, band is determined by dominant style
                # These are fallback bands by total; actual label is computed in route
                (0, 3,  "Multimodal",        "primary", "You show a balanced or mixed learning preference, drawing on multiple styles depending on the context."),
                (4, 6,  "Moderate Preference","primary", "You show a moderate preference for one or two learning styles."),
                (7, 10, "Strong Preference",  "primary", "You show a strong preference for a particular learning style."),
            ]
        }
    },

    # ── 6. Emotional Intelligence (EQ) ────────────────────────────────────
    "eq": {
        "label":       "Emotional Intelligence",
        "icon":        "❤️",
        "color":       "#fee2e2",
        "time":        "~7 min",
        "sections":    ["Self-Awareness", "Empathy", "Regulation", "Social Skills"],
        "description": "Assess how you recognise, understand, and manage emotions in yourself and in your interactions with others.",
        "instructions": (
            "Rate how often each statement describes you, based on your "
            "typical behaviour and feelings. Be honest — this is for "
            "your own self-reflection, not a test of social desirability."
        ),
        "purpose": (
            "Based on established EI frameworks (Mayer–Salovey–Caruso, Goleman). "
            "Emotional intelligence is a learnable set of skills, not a fixed trait."
        ),
        "questions": [
            {
                "text": "I can usually identify the specific emotion I am feeling rather than just feeling 'bad' or 'good'.",
                "type": "rate5",
                "key":  "self_awareness",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "When I am upset, I can calm myself down without it taking over my day.",
                "type": "rate5",
                "key":  "regulation",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "I notice when someone is upset or uncomfortable, even if they do not say so.",
                "type": "rate5",
                "key":  "empathy",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "I am able to adapt my communication style depending on who I am talking to.",
                "type": "rate5",
                "key":  "social",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "I understand how my mood can affect how I behave towards others.",
                "type": "rate5",
                "key":  "self_awareness",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "When I make a mistake, I can acknowledge it without dwelling on it excessively.",
                "type": "rate5",
                "key":  "regulation",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "I can put myself in someone else's position and genuinely understand their perspective.",
                "type": "rate5",
                "key":  "empathy",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "I handle disagreements or conflict without becoming aggressive or shutting down.",
                "type": "rate5",
                "key":  "social",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "I am aware of my own emotional triggers and what tends to set me off.",
                "type": "rate5",
                "key":  "self_awareness",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
            {
                "text": "People tend to feel comfortable opening up to me about their feelings.",
                "type": "rate5",
                "key":  "social",
                "options": [
                    ("Almost never",    1),
                    ("Rarely",          2),
                    ("Sometimes",       3),
                    ("Often",           4),
                    ("Almost always",   5),
                ]
            },
        ],
        "scoring": {
            "method": "sum",
            "max": 50,
            "bands": [
                (0,  24, "Developing", "warning", "Your responses suggest EI skills that may benefit from further development. Emotional intelligence is highly learnable — awareness is already the first step."),
                (25, 37, "Moderate",   "primary",  "Moderate emotional intelligence. You show reasonable self-awareness and empathy, with some areas for growth."),
                (38, 50, "Strong",     "success",  "Strong emotional intelligence reported. Your responses suggest good self-awareness, empathy, and interpersonal effectiveness."),
            ]
        }
    },

    # ── 7. ASD Assessment-Support System ─────────────────────────────────
    "asd": {
        "label":       "ASD Assessment-Support",
        "icon":        "🧩",
        "color":       "#ecfdf5",
        "time":        "~15 min",
        "sections":    ["Social Communication", "Social Interaction",
                        "Repetitive Patterns", "Focused Interests", "Sensory Experiences"],
        "description": (
            "A structured observation-based support screen across five core "
            "ASD-related behavioural areas. Suitable for parents, caregivers, "
            "teachers, or self-reporting adults."
        ),
        "instructions": (
            "The following questions ask about behaviours and traits observed "
            "over the past year. For each item, choose the option that most "
            "accurately reflects typical behaviour — not an occasional or "
            "unusual occurrence. Answer as honestly as possible. "
            "This is a support screen only and cannot diagnose autism."
        ),
        "purpose": (
            "Inspired by established ASD behavioural screening frameworks "
            "(including elements of the Social Communication Questionnaire, "
            "SRS-2 and the DSM-5 criteria). A positive screen indicates it "
            "may be worth seeking a professional evaluation — it is not a "
            "diagnosis and does not confirm the presence of autism."
        ),
        "questions": [

            # ── DOMAIN 1: Social Communication (Q1–Q4) ───────────────────
            {
                "text": "How often does this person have difficulty starting or maintaining a two-way conversation?",
                "type": "freq5",
                "key":  "social_comm",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person take things said to them too literally, missing sarcasm, jokes, or implied meaning?",
                "type": "freq5",
                "key":  "social_comm",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person have difficulty adjusting their communication style depending on the listener (e.g. speaking to a child vs. an adult)?",
                "type": "freq5",
                "key":  "social_comm",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person use unusual or overly formal language that seems out of place for the social situation?",
                "type": "freq5",
                "key":  "social_comm",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },

            # ── DOMAIN 2: Social Interaction (Q5–Q8) ─────────────────────
            {
                "text": "How often does this person seem unaware of, or uninterested in, what others are thinking or feeling?",
                "type": "freq5",
                "key":  "social_interact",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person have difficulty making or keeping friends of a similar age?",
                "type": "freq5",
                "key":  "social_interact",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person avoid or show discomfort with eye contact?",
                "type": "freq5",
                "key":  "social_interact",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person appear to prefer being alone rather than spending time with peers or family?",
                "type": "freq5",
                "key":  "social_interact",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },

            # ── DOMAIN 3: Repetitive Patterns / Behaviours (Q9–Q12) ──────
            {
                "text": "How often does this person insist on following the same routine or become very upset when routines change unexpectedly?",
                "type": "freq5",
                "key":  "repetitive",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person repeat the same movements, words, or phrases (e.g. rocking, hand-flapping, echoing words)?",
                "type": "freq5",
                "key":  "repetitive",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person become highly distressed by small changes to their environment (e.g. furniture moved, different route taken)?",
                "type": "freq5",
                "key":  "repetitive",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person arrange objects in lines or patterns, or become upset when these are disturbed?",
                "type": "freq5",
                "key":  "repetitive",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },

            # ── DOMAIN 4: Focused Interests (Q13–Q16) ────────────────────
            {
                "text": "How often does this person talk about or focus on one or two topics to the exclusion of most others?",
                "type": "freq5",
                "key":  "focused",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person demonstrate an unusually deep level of knowledge about a very specific topic?",
                "type": "freq5",
                "key":  "focused",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person have difficulty shifting attention away from a preferred activity when asked?",
                "type": "freq5",
                "key":  "focused",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person use objects in repetitive or unusual ways (e.g. spinning wheels, lining up toys)?",
                "type": "freq5",
                "key":  "focused",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },

            # ── DOMAIN 5: Sensory Experiences (Q17–Q20) ──────────────────
            {
                "text": "How often does this person show an unusually strong reaction to sounds (e.g. covering ears, becoming very distressed by everyday noises)?",
                "type": "freq5",
                "key":  "sensory",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person appear unusually sensitive or insensitive to textures, tastes, smells, or physical touch?",
                "type": "freq5",
                "key":  "sensory",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person seem to seek out strong sensory experiences (e.g. spinning, pressing against surfaces, sniffing objects)?",
                "type": "freq5",
                "key":  "sensory",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
            {
                "text": "How often does this person show an unusually strong reaction to visual stimuli (e.g. bright lights, certain colours, or moving objects)?",
                "type": "freq5",
                "key":  "sensory",
                "options": [
                    ("Never",       0),
                    ("Rarely",      1),
                    ("Sometimes",   2),
                    ("Often",       3),
                    ("Very often",  4),
                ]
            },
        ],
        "scoring": {
            "method": "asd",
            "max": 80,       # 20 questions × max 4 points each
            "bands": [
                # Lower Indication — few traits reported
                (0,  26, "Lower Indication",     "asd_lower",
                 "Responses across the five areas suggest few traits associated with autism "
                 "at this time. This does not rule out autism — many individuals present "
                 "differently across environments. Continue awareness and seek professional "
                 "guidance if concerns remain."),
                # Requires Attention — moderate pattern
                (27, 53, "Requires Attention",   "asd_attention",
                 "Responses suggest a moderate number of traits across one or more ASD-related "
                 "areas. This does not confirm autism, but the overall pattern warrants "
                 "consideration. We recommend discussing these observations with a qualified "
                 "professional — such as a paediatrician, psychologist, or autism specialist."),
                # Higher Indication — strong pattern across multiple domains
                (54, 80, "Higher Indication",    "asd_higher",
                 "Responses suggest a higher number of traits across multiple ASD-related "
                 "areas. This is a screening tool only and cannot diagnose autism. However, "
                 "this result indicates that a professional evaluation would be strongly "
                 "advisable. Please seek a formal assessment from a qualified clinician."),
            ]
        }
    },
}


def compute_score(a_type, answers):
    """
    Compute a numeric score and band from session answers.
    Returns (raw_score, pct_score, band_label, band_colour, interpretation, extra).
    extra carries VARK tally or ASD domain breakdown.
    """
    cfg = ASSESSMENT_TYPES.get(a_type)
    if not cfg:
        return 50, 50, "N/A", "primary", "Unknown assessment type.", {}

    questions = cfg["questions"]
    scoring   = cfg["scoring"]
    method    = scoring["method"]
    max_score = scoring["max"]

    raw = 0
    extra = {}

    # ── ASD: domain-by-domain tally ───────────────────────────────────────
    if method == "asd":
        DOMAIN_LABELS = {
            "social_comm":    "Social Communication",
            "social_interact":"Social Interaction",
            "repetitive":     "Repetitive Patterns",
            "focused":        "Focused Interests",
            "sensory":        "Sensory Experiences",
        }
        domain_scores = {d: 0 for d in DOMAIN_LABELS}
        domain_max    = {d: 0 for d in DOMAIN_LABELS}

        for i, q in enumerate(questions, start=1):
            ans   = answers.get(f"q{i}", "")
            domain = q["key"]
            for label, score_val in q["options"]:
                if label == ans:
                    domain_scores[domain] = domain_scores.get(domain, 0) + score_val
                    break
            # max possible per question = highest option score
            domain_max[domain] = domain_max.get(domain, 0) + max(v for _, v in q["options"])

        raw = sum(domain_scores.values())

        # Domain percentages (0–100 each)
        domain_pct = {
            d: round((domain_scores[d] / domain_max[d]) * 100) if domain_max[d] else 0
            for d in DOMAIN_LABELS
        }
        extra = {
            "domain_scores": domain_scores,
            "domain_max":    domain_max,
            "domain_pct":    domain_pct,
            "domain_labels": DOMAIN_LABELS,
        }

    # ── VARK: category tally ─────────────────────────────────────────────
    elif method == "vark":
        tally = {"visual": 0, "auditory": 0, "read_write": 0, "kinaesthetic": 0}
        for i, q in enumerate(questions, start=1):
            ans = answers.get(f"q{i}", "")
            for label, code in q["options"]:
                if label == ans:
                    tally[code] = tally.get(code, 0) + 1
                    break
        dominant = max(tally, key=tally.get)
        raw = tally[dominant]
        extra = {"tally": tally, "dominant": dominant}

    # ── Standard sum ─────────────────────────────────────────────────────
    else:
        for i, q in enumerate(questions, start=1):
            ans = answers.get(f"q{i}", "")
            for label, score_val in q["options"]:
                if label == ans:
                    raw += score_val
                    break

    pct = round((raw / max_score) * 100) if max_score else 0
    pct = max(0, min(100, pct))

    band_label     = "N/A"
    band_colour    = "primary"
    interpretation = ""
    for lo, hi, bl, bc, interp in scoring["bands"]:
        if lo <= raw <= hi:
            band_label    = bl
            band_colour   = bc
            interpretation = interp
            break

    return raw, pct, band_label, band_colour, interpretation, extra


# ── Assessment Selection ──────────────────────────────────────────────────
@assessment.route("/select", methods=["GET", "POST"])
@login_required
def select():
    if request.method == "POST":
        a_type = request.form.get("assessment_type", "").strip()
        if a_type not in ASSESSMENT_TYPES:
            flash("Please select a valid assessment type.", "warning")
            return redirect(url_for("assessment.select"))
        session["assessment_type"]  = a_type
        session["assessment_label"] = ASSESSMENT_TYPES[a_type]["label"]
        session.pop("personal_info", None)
        session.pop("answers", None)
        return redirect(url_for("assessment.personal_info"))
    return render_template("assessment/select.html",
                           title="Choose Assessment",
                           assessment_types={
                               k: {
                                   "label":        v["label"],
                                   "icon":         v["icon"],
                                   "color":        v["color"],
                                   "time":         v["time"],
                                   "sections":     v["sections"],
                                   "description":  v["description"],
                                   "instructions": v["instructions"],
                                   "purpose":      v["purpose"],
                                   "question_count": len(v["questions"]),
                               }
                               for k, v in ASSESSMENT_TYPES.items()
                           })


# ── Personal Information ──────────────────────────────────────────────────
@assessment.route("/personal-info", methods=["GET", "POST"])
@login_required
def personal_info():
    if not session.get("assessment_type"):
        flash("Please select an assessment first.", "warning")
        return redirect(url_for("assessment.select"))

    a_type  = session.get("assessment_type", "")
    is_asd  = (a_type == "asd")

    if request.method == "POST":
        info = {
            "first_name": request.form.get("first_name",  "").strip(),
            "last_name":  request.form.get("last_name",   "").strip(),
            "goal":       request.form.get("goal",        ""),
            "notes":      request.form.get("notes",       "").strip(),
        }

        if is_asd:
            # ASD-specific fields
            info["responder_role"]       = request.form.get("responder_role",       "").strip()
            info["subject_name"]         = request.form.get("subject_name",         "").strip()
            info["subject_age_group"]    = request.form.get("subject_age_group",    "")
            info["subject_gender"]       = request.form.get("subject_gender",       "")
            info["previous_assessment"]  = request.form.get("previous_assessment",  "")
            info["developmental_notes"]  = request.form.get("developmental_notes",  "").strip()

            if not info["responder_role"]:
                flash("Please select who is completing this screen.", "warning")
                return redirect(url_for("assessment.personal_info"))
            if not info["subject_age_group"]:
                flash("Please select the age group of the person being assessed.", "warning")
                return redirect(url_for("assessment.personal_info"))
        else:
            # Standard fields
            info["age_group"]  = request.form.get("age_group",  "")
            info["gender"]     = request.form.get("gender",     "")
            info["education"]  = request.form.get("education",  "")
            info["occupation"] = request.form.get("occupation", "").strip()

        session["personal_info"] = info
        return redirect(url_for("assessment.questionnaire"))

    return render_template("assessment/personal_info.html",
                           title="Personal Information",
                           assessment_label=ASSESSMENT_TYPES.get(a_type, {}).get("label", "Assessment"),
                           is_asd=is_asd)


# ── Questionnaire ─────────────────────────────────────────────────────────
@assessment.route("/questionnaire", methods=["GET", "POST"])
@login_required
def questionnaire():
    a_type = session.get("assessment_type")
    if not a_type or a_type not in ASSESSMENT_TYPES:
        flash("Please start from the beginning.", "warning")
        return redirect(url_for("assessment.select"))

    cfg = ASSESSMENT_TYPES[a_type]
    questions = cfg["questions"]
    total_q   = len(questions)

    if request.method == "POST":
        answers = {}
        for i in range(1, total_q + 1):
            val = request.form.get(f"q{i}", "").strip()
            if val:
                answers[f"q{i}"] = val
        session["answers"] = answers
        if len(answers) < total_q:
            flash(f"Please answer all {total_q} questions. You answered {len(answers)}.", "warning")
            return redirect(url_for("assessment.questionnaire"))
        return redirect(url_for("assessment.review"))

    saved = session.get("answers", {})
    return render_template("assessment/questionnaire.html",
                           title="Questionnaire",
                           assessment_label=cfg["label"],
                           assessment_instructions=cfg["instructions"],
                           questions=questions,
                           total_q=total_q,
                           saved_answers=saved)


# ── Progress Tracking ─────────────────────────────────────────────────────
@assessment.route("/progress")
@login_required
def progress():
    return render_template("assessment/progress.html", title="Progress Tracking")


# ── Review Answers ────────────────────────────────────────────────────────
@assessment.route("/review", methods=["GET", "POST"])
@login_required
def review():
    a_type = session.get("assessment_type")
    if not session.get("answers") or not a_type:
        flash("No answers found. Please complete the questionnaire first.", "warning")
        return redirect(url_for("assessment.questionnaire"))

    if request.method == "POST":
        # Final report submission is temporarily disabled.
        flash("Final submission is temporarily disabled. Please check back later.", "info")
        return redirect(url_for("assessment.review"))

    cfg           = ASSESSMENT_TYPES.get(a_type, {})
    questions     = cfg.get("questions", [])
    answers       = session.get("answers", {})
    p_info        = session.get("personal_info", {})
    a_label       = session.get("assessment_label", "Assessment")
    total_q       = len(questions)
    answered_count = len(answers)

    return render_template(
        "assessment/review.html",
        title="Review Answers",
        questions=questions,
        answers=answers,
        personal_info=p_info,
        assessment_type=a_type,
        assessment_label=a_label,
        total_q=total_q,
        answered_count=answered_count,
    )


# ── Processing ────────────────────────────────────────────────────────────
@assessment.route("/processing")
@login_required
def processing():
    if not session.get("answers"):
        return redirect(url_for("assessment.select"))
    return render_template("assessment/processing.html", title="Processing")


# ── Result ────────────────────────────────────────────────────────────────
@assessment.route("/result")
@login_required
def result():
    a_type  = session.get("assessment_type", "")
    a_label = session.get("assessment_label", "Assessment")
    answers = session.get("answers", {})
    cfg     = ASSESSMENT_TYPES.get(a_type, {})

    raw, pct, band, band_color, interpretation, extra = compute_score(a_type, answers)

    return render_template(
        "assessment/result.html",
        title="Your Results",
        score=pct,
        raw_score=raw,
        band=band,
        band_color=band_color,
        interpretation=interpretation,
        assessment_type=a_type,
        assessment_label=a_label,
        assessment_info=cfg,
        answers=answers,
        extra=extra,
        personal_info=session.get("personal_info", {}),
    )


# ── Guidance / Recommendations ────────────────────────────────────────────
@assessment.route("/recommendations")
@login_required
def recommendations():
    a_type  = session.get("assessment_type", "")
    a_label = session.get("assessment_label", "Assessment")
    answers = session.get("answers", {})
    cfg     = ASSESSMENT_TYPES.get(a_type, {})

    # Re-use compute_score so the guidance page has full band context
    raw, pct, band, band_color, interpretation, extra = compute_score(a_type, answers)

    return render_template(
        "assessment/recommendations.html",
        title="Guidance & Interpretation",
        assessment_type=a_type,
        assessment_label=a_label,
        band=band,
        band_color=band_color,
        interpretation=interpretation,
        extra=extra,
        personal_info=session.get("personal_info", {}),
    )


# ── History ───────────────────────────────────────────────────────────────
@assessment.route("/history")
@login_required
def history():
    return render_template("assessment/history.html", title="Assessment History")


# ── Help / Information ────────────────────────────────────────────────────
@assessment.route("/help")
def help_page():
    return render_template("assessment/help.html", title="Help & Information")


# ── Delete stub ───────────────────────────────────────────────────────────
@assessment.route("/delete/<int:assessment_id>", methods=["POST"])
@login_required
def delete_assessment(assessment_id):
    flash("Assessment record deleted.", "success")
    return redirect(url_for("assessment.history"))
