# Product, UI, and data usage

Use when designing, implementing, changing, or verifying product behavior, architecture, UI, or data. Common requirements: [section 3](../AGENTS.md#3-implementation-and-verification).

## Screens and assets

- Compare layout, behavior, and states with the prototype/current screens. Locate and reuse implemented themes, tokens, and shared components.
- Touch targets: at least 44×44pt on iOS and 48×48dp on Android; apply stricter project requirements. Check visual size separately.
- Derive sprite coordinates from original dimensions, metadata, and confirmed boundaries; inspect clipping and adjacent-pixel contamination.

## Comparison captures

- Temporary locations: `tmp/screenshots/` or `.codex/screenshots/`.
- Keep the `FEATURE_한국어화면` naming convention and consistent screen tags. Add state/platform suffixes only when needed; use `_수정전`/`_수정후` for comparisons.
- Connect matching device, language, theme, account/data, build, and interaction records to the report.
- Label before/after images and embed actual captures with absolute local paths. Apply central redaction to sensitive content.
