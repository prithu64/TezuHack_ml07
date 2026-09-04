import type { ContributingFactor } from "@/types/prediction";

export function ContributingFactors({ factors }: { factors?: ContributingFactor[] }) {
  if (!factors?.length) return <div className="empty-panel compact"><h3>No contributing factors returned</h3><p>The backend did not provide supporting indicators for this prediction.</p></div>;
  return <div className="factor-list">{factors.map((factor, index) => <article className="factor-row" key={`${factor.feature}-${index}`}><div className="factor-index">0{index + 1}</div><div><h3>{factor.feature.replaceAll("_", " ")}</h3><p>{factor.reason}</p></div><strong>{factor.value}</strong></article>)}</div>;
}
