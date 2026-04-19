import { test } from "node:test";
import assert from "node:assert/strict";
import { CALLOUT_TYPES, wrapSelection } from "../src/callout";

test("CALLOUT_TYPES exposes 7 hardcoded Obsidian callout names", () => {
  assert.deepEqual(
    [...CALLOUT_TYPES],
    ["question", "tip", "error", "hint", "note", "warning", "info"],
  );
});

test("wrapSelection wraps single line with callout header", () => {
  assert.equal(wrapSelection("hello", "tip"), "> [!tip]\n> hello");
});

test("wrapSelection preserves each line with `> ` prefix on multi-line", () => {
  assert.equal(
    wrapSelection("line1\nline2", "warning"),
    "> [!warning]\n> line1\n> line2",
  );
});

test("wrapSelection keeps blank lines as `> ` (not stripped)", () => {
  assert.equal(
    wrapSelection("a\n\nb", "note"),
    "> [!note]\n> a\n> \n> b",
  );
});

test("wrapSelection handles pure whitespace line", () => {
  assert.equal(
    wrapSelection("  ", "hint"),
    "> [!hint]\n>   ",
  );
});

test("wrapSelection works for every CALLOUT_TYPES entry", () => {
  for (const type of CALLOUT_TYPES) {
    const out = wrapSelection("x", type);
    assert.equal(out, `> [!${type}]\n> x`);
  }
});
