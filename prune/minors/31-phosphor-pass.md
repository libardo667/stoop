# Phosphor pass: the retro-terminal aesthetic for the portal

> **Status: Shipped (2026-06-23), folded into major 04.** Implemented as a `phosphor` *skin* in the
> theming system: pure CSS keyed off `body[data-skin]` (dark CRT palette, monospace, neon glow, faint
> scanlines), no JS-injected styles, no external deps. A keeper selects it from the admin console.

## Problem

The portal should feel like the cyberpunk dead-drop that inspired this ("YOU CAN'T STOP THE SIGNAL"),
not a default HTML form. Aesthetic is part of the delight and costs little.

## Proposed Solution

A small, dependency-light CSS layer: phosphor/CRT terminal styling for the Exchange and Murmur,
themeable per keeper config. Keep it tiny enough for the ESP32 payload budget.

## Files Affected

- `web/style.css` (and any theme tokens in `src/config.*`)

## Acceptance Criteria

- [x] The portal renders in a coherent retro-terminal aesthetic.
- [x] The CSS is small (fits the device payload budget) and has no external dependencies.
