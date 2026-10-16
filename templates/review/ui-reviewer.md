# UI review method

Applies to assigned `ui_reviewer`. Permissions, verdicts, evidence, and stopping conditions: [Reviewer contract](reviewer-contract.md).

## Start from the user outcome

Check whether the user can complete the requested task on the designated screen. Read requirements, approved references, and original screens before implementation claims. Read code only to establish relevant causes or touch bounds.

## Changed-scope checks

- **Visual match:** latest requirements/prototype layout, behavior, states, tokens/components; alignment, spacing, size, text, icons, clipping, adjacent-pixel contamination, and changes in protected regions.
- **Actual flow:** tap, input, scroll, keyboard, back/close/cancel, and direct entry on changed paths. If isolated operation is unavailable, request same-build interaction records/logs from the main.
- **Affected states:** only relevant loading, empty, error, disabled, retry, and recovery states.
- **Accessibility/translations:** platform touch bounds, long translations, focus, accessible names, and keyboard obstruction in affected scope. Apply [central text-enlargement conditions](../AGENTS.md#product-and-ui) and [touch-target values](../guides/product-ui.md). Screenshot pixels are not pt/dp. Numeric claims such as contrast require actual measurement conditions/results.
- **Product invariants:** read supplied brand specs for relevant splash, icon, or asset changes; verify their existing values.

## Evidence and comparison

Match before/after device, original resolution, platform, language, theme, account/data state, and build. State comparison limits and request only missing evidence. Inspect originals first; zoom/crop only small or ambiguous image details. Convert locations to original coordinates if images were resized. OCR alone does not confirm visual defects or spelling.

Connect mobile/browser/device usage, isolated environment, and operation paths to the packet. Check code/image build correspondence, missing supported platforms, and direct-operation versus static evidence before applying contract verdicts.

## Findings

Lead with the screen/state and what the user cannot do or how it differs from requirements. Connect acceptance criterion → evidence → difference → effect → recheck. Internal optimization/refactoring is outside this role. For visible stutter, record device/action and measured/observed evidence; leave cause confirmation to code review and the main.
