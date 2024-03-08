// (c) 2015 Chute Corporation. Released under the terms of the MIT License.
// Modified to use TypeScript and handle edge cases with tuples

/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-prototype-builtins */

"use strict";

/**
 * check whether item is plain object
 * @param {*} item
 * @return {Boolean}
 */
const isObject = (item: unknown): item is Record<string, unknown> => {
  return (
    typeof item === "object" &&
    item !== null &&
    item.toString() === {}.toString()
  );
};

/**
 * deep JSON object clone
 *
 * @param {Object} source
 * @return {Object}
 */
const cloneJSON = (source: any): any => {
  return JSON.parse(JSON.stringify(source));
};

/**
 * returns a result of deep merge of two objects
 *
 * @param {Object} target
 * @param {Object} source
 * @return {Object}
 */
const merge = (
  target: Record<string, unknown>,
  source: Record<string, unknown>,
) => {
  target = cloneJSON(target);

  for (const key in source) {
    if (source.hasOwnProperty(key)) {
      const sourceKeyValue = source[key];
      const targetKeyValue = target[key];

      if (isObject(sourceKeyValue) && isObject(targetKeyValue)) {
        target[key] = merge(targetKeyValue, sourceKeyValue);
      } else {
        target[key] = sourceKeyValue;
      }
    }
  }
  return target;
};

/**
 * get object by reference. works only with local references that points on
 * definitions object
 *
 * @param {String} path
 * @param {Object} definitions
 * @return {Object}
 */
const getLocalRef = function (
  inputPath: string,
  definitions: Record<string, unknown>,
) {
  const path = inputPath.replace(/^#\/definitions\//, "").split("/");

  const find = function (path: string[], root: any): any {
    const key = path.shift();
    if (!key) return {};

    if (!root[key]) {
      return {};
    } else if (!path.length) {
      return root[key];
    } else {
      return find(path, root[key]);
    }
  };

  const result = find(path, definitions);

  if (!isObject(result)) {
    return result;
  }
  return cloneJSON(result);
};

/**
 * merge list of objects from allOf properties
 * if some of objects contains $ref field extracts this reference and merge it
 *
 * @param {Array} allOfList
 * @param {Object} definitions
 * @return {Object}
 */
const mergeAllOf = function (allOfList: any[], definitions: any) {
  const length = allOfList.length;
  let index = -1,
    result = {};

  while (++index < length) {
    let item = allOfList[index];

    item =
      typeof item.$ref !== "undefined"
        ? getLocalRef(item.$ref, definitions)
        : item;

    result = merge(result, item);
  }

  return result;
};

/**
 * returns a object that built with default values from json schema
 *
 * @param {Object} schema
 * @param {Object} definitions
 * @return {Object}
 */
const defaults = (schema: any, definitions: Record<string, any>): unknown => {
  if (typeof schema["default"] !== "undefined") {
    return schema["default"];
  } else if (typeof schema.allOf !== "undefined") {
    const mergedItem = mergeAllOf(schema.allOf, definitions);
    return defaults(mergedItem, definitions);
  } else if (typeof schema.$ref !== "undefined") {
    const reference = getLocalRef(schema.$ref, definitions);
    return defaults(reference, definitions);
  } else if (schema.type === "object") {
    if (!schema.properties) {
      return {};
    }

    for (const key in schema.properties) {
      if (schema.properties.hasOwnProperty(key)) {
        schema.properties[key] = defaults(schema.properties[key], definitions);

        if (typeof schema.properties[key] === "undefined") {
          delete schema.properties[key];
        }
      }
    }

    return schema.properties;
  } else if (schema.type === "array") {
    if (!schema.items) {
      return [];
    }

    // minimum item count
    const ct = schema.minItems || 0;

    // tuple-typed arrays
    if (schema.items.constructor === Array) {
      const values = schema.items.map((item: unknown) =>
        defaults(item, definitions),
      );

      // remove undefined items at the end (unless required by minItems)
      for (let i = values.length - 1; i >= 0; i--) {
        if (typeof values[i] !== "undefined") {
          break;
        }
        if (i + 1 > ct) {
          values.pop();
        }
      }

      // if all values are undefined -> return undefined even
      // if minItems is set
      if (values.every((item: unknown) => typeof item === "undefined")) {
        return undefined;
      }

      return values;
    }

    // object-typed arrays
    const value = defaults(schema.items, definitions);

    if (typeof value === "undefined") {
      return [];
    } else {
      const values = [];
      for (let i = 0; i < Math.max(1, ct); i++) {
        values.push(cloneJSON(value));
      }
      return values;
    }
  }
};

/**
 * main function
 *
 * @param {Object} schema
 * @param {Object|undefined} definitions
 * @return {Object}
 */
export function getDefaults(
  schema: any,
  definitions?: Record<string, unknown> | undefined,
) {
  if (typeof definitions === "undefined") {
    definitions = (schema.definitions as Record<string, unknown>) || {};
  } else if (isObject(schema.definitions)) {
    definitions = merge(definitions, schema.definitions);
  }

  return defaults(cloneJSON(schema), definitions);
}
