"use client";

import { useEffect, useState } from "react";
import { DashboardHeader } from "@/components/DashboardHeader";
import { LoadingState } from "@/components/LoadingState";
import { PredictionForm } from "@/components/PredictionForm";
import { PredictionHistory } from "@/components/PredictionHistory";
import { PredictionResult } from "@/components/PredictionResult";
import { SummaryCards } from "@/components/SummaryCards";
import { deletePrediction, getPredictionHistory } from "@/lib/api";
import type { HistoryRecord, PredictionResponse } from "@/types/prediction";

export default function DashboardPage() {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState("");

  useEffect(() => {
    getPredictionHistory()
      .then(setHistory)
      .catch((error: unknown) => {
        setHistoryError(
          error instanceof Error
            ? error.message
            : "Unable to load prediction history. Please check the FastAPI backend.",
        );
      })
      .finally(() => setHistoryLoading(false));
  }, []);

  function handlePrediction(result: PredictionResponse) {
    setPrediction(result);
    getPredictionHistory()
      .then(setHistory)
      .catch(() => undefined);
  }

  async function handleDeletePrediction(predictionId: string) {
    await deletePrediction(predictionId);
    setHistory((current) =>
      current.filter((record) => record.id !== predictionId),
    );
  }

  return (
    <main className="app-shell">
      <DashboardHeader />
      <SummaryCards history={history} />
      <div className="dashboard-grid">
        <section className="panel form-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">New assessment</p>
              <h2>Assess student indicators</h2>
            </div>
            <span className="live-label">
              <span /> API connected
            </span>
          </div>
          <PredictionForm onPrediction={handlePrediction} />
        </section>
        <section className="panel result-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Latest result</p>
              <h2>Prediction result</h2>
            </div>
            <span className="panel-code">01</span>
          </div>
          <PredictionResult prediction={prediction} />
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Recorded assessments</p>
            <h2>Prediction history</h2>
          </div>
          <span className="panel-code">02</span>
        </div>
        {historyLoading ? (
          <LoadingState label="Loading prediction history..." />
        ) : (
          <PredictionHistory
            history={history}
            error={historyError}
            onDelete={handleDeletePrediction}
          />
        )}
      </section>
      <footer className="app-footer">
        <span>Student Support Risk Prediction System</span>
        <span>3G1T</span>
      </footer>
    </main>
  );
}
