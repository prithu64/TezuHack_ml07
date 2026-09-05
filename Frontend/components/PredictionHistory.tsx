import type { HistoryRecord } from "@/types/prediction";

function formatDate(record: HistoryRecord) {
  const dateValue = record.created_at ?? record.timestamp;
  if (!dateValue) return "Date unavailable";
  const date = new Date(dateValue);
  return Number.isNaN(date.getTime())
    ? dateValue
    : date.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
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
        <h3>No prediction history available yet.</h3>
        <p>
          Completed assessments will appear here once the backend records them.
        </p>
      </div>
    );
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Attendance</th>
            <th>Previous grade</th>
            <th>Risk category</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {history.map((record, index) => (
            <tr key={record.id ?? `${record.created_at}-${index}`}>
              <td>{formatDate(record)}</td>
              <td>{record.attendance}%</td>
              <td>{record.previous_grade}</td>
              <td>
                <span
                  className={`table-risk ${record.risk_category.toLowerCase()}`}
                >
                  {record.risk_category}
                </span>
              </td>
              <td>{Math.round(record.confidence * 100)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
