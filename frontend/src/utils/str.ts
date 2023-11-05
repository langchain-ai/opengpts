export function str(o: unknown): React.ReactNode {
  return typeof o === "object"
    ? JSON.stringify(o, null, 2)
    : (o as React.ReactNode);
}
