export function ContributingFactors({ factors }: { factors?: string[] }) {
  if (!factors?.length)
    return (
      <div className="empty-panel compact">
        <h3>No contributing factors returned</h3>
        <p>
          The backend did not provide supporting indicators for this prediction.
        </p>
      </div>
    );
  return (
    <div className="factor-list">
      {factors.map((factor, index) => (
        <article className="factor-row" key={`${factor}-${index}`}>
          <div className="factor-index">0{index + 1}</div>
          <h3>{factor}</h3>
        </article>
      ))}
    </div>
  );
}
