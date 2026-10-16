# Image asset usage

Use for generation, edits, transparency, or model/quality comparison. Support, originals, verification, and comparison rules: [section 5](../AGENTS.md#5-tools-accounts-and-security).

## Models and supported values

- Only among supported user-nominated candidates: consider `gpt-image-2.5-flare` for routine generation and `gpt-image-2.5-sunburst` for precise edits, subject preservation, or quality-first work.
- Verify current tool limits. Legacy GPT Image 2.5 reference: each side ≤3,840px and a multiple of 16; aspect ratio ≤3:1; total pixels 655,360–8,294,400. These are reference values, not support guarantees. Use verified limits and report final dimensions.

## Prompt and output

- Order prompts as outcome/use → subject → composition/layout → style/material/light → constraints. Keep them easy to read/edit.
- Quote exact text; specify count, placement, and type direction. Exclude extra text, watermarks, and unrelated logos; check spelling/readability directly.
- Transparency needs a supported tool option (for example `background="transparent"`) plus PNG/WebP, never JPEG. Specify fully transparent background with no checkerboard, solid fill, or shadow; the word “transparent” alone is insufficient.
- Inspect alpha and genuinely transparent pixels, plus hair/glass/shadow/edge residue and color bleed. Painted checkerboards, RGB-only output, or fully opaque alpha fail transparency verification.
- Regenerate or postprocess based on the failure. For tools without transparency, use a solid chroma key (green; magenta if the subject contains much green), convert to transparent PNG, and inspect edges.

## Edits and preservation

Specify “change only X,” retained identity/shape/layout/light/labels, and reference numbers/roles. Change one thing at a time. For pixel-exact retained regions, composite the authorized edit onto the original rather than relying solely on a prompt.

## Comparing settings

Keep representative prompts/references and a baseline output. Change one setting while retaining prompt, references, size, and other quality settings. Compare quality, consistency, latency, failures, retries, and cost per accepted result; meet required quality before reducing latency/cost.
