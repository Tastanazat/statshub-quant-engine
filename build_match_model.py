import json
import math
import os

# ============================================================
# STATSHUB MATCH MODEL
# PSV vs SHAKHTAR
# ============================================================

INPUT_FILE = "data/statshub_team_analysis.json"
OUTPUT_FILE = "data/statshub_match_model.json"

HOME = "PSV"
AWAY = "Shakhtar"

# ============================================================
# DOSYA
# ============================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Bulunamadı: {INPUT_FILE}"
    )

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:
    data = json.load(f)


# ============================================================
# VERİ OKUMA
# ============================================================

home = data["team_analysis"][HOME]
away = data["team_analysis"][AWAY]


def get_stat(team, name):

    return (
        team
        .get("statistics", {})
        .get(name, {})
        .get("average")
    )


def get_goal_for(team):

    return (
        team
        .get("goals", {})
        .get("goals_for", {})
        .get("average")
    )


def get_goal_against(team):

    return (
        team
        .get("goals", {})
        .get("goals_against", {})
        .get("average")
    )


# ============================================================
# TEMEL VERİLER
# ============================================================

home_goals_for = get_goal_for(home)
home_goals_against = get_goal_against(home)

away_goals_for = get_goal_for(away)
away_goals_against = get_goal_against(away)

home_xg = get_stat(
    home,
    "expectedGoals"
)

away_xg = get_stat(
    away,
    "expectedGoals"
)

home_shots = get_stat(
    home,
    "shots"
)

away_shots = get_stat(
    away,
    "shots"
)

home_corners = get_stat(
    home,
    "corners"
)

away_corners = get_stat(
    away,
    "corners"
)

home_possession = get_stat(
    home,
    "possession"
)

away_possession = get_stat(
    away,
    "possession"
)


# ============================================================
# GÜVENLİ ORTALAMA
# ============================================================

def safe_mean(values):

    values = [
        v for v in values
        if v is not None
    ]

    if not values:
        return None

    return sum(values) / len(values)


# ============================================================
# HAM GOL MODELİ
#
# Home attack + Away defense
# Away attack + Home defense
# ============================================================

home_lambda_base = safe_mean([
    home_goals_for,
    away_goals_against
])

away_lambda_base = safe_mean([
    away_goals_for,
    home_goals_against
])


# ============================================================
# xG DESTEK KATMANI
#
# xG'yi tamamen göz ardı etmiyoruz.
# Ancak ham gol ortalamasını tek başına da kullanmıyoruz.
# ============================================================

home_lambda_components = [
    home_lambda_base,
    home_xg
]

away_lambda_components = [
    away_lambda_base,
    away_xg
]

home_lambda = safe_mean(
    home_lambda_components
)

away_lambda = safe_mean(
    away_lambda_components
)


# ============================================================
# POISSON
# ============================================================

def poisson_probability(
    goals,
    lam
):

    if lam is None:
        return None

    return (
        math.exp(-lam)
        * (lam ** goals)
        / math.factorial(goals)
    )


MAX_GOALS = 10

home_goal_probs = {}
away_goal_probs = {}

for g in range(
    MAX_GOALS + 1
):

    home_goal_probs[g] = poisson_probability(
        g,
        home_lambda
    )

    away_goal_probs[g] = poisson_probability(
        g,
        away_lambda
    )


# ============================================================
# SKOR MATRİSİ
# ============================================================

score_matrix = {}

home_win_probability = 0
draw_probability = 0
away_win_probability = 0

for home_goals in range(
    MAX_GOALS + 1
):

    for away_goals in range(
        MAX_GOALS + 1
    ):

        probability = (
            home_goal_probs[home_goals]
            * away_goal_probs[away_goals]
        )

        score = (
            home_goals,
            away_goals
        )

        score_matrix[
            f"{home_goals}-{away_goals}"
        ] = probability

        if home_goals > away_goals:

            home_win_probability += (
                probability
            )

        elif home_goals == away_goals:

            draw_probability += (
                probability
            )

        else:

            away_win_probability += (
                probability
            )


# ============================================================
# EN OLASI SKORLAR
# ============================================================

top_scores = sorted(
    score_matrix.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]


# ============================================================
# OVER 2.5 / UNDER 2.5
# ============================================================

over_25 = 0
under_25 = 0

for score, probability in score_matrix.items():

    h, a = map(
        int,
        score.split("-")
    )

    total = h + a

    if total >= 3:

        over_25 += probability

    else:

        under_25 += probability


# ============================================================
# BTTS
# ============================================================

btts_yes = 0
btts_no = 0

for score, probability in score_matrix.items():

    h, a = map(
        int,
        score.split("-")
    )

    if h >= 1 and a >= 1:

        btts_yes += probability

    else:

        btts_no += probability


# ============================================================
# MODEL ÇIKTISI
# ============================================================

model = {

    "source": "StatsHub",

    "fixture": {
        "home": HOME,
        "away": AWAY
    },

    "input": {

        "home_goals_for":
            home_goals_for,

        "home_goals_against":
            home_goals_against,

        "away_goals_for":
            away_goals_for,

        "away_goals_against":
            away_goals_against,

        "home_xg":
            home_xg,

        "away_xg":
            away_xg,

        "home_shots":
            home_shots,

        "away_shots":
            away_shots,

        "home_corners":
            home_corners,

        "away_corners":
            away_corners,

        "home_possession":
            home_possession,

        "away_possession":
            away_possession

    },

    "lambda": {

        "home":
            round(
                home_lambda,
                4
            ),

        "away":
            round(
                away_lambda,
                4
            )

    },

    "probabilities": {

        "home_win":
            round(
                home_win_probability,
                6
            ),

        "draw":
            round(
                draw_probability,
                6
            ),

        "away_win":
            round(
                away_win_probability,
                6
            ),

        "over_2_5":
            round(
                over_25,
                6
            ),

        "under_2_5":
            round(
                under_25,
                6
            ),

        "btts_yes":
            round(
                btts_yes,
                6
            ),

        "btts_no":
            round(
                btts_no,
                6
            )

    },

    "top_scores": [

        {
            "score":
                score,

            "probability":
                round(
                    probability,
                    6
                )

        }

        for score, probability
        in top_scores

    ],

    "model_version":
        "SH-POISSON-001"

}


# ============================================================
# KAYDET
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        model,
        f,
        ensure_ascii=False,
        indent=2
    )


# ============================================================
# EKRAN
# ============================================================

print("")
print("==========================================")
print("STATSHUB MATCH MODEL")
print("==========================================")
print("")

print(
    f"{HOME} λ =",
    round(home_lambda, 4)
)

print(
    f"{AWAY} λ =",
    round(away_lambda, 4)
)

print("")

print(
    "Home Win:",
    round(
        home_win_probability * 100,
        2
    ),
    "%"
)

print(
    "Draw:",
    round(
        draw_probability * 100,
        2
    ),
    "%"
)

print(
    "Away Win:",
    round(
        away_win_probability * 100,
        2
    ),
    "%"
)

print("")

print(
    "Over 2.5:",
    round(
        over_25 * 100,
        2
    ),
    "%"
)

print(
    "BTTS:",
    round(
        btts_yes * 100,
        2
    ),
    "%"
)

print("")
print("En olası skorlar:")

for score, probability in top_scores[:5]:

    print(
        score,
        "→",
        round(
            probability * 100,
            2
        ),
        "%"
    )

print("")
print(
    "Çıktı:",
    OUTPUT_FILE
)
