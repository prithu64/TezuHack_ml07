from pathlib import Path
import json

import pandas as pd
import joblib
import xgboost as xgb

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score
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
from sklearn.ensemble import RandomForestClassifier

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

print("\nDataset shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())


# ============================================================
# 3. TARGET DISTRIBUTION
# ============================================================

target = "risk_category"

print("\n" + "=" * 60)
print("TARGET DISTRIBUTION")
print("=" * 60)

print("\nOriginal target distribution:")
print(df[target].value_counts())

print("\nTarget distribution percentage:")
print(
    (df[target].value_counts(normalize=True) * 100).round(2)
)


# ============================================================
# 4. ENCODE TARGET LABELS
# ============================================================

print("\n" + "=" * 60)
print("ENCODING TARGET LABELS")
print("=" * 60)

label_encoder = LabelEncoder()

y = label_encoder.fit_transform(df[target])

print("\nTarget classes:")
print(label_encoder.classes_)

print("\nTarget mapping:")

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


# Interaction between attendance and study hours
df["study_attendance_score"] = (
    df["study_hours"] * df["attendance"]
)


# Academic performance score
df["performance_score"] = (
    df["previous_grade"] *
    df["assignments_completed_pct"]
)


# Failure risk score
df["failure_risk"] = (
    df["past_failures"] /
    (df["previous_grade"] + 1)
)


# Study efficiency
df["study_efficiency"] = (
    df["assignments_completed_pct"] /
    (df["study_hours"] + 1)
)


print("\nNew features created:")

print("- study_attendance_score")
print("- performance_score")
print("- failure_risk")
print("- study_efficiency")


# ============================================================
# 6. SELECT FEATURES
# ============================================================

features = [

    # Original numerical features
    "attendance",
    "study_hours",
    "past_failures",
    "assignments_completed_pct",
    "previous_grade",

    # Original categorical features
    "parental_education",
    "family_income",
    "extracurricular",
    "internet_access",

    # Engineered features
    "study_attendance_score",
    "performance_score",
    "failure_risk",
    "study_efficiency"
]


X = df[features]

print("\nTotal features used:", len(features))

print("\nFeatures:")
print(features)


# ============================================================
# 7. NUMERIC AND CATEGORICAL FEATURES
# ============================================================

numeric_features = [

    "attendance",
    "study_hours",
    "past_failures",
    "assignments_completed_pct",
    "previous_grade",

    "study_attendance_score",
    "performance_score",
    "failure_risk",
    "study_efficiency"
]


categorical_features = [

    "parental_education",
    "family_income",
    "extracurricular",
    "internet_access"
]


# ============================================================
# 8. PREPROCESSING PIPELINES
# ============================================================

print("\n" + "=" * 60)
print("DATA PREPROCESSING")
print("=" * 60)


# Numerical preprocessing

numeric_pipeline = Pipeline([

    (
        "imputer",
        SimpleImputer(strategy="median")
    ),

    (
        "scaler",
        StandardScaler()
    )
])


# Categorical preprocessing

categorical_pipeline = Pipeline([

    (
        "imputer",
        SimpleImputer(strategy="most_frequent")
    ),

    (
        "onehot",
        OneHotEncoder(
            handle_unknown="ignore"
        )
    )
])


# Combine preprocessing

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
# 9. TRAIN TEST SPLIT
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


print("\nTraining data shape:", X_train.shape)

print("Testing data shape:", X_test.shape)


# ============================================================
# 10. CROSS VALIDATION SETUP
# ============================================================

cv = StratifiedKFold(

    n_splits=5,

    shuffle=True,

    random_state=42
)


# ============================================================
# 11. DEFINE MODELS
# ============================================================

print("\n" + "=" * 60)
print("INITIALIZING MODELS")
print("=" * 60)


models = {


    # --------------------------------------------------------
    # Logistic Regression
    # --------------------------------------------------------

    "Logistic Regression": LogisticRegression(

        max_iter=2000,

        random_state=42
    ),


    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    "Random Forest": RandomForestClassifier(

        n_estimators=300,

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

    "XGBoost": xgb.XGBClassifier(

        n_estimators=400,

        learning_rate=0.05,

        max_depth=6,

        min_child_weight=2,

        subsample=0.85,

        colsample_bytree=0.85,

        gamma=0.1,

        reg_alpha=0.05,

        reg_lambda=1.0,

        random_state=42,

        eval_metric="mlogloss",

        verbosity=0,

        n_jobs=-1
    )
}


# ============================================================
# 12. TRAIN AND COMPARE MODELS
# ============================================================

print("\n" + "=" * 60)
print("MODEL TRAINING AND EVALUATION")
print("=" * 60)


results = {}


best_model_name = None

best_macro_f1 = -1


for name, model in models.items():

    print("\n")

    print("=" * 60)

    print(f"TRAINING MODEL: {name}")

    print("=" * 60)


    # --------------------------------------------------------
    # Create Pipeline
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Train Model
    # --------------------------------------------------------

    print("\nTraining model...")

    pipeline.fit(
        X_train,
        y_train
    )


    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    predictions = pipeline.predict(
        X_test
    )


    # --------------------------------------------------------
    # Calculate Accuracy
    # --------------------------------------------------------

    accuracy = accuracy_score(

        y_test,

        predictions
    )


    # --------------------------------------------------------
    # Weighted F1 Score
    # --------------------------------------------------------

    weighted_f1 = f1_score(

        y_test,

        predictions,

        average="weighted"
    )


    # --------------------------------------------------------
    # Macro F1 Score
    # --------------------------------------------------------

    macro_f1 = f1_score(

        y_test,

        predictions,

        average="macro"
    )


    # --------------------------------------------------------
    # Display Results
    # --------------------------------------------------------

    print("\nMODEL PERFORMANCE")

    print("-" * 40)

    print(f"Accuracy: {accuracy:.4f}")

    print(f"Weighted F1 Score: {weighted_f1:.4f}")

    print(f"Macro F1 Score: {macro_f1:.4f}")


    # --------------------------------------------------------
    # Classification Report
    # --------------------------------------------------------

    print("\nClassification Report:")

    print(

        classification_report(

            y_test,

            predictions,

            target_names=label_encoder.classes_,

            zero_division=0
        )
    )


    # --------------------------------------------------------
    # Confusion Matrix
    # --------------------------------------------------------

    print("Confusion Matrix:")

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


    print(f"Cross Validation Macro F1: {cv_mean:.4f}")


    # --------------------------------------------------------
    # Save Results
    # --------------------------------------------------------

    results[name] = {

        "accuracy": float(accuracy),

        "weighted_f1": float(weighted_f1),

        "macro_f1": float(macro_f1),

        "cv_macro_f1_mean": float(cv_mean)
    }


    # --------------------------------------------------------
    # Select Best Model
    # --------------------------------------------------------

    if macro_f1 > best_macro_f1:

        best_macro_f1 = macro_f1

        best_model_name = name


# ============================================================
# 13. DISPLAY BEST MODEL
# ============================================================

print("\n")

print("=" * 60)

print("BEST MODEL")

print("=" * 60)


print(f"\nBest Model: {best_model_name}")

print(f"Best Macro F1 Score: {best_macro_f1:.4f}")


print("\nAll Model Results:")

print(

    json.dumps(

        results,

        indent=4
    )
)


# ============================================================
# 14. RETRAIN BEST MODEL ON FULL DATASET
# ============================================================

print("\n")

print("=" * 60)

print("RETRAINING BEST MODEL")

print("=" * 60)


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


print("\nTraining best model using full dataset...")


final_pipeline.fit(

    X,

    y
)


# ============================================================
# 15. SAVE MODEL
# ============================================================

print("\n")

print("=" * 60)

print("SAVING MODEL FILES")

print("=" * 60)


# Save trained model

joblib.dump(

    final_pipeline,

    MODEL_PATH
)


# Save label encoder

joblib.dump(

    label_encoder,

    ENCODER_PATH
)


# Save feature names after preprocessing

joblib.dump(

    final_pipeline
    .named_steps["preprocessor"]
    .get_feature_names_out(),

    FEATURES_PATH
)


# Save model results

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
# 16. DISPLAY SAVED FILES
# ============================================================

print("\nSaved Files:")

print("-" * 40)

print(f"Model: {MODEL_PATH.name}")

print(f"Label Encoder: {ENCODER_PATH.name}")

print(f"Feature Names: {FEATURES_PATH.name}")

print(f"Model Results: {RESULTS_PATH.name}")


# ============================================================
# 17. FINAL MESSAGE
# ============================================================

print("\n")

print("=" * 60)

print("TRAINING COMPLETED SUCCESSFULLY")

print("=" * 60)