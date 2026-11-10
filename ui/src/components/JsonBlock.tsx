export function JsonBlock(props: { title: string; value: any }) {
  return (
    <div className="rounded-2xl border border-line bg-surface shadow-soft">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="text-sm font-semibold text-ink">{props.title}</div>
      </div>
      <pre className="overflow-auto p-4 text-xs leading-relaxed text-ink/80">
        {JSON.stringify(props.value, null, 2)}
      </pre>
    </div>
  );
}
