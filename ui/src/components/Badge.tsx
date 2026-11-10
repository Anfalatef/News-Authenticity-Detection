type Props = {
  label: string;
  tone?: "neutral" | "good" | "warn" | "bad";
};

const tones: Record<string, string> = {
  neutral: "bg-canvas text-ink/80 ring-line",
  good: "bg-brand-50 text-brand-700 ring-brand-200",
  warn: "bg-warning-bg text-warning-text ring-warning-border",
  bad: "bg-error-bg text-error-text ring-error-border",
};

export function Badge({ label, tone = "neutral" }: Props) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${tones[tone]}`}>
      {label}
    </span>
  );
}
