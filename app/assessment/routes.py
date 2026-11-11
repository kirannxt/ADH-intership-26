import json
from datetime import datetime

from flask import render_template, redirect, url_for, request, session, flash, current_app
from flask_login import login_required, current_user

from app import db
from app.models import AssessmentRecord
from app.assessment import assessment

# --------------------------------------------------------------------------
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
# --------------------------------------------------------------------------

ASSESSMENT_TYPES = {

    # -- 1. ADHD Screening -------------------------------------------------
    "adhd": {
        "label":       "ADHD Screening",
        "icon":        "",
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

    # -- 2. Anxiety Screening (GAD-7 structure) ----------------------------
    "anxiety": {
        "label":       "Anxiety Screening",
        "icon":        "",
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

    # -- 3. Depression Screening (PHQ-9 structure) -------------------------
    "depression": {
        "label":       "Depression Screening",
        "icon":        "",
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

    # -- 4. Perceived Stress Scale (PSS-10 structure) ----------------------
    "stress": {
        "label":       "Perceived Stress",
        "icon":        "",
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

    # -- 5. Learning Style Inventory (VARK-inspired) -----------------------
    "learning": {
        "label":       "Learning Style",
        "icon":        "",
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

    # -- 6. Emotional Intelligence (EQ) ------------------------------------
    "eq": {
        "label":       "Emotional Intelligence",
        "icon":        "",
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

    # -- 7. ASD Assessment-Support System ---------------------------------
    "asd": {
        "label":       "ASD Assessment-Support",
        "icon":        "",
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

            # -- DOMAIN 1: Social Communication (Q1–Q4) -------------------
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

            # -- DOMAIN 2: Social Interaction (Q5–Q8) ---------------------
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

            # -- DOMAIN 3: Repetitive Patterns / Behaviours (Q9–Q12) ------
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

            # -- DOMAIN 4: Focused Interests (Q13–Q16) --------------------
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

            # -- DOMAIN 5: Sensory Experiences (Q17–Q20) ------------------
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

    # -- ASD: domain-by-domain tally ---------------------------------------
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

    # -- VARK: category tally ---------------------------------------------
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

    # -- Standard sum -----------------------------------------------------
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


# -- Assessment Selection --------------------------------------------------
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


# -- Personal Information --------------------------------------------------
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


# -- Questionnaire ---------------------------------------------------------
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


# -- Progress Tracking -----------------------------------------------------
@assessment.route("/progress")
@login_required
def progress():
    from app.ml import run_ml_insights
    from datetime import datetime

    records = (
        AssessmentRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(AssessmentRecord.completed_at.desc())
        .all()
    )

    total       = len(records)
    completed   = sum(1 for r in records if r.status == "completed")
    in_progress = sum(1 for r in records if r.status == "in_progress")
    avg_score   = (
        round(sum(r.pct_score for r in records if r.status == "completed") / completed)
        if completed else None
    )

    # Score by category: latest pct per type
    type_scores = {}
    for r in reversed(records):           # oldest first so latest overwrites
        if r.status == "completed":
            type_scores[r.assessment_type] = {
                "label": r.assessment_label,
                "pct":   r.pct_score,
                "band":  r.band,
                "color": r.color_bg,
                "icon":  r.icon,
            }

    # Milestones
    used_types = {r.assessment_type for r in records if r.status == "completed"}
    all_types  = set(ASSESSMENT_TYPES.keys())
    milestones = [
        ("First Assessment",   "Complete your first assessment",           completed >= 1),
        ("Honest Responder",   "Complete any assessment without skipping", completed >= 1),
        ("Consistent Learner", "Complete 3 assessments",                   completed >= 3),
        ("Explorer",           "Try 3 different assessment types",         len(used_types) >= 3),
        ("Well-Rounded",       "Complete all assessment types",            used_types >= all_types),
    ]

    # -- Read active ML filter from session --------------------------------
    ml_filter = session.get("ml_filter", {})
    date_from_str    = ml_filter.get("date_from")
    date_to_str      = ml_filter.get("date_to")
    types_include    = ml_filter.get("types_include") or None
    mode             = ml_filter.get("mode", "all")

    date_from = datetime.strptime(date_from_str, "%Y-%m-%d") if date_from_str else None
    date_to   = datetime.strptime(date_to_str,   "%Y-%m-%d") if date_to_str   else None

    # ML insights — re-runs fresh with current filter every page visit
    ml = run_ml_insights(
        records,
        date_from=date_from,
        date_to=date_to,
        types_include=types_include,
        mode=mode,
    )

    # -- Load trained model predictions if models exist --------------------
    from app.ml import load_and_predict
    trained_preds = load_and_predict(
        records,
        user_id=current_user.id,
        instance_path=current_app.instance_path,
        assessment_types_meta=ASSESSMENT_TYPES,
    )
    ml["trained_predictions"] = trained_preds

    return render_template(
        "assessment/progress.html",
        title="Progress Tracking",
        total=total,
        completed=completed,
        in_progress=in_progress,
        avg_score=avg_score,
        type_scores=type_scores,
        milestones=milestones,
        has_data=(total > 0),
        ml=ml,
        all_assessment_types=ASSESSMENT_TYPES,
    )


# -- Retrain Insights page -------------------------------------------------
@assessment.route("/retrain", methods=["GET", "POST"])
@login_required
def retrain_insights():
    """
    GET  — render the standalone Retrain Insights settings page.
    POST — validate inputs, store filter in session, redirect back to this page
           (or to progress on reset).
    """
    from datetime import datetime

    if request.method == "POST":
        action = request.form.get("action", "apply")

        if action == "reset":
            session.pop("ml_filter", None)
            flash("Insights reset to all data.", "success")
            return redirect(url_for("assessment.retrain_insights"))

        # -- Parse & validate inputs --------------------------------------
        date_from_str = request.form.get("date_from", "").strip()
        date_to_str   = request.form.get("date_to",   "").strip()
        mode          = request.form.get("mode", "all").strip()
        types_raw     = request.form.getlist("types_include")

        date_from = date_to = None
        try:
            if date_from_str:
                date_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            if date_to_str:
                date_to = datetime.strptime(date_to_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Please use the date picker.", "danger")
            return redirect(url_for("assessment.retrain_insights"))

        if date_from and date_to and date_from > date_to:
            flash("'From' date must be before 'To' date.", "danger")
            return redirect(url_for("assessment.retrain_insights"))

        valid_modes     = {"all", "recent", "trend"}
        valid_type_keys = {"adhd", "anxiety", "depression", "stress", "learning", "eq", "asd"}

        if mode not in valid_modes:
            mode = "all"

        types_include = [t for t in types_raw if t in valid_type_keys] or None

        session["ml_filter"] = {
            "date_from":     date_from_str if date_from else None,
            "date_to":       date_to_str   if date_to   else None,
            "types_include": types_include,
            "mode":          mode,
        }

        flash("Insights retrained with your selected settings.", "success")
        return redirect(url_for("assessment.retrain_insights"))

    # -- GET: build current_filter summary to pre-fill the form -----------
    ml_filter_raw = session.get("ml_filter", {})

    # Count how many completed records the user has (for the status banner)
    all_records = (
        AssessmentRecord.query
        .filter_by(user_id=current_user.id)
        .filter(AssessmentRecord.status == "completed")
        .count()
    )

    current_filter = None
    if ml_filter_raw:
        current_filter = dict(ml_filter_raw)
        current_filter["is_active"] = bool(
            current_filter.get("date_from")
            or current_filter.get("date_to")
            or current_filter.get("types_include")
            or current_filter.get("mode", "all") != "all"
        )
        current_filter["n_records"] = all_records

    # -- Model status (which types have trained models on disk) ------------
    from app.ml import get_model_status
    from app.models import MLModel
    model_status = get_model_status(current_user.id, current_app.instance_path)

    # Enrich with DB metadata (accuracy, trained_at)
    db_rows = {
        row.assessment_type: row
        for row in MLModel.query.filter_by(user_id=current_user.id).all()
    }
    for a_type, info in model_status.items():
        if a_type in db_rows:
            row = db_rows[a_type]
            info["accuracy_pct"] = row.accuracy_pct
            info["trained_at"]   = row.trained_at.strftime("%Y-%m-%d %H:%M") \
                                   if row.trained_at else None
            info["trained_ago"]  = row.trained_ago

    # Record counts per type for the training status panel
    type_counts: dict[str, int] = {}
    for r in AssessmentRecord.query.filter_by(
        user_id=current_user.id, status="completed"
    ).all():
        type_counts[r.assessment_type] = type_counts.get(r.assessment_type, 0) + 1

    return render_template(
        "assessment/retrain.html",
        title="Retrain AI Insights",
        current_filter=current_filter,
        all_assessment_types=ASSESSMENT_TYPES,
        model_status=model_status,
        type_counts=type_counts,
    )


# -- Train ML Models -------------------------------------------------------
@assessment.route("/retrain/train", methods=["POST"])
@login_required
def train_ml_models():
    """
    Trigger supervised model training for all assessment types.
    Trains one sklearn Pipeline per type, persists to disk with joblib,
    and upserts metadata into the MLModel table.
    """
    from app.ml import train_models, get_model_status
    from app.models import MLModel
    from datetime import datetime

    records = (
        AssessmentRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(AssessmentRecord.completed_at.asc())
        .all()
    )

    results = train_models(
        records,
        user_id=current_user.id,
        instance_path=current_app.instance_path,
        assessment_types_meta=ASSESSMENT_TYPES,
    )

    # -- Upsert MLModel metadata rows --------------------------------------
    trained_count = 0
    for a_type, info in results.items():
        if not info.get("trained"):
            continue
        row = MLModel.query.filter_by(
            user_id=current_user.id,
            assessment_type=a_type,
        ).first()
        if row is None:
            row = MLModel(user_id=current_user.id, assessment_type=a_type)
            db.session.add(row)
        row.algorithm   = info["algorithm"]
        row.n_samples   = info["n_samples"]
        row.n_features  = info["n_features"]
        row.accuracy    = info.get("accuracy")
        row.model_path  = info["model_path"]
        row.trained_at  = datetime.utcnow()
        trained_count  += 1

    db.session.commit()

    skipped = [t for t, i in results.items() if not i.get("trained")]

    if trained_count == 0:
        flash(
            "No models were trained — you need at least 4 completed records "
            "per assessment type. Upload a CSV or complete more assessments first.",
            "warning",
        )
    else:
        msg = f"[OK] Trained {trained_count} model(s) successfully."
        if skipped:
            msg += f" {len(skipped)} type(s) skipped (not enough data)."
        flash(msg, "success")

    return redirect(url_for("assessment.retrain_insights"))


# -- CSV Template download -------------------------------------------------
@assessment.route("/retrain/csv-template")
@login_required
def csv_template():
    """Return a ready-to-fill CSV template the user can populate and re-upload."""
    import io
    from flask import Response

    lines = [
        "date,assessment_type,pct_score,band",
        "# date        : YYYY-MM-DD format",
        "# assessment_type : adhd | anxiety | depression | stress | learning | eq | asd",
        "# pct_score   : integer 0-100",
        "# band        : your result label, e.g. Mild / Moderate / High (optional)",
        "# Delete these comment lines before uploading.",
        "2026-01-15,anxiety,42,Mild",
        "2026-02-10,anxiety,38,Mild",
        "2026-03-05,eq,74,High",
    ]
    content = "\n".join(lines) + "\n"
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=assessme_import_template.csv"},
    )


# -- CSV Upload ------------------------------------------------------------
@assessment.route("/retrain/upload-csv", methods=["POST"])
@login_required
def upload_csv():
    """
    Parse an uploaded CSV file and import rows as AssessmentRecord entries.

    Expected columns (order-independent, case-insensitive header):
        date            YYYY-MM-DD
        assessment_type adhd | anxiety | depression | stress | learning | eq | asd
        pct_score       integer 0–100
        band            (optional) text label

    Rows with errors are skipped; a summary flash message reports
    how many were imported and how many were rejected.
    """
    import csv
    import io
    from datetime import datetime

    _VALID_TYPES = {
        "adhd", "anxiety", "depression", "stress", "learning", "eq", "asd"
    }
    _TYPE_LABELS = {
        "adhd":       "ADHD Screening",
        "anxiety":    "Anxiety Screening",
        "depression": "Depression Screening",
        "stress":     "Perceived Stress",
        "learning":   "Learning Style",
        "eq":         "Emotional Intelligence",
        "asd":        "ASD Support Screen",
    }
    _BAND_COLORS = {
        "low": "success", "mild": "success",
        "moderate": "warning", "medium": "warning",
        "high": "danger", "severe": "danger",
        "very high": "danger",
    }

    uploaded = request.files.get("csv_file")
    if not uploaded or uploaded.filename == "":
        flash("No file selected. Please choose a CSV file.", "warning")
        return redirect(url_for("assessment.retrain_insights"))

    if not uploaded.filename.lower().endswith(".csv"):
        flash("Only .csv files are accepted.", "danger")
        return redirect(url_for("assessment.retrain_insights"))

    # Read file content — limit to 1 MB
    raw_bytes = uploaded.read(1_048_577)
    if len(raw_bytes) > 1_048_576:
        flash("File too large. Maximum size is 1 MB.", "danger")
        return redirect(url_for("assessment.retrain_insights"))

    try:
        content = raw_bytes.decode("utf-8-sig")   # strip BOM if present
    except UnicodeDecodeError:
        flash("Could not read file. Make sure it is saved as UTF-8.", "danger")
        return redirect(url_for("assessment.retrain_insights"))

    imported = 0
    skipped  = 0
    errors   = []

    reader = csv.DictReader(io.StringIO(content))

    # Normalise header names (strip whitespace, lowercase)
    if reader.fieldnames is None:
        flash("CSV file appears to be empty.", "warning")
        return redirect(url_for("assessment.retrain_insights"))

    fieldnames_norm = [f.strip().lower() for f in reader.fieldnames]

    required = {"date", "assessment_type", "pct_score"}
    if not required.issubset(set(fieldnames_norm)):
        missing = required - set(fieldnames_norm)
        flash(f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
              f"Download the template to see the correct format.", "danger")
        return redirect(url_for("assessment.retrain_insights"))

    for line_num, raw_row in enumerate(reader, start=2):
        # Skip comment lines (cell starts with #)
        first_val = next(iter(raw_row.values()), "").strip()
        if first_val.startswith("#"):
            continue

        # Normalise keys
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}

        # -- Validate date ------------------------------------------------
        try:
            completed_at = datetime.strptime(row.get("date", ""), "%Y-%m-%d")
        except ValueError:
            skipped += 1
            errors.append(f"Row {line_num}: invalid date '{row.get('date')}' (use YYYY-MM-DD)")
            continue

        if completed_at > datetime.utcnow():
            skipped += 1
            errors.append(f"Row {line_num}: date {row['date']} is in the future")
            continue

        # -- Validate assessment_type -------------------------------------
        a_type = row.get("assessment_type", "").lower().strip()
        if a_type not in _VALID_TYPES:
            skipped += 1
            errors.append(f"Row {line_num}: unknown type '{a_type}'")
            continue

        # -- Validate pct_score -------------------------------------------
        try:
            pct = int(row.get("pct_score", ""))
            if not 0 <= pct <= 100:
                raise ValueError
        except ValueError:
            skipped += 1
            errors.append(f"Row {line_num}: pct_score must be an integer 0–100")
            continue

        # -- Optional band ------------------------------------------------
        band       = row.get("band", "").strip() or "Imported"
        band_color = _BAND_COLORS.get(band.lower(), "primary")

        # -- Insert record ------------------------------------------------
        record = AssessmentRecord(
            user_id           = current_user.id,
            assessment_type   = a_type,
            assessment_label  = _TYPE_LABELS[a_type],
            raw_score         = pct,          # raw stored as pct for CSV imports
            pct_score         = pct,
            band              = band,
            band_color        = band_color,
            status            = "completed",
            answers_json      = "{}",
            personal_info_json= "{}",
            completed_at      = completed_at,
        )
        db.session.add(record)
        imported += 1

    if imported:
        db.session.commit()

    # -- Build summary flash ----------------------------------------------
    if imported == 0 and skipped == 0:
        flash("The CSV had no data rows to import.", "warning")
    elif imported > 0 and skipped == 0:
        flash(f"[OK] Successfully imported {imported} record(s). "
              f"Visit Progress to see your updated insights.", "success")
    elif imported > 0 and skipped > 0:
        err_preview = "; ".join(errors[:3])
        if len(errors) > 3:
            err_preview += f" … and {len(errors) - 3} more"
        flash(f"[!] Imported {imported} record(s), skipped {skipped} row(s): {err_preview}",
              "warning")
    else:
        err_preview = "; ".join(errors[:3])
        flash(f"[X] No records imported. Errors: {err_preview}", "danger")

    return redirect(url_for("assessment.retrain_insights"))


# -- Review Answers --------------------------------------------------------
@assessment.route("/review", methods=["GET", "POST"])
@login_required
def review():
    a_type = session.get("assessment_type")
    if not session.get("answers") or not a_type:
        flash("No answers found. Please complete the questionnaire first.", "warning")
        return redirect(url_for("assessment.questionnaire"))

    if request.method == "POST":
        answers  = session.get("answers", {})
        p_info   = session.get("personal_info", {})

        raw, pct, band, band_color, interpretation, extra = compute_score(a_type, answers)

        # Duration: stored in session by the questionnaire JS as seconds
        duration = session.get("duration_seconds")

        record = AssessmentRecord(
            user_id           = current_user.id,
            assessment_type   = a_type,
            assessment_label  = session.get("assessment_label", "Assessment"),
            raw_score         = raw,
            pct_score         = pct,
            band              = band,
            band_color        = band_color,
            status            = "completed",
            duration_seconds  = int(duration) if duration else None,
            answers_json      = json.dumps(answers),
            personal_info_json = json.dumps(p_info),
            completed_at      = datetime.utcnow(),
        )
        db.session.add(record)
        db.session.commit()

        # Store the record id in session so result/recommendations pages can load it
        session["last_record_id"] = record.id

        return redirect(url_for("assessment.processing"))

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


# -- Processing ------------------------------------------------------------
@assessment.route("/processing")
@login_required
def processing():
    if not session.get("answers"):
        return redirect(url_for("assessment.select"))
    return render_template("assessment/processing.html", title="Processing")


# -- Result ----------------------------------------------------------------
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


# -- Guidance / Recommendations --------------------------------------------
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


# -- History ---------------------------------------------------------------
@assessment.route("/history")
@login_required
def history():
    records = (
        AssessmentRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(AssessmentRecord.completed_at.desc())
        .all()
    )
    return render_template("assessment/history.html",
                           title="Assessment History",
                           records=records)


# -- Help / Information ----------------------------------------------------
@assessment.route("/help")
def help_page():
    return render_template("assessment/help.html", title="Help & Information")


# -- Delete ----------------------------------------------------------------
@assessment.route("/delete/<int:assessment_id>", methods=["POST"])
@login_required
def delete_assessment(assessment_id):
    record = AssessmentRecord.query.filter_by(
        id=assessment_id, user_id=current_user.id
    ).first()
    if record:
        db.session.delete(record)
        db.session.commit()
        flash("Assessment record deleted.", "success")
    else:
        flash("Record not found or you do not have permission to delete it.", "warning")
    return redirect(url_for("assessment.history"))
