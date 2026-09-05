import type { HistoryRecord } from "@/types/prediction";

function formatDate(record: HistoryRecord) {
  const date = new Date(record.created_at);
  if (Number.isNaN(date.getTime())) return "Date unavailable";
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function PredictionHistory({
  history,
  error,
}: {
  history: HistoryRecord[];
  error?: string;
}) {
  if (error)
    return (
      <div className="state-block error-state" role="alert">
        {error}
      </div>
    );
  if (!history.length)
    return (
      <div className="empty-panel compact">
        <h3>No predictions have been recorded yet</h3>
        <p>Completed assessments will appear here after the first prediction.</p>
      </div>
    );
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Risk category</th>
            <th>Attendance</th>
            <th>Previous grade</th>
            <th>Study hours</th>
            <th>Contributing factors</th>
          </tr>
        </thead>
        <tbody>
          {history.map((record, index) => (
            <tr key={record.id ?? `${record.created_at}-${index}`}>
              <td>{formatDate(record)}</td>
              <td>
                <span
                  className={`table-risk ${record.risk_category.toLowerCase()}`}
                >
                  {record.risk_category}
                </span>
              </td>
              <td>{record.input_data.attendance}%</td>
              <td>{record.input_data.previous_grade}</td>
              <td>{record.input_data.study_hours}</td>
              <td>
                <ul className="history-factors">
                  {record.contributing_factors.map((factor) => (
                    <li key={factor}>{factor}</li>
                  ))}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
