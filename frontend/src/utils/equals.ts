export function deepEquals(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  a: Record<string, any>,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  b: Record<string, any>,
): boolean {
  if (a === b) return true;

  if (
    typeof a !== "object" ||
    a === null ||
    typeof b !== "object" ||
    b === null
  ) {
    return false;
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);

  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!keysB.includes(key)) return false;

    if (
      typeof a[key] === "object" &&
      a[key] !== null &&
      typeof b[key] === "object" &&
      b[key] !== null
    ) {
      if (!deepEquals(a[key], b[key])) return false;
    } else {
      if (a[key] !== b[key]) return false;
    }
  }

  return true;
}
