/* eslint-disable @typescript-eslint/no-explicit-any */
import { JsonRefs } from "./json-refs";

// jsonforms doesn't support schemas with root $ref
// so we resolve root $ref and replace it with the actual schema
export function simplifySchema(schema: any) {
  return JsonRefs.resolveRefs(schema)
    .then((r: any) => r.resolved)
    .then((r) => {
      const configurable = r.properties.configurable.properties;
      if (configurable) {
        for (const key in configurable) {
          if (configurable[key].allOf && configurable[key].allOf.length === 1) {
            configurable[key] = {
              ...configurable[key].allOf[0],
              title: configurable[key].title,
              description: configurable[key].description,
              default: configurable[key].default,
            };
          }
        }
      }
      return r;
    });
}
