from pathlib import Path
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# --------------------------------------------------
# 1. File paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "student_risk_model.pkl"
LABEL_ENCODER_PATH = BASE_DIR / "label_encoder.pkl"
FEATURE_NAMES_PATH = BASE_DIR / "feature_names.pkl"
MODEL_RESULTS_PATH = BASE_DIR / "model_results.json"


# --------------------------------------------------
# 2. Load trained files
# --------------------------------------------------

try:
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    feature_names = joblib.load(FEATURE_NAMES_PATH)

    print("Trained model loaded successfully.")

except FileNotFoundError as error:
    raise RuntimeError(
        f"Required model file was not found: {error.filename}. "
        "Run train_model.py first."
    )


# --------------------------------------------------
# 3. Create FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Student Support Risk Prediction API",
    description="API for predicting student academic risk categories.",
    version="1.0.0",
)


# --------------------------------------------------
# 4. Enable frontend access
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# 5. Request data model
# --------------------------------------------------

class StudentData(BaseModel):
    attendance: float = Field(..., ge=0, le=100)
    study_hours: float = Field(..., ge=0)
    past_failures: int = Field(..., ge=0, le=5)
    assignments_completed_pct: float = Field(..., ge=0, le=100)

    parental_education: str
    family_income: Literal["low", "medium", "high"]

    extracurricular: Literal["yes", "no"]
    internet_access: Literal["yes", "no"]

    previous_grade: float = Field(..., ge=0, le=100)


# --------------------------------------------------
# 6. Health-check endpoint
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Student Support Risk Prediction API is running",
        "docs": "/docs",
    }


# --------------------------------------------------
# 7. Prediction endpoint
# --------------------------------------------------

@app.post("/predict")
def predict_risk(student: StudentData):
    try:
        # Convert incoming request into a dictionary
        student_data = student.model_dump()

        # Create DataFrame using the exact feature order
        input_data = pd.DataFrame(
            [student_data],
            columns=feature_names,
        )

        # Generate numeric prediction
        prediction = model.predict(input_data)[0]

        # Convert numeric prediction into category name
        predicted_category = label_encoder.inverse_transform(
            [prediction]
        )[0]

        # Generate prediction probabilities
        probabilities_array = model.predict_proba(input_data)[0]

        probability_dict = {
            class_name: round(float(probability), 4)
            for class_name, probability in zip(
                label_encoder.classes_,
                probabilities_array,
            )
        }

        return {
            "risk_category": predicted_category,
            "probabilities": probability_dict,
            "message": (
                f"The model predicts that this student is "
                f"{predicted_category}."
            ),
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}",
        )