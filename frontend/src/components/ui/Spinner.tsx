export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="spinner-wrap">
      <span className="spinner" aria-hidden="true" />
      <span className="spinner-label">{label}</span>
    </div>
  );
}

export function PageLoader() {
  return (
    <div style={{ minHeight: 320, display: "grid", placeItems: "center" }}>
      <Spinner />
    </div>
  );
}