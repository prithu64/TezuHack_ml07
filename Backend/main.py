from pathlib import Path
from typing import Literal
from datetime import datetime, timezone

import joblib
import pandas as pd
from bson import ObjectId
from pymongo.errors import PyMongoError

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import check_database_connection, predictions_collection

# Paths
BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "student_risk_model.pkl"
ENCODER_PATH = BASE_DIR / "label_encoder.pkl"
FEATURES_PATH = BASE_DIR / "feature_names.pkl"



# Load trained files
model = joblib.load(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)
feature_names = joblib.load(FEATURES_PATH)

print("Loaded model successfully.")
print("Expected input features:")
print(feature_names)



# FastAPI application
app = FastAPI(
    title="Student Support Risk Prediction API",
    description="Predicts student academic risk and identifies supporting indicators.",
    version="1.0.0"
)



# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002"
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



# Health check
@app.get("/")
def root():
    return {
        "message": "Student Risk Prediction API is running"
    }



# Generate contributing factors
def get_contributing_factors(student: StudentData):

    factors = []

    if student.attendance < 75:
        factors.append(
            f"Low attendance: {student.attendance}%"
        )

    if student.study_hours < 2:
        factors.append(
            f"Low study hours: {student.study_hours} hours per day"
        )

    if student.assignments_completed_pct < 60:
        factors.append(
            "Low assignment completion: "
            f"{student.assignments_completed_pct}%"
        )

    if student.previous_grade < 50:
        factors.append(
            f"Low previous grade: {student.previous_grade}"
        )

    if student.past_failures > 0:
        factors.append(
            f"{student.past_failures} previous academic failure(s)"
        )

    if student.internet_access == "no":
        factors.append(
            "Limited internet access may affect learning resources"
        )

    if not factors:
        factors.append(
            "No major risk indicators detected"
        )

    return factors



# Generate support message
def get_support_message(risk_category: str):

    if risk_category == "High-Risk":
        return (
            "This student may require immediate academic support, "
            "regular monitoring, and individual mentoring."
        )

    if risk_category == "At-Risk":
        return (
            "This student may benefit from additional academic guidance, "
            "attendance monitoring, and study support."
        )

    return (
        "This student currently appears to be academically safe. "
        "Continue regular monitoring and encouragement."
    )


# Prediction endpoint
@app.post("/predict")
def predict_student_risk(student: StudentData):

    try:
        check_database_connection()

        # Convert request data into a dictionary
        student_data = student.model_dump()

        # Create DataFrame using the exact original
        # feature names used during training
        input_data = pd.DataFrame(
            [student_data],
            columns=feature_names
        )

        # Predict encoded class
        prediction = model.predict(input_data)[0]

        # Convert encoded class into original category
        predicted_category = label_encoder.inverse_transform(
            [prediction]
        )[0]

        # Get prediction probabilities
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

        # Generate supporting indicators
        contributing_factors = get_contributing_factors(student)

        # Generate support message
        support_message = get_support_message(
            predicted_category
        )

        prediction_result = {
            "risk_category": predicted_category,
            "probabilities": probability_dict,
            "contributing_factors": contributing_factors,
            "message": support_message
        }

        predictions_collection.insert_one({
            "input_data": student_data,
            **prediction_result,
            "created_at": datetime.now(timezone.utc),
        })

        return prediction_result

    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable. Please make sure the local MongoDB server is running."
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Prediction failed. Please check the backend logs."
        )


def serialize_prediction(document: dict) -> dict:
    document["id"] = str(document.pop("_id"))
    if isinstance(document.get("created_at"), datetime):
        document["created_at"] = document["created_at"].isoformat()
    return document


@app.get("/predictions")
def get_predictions():
    try:
        check_database_connection()
        documents = predictions_collection.find().sort("created_at", -1)
        return [serialize_prediction(document) for document in documents]
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable. Please make sure the local MongoDB server is running."
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to load prediction history. Please check the backend logs."
        )


@app.get("/predictions/{prediction_id}")
def get_prediction(prediction_id: str):
    if not ObjectId.is_valid(prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction id.")

    try:
        check_database_connection()
        document = predictions_collection.find_one({"_id": ObjectId(prediction_id)})
        if document is None:
            raise HTTPException(status_code=404, detail="Prediction not found.")
        return serialize_prediction(document)
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable. Please make sure the local MongoDB server is running."
        )
    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Unable to load the prediction. Please check the backend logs."
        )


@app.delete("/predictions/{prediction_id}")
def delete_prediction(prediction_id: str):
    if not ObjectId.is_valid(prediction_id):
        raise HTTPException(status_code=400, detail="Invalid prediction id.")

    try:
        check_database_connection()
        result = predictions_collection.delete_one({"_id": ObjectId(prediction_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Prediction not found.")
        return {"message": "Prediction deleted successfully."}
    except HTTPException:
        raise
    except PyMongoError:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is unavailable. Please make sure the local MongoDB server is running."
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to delete the prediction. Please check the backend logs."
        )
