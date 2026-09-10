import json
import math
import os


# ============================================================
# STATSHUB MATCH MODEL V2
# DETERMINISTIC MODEL + VALIDATION
# ============================================================

INPUT_FILE = "data/statshub_team_analysis.json"
OUTPUT_FILE = "data/statshub_match_model.json"

HOME = "PSV"
AWAY = "Shakhtar"

MODEL_VERSION = "SH-POISSON-002"

# Probability tail is controlled with a high goal limit.
# This prevents the artificial 0-10 truncation problem.
MAX_GOALS = 20

TOLERANCE = 1e-9


# ============================================================
# FILE CHECK
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
# DATA CHECK
# ============================================================

if "team_analysis" not in data:
    raise ValueError(
        "JSON içinde 'team_analysis' bulunamadı."
    )

if HOME not in data["team_analysis"]:
    raise ValueError(
        f"Home takım bulunamadı: {HOME}"
    )

if AWAY not in data["team_analysis"]:
    raise ValueError(
        f"Away takım bulunamadı: {AWAY}"
    )


home = data["team_analysis"][HOME]
away = data["team_analysis"][AWAY]


# ============================================================
# HELPERS
# ============================================================

def get_stat(team, name):

    value = (
        team
        .get("statistics", {})
        .get(name, {})
        .get("average")
    )

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_goal_for(team):

    value = (
        team
        .get("goals", {})
        .get("goals_for", {})
        .get("average")
    )

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_goal_against(team):

    value = (
        team
        .get("goals", {})
        .get("goals_against", {})
        .get("average")
    )

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_mean(values):

    clean = []

    for value in values:

        if value is None:
            continue

        if not math.isfinite(value):
            continue

        clean.append(value)

    if not clean:
        return None

    return sum(clean) / len(clean)


def require_positive_or_zero(
    value,
    name
):

    if value is None:
        raise ValueError(
            f"Eksik model girdisi: {name}"
        )

    if not math.isfinite(value):
        raise ValueError(
            f"Geçersiz model girdisi: {name}"
        )

    if value < 0:
        raise ValueError(
            f"Negatif model girdisi: {name}"
        )

    return value


# ============================================================
# INPUT DATA
# ============================================================

home_goals_for = require_positive_or_zero(
    get_goal_for(home),
    "home_goals_for"
)

home_goals_against = require_positive_or_zero(
    get_goal_against(home),
    "home_goals_against"
)

away_goals_for = require_positive_or_zero(
    get_goal_for(away),
    "away_goals_for"
)

away_goals_against = require_positive_or_zero(
    get_goal_against(away),
    "away_goals_against"
)

home_xg = require_positive_or_zero(
    get_stat(home, "expectedGoals"),
    "home_xg"
)

away_xg = require_positive_or_zero(
    get_stat(away, "expectedGoals"),
    "away_xg"
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
# BASE GOAL MODEL
#
# Home attack:
#   Home GF + Away GA
#
# Away attack:
#   Away GF + Home GA
# ============================================================

home_lambda_base = safe_mean(
    [
        home_goals_for,
        away_goals_against
    ]
)

away_lambda_base = safe_mean(
    [
        away_goals_for,
        home_goals_against
    ]
)


if home_lambda_base is None:
    raise ValueError(
        "Home base lambda hesaplanamadı."
    )

if away_lambda_base is None:
    raise ValueError(
        "Away base lambda hesaplanamadı."
    )


# ============================================================
# xG BLEND
#
# IMPORTANT:
# This is only a temporary deterministic blend.
# The weight will later be optimized by backtesting.
# ============================================================

GOAL_MODEL_WEIGHT = 0.50
XG_MODEL_WEIGHT = 0.50


home_lambda = (
    home_lambda_base * GOAL_MODEL_WEIGHT
    +
    home_xg * XG_MODEL_WEIGHT
)


away_lambda = (
    away_lambda_base * GOAL_MODEL_WEIGHT
    +
    away_xg * XG_MODEL_WEIGHT
)


if home_lambda <= 0:
    raise ValueError(
        "Home lambda sıfır veya negatif."
    )

if away_lambda <= 0:
    raise ValueError(
        "Away lambda sıfır veya negatif."
    )


# ============================================================
# POISSON
# ============================================================

def poisson_probability(
    goals,
    lam
):

    return (
        math.exp(-lam)
        *
        (lam ** goals)
        /
        math.factorial(goals)
    )


home_goal_probs = {}
away_goal_probs = {}


for goals in range(
    MAX_GOALS + 1
):

    home_goal_probs[goals] = (
        poisson_probability(
            goals,
            home_lambda
        )
    )

    away_goal_probs[goals] = (
        poisson_probability(
            goals,
            away_lambda
        )
    )


# ============================================================
# SINGLE-TEAM DISTRIBUTION VALIDATION
# ============================================================

home_goal_distribution_sum = sum(
    home_goal_probs.values()
)

away_goal_distribution_sum = sum(
    away_goal_probs.values()
)


# ============================================================
# SCORE MATRIX
# ============================================================

score_matrix = {}

home_win_probability = 0.0
draw_probability = 0.0
away_win_probability = 0.0


for home_goals in range(
    MAX_GOALS + 1
):

    for away_goals in range(
        MAX_GOALS + 1
    ):

        probability = (
            home_goal_probs[home_goals]
            *
            away_goal_probs[away_goals]
        )

        score = (
            home_goals,
            away_goals
        )

        score_key = (
            f"{home_goals}-{away_goals}"
        )

        score_matrix[
            score_key
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
# SCORE MATRIX SUM
# ============================================================

score_matrix_sum = sum(
    score_matrix.values()
)


# ============================================================
# TOP SCORES
# ============================================================

top_scores = sorted(
    score_matrix.items(),
    key=lambda x: x[1],
    reverse=True
)


# ============================================================
# OVER / UNDER
# ============================================================

markets = {}


for line in [
    0.5,
    1.5,
    2.5,
    3.5,
    4.5
]:

    over = 0.0
    under = 0.0

    for score, probability in score_matrix.items():

        home_goals, away_goals = map(
            int,
            score.split("-")
        )

        total_goals = (
            home_goals
            +
            away_goals
        )

        if total_goals > line:

            over += probability

        else:

            under += probability


    markets[
        f"over_{str(line).replace('.', '_')}"
    ] = over

    markets[
        f"under_{str(line).replace('.', '_')}"
    ] = under


# ============================================================
# BTTS
# ============================================================

btts_yes = 0.0
btts_no = 0.0


for score, probability in score_matrix.items():

    home_goals, away_goals = map(
        int,
        score.split("-")
    )

    if (
        home_goals >= 1
        and
        away_goals >= 1
    ):

        btts_yes += probability

    else:

        btts_no += probability


# ============================================================
# MATHEMATICAL VALIDATION
# ============================================================

checks = {}


checks[
    "home_goal_distribution"
] = (
    abs(
        home_goal_distribution_sum - 1
    )
    <= TOLERANCE
)


checks[
    "away_goal_distribution"
] = (
    abs(
        away_goal_distribution_sum - 1
    )
    <= TOLERANCE
)


checks[
    "score_matrix"
] = (
    abs(
        score_matrix_sum - 1
    )
    <= TOLERANCE
)


checks[
    "one_x_two"
] = (
    abs(
        (
            home_win_probability
            +
            draw_probability
            +
            away_win_probability
        )
        - 1
    )
    <= TOLERANCE
)


checks[
    "over_under_0_5"
] = (
    abs(
        markets["over_0_5"]
        +
        markets["under_0_5"]
        - 1
    )
    <= TOLERANCE
)


checks[
    "over_under_1_5"
] = (
    abs(
        markets["over_1_5"]
        +
        markets["under_1_5"]
        - 1
    )
    <= TOLERANCE
)


checks[
    "over_under_2_5"
] = (
    abs(
        markets["over_2_5"]
        +
        markets["under_2_5"]
        - 1
    )
    <= TOLERANCE
)


checks[
    "over_under_3_5"
] = (
    abs(
        markets["over_3_5"]
        +
        markets["under_3_5"]
        - 1
    )
    <= TOLERANCE
)


checks[
    "over_under_4_5"
] = (
    abs(
        markets["over_4_5"]
        +
        markets["under_4_5"]
        - 1
    )
    <= TOLERANCE
)


checks[
    "btts"
] = (
    abs(
        btts_yes
        +
        btts_no
        - 1
    )
    <= TOLERANCE
)


validation_passed = all(
    checks.values()
)


# ============================================================
# MODEL OUTPUT
# ============================================================

model = {

    "source": "StatsHub",

    "fixture": {
        "home": HOME,
        "away": AWAY
    },

    "model_version":
        MODEL_VERSION,

    "model_type":
        "Independent Poisson",

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

        "home_base":
            round(
                home_lambda_base,
                6
            ),

        "away_base":
            round(
                away_lambda_base,
                6
            ),

        "goal_model_weight":
            GOAL_MODEL_WEIGHT,

        "xg_model_weight":
            XG_MODEL_WEIGHT,

        "home":
            round(
                home_lambda,
                6
            ),

        "away":
            round(
                away_lambda,
                6
            )
    },

    "probabilities": {

        "home_win":
            round(
                home_win_probability,
                8
            ),

        "draw":
            round(
                draw_probability,
                8
            ),

        "away_win":
            round(
                away_win_probability,
                8
            ),

        "over_0_5":
            round(
                markets["over_0_5"],
                8
            ),

        "under_0_5":
            round(
                markets["under_0_5"],
                8
            ),

        "over_1_5":
            round(
                markets["over_1_5"],
                8
            ),

        "under_1_5":
            round(
                markets["under_1_5"],
                8
            ),

        "over_2_5":
            round(
                markets["over_2_5"],
                8
            ),

        "under_2_5":
            round(
                markets["under_2_5"],
                8
            ),

        "over_3_5":
            round(
                markets["over_3_5"],
                8
            ),

        "under_3_5":
            round(
                markets["under_3_5"],
                8
            ),

        "over_4_5":
            round(
                markets["over_4_5"],
                8
            ),

        "under_4_5":
            round(
                markets["under_4_5"],
                8
            ),

        "btts_yes":
            round(
                btts_yes,
                8
            ),

        "btts_no":
            round(
                btts_no,
                8
            )
    },

    "validation": {

        "home_goal_distribution_sum":
            home_goal_distribution_sum,

        "away_goal_distribution_sum":
            away_goal_distribution_sum,

        "score_matrix_sum":
            score_matrix_sum,

        "one_x_two_sum":
            (
                home_win_probability
                +
                draw_probability
                +
                away_win_probability
            ),

        "btts_sum":
            btts_yes + btts_no,

        "checks":
            checks,

        "validation_passed":
            validation_passed
    },

    "top_scores": [

        {
            "score":
                score,

            "probability":
                round(
                    probability,
                    8
                )
        }

        for score, probability
        in top_scores[:15]
    ]
}


# ============================================================
# SAVE
# ============================================================

os.makedirs(
    os.path.dirname(OUTPUT_FILE),
    exist_ok=True
)


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
# CONSOLE
# ============================================================

print("")
print("==========================================")
print("STATSHUB MATCH MODEL V2")
print("==========================================")
print("")

print(
    f"{HOME} λ =",
    round(home_lambda, 6)
)

print(
    f"{AWAY} λ =",
    round(away_lambda, 6)
)

print("")

print(
    "Home Win:",
    round(
        home_win_probability * 100,
        4
    ),
    "%"
)

print(
    "Draw:",
    round(
        draw_probability * 100,
        4
    ),
    "%"
)

print(
    "Away Win:",
    round(
        away_win_probability * 100,
        4
    ),
    "%"
)

print("")

print(
    "Over 2.5:",
    round(
        markets["over_2_5"] * 100,
        4
    ),
    "%"
)

print(
    "Under 2.5:",
    round(
        markets["under_2_5"] * 100,
        4
    ),
    "%"
)

print(
    "BTTS Yes:",
    round(
        btts_yes * 100,
        4
    ),
    "%"
)

print(
    "BTTS No:",
    round(
        btts_no * 100,
        4
    ),
    "%"
)

print("")
print("MATEMATIK KONTROLLERİ")
print("------------------------------------------")

for name, result in checks.items():

    print(
        name,
        ":",
        "PASS" if result else "FAIL"
    )

print("------------------------------------------")

print(
    "VALIDATION:",
    "PASS" if validation_passed else "FAIL"
)

print("")
print("En olası 5 skor:")

for score, probability in top_scores[:5]:

    print(
        score,
        "→",
        round(
            probability * 100,
            4
        ),
        "%"
    )

print("")
print(
    "Çıktı:",
    OUTPUT_FILE
)
