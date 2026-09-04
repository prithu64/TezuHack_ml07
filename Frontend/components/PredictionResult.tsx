import type { PredictionResponse, RiskCategory } from "@/types/prediction";

const categories: RiskCategory[] = ["Safe", "At-Risk", "High-Risk"];

export function PredictionResult({ prediction }: { prediction: PredictionResponse | null }) {
  if (!prediction) return <div className="empty-panel"><span className="empty-icon">+</span><h3>Awaiting a prediction</h3><p>Submit academic and background indicators to see the model&apos;s assessment.</p></div>;
  return <div className="result-content"><div className={`risk-badge ${prediction.risk_category.toLowerCase().replace("-", "-")}`}><span className="status-dot" />{prediction.risk_category}</div><h3>The model predicts that this student is {prediction.risk_category}.</h3><p>This student may benefit from additional academic support based on the indicators provided.</p><div className="confidence-line"><span>Model confidence</span><strong>{Math.round(prediction.confidence * 100)}%</strong></div><div className="probability-list" aria-label="Probability distribution">{categories.map((category) => { const probability = prediction.probabilities?.[category]; return <div className="probability-row" key={category}><div><span>{category}</span><span>{probability === undefined ? "Unavailable" : `${Math.round(probability * 100)}%`}</span></div>{probability !== undefined && <div className="bar-track"><div className={`bar-fill ${category.toLowerCase().replace("-", "-")}`} style={{ width: `${Math.max(0, Math.min(100, probability * 100))}%` }} /></div>}</div>; })}</div></div>;
}
