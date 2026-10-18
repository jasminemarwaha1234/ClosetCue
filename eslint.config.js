// https://docs.expo.dev/guides/using-eslint/
const { defineConfig } = require('eslint/config');
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ["dist/*"],
  },
  {
    // Apostrophes in <Text> are safe in React Native; the rule guards against HTML parsing.
    rules: { "react/no-unescaped-entities": "off" },
  },
]);
