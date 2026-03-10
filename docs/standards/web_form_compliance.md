# Web Form Standards Compliance

This document maps the app to `standards/web_form_standards.md` and captures what is implemented.

## Implemented
- Task-based sections on both KPI Definition and KPI Usage pages.
- Required-field clarity using explicit `(Required)` labels.
- Progressive disclosure for optional/advanced inputs:
  - Definition: source/filter JSON block under `More options`.
  - Usage: display/security preferences under `More options`.
- Validation UX improvements:
  - Top-of-form error summary.
  - Field-level inline validation messages.
  - User input preserved after validation failures.
- Save-state handling:
  - Submit button is disabled during submit.
  - Submit text changes to `Saving...` to reduce double-submit risk.
- Unsaved-change warning on form navigation.
- Accessibility baseline improvements:
  - Programmatic labels for fields.
  - Error summary uses `role="alert"`.
  - Keyboard-native controls (inputs/selects/checkboxes/details).
- KPI Usage specific standards:
  - Search assist by KPI ID or slug.
  - Multi-select consumer tools on create (one row per selected tool).
  - Plain-language definitions for `Reference Name`, `Source System`, `Reference URL`, and `Additional Notes`.

## Partially Implemented / Next Improvements
- Asynchronous uniqueness checks are not implemented (server-side checks are authoritative).
- Concurrency control (`updated_at`/ETag conflict handling) is not yet implemented for edit conflicts.
- Soft-delete patterns are not implemented (current flows are create/update/list).
- Correlation/request IDs are not yet surfaced in UI for support workflows.

## Notes
- The app currently uses a split workspace layout for speed and operational visibility.
- This intentionally diverges from strict single-column-only guidance, while preserving readable sectioning and responsiveness.
