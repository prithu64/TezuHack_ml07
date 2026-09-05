import type { ModelResult } from "@/types/prediction";

function metric(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function ModelComparison({
  results,
  error,
}: {
  results: ModelResult[];
  error?: string;
}) {
  if (error)
    return (
      <div className="state-block error-state" role="alert">
        {error}
      </div>
    );
  if (!results.length)
    return (
      <div className="empty-panel compact">
        <h3>No model results available</h3>
        <p>
          Model comparison metrics will appear when the backend endpoint returns
          data.
        </p>
      </div>
    );
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Model</th>
            <th>Accuracy</th>
            <th>Weighted F1</th>
            <th>Macro F1</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr key={result.model}>
              <td>
                <strong>{result.model}</strong>
              </td>
              <td>{metric(result.accuracy)}</td>
              <td>{metric(result.weighted_f1)}</td>
              <td>{metric(result.macro_f1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
