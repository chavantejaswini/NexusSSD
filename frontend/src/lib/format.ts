export function formatBytes(bytes: number): string {
  if (bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  const i = Math.min(units.length - 1, Math.floor(Math.log10(bytes) / 3));
  const value = bytes / 1000 ** i;
  return `${value.toFixed(value >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}

export function formatPct(fraction: number | null, digits = 0): string {
  if (fraction == null) return "—";
  return `${(fraction * 100).toFixed(digits)}%`;
}

export function formatDate(iso: string): string {
  return iso.slice(0, 10);
}
