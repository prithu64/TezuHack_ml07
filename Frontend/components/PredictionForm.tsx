"use client";

import { FormEvent, useState } from "react";
import { predictStudent } from "@/lib/api";
import type { PredictionRequest, PredictionResponse } from "@/types/prediction";

interface PredictionFormProps {
  onPrediction: (prediction: PredictionResponse) => void;
}

type FormValues = Record<keyof PredictionRequest, string>;
type FormErrors = Partial<Record<keyof PredictionRequest, string>>;

const initialValues: FormValues = {
  attendance: "",
  study_hours: "",
  past_failures: "",
  assignments_completed_pct: "",
  parental_education: "",
  family_income: "",
  extracurricular: "",
  internet_access: "",
  previous_grade: "",
};

const numericFields: Array<keyof PredictionRequest> = [
  "attendance",
  "study_hours",
  "past_failures",
  "assignments_completed_pct",
  "previous_grade",
];

function validate(values: FormValues): FormErrors {
  const errors: FormErrors = {};
  const requiredFields = Object.keys(values) as Array<keyof PredictionRequest>;

  for (const field of requiredFields) {
    if (!values[field].trim()) errors[field] = "This field is required.";
  }

  for (const field of numericFields) {
    if (!values[field].trim()) continue;
    const value = Number(values[field]);
    if (!Number.isFinite(value)) errors[field] = "Enter a valid number.";

    if (field === "attendance" || field === "assignments_completed_pct" || field === "previous_grade") {
      if (value < 0 || value > 100) errors[field] = "Enter a value from 0 to 100.";
    }
    if (field === "study_hours" && value < 0) errors[field] = "Study hours cannot be negative.";
    if (field === "past_failures" && (!Number.isInteger(value) || value < 0 || value > 5)) {
      errors[field] = "Enter a whole number from 0 to 5.";
    }
  }

  return errors;
}

function toRequest(values: FormValues): PredictionRequest {
  return {
    attendance: Number(values.attendance),
    study_hours: Number(values.study_hours),
    past_failures: Number(values.past_failures),
    assignments_completed_pct: Number(values.assignments_completed_pct),
    parental_education: values.parental_education,
    family_income: values.family_income,
    extracurricular: values.extracurricular,
    internet_access: values.internet_access,
    previous_grade: Number(values.previous_grade),
  };
}

export function PredictionForm({ onPrediction }: PredictionFormProps) {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitError, setSubmitError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function updateField(field: keyof PredictionRequest, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setSubmitError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationErrors = validate(values);
    setErrors(validationErrors);
    setSubmitError("");
    if (Object.keys(validationErrors).length > 0) return;

    setIsSubmitting(true);
    try {
      const prediction = await predictStudent(toRequest(values));
      onPrediction(prediction);
    } catch {
      setSubmitError("Unable to connect to the prediction service. Please check that the FastAPI backend is running and try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="prediction-form" onSubmit={handleSubmit} noValidate>
      <div className="form-section">
        <div className="section-heading">
          <span className="section-number">01</span>
          <div><h3>Academic information</h3><p>Core indicators from the student record.</p></div>
        </div>
        <div className="form-grid">
          <Field label="Attendance" name="attendance" value={values.attendance} onChange={updateField} error={errors.attendance} type="number" min="0" max="100" suffix="%" />
          <Field label="Study hours" name="study_hours" value={values.study_hours} onChange={updateField} error={errors.study_hours} type="number" min="0" step="0.5" suffix="hrs / week" />
          <Field label="Past failures" name="past_failures" value={values.past_failures} onChange={updateField} error={errors.past_failures} type="number" min="0" max="5" step="1" />
          <Field label="Assignments completed" name="assignments_completed_pct" value={values.assignments_completed_pct} onChange={updateField} error={errors.assignments_completed_pct} type="number" min="0" max="100" suffix="%" />
          <Field label="Previous grade" name="previous_grade" value={values.previous_grade} onChange={updateField} error={errors.previous_grade} type="number" min="0" max="100" suffix="/ 100" />
        </div>
      </div>
      <div className="form-section">
        <div className="section-heading">
          <span className="section-number">02</span>
          <div><h3>Background information</h3><p>Contextual indicators used by the model.</p></div>
        </div>
        <div className="form-grid">
          <SelectField label="Parental education" name="parental_education" value={values.parental_education} onChange={updateField} error={errors.parental_education} options={["Higher", "Secondary", "Primary", "none"]} />
          <SelectField label="Family income" name="family_income" value={values.family_income} onChange={updateField} error={errors.family_income} options={["High", "Medium", "Low"]} />
          <SelectField label="Extracurricular" name="extracurricular" value={values.extracurricular} onChange={updateField} error={errors.extracurricular} options={["Yes", "No"]} />
          <SelectField label="Internet access" name="internet_access" value={values.internet_access} onChange={updateField} error={errors.internet_access} options={["Yes", "No"]} />
        </div>
      </div>
      {submitError && <p className="form-error form-error-banner" role="alert">{submitError}</p>}
      <div className="form-actions">
        <p>Predictions support review and intervention planning; they do not determine a student&apos;s future.</p>
        <button className="primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? <><span className="button-spinner" aria-hidden="true" /> Analyzing indicators...</> : <>Run risk assessment <span aria-hidden="true">-&gt;</span></>}
        </button>
      </div>
    </form>
  );
}

interface FieldProps {
  label: string; name: keyof PredictionRequest; value: string; type: "number"; min: string; max?: string; step?: string; suffix?: string; error?: string; onChange: (name: keyof PredictionRequest, value: string) => void;
}
function Field({ label, name, value, type, min, max, step, suffix, error, onChange }: FieldProps) {
  return <label className="field">{label}<span className="input-wrap"><input name={name} value={value} onChange={(event) => onChange(name, event.target.value)} type={type} min={min} max={max} step={step} aria-invalid={Boolean(error)} />{suffix && <span>{suffix}</span>}</span>{error && <small className="field-error">{error}</small>}</label>;
}

interface SelectFieldProps { label: string; name: keyof PredictionRequest; value: string; options: string[]; error?: string; onChange: (name: keyof PredictionRequest, value: string) => void; }
function SelectField({ label, name, value, options, error, onChange }: SelectFieldProps) {
  return <label className="field">{label}<span className="select-wrap"><select name={name} value={value} onChange={(event) => onChange(name, event.target.value)} aria-invalid={Boolean(error)}><option value="">Select an option</option>{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></span>{error && <small className="field-error">{error}</small>}</label>;
}
