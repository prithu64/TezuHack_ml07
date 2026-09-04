from pathlib import Path
import json

import pandas as pd
import joblib
import xgboost as xgb

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score,
    RandomizedSearchCV
)

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
    LabelEncoder
)

from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression

from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier
)

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    confusion_matrix
)


# ============================================================
# 1. FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "student_data_100000.csv"

MODEL_PATH = BASE_DIR / "student_risk_model.pkl"

ENCODER_PATH = BASE_DIR / "label_encoder.pkl"

RESULTS_PATH = BASE_DIR / "model_results.json"

FEATURES_PATH = BASE_DIR / "feature_names.pkl"


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("=" * 60)
print("LOADING DATASET")
print("=" * 60)

df = pd.read_csv(DATA_PATH)

print("\nDataset Shape:")
print(df.shape)

print("\nDataset Columns:")
print(df.columns.tolist())

print("\nMissing Values:")
print(df.isnull().sum())


# ============================================================
# 3. TARGET DISTRIBUTION
# ============================================================

target = "risk_category"

print("\n" + "=" * 60)
print("TARGET DISTRIBUTION")
print("=" * 60)

print("\nClass Counts:")
print(df[target].value_counts())

print("\nClass Percentage:")

print(
    (df[target]
     .value_counts(normalize=True) * 100)
    .round(2)
)


# ============================================================
# 4. ENCODE TARGET LABELS
# ============================================================

print("\n" + "=" * 60)
print("ENCODING TARGET")
print("=" * 60)

label_encoder = LabelEncoder()

y = label_encoder.fit_transform(
    df[target]
)

print("\nClasses:")
print(label_encoder.classes_)

print("\nClass Mapping:")

target_mapping = {

    class_name: int(encoded_value)

    for encoded_value, class_name

    in enumerate(label_encoder.classes_)
}

print(target_mapping)


# ============================================================
# 5. FEATURE ENGINEERING
# ============================================================

print("\n" + "=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)


# ------------------------------------------------------------
# Study and Attendance Relationship
# ------------------------------------------------------------

df["study_attendance_score"] = (

    df["study_hours"]

    *

    df["attendance"]
)


# ------------------------------------------------------------
# Academic Performance
# ------------------------------------------------------------

df["performance_score"] = (

    df["previous_grade"]

    *

    df["assignments_completed_pct"]
)


# ------------------------------------------------------------
# Failure Risk
# ------------------------------------------------------------

df["failure_risk"] = (

    df["past_failures"]

    /

    (
        df["previous_grade"] + 1
    )
)


# ------------------------------------------------------------
# Study Efficiency
# ------------------------------------------------------------

df["study_efficiency"] = (

    df["assignments_completed_pct"]

    /

    (
        df["study_hours"] + 1
    )
)


# ------------------------------------------------------------
# Student Engagement
# ------------------------------------------------------------

df["engagement_score"] = (

    df["attendance"]

    +

    df["assignments_completed_pct"]

) / 2


# ------------------------------------------------------------
# Grade and Attendance Score
# ------------------------------------------------------------

df["grade_attendance_score"] = (

    df["previous_grade"]

    *

    df["attendance"]
)


# ------------------------------------------------------------
# Student Effort Score
# ------------------------------------------------------------

df["effort_score"] = (

    df["study_hours"]

    *

    df["assignments_completed_pct"]
)


# ------------------------------------------------------------
# Failure Impact
# ------------------------------------------------------------

df["failure_impact"] = (

    df["past_failures"]

    *

    (
        100 - df["attendance"]
    )
)


# ------------------------------------------------------------
# Grade Efficiency
# ------------------------------------------------------------

df["grade_efficiency"] = (

    df["previous_grade"]

    /

    (
        df["study_hours"] + 1
    )
)


# ------------------------------------------------------------
# Assignment Gap
# ------------------------------------------------------------

df["assignment_gap"] = (

    100

    -

    df["assignments_completed_pct"]
)


print("\nNew Features Created:")

new_features = [

    "study_attendance_score",

    "performance_score",

    "failure_risk",

    "study_efficiency",

    "engagement_score",

    "grade_attendance_score",

    "effort_score",

    "failure_impact",

    "grade_efficiency",

    "assignment_gap"
]

for feature in new_features:

    print("-", feature)


# ============================================================
# 6. DEFINE FEATURES
# ============================================================


# Numerical Features

numeric_features = [

    "attendance",

    "study_hours",

    "past_failures",

    "assignments_completed_pct",

    "previous_grade",


    # Engineered Features

    "study_attendance_score",

    "performance_score",

    "failure_risk",

    "study_efficiency",

    "engagement_score",

    "grade_attendance_score",

    "effort_score",

    "failure_impact",

    "grade_efficiency",

    "assignment_gap"
]


# Categorical Features

categorical_features = [

    "parental_education",

    "family_income",

    "extracurricular",

    "internet_access"
]


# Combine All Features

features = (

    numeric_features

    +

    categorical_features
)


X = df[features]


print("\nTotal Features Used:", len(features))


# ============================================================
# 7. PREPROCESSING
# ============================================================

print("\n" + "=" * 60)
print("DATA PREPROCESSING")
print("=" * 60)


# Numerical Pipeline

numeric_pipeline = Pipeline([

    (

        "imputer",

        SimpleImputer(
            strategy="median"
        )

    ),

    (

        "scaler",

        StandardScaler()

    )
])


# Categorical Pipeline

categorical_pipeline = Pipeline([

    (

        "imputer",

        SimpleImputer(
            strategy="most_frequent"
        )

    ),

    (

        "onehot",

        OneHotEncoder(
            handle_unknown="ignore"
        )

    )
])


# Combine Pipelines

preprocessor = ColumnTransformer([

    (

        "num",

        numeric_pipeline,

        numeric_features

    ),

    (

        "cat",

        categorical_pipeline,

        categorical_features

    )
])


# ============================================================
# 8. TRAIN TEST SPLIT
# ============================================================

print("\n" + "=" * 60)
print("TRAIN TEST SPLIT")
print("=" * 60)


X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.20,

    random_state=42,

    stratify=y
)


print("\nTraining Shape:")

print(X_train.shape)


print("\nTesting Shape:")

print(X_test.shape)


# ============================================================
# 9. CROSS VALIDATION
# ============================================================

cv = StratifiedKFold(

    n_splits=3,

    shuffle=True,

    random_state=42
)


# ============================================================
# 10. DEFINE MODELS
# ============================================================

print("\n" + "=" * 60)
print("INITIALIZING MODELS")
print("=" * 60)


models = {


    # --------------------------------------------------------
    # Logistic Regression
    # --------------------------------------------------------

    "Logistic Regression":

    LogisticRegression(

        max_iter=3000,

        random_state=42
    ),


    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    "Random Forest":

    RandomForestClassifier(

        n_estimators=400,

        max_depth=None,

        min_samples_split=2,

        min_samples_leaf=1,

        class_weight="balanced",

        random_state=42,

        n_jobs=-1
    ),


    # --------------------------------------------------------
    # Extra Trees
    # --------------------------------------------------------

    "Extra Trees":

    ExtraTreesClassifier(

        n_estimators=400,

        max_depth=None,

        min_samples_split=2,

        min_samples_leaf=1,

        class_weight="balanced",

        random_state=42,

        n_jobs=-1
    ),


    # --------------------------------------------------------
    # Improved XGBoost
    # --------------------------------------------------------

    "XGBoost":

    xgb.XGBClassifier(

        n_estimators=500,

        learning_rate=0.03,

        max_depth=5,

        min_child_weight=2,

        subsample=0.9,

        colsample_bytree=0.9,

        gamma=0.05,

        reg_alpha=0.01,

        reg_lambda=1.5,

        objective="multi:softprob",

        eval_metric="mlogloss",

        random_state=42,

        verbosity=0,

        n_jobs=-1
    )
}


# ============================================================
# 11. TRAIN AND COMPARE MODELS
# ============================================================

print("\n" + "=" * 60)
print("MODEL TRAINING")
print("=" * 60)


results = {}

best_model_name = None

best_macro_f1 = -1


for name, model in models.items():

    print("\n")

    print("=" * 60)

    print(f"TRAINING: {name}")

    print("=" * 60)


    # Create Pipeline

    pipeline = Pipeline([

        (

            "preprocessor",

            preprocessor

        ),

        (

            "model",

            model

        )
    ])


    # Train Model

    print("\nTraining model...")

    pipeline.fit(

        X_train,

        y_train
    )


    # Predictions

    predictions = pipeline.predict(

        X_test
    )


    # Accuracy

    accuracy = accuracy_score(

        y_test,

        predictions
    )


    # Weighted F1

    weighted_f1 = f1_score(

        y_test,

        predictions,

        average="weighted"
    )


    # Macro F1

    macro_f1 = f1_score(

        y_test,

        predictions,

        average="macro"
    )


    # Print Results

    print("\nMODEL RESULTS")

    print("-" * 40)

    print(f"Accuracy: {accuracy:.4f}")

    print(f"Weighted F1: {weighted_f1:.4f}")

    print(f"Macro F1: {macro_f1:.4f}")


    # Classification Report

    print("\nClassification Report:")

    print(

        classification_report(

            y_test,

            predictions,

            target_names=label_encoder.classes_,

            zero_division=0
        )
    )


    # Confusion Matrix

    print("\nConfusion Matrix:")

    print(

        confusion_matrix(

            y_test,

            predictions
        )
    )


    # --------------------------------------------------------
    # Cross Validation
    # --------------------------------------------------------

    print("\nRunning Cross Validation...")


    cv_scores = cross_val_score(

        pipeline,

        X,

        y,

        cv=cv,

        scoring="f1_macro",

        n_jobs=-1
    )


    cv_mean = cv_scores.mean()


    print(

        f"Cross Validation Macro F1: {cv_mean:.4f}"
    )


    # --------------------------------------------------------
    # Save Results
    # --------------------------------------------------------

    results[name] = {

        "accuracy":

        float(accuracy),


        "weighted_f1":

        float(weighted_f1),


        "macro_f1":

        float(macro_f1),


        "cv_macro_f1_mean":

        float(cv_mean)
    }


    # --------------------------------------------------------
    # Select Best Model
    # --------------------------------------------------------

    if macro_f1 > best_macro_f1:

        best_macro_f1 = macro_f1

        best_model_name = name


# ============================================================
# 12. DISPLAY INITIAL RESULTS
# ============================================================

print("\n")

print("=" * 60)

print("INITIAL MODEL RESULTS")

print("=" * 60)


print(

    json.dumps(

        results,

        indent=4
    )
)


print(

    f"\nBest Initial Model: {best_model_name}"
)


print(

    f"Best Macro F1: {best_macro_f1:.4f}"
)


# ============================================================
# 13. XGBOOST HYPERPARAMETER TUNING
# ============================================================

print("\n")

print("=" * 60)

print("XGBOOST HYPERPARAMETER TUNING")

print("=" * 60)


# Base XGBoost Model

xgb_base = xgb.XGBClassifier(

    objective="multi:softprob",

    eval_metric="mlogloss",

    random_state=42,

    n_jobs=-1,

    verbosity=0
)


# XGBoost Pipeline

xgb_pipeline = Pipeline([

    (

        "preprocessor",

        preprocessor

    ),

    (

        "model",

        xgb_base

    )
])


# Parameter Search Space

param_distributions = {


    "model__n_estimators":

    [

        200,

        300,

        400,

        500,

        600
    ],


    "model__max_depth":

    [

        3,

        4,

        5,

        6,

        7
    ],


    "model__learning_rate":

    [

        0.01,

        0.03,

        0.05,

        0.07,

        0.1
    ],


    "model__subsample":

    [

        0.7,

        0.8,

        0.9,

        1.0
    ],


    "model__colsample_bytree":

    [

        0.7,

        0.8,

        0.9,

        1.0
    ],


    "model__min_child_weight":

    [

        1,

        2,

        3,

        5
    ],


    "model__gamma":

    [

        0,

        0.05,

        0.1,

        0.2
    ],


    "model__reg_alpha":

    [

        0,

        0.01,

        0.05,

        0.1
    ],


    "model__reg_lambda":

    [

        0.5,

        1,

        1.5,

        2
    ]
}


# Random Search

random_search = RandomizedSearchCV(

    estimator=xgb_pipeline,

    param_distributions=param_distributions,

    n_iter=20,

    scoring="f1_macro",

    cv=3,

    verbose=2,

    random_state=42,

    n_jobs=-1
)


print("\nStarting XGBoost tuning...")

print("This may take some time.")


# Train Random Search

random_search.fit(

    X_train,

    y_train
)


# ============================================================
# 14. BEST XGBOOST PARAMETERS
# ============================================================

print("\n")

print("=" * 60)

print("BEST XGBOOST PARAMETERS")

print("=" * 60)


print(

    random_search.best_params_
)


print(

    f"\nBest CV Macro F1: "
    f"{random_search.best_score_:.4f}"
)


# ============================================================
# 15. TEST TUNED XGBOOST
# ============================================================

best_xgb_pipeline = (

    random_search.best_estimator_
)


xgb_predictions = (

    best_xgb_pipeline.predict(

        X_test
    )
)


xgb_accuracy = accuracy_score(

    y_test,

    xgb_predictions
)


xgb_weighted_f1 = f1_score(

    y_test,

    xgb_predictions,

    average="weighted"
)


xgb_macro_f1 = f1_score(

    y_test,

    xgb_predictions,

    average="macro"
)


print("\n")

print("=" * 60)

print("TUNED XGBOOST RESULTS")

print("=" * 60)


print(

    f"\nAccuracy: "
    f"{xgb_accuracy:.4f}"
)


print(

    f"Weighted F1: "
    f"{xgb_weighted_f1:.4f}"
)


print(

    f"Macro F1: "
    f"{xgb_macro_f1:.4f}"
)


# Classification Report

print("\nClassification Report:")

print(

    classification_report(

        y_test,

        xgb_predictions,

        target_names=label_encoder.classes_,

        zero_division=0
    )
)


# Confusion Matrix

print("\nConfusion Matrix:")

print(

    confusion_matrix(

        y_test,

        xgb_predictions
    )
)


# ============================================================
# 16. ADD TUNED XGBOOST TO RESULTS
# ============================================================

results["Tuned XGBoost"] = {

    "accuracy":

    float(xgb_accuracy),


    "weighted_f1":

    float(xgb_weighted_f1),


    "macro_f1":

    float(xgb_macro_f1),


    "cv_macro_f1_mean":

    float(random_search.best_score_)
}


# ============================================================
# 17. CHECK IF TUNED XGBOOST IS BEST
# ============================================================

if xgb_macro_f1 > best_macro_f1:

    best_macro_f1 = xgb_macro_f1

    best_model_name = "Tuned XGBoost"

    best_pipeline = best_xgb_pipeline

else:

    best_pipeline = None


# ============================================================
# 18. FINAL RESULTS
# ============================================================

print("\n")

print("=" * 60)

print("FINAL MODEL COMPARISON")

print("=" * 60)


print(

    json.dumps(

        results,

        indent=4
    )
)


print(

    f"\nFINAL BEST MODEL: "
    f"{best_model_name}"
)


print(

    f"FINAL BEST MACRO F1: "
    f"{best_macro_f1:.4f}"
)


# ============================================================
# 19. RETRAIN BEST MODEL
# ============================================================

print("\n")

print("=" * 60)

print("RETRAINING BEST MODEL ON FULL DATA")

print("=" * 60)


# If tuned XGBoost wins

if best_model_name == "Tuned XGBoost":

    final_pipeline = best_xgb_pipeline

    print("\nUsing Tuned XGBoost")

else:

    best_model = models[best_model_name]

    final_pipeline = Pipeline([

        (

            "preprocessor",

            preprocessor

        ),

        (

            "model",

            best_model

        )
    ])

    print(

        f"\nUsing {best_model_name}"
    )


# Train using complete dataset

print("\nTraining final model...")

final_pipeline.fit(

    X,

    y
)


# ============================================================
# 20. SAVE MODEL
# ============================================================

print("\n")

print("=" * 60)

print("SAVING MODEL FILES")

print("=" * 60)


# Save trained pipeline

joblib.dump(

    final_pipeline,

    MODEL_PATH
)


# Save Label Encoder

joblib.dump(

    label_encoder,

    ENCODER_PATH
)


# Save Feature Names

joblib.dump(

    final_pipeline
    .named_steps["preprocessor"]
    .get_feature_names_out(),

    FEATURES_PATH
)


# Save Results

with open(

    RESULTS_PATH,

    "w"

) as file:

    json.dump(

        results,

        file,

        indent=4
    )


# ============================================================
# 21. DISPLAY SAVED FILES
# ============================================================

print("\nSaved Files:")

print("-" * 40)

print(

    "Model:",
    MODEL_PATH.name
)


print(

    "Label Encoder:",
    ENCODER_PATH.name
)


print(

    "Feature Names:",
    FEATURES_PATH.name
)


print(

    "Results:",
    RESULTS_PATH.name
)


# ============================================================
# 22. COMPLETION MESSAGE
# ============================================================

print("\n")

print("=" * 60)

print("TRAINING COMPLETED SUCCESSFULLY")

print("=" * 60)