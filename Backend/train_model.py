from pathlib import Path
import json

import pandas as pd
import joblib
import xgboost as xgb

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    confusion_matrix
)



#1 . FILE PATHS
BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = BASE_DIR / "student_data_100000.csv"
MODEL_PATH = BASE_DIR / "student_risk_model.pkl"
ENCODER_PATH = BASE_DIR / "label_encoder.pkl"
RESULTS_PATH = BASE_DIR / "model_results.json"
FEATURES_PATH = BASE_DIR / "feature_names.pkl"


# 2. LOAD DATASET
df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())



# 3. TARGET DISTRIBUTION
target = "risk_category"

print("\nOriginal target distribution:")
print(df[target].value_counts())


# 4. ENCODE TARGET LABELS
label_encoder = LabelEncoder()

y = label_encoder.fit_transform(df[target])

print("\nTarget classes:")
print(label_encoder.classes_)

print("\nTarget mapping:")
print({
    class_name: int(encoded_value)
    for encoded_value, class_name
    in enumerate(label_encoder.classes_)
})

# 5. SELECT FEATURES
features = [
    "attendance",
    "study_hours",
    "past_failures",
    "assignments_completed_pct",
    "parental_education",
    "family_income",
    "extracurricular",
    "internet_access",
    "previous_grade"
]

X = df[features]

# 6. NUMERIC AND CATEGORICAL FEATURES
numeric_features = [
    "attendance",
    "study_hours",
    "past_failures",
    "assignments_completed_pct",
    "previous_grade"
]

categorical_features = [
    "parental_education",
    "family_income",
    "extracurricular",
    "internet_access"
]

# 7. PREPROCESSING
numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("num", numeric_pipeline, numeric_features),
    ("cat", categorical_pipeline, categorical_features)
])

# 8. TRAIN-TEST SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 9. MODELS
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    ),

    "XGBoost": xgb.XGBClassifier(
        n_estimators=100,
        random_state=42,
        eval_metric="mlogloss",
        verbosity=0
    )
}

# 10. TRAIN AND COMPARE MODELS
results = {}

best_model_name = None
best_macro_f1 = -1

for name, model in models.items():

    print(f"\n{'=' * 50}")
    print(f"Training: {name}")
    print(f"{'=' * 50}")

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model)
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    weighted_f1 = f1_score(
        y_test,
        predictions,
        average="weighted"
    )

    macro_f1 = f1_score(
        y_test,
        predictions,
        average="macro"
    )

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")

    print("\nClassification report:")
    print(
        classification_report(
            y_test,
            predictions,
            target_names=label_encoder.classes_,
            zero_division=0
        )
    )

    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions))

    results[name] = {
        "accuracy": float(accuracy),
        "weighted_f1": float(weighted_f1),
        "macro_f1": float(macro_f1)
    }

    # Select best model using macro F1
    if macro_f1 > best_macro_f1:
        best_macro_f1 = macro_f1
        best_model_name = name


# 11. DISPLAY BEST MODEL
print(f"\nBest model: {best_model_name}")

print("\nAll model results:")
print(json.dumps(results, indent=4))



# 12. RETRAIN BEST MODEL ON FULL DATASET
best_model = models[best_model_name]

final_pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", best_model)
])

final_pipeline.fit(X, y)


# 13. SAVE MODEL AND SUPPORTING FILES
joblib.dump(final_pipeline, MODEL_PATH)

joblib.dump(label_encoder, ENCODER_PATH)

joblib.dump(
    final_pipeline.named_steps["preprocessor"].get_feature_names_out(),
    FEATURES_PATH
)

with open(RESULTS_PATH, "w") as file:
    json.dump(results, file, indent=4)


print("\nSaved files:")
print(MODEL_PATH.name)
print(ENCODER_PATH.name)
print(FEATURES_PATH.name)
print(RESULTS_PATH.name)

print("\nTraining completed successfully.")