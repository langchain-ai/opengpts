/* eslint-disable @typescript-eslint/no-explicit-any */
import { JsonRefs } from "./json-refs";

// jsonforms doesn't support schemas with root $ref
// so we resolve root $ref and replace it with the actual schema
export function simplifySchema(schema: any) {
  return JsonRefs.resolveRefs(schema).then((r: any) => r.resolved);
}
