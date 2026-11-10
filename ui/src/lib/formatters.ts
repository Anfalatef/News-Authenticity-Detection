export function formatVeracityLabel(
  label: string | null | undefined,
  t: (key: string) => string
): string {
  const normalized = String(label ?? "").trim().toLowerCase();
  if (!normalized) return t("labelUnknown");
  if (normalized === "real") return t("veracityReal");
  if (normalized === "fake") return t("veracityFake");
  if (normalized === "unclear") return t("veracityUnclear");
  return label ?? t("labelUnknown");
}

export function formatYesNo(value: unknown, t: (key: string) => string): string {
  return value ? t("labelYes") : t("labelNo");
}
