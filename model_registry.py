import json
import os
from datetime import datetime, timezone


# ============================================================
# STATSHUB QUANT ENGINE
# MODEL REGISTRY ENGINE V1
# ============================================================

MODEL_FILE = (
    "data/statshub_match_model.json"
)

OUTPUT_DIRECTORY = (
    "data/models"
)

REGISTRY_FILE = (
    "data/models/model_registry.json"
)

SOURCE_REQUIRED = "StatsHub"

DEFAULT_ACTIVE_MODEL = (
    "SH-POISSON-002"
)

REGISTRY_VERSION = (
    "SH-REGISTRY-001"
)


# ============================================================
# HELPERS
# ============================================================

def now_utc():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# SAFE JSON LOAD
# ============================================================

def load_json(path):

    if not os.path.exists(path):

        raise SystemExit(
            f"MODEL REGISTRY ERROR: "
            f"Dosya bulunamadı: {path}"
        )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except json.JSONDecodeError as error:

        raise SystemExit(
            f"MODEL REGISTRY ERROR: "
            f"JSON okunamadı: {error}"
        )


# ============================================================
# MODEL VALIDATION
# ============================================================

def validate_model(model):

    if not isinstance(
        model,
        dict
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Model JSON object değil."
        )


    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source = model.get(
        "source"
    )

    if source != SOURCE_REQUIRED:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            f"Model kaynağı StatsHub değil: {source}"
        )


    # --------------------------------------------------------
    # MODEL VERSION
    # --------------------------------------------------------

    model_version = model.get(
        "model_version"
    )

    if not model_version:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "model_version bulunamadı."
        )


    # --------------------------------------------------------
    # FIXTURE
    # --------------------------------------------------------

    fixture = model.get(
        "fixture"
    )

    if not isinstance(
        fixture,
        dict
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "fixture bilgisi bulunamadı."
        )


    home = fixture.get(
        "home"
    )

    away = fixture.get(
        "away"
    )

    if not home or not away:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Home/Away bilgisi eksik."
        )


    # --------------------------------------------------------
    # LAMBDA
    # --------------------------------------------------------

    lambdas = model.get(
        "lambda"
    )

    if not isinstance(
        lambdas,
        dict
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "lambda bilgisi bulunamadı."
        )


    lambda_home = lambdas.get(
        "home"
    )

    lambda_away = lambdas.get(
        "away"
    )

    if lambda_home is None:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "lambda.home bulunamadı."
        )


    if lambda_away is None:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "lambda.away bulunamadı."
        )


    try:

        lambda_home = float(
            lambda_home
        )

        lambda_away = float(
            lambda_away
        )

    except (
        TypeError,
        ValueError
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Lambda değerleri sayısal değil."
        )


    if lambda_home <= 0:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "lambda.home <= 0."
        )


    if lambda_away <= 0:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "lambda.away <= 0."
        )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    validation = model.get(
        "validation",
        {}
    )

    if validation.get(
        "validation_passed"
    ) is not True:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Model mathematical validation PASS değil."
        )


    return {
        "model_version":
            model_version,

        "source":
            source,

        "home":
            home,

        "away":
            away,

        "lambda_home":
            lambda_home,

        "lambda_away":
            lambda_away
    }


# ============================================================
# CREATE EMPTY REGISTRY
# ============================================================

def create_empty_registry():

    return {

        "source":
            SOURCE_REQUIRED,

        "registry_version":
            REGISTRY_VERSION,

        "generated_at":
            now_utc(),

        "active_model":
            None,

        "models":
            {},

        "history":
            []

    }


# ============================================================
# LOAD EXISTING REGISTRY
# ============================================================

def load_registry():

    if not os.path.exists(
        REGISTRY_FILE
    ):

        return create_empty_registry()


    try:

        with open(
            REGISTRY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            registry = json.load(f)

    except json.JSONDecodeError as error:

        raise SystemExit(
            f"MODEL REGISTRY ERROR: "
            f"Registry JSON okunamadı: {error}"
        )


    if not isinstance(
        registry,
        dict
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Registry object değil."
        )


    return registry


# ============================================================
# REGISTER MODEL
# ============================================================

def register_model(
    registry,
    model_info
):

    model_version = (
        model_info["model_version"]
    )


    models = registry.setdefault(
        "models",
        {}
    )


    existing = models.get(
        model_version
    )


    model_record = {

        "model_version":
            model_version,

        "source":
            model_info["source"],

        "home":
            model_info["home"],

        "away":
            model_info["away"],

        "lambda_home":
            model_info["lambda_home"],

        "lambda_away":
            model_info["lambda_away"],

        "status":
            "REGISTERED",

        "eligible_for_activation":
            False,

        "registered_at":
            (
                existing.get(
                    "registered_at"
                )
                if existing
                else now_utc()
            ),

        "last_validated_at":
            now_utc()

    }


    # --------------------------------------------------------
    # PRESERVE ACTIVE STATUS
    # --------------------------------------------------------

    if (
        registry.get(
            "active_model"
        )
        ==
        model_version
    ):

        model_record[
            "status"
        ] = "ACTIVE"


    models[
        model_version
    ] = model_record


# ============================================================
# ACTIVATE DEFAULT MODEL
# ============================================================

def ensure_active_model(
    registry,
    current_model_version
):

    active_model = registry.get(
        "active_model"
    )


    # --------------------------------------------------------
    # NO ACTIVE MODEL
    # --------------------------------------------------------

    if not active_model:

        if (
            current_model_version
            ==
            DEFAULT_ACTIVE_MODEL
        ):

            registry[
                "active_model"
            ] = DEFAULT_ACTIVE_MODEL

            registry[
                "models"
            ][
                DEFAULT_ACTIVE_MODEL
            ][
                "status"
            ] = "ACTIVE"

            return (
                DEFAULT_ACTIVE_MODEL,
                "INITIALIZED"
            )


        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Aktif model yok ve mevcut model "
            f"{DEFAULT_ACTIVE_MODEL} değil."
        )


    # --------------------------------------------------------
    # ACTIVE MODEL MUST EXIST
    # --------------------------------------------------------

    if active_model not in registry.get(
        "models",
        {}
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            f"Aktif model registry'de bulunamadı: "
            f"{active_model}"
        )


    # --------------------------------------------------------
    # NEVER AUTO-SWITCH
    # --------------------------------------------------------

    if (
        current_model_version
        !=
        active_model
    ):

        registry[
            "models"
        ][
            current_model_version
        ][
            "status"
        ] = "CANDIDATE"


        registry[
            "models"
        ][
            current_model_version
        ][
            "eligible_for_activation"
        ] = False


        return (
            active_model,
            "PRESERVED"
        )


    # --------------------------------------------------------
    # ACTIVE MODEL STILL VALID
    # --------------------------------------------------------

    registry[
        "models"
    ][
        active_model
    ][
        "status"
    ] = "ACTIVE"


    return (
        active_model,
        "UNCHANGED"
    )


# ============================================================
# HISTORY
# ============================================================

def append_history(
    registry,
    model_version,
    action
):

    history = registry.setdefault(
        "history",
        []
    )


    # --------------------------------------------------------
    # DUPLICATE HISTORY PROTECTION
    # --------------------------------------------------------

    for item in history:

        if (
            item.get(
                "model_version"
            )
            ==
            model_version

            and

            item.get(
                "action"
            )
            ==
            action
        ):

            return


    history.append({

        "timestamp":
            now_utc(),

        "model_version":
            model_version,

        "action":
            action

    })


# ============================================================
# SAVE REGISTRY
# ============================================================

def save_registry(
    registry
):

    os.makedirs(
        OUTPUT_DIRECTORY,
        exist_ok=True
    )


    registry[
        "generated_at"
    ] = now_utc()


    temporary_file = (
        REGISTRY_FILE
        +
        ".tmp"
    )


    with open(
        temporary_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            registry,
            f,
            ensure_ascii=False,
            indent=2
        )


    os.replace(
        temporary_file,
        REGISTRY_FILE
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("")
    print("==========================================")
    print("STATSHUB MODEL REGISTRY ENGINE V1")
    print("==========================================")
    print("")


    print(
        "Model file:",
        MODEL_FILE
    )

    print(
        "Registry file:",
        REGISTRY_FILE
    )

    print("")


    # --------------------------------------------------------
    # LOAD CURRENT MODEL
    # --------------------------------------------------------

    model = load_json(
        MODEL_FILE
    )


    # --------------------------------------------------------
    # VALIDATE CURRENT MODEL
    # --------------------------------------------------------

    model_info = validate_model(
        model
    )


    current_model_version = (
        model_info["model_version"]
    )


    print(
        "Current model:",
        current_model_version
    )

    print(
        "Source:",
        model_info["source"]
    )

    print(
        "Match:",
        model_info["home"],
        "vs",
        model_info["away"]
    )

    print(
        "Home Lambda:",
        model_info["lambda_home"]
    )

    print(
        "Away Lambda:",
        model_info["lambda_away"]
    )

    print("")


    # --------------------------------------------------------
    # LOAD REGISTRY
    # --------------------------------------------------------

    registry = load_registry()


    # --------------------------------------------------------
    # SOURCE VALIDATION
    # --------------------------------------------------------

    if registry.get(
        "source",
        SOURCE_REQUIRED
    ) != SOURCE_REQUIRED:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Registry source StatsHub değil."
        )


    registry[
        "registry_version"
    ] = REGISTRY_VERSION


    # --------------------------------------------------------
    # REGISTER CURRENT MODEL
    # --------------------------------------------------------

    register_model(
        registry,
        model_info
    )


    # --------------------------------------------------------
    # ACTIVE MODEL
    # --------------------------------------------------------

    active_model, action = (
        ensure_active_model(
            registry,
            current_model_version
        )
    )


    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    append_history(
        registry,
        current_model_version,
        action
    )


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    save_registry(
        registry
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    saved_registry = load_json(
        REGISTRY_FILE
    )


    if (
        saved_registry.get(
            "active_model"
        )
        !=
        active_model
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Active model doğrulaması başarısız."
        )


    if current_model_version not in (
        saved_registry.get(
            "models",
            {}
        )
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Current model registry'ye kaydedilmedi."
        )


    registered_model = (
        saved_registry[
            "models"
        ][
            current_model_version
        ]
    )


    if registered_model.get(
        "source"
    ) != SOURCE_REQUIRED:

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Registered model StatsHub değil."
        )


    if not os.path.exists(
        REGISTRY_FILE
    ):

        raise SystemExit(
            "MODEL REGISTRY ERROR: "
            "Registry dosyası oluşturulamadı."
        )


    # ========================================================
    # OUTPUT
    # ========================================================

    print("")
    print("==========================================")
    print("MODEL REGISTRY VALIDATION")
    print("==========================================")
    print("")

    print(
        "Current model:",
        current_model_version
    )

    print(
        "Active model:",
        active_model
    )

    print(
        "Action:",
        action
    )

    print(
        "Registered models:",
        len(
            saved_registry.get(
                "models",
                {}
            )
        )
    )

    print(
        "Registry:",
        REGISTRY_FILE
    )

    print("")


    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    print(
        "Prediction records were not modified."
    )

    print(
        "Model lock was not modified."
    )

    print(
        "Performance records were not modified."
    )

    print(
        "Calibration records were not modified."
    )

    print("")


    # --------------------------------------------------------
    # ACTIVE MODEL RULE
    # --------------------------------------------------------

    if active_model == current_model_version:

        print(
            "ACTIVE MODEL:",
            active_model
        )

    else:

        print(
            "ACTIVE MODEL PRESERVED:",
            active_model
        )

        print(
            "Candidate model:",
            current_model_version
        )

        print(
            "Automatic model switch: DISABLED"
        )


    print("")

    print(
        "VALIDATION: PASS"
    )

    print("")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
