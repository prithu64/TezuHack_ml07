<<<<<<< HEAD
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
=======
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Literal

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import DESCENDING, MongoClient
from pymongo.collection import Collection


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "student_support")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "predictions")
FRONTEND_ORIGINS = [
	origin.strip()
	for origin in os.getenv(
		"FRONTEND_ORIGIN", "http://localhost:3000,http://localhost:3001"
	).split(",")
	if origin.strip()
]

FEATURES = [
	"attendance",
	"study_hours",
	"past_failures",
	"assignments_completed_pct",
	"parental_education",
	"family_income",
	"extracurricular",
	"internet_access",
	"previous_grade",
]

RiskCategory = Literal["Safe", "At-Risk", "High-Risk"]


class PredictionRequest(BaseModel):
	attendance: float = Field(ge=0, le=100)
	study_hours: float = Field(ge=0)
	past_failures: int = Field(ge=0, le=5)
	assignments_completed_pct: float = Field(ge=0, le=100)
	parental_education: str
	family_income: str
	extracurricular: str
	internet_access: str
	previous_grade: float = Field(ge=0, le=100)


class ContributingFactor(BaseModel):
	feature: str
	value: str | float | int
	reason: str


class PredictionResponse(BaseModel):
	risk_category: RiskCategory
	confidence: float
	probabilities: dict[str, float]
	contributingFactors: list[ContributingFactor]


class PredictionRecord(PredictionRequest):
	id: str
	created_at: datetime
	risk_category: RiskCategory
	confidence: float


model = joblib.load(BASE_DIR / "student_risk_model.pkl")
label_encoder = joblib.load(BASE_DIR / "label_encoder.pkl")
mongo_client: MongoClient | None = None
prediction_collection: Collection[dict[str, Any]] | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
	global mongo_client, prediction_collection
	mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
	try:
		mongo_client.admin.command("ping")
		prediction_collection = mongo_client[MONGODB_DATABASE][MONGODB_COLLECTION]
		prediction_collection.create_index([("created_at", DESCENDING)])
	except Exception:
		mongo_client.close()
		mongo_client = None
		prediction_collection = None
	yield
	if mongo_client is not None:
		mongo_client.close()


app = FastAPI(
	title="Student Support Risk Prediction API",
	lifespan=lifespan,
)
app.add_middleware(
	CORSMiddleware,
	allow_origins=FRONTEND_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


def get_collection() -> Collection[dict[str, Any]]:
	if prediction_collection is None:
		raise HTTPException(
			status_code=503,
			detail="MongoDB is unavailable. Start MongoDB and try again.",
		)
	return prediction_collection


def build_contributing_factors(student: PredictionRequest) -> list[ContributingFactor]:
	factors: list[ContributingFactor] = []
	if student.attendance < 75:
		factors.append(ContributingFactor(
			feature="attendance",
			value=student.attendance,
			reason="Lower attendance may be associated with increased academic support needs.",
		))
	if student.assignments_completed_pct < 75:
		factors.append(ContributingFactor(
			feature="assignments_completed_pct",
			value=student.assignments_completed_pct,
			reason="Lower assignment completion may indicate a need for additional support.",
		))
	if student.past_failures > 0:
		factors.append(ContributingFactor(
			feature="past_failures",
			value=student.past_failures,
			reason="Previous failures are an academic indicator associated with support needs.",
		))
	if student.previous_grade < 60:
		factors.append(ContributingFactor(
			feature="previous_grade",
			value=student.previous_grade,
			reason="A lower previous grade may be associated with a need for academic support.",
		))
	return factors


@app.get("/health")
def health() -> dict[str, str]:
	get_collection()
	return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(student: PredictionRequest) -> PredictionResponse:
	collection = get_collection()
	input_frame = pd.DataFrame([{feature: getattr(student, feature) for feature in FEATURES}])
	try:
		predicted_value = model.predict(input_frame)[0]
		probabilities = model.predict_proba(input_frame)[0]
		categories = label_encoder.inverse_transform(range(len(probabilities)))
		probability_map = {
			str(category): round(float(probability), 6)
			for category, probability in zip(categories, probabilities)
		}
		risk_category = str(label_encoder.inverse_transform([predicted_value])[0])
		confidence = probability_map[risk_category]
		result = PredictionResponse(
			risk_category=risk_category,  # type: ignore[arg-type]
			confidence=confidence,
			probabilities=probability_map,
			contributingFactors=build_contributing_factors(student),
		)
	except Exception as error:
		raise HTTPException(status_code=500, detail="Unable to run the risk model.") from error

	record = student.model_dump()
	record.update(
		{
			"risk_category": result.risk_category,
			"confidence": result.confidence,
			"created_at": datetime.now(timezone.utc),
		}
	)
	collection.insert_one(record)
	return result


@app.get("/history", response_model=list[PredictionRecord])
def history() -> list[PredictionRecord]:
	collection = get_collection()
	records = []
	for record in collection.find({}, sort=[("created_at", DESCENDING)]):
		records.append(PredictionRecord(
			id=str(record["_id"]),
			**{field: record[field] for field in FEATURES},
			created_at=record["created_at"],
			risk_category=record["risk_category"],
			confidence=record["confidence"],
		))
	return records


@app.get("/model-results")
def model_results() -> dict[str, Any]:
	with (BASE_DIR / "model_results.json").open(encoding="utf-8") as file:
		return json.load(file)
>>>>>>> 8cc39f9921595a21a00d9a743ab4eef89351e871
