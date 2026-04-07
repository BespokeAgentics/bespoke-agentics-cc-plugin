import betterMaxParams from "eslint-plugin-better-max-params";
import noComments from "eslint-plugin-no-comments";

export default [
  {
    plugins: {
      "better-max-params": betterMaxParams,
      "no-comments": noComments,
    },
    rules: {
      "no-comments/disallowComments": "error",

      "better-max-params/better-max-params": [
        "error",
        { constructor: 10, func: 2 },
      ],

      "max-lines-per-function": [
        "error",
        { max: 50, skipBlankLines: true, skipComments: true },
      ],

      "max-lines": [
        "error",
        { max: 250, skipBlankLines: true, skipComments: true },
      ],

      "no-magic-numbers": [
        "error",
        {
          detectObjects: false,
          enforceConst: true,
          ignore: [0, 1, -1, 2],
          ignoreArrayIndexes: true,
        },
      ],

      "max-statements": ["error", 20],
      "max-depth": ["error", 4],
      "max-classes-per-file": ["error", 1],
      "id-length": ["error", { min: 2, exceptions: ["_"] }],

      "no-restricted-syntax": [
        "error",
        {
          selector:
            "MemberExpression[object.name='process'][property.name='env']",
          message:
            "Direct process.env access is forbidden. Inject configuration instead.",
        },
      ],
    },
  },
];
