import { useState } from "react";
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
  onDelete,
}: {
  history: HistoryRecord[];
  error?: string;
  onDelete: (predictionId: string) => Promise<void>;
}) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<HistoryRecord | null>(
    null,
  );

  async function handleDelete() {
    if (!pendingDelete?.id) return;

    const predictionId = pendingDelete.id;
    setDeletingId(predictionId);
    try {
      await onDelete(predictionId);
      setPendingDelete(null);
    } finally {
      setDeletingId(null);
    }
  }

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
    <>
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
            <th aria-label="Actions" />
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
              <td>
                {record.id && (
                  <button
                    className="delete-button"
                    type="button"
                    title="Delete prediction"
                    aria-label={`Delete prediction from ${formatDate(record)}`}
                    disabled={deletingId === record.id}
                    onClick={() => setPendingDelete(record)}
                  >
                    {deletingId === record.id ? "..." : "🗑"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
      {pendingDelete && (
        <div className="modal-backdrop" role="presentation">
          <div
            className="confirmation-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-dialog-title"
          >
            <p className="eyebrow">Delete prediction</p>
            <h3 id="delete-dialog-title">
              Are you sure you want to delete this record?
            </h3>
            <p>This action will permanently remove it from prediction history.</p>
            <div className="modal-actions">
              <button
                className="modal-cancel"
                type="button"
                onClick={() => setPendingDelete(null)}
                disabled={deletingId !== null}
              >
                Cancel
              </button>
              <button
                className="modal-delete"
                type="button"
                onClick={handleDelete}
                disabled={deletingId !== null}
              >
                {deletingId !== null ? "Deleting..." : "Delete record"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
