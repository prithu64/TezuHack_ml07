import type { HistoryRecord } from "@/types/prediction";

export function SummaryCards({ history }: { history: HistoryRecord[] }) {
  const total = history.length;
  const atRisk = history.filter((record) => record.risk_category === "At-Risk").length;
  const highRisk = history.filter((record) => record.risk_category === "High-Risk").length;
  const average = total ? history.reduce((sum, record) => sum + record.confidence, 0) / total : null;
  const cards = [["Total predictions", total ? total.toString() : "--", "All completed assessments"], ["At-Risk students", total ? atRisk.toString() : "--", "May need additional support"], ["High-Risk students", total ? highRisk.toString() : "--", "Requires closer attention"], ["Average confidence", average === null ? "--" : `${Math.round(average * 100)}%`, "Across recorded predictions"]];

  return <section className="summary-grid" aria-label="Prediction summary">{cards.map(([label, value, note]) => <article className="summary-card" key={label}><p>{label}</p><strong>{value}</strong><span>{note}</span></article>)}</section>;
}
