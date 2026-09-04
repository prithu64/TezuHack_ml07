export function LoadingState({ label }: { label: string }) {
  return (
    <div className="state-block" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
