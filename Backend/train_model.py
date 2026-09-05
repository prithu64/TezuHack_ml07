from pathlib import Path
import json
import joblib
import pandas as pd

from xgboost import XGBClassifier

from sklearn.model_selection import train_test_split
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
    f1_score,
    classification_report,
    confusion_matrix
)



# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "student_data_100000.csv"
MODEL_PATH = BASE_DIR / "student_risk_model.pkl"
ENCODER_PATH = BASE_DIR / "label_encoder.pkl"
RESULTS_PATH = BASE_DIR / "model_results.json"
FEATURES_PATH = BASE_DIR / "feature_names.pkl"


# Load dataset
df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)
print("Dataset columns:", list(df.columns))
print("\nMissing values:")
print(df.isnull().sum())



# Target encoding
target_column = "risk_category"

label_encoder = LabelEncoder()

y = label_encoder.fit_transform(df[target_column])

print("\nTarget classes:")
print(label_encoder.classes_)

print("\nTarget mapping:")
for class_name, encoded_value in zip(
    label_encoder.classes_,
    range(len(label_encoder.classes_))
):
    print(f"{class_name} -> {encoded_value}")



# Input features
# final_score is intentionally excluded because it
# may have been used to create risk_category.
# Including it could cause target leakage.

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

X = df[features].copy()



# Feature types
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



# Preprocessing
numeric_transformer = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        )
    ]
)

categorical_transformer = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore")
        )
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "num",
            numeric_transformer,
            numeric_features
        ),
        (
            "cat",
            categorical_transformer,
            categorical_features
        )
    ]
)



# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))



# Models
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

    "XGBoost": XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="mlogloss"
    )
}



# Train and evaluate models
results = {}

best_model_name = None
best_macro_f1 = -1

for model_name, model in models.items():

    print("\n" + "=" * 60)
    print(f"Training {model_name}")
    print("=" * 60)

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model)
        ]
    )

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    weighted_f1 = f1_score(
        y_test,
        y_pred,
        average="weighted"
    )

    macro_f1 = f1_score(
        y_test,
        y_pred,
        average="macro"
    )

    report = classification_report(
        y_test,
        y_pred,
        target_names=label_encoder.classes_,
        output_dict=True
    )

    matrix = confusion_matrix(
        y_test,
        y_pred
    )

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=label_encoder.classes_
        )
    )

    print("Confusion Matrix:")
    print(matrix)

    results[model_name] = {
        "accuracy": round(float(accuracy), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "macro_f1": round(float(macro_f1), 4),
        "classification_report": report,
        "confusion_matrix": matrix.tolist()
    }

    if macro_f1 > best_macro_f1:
        best_macro_f1 = macro_f1
        best_model_name = model_name


# Retrain best model on complete dataset
print("\n" + "=" * 60)
print(f"Best model: {best_model_name}")
print("=" * 60)

best_model = models[best_model_name]

final_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", best_model)
    ]
)

final_pipeline.fit(X, y)



# Save model and supporting files
joblib.dump(final_pipeline, MODEL_PATH)

joblib.dump(
    label_encoder,
    ENCODER_PATH
)

# IMPORTANT:
# Save the original input feature names,
# not the transformed feature names.

joblib.dump(
    features,
    FEATURES_PATH
)

with open(RESULTS_PATH, "w") as file:
    json.dump(
        {
            "best_model": best_model_name,
            "features": features,
            "results": results
        },
        file,
        indent=4
    )

print("\nFiles saved successfully:")
print(MODEL_PATH)
print(ENCODER_PATH)
print(FEATURES_PATH)
print(RESULTS_PATH)

print("\nOriginal input features saved:")
print(features)

