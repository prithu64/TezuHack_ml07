from pathlib import Path
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field



# Paths
BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "student_risk_model.pkl"
ENCODER_PATH = BASE_DIR / "label_encoder.pkl"
FEATURES_PATH = BASE_DIR / "feature_names.pkl"



# Load trained files
model = joblib.load(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)
feature_names = joblib.load(FEATURES_PATH)

print("Loaded features:")
print(feature_names)



# FastAPI app
app = FastAPI(
    title="Student Support Risk Prediction API",
    description="Predicts student academic risk using machine learning.",
    version="1.0.0"
)



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



# Request schema
class StudentData(BaseModel):

    attendance: float = Field(
        ...,
        ge=0,
        le=100,
        description="Attendance percentage"
    )

    study_hours: float = Field(
        ...,
        ge=0,
        le=24,
        description="Average daily study hours"
    )

    past_failures: int = Field(
        ...,
        ge=0,
        description="Number of previous academic failures"
    )

    assignments_completed_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of assignments completed"
    )

    parental_education: str

    family_income: Literal[
        "low",
        "medium",
        "high"
    ]

    extracurricular: Literal[
        "yes",
        "no"
    ]

    internet_access: Literal[
        "yes",
        "no"
    ]

    previous_grade: float = Field(
        ...,
        ge=0,
        le=100,
        description="Previous academic grade"
    )



# Health-check endpoint
@app.get("/")
def root():
    return {
        "message": "Student Risk Prediction API is running"
    }


# Prediction endpoint
@app.post("/predict")
def predict_student_risk(student: StudentData):

    try:
        student_data = student.model_dump()

        # Create DataFrame using the exact original
        # feature names used during model training.

        input_data = pd.DataFrame(
            [student_data],
            columns=feature_names
        )

        # Predict encoded class
        prediction = model.predict(input_data)[0]

        # Convert encoded class back to original label
        predicted_category = label_encoder.inverse_transform(
            [prediction]
        )[0]

        response = {
            "risk_category": predicted_category
        }

        # Add probabilities if supported
        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(
                input_data
            )[0]

            probability_dict = {
                class_name: round(float(probability), 4)
                for class_name, probability in zip(
                    label_encoder.classes_,
                    probabilities
                )
            }

            response["probabilities"] = probability_dict

        # Add a simple explanation
        if predicted_category == "High-Risk":
            response["message"] = (
                "This student may require immediate academic support."
            )

        elif predicted_category == "At-Risk":
            response["message"] = (
                "This student may benefit from additional monitoring "
                "and academic guidance."
            )

        else:
            response["message"] = (
                "This student currently appears to be academically safe."
            )

        return response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(error)}"
        )
