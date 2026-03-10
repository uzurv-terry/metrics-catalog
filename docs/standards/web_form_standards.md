# Modern web form best practices for an internal CRUD app

These practices assume an authenticated internal web app with create/read/update/delete flows, moderate data complexity, and users who care about speed and correctness more than “marketing polish.”

---

## 1) Design the form around the job-to-be-done

- **Prefer task-based forms**: group fields in the order people think, not the database schema.
- **Minimize mandatory fields**: require only what’s needed to create a valid record; collect optional details later.
- **Use progressive disclosure**: hide advanced fields behind “More options” or collapsible sections.
- **Default aggressively**: prefill from context (current user/team, last-used values, related records).

**Checklist**
- [ ] Can a user complete the main task in < 30–60 seconds?
- [ ] Are optional/rare fields visually de-emphasized?
- [ ] Are defaults meaningful and safe?

---

## 2) Choose sensible CRUD patterns

### Create
- **Start with a minimal create form**; allow editing after creation for rare fields.
- **Offer “Create another”** for high-throughput entry work.
- **Support templates** if users repeatedly create similar records.

### Read / View
- **Make view pages scannable**: summarize key fields, show metadata (created by/at, updated by/at).
- **Include inline related entities** (links + key context) rather than forcing context switching.

### Update
- **Prefer inline edit** for small changes (single field or short set).
- **Use full edit forms** for multi-step or high-impact edits.

### Delete
- **Use soft-delete by default** for internal apps (undo, audit).
- **Provide a clear destructive action pattern**: confirm with context and consequences.

---

## 3) Validation that feels fast and trustworthy

- **Validate on blur** (field-level) and **on submit** (form-level). Don’t rely on submit-only.
- **Keep messages specific**:
  - Bad: “Invalid input”
  - Good: “Phone number must include country code, e.g., +1 555-555-5555”
- **Show errors near the field**, plus a **summary at top** for long forms.
- **Preserve user input** on validation errors and navigation.
- **Make server validation authoritative**; client validation is for speed and hints.

**Edge-case handling**
- **Uniqueness**: if “Name must be unique,” check asynchronously and re-check server-side.
- **Cross-field rules**: highlight both fields and explain the relationship.
- **Partial saves**: if you allow drafts, validate only what’s necessary for the current state.

---

## 4) Accessibility (yes, for internal apps too)

- **Label every input** with a programmatic label (`<label for="">` or `aria-label`).
- **Keyboard works end-to-end**: tab order, focus states, no keyboard traps.
- **Announce validation errors**: use `aria-describedby` and error regions that screen readers detect.
- **Use semantic elements**: fieldsets + legends for grouped inputs.
- **Color is not the only signal**: use icons/text for success/error states.

**Quick tests**
- [ ] Can you complete the form with keyboard only?
- [ ] Zoom to 200%: still usable without horizontal scrolling?
- [ ] Screen reader: error messages are read when they appear?

---

## 5) Prevent data loss and concurrency issues

- **Autosave** drafts for long forms; show “Saved” timestamp.
- **Warn on unsaved changes** when navigating away.
- **Optimistic locking** (recommended): include a `version`/`updated_at` and detect conflicting updates.
  - If conflict: show a merge UI or re-apply changes atop the latest version.

**Good conflict UX**
- Explain: “This record was updated by Alex at 3:12 PM.”
- Offer: “Review changes” + “Overwrite anyway (admin)” if appropriate.

---

## 6) Handle latency and asynchronous actions cleanly

- **Disable submit** while saving; show inline progress.
- **Prevent double-submits** with idempotency keys or server-side protections.
- **Never hide failures**: show errors, keep form state intact, provide retry.
- **Treat slow lookups as first-class**: loading states for dropdowns/autocomplete.

---

## 7) Use the right input controls

### Text inputs
- Choose correct types (`email`, `tel`, `number` only if truly numeric).
- Provide placeholder examples sparingly; placeholders are not labels.

### Selects / dropdowns
- Use dropdown when options are small and stable (≈ 2–20).
- Use **autocomplete** for large option sets (users, locations, SKUs).
- Allow **search + keyboard navigation**.

### Dates / times
- Support manual entry + picker.
- Store and display time zones explicitly where relevant.

### Booleans
- Use a switch/checkbox with **clear labels** (“Enabled”, “Send notifications”).
- Avoid ambiguous labels (“Active?”) without context.

### Repeating groups
- Use “Add another” patterns for multiple phones/emails/line items.
- Validate each row independently; allow reordering if it matters.

---

## 8) Make required/optional status obvious

- **Mark required fields** clearly; don’t rely on “*” alone—include text like “Required”.
- For internal CRUD, consider **default optional** and validate “completeness” as a separate concept.

---

## 9) Keep forms readable and scannable

- **One column layout** for most forms; two columns only for very short/simple forms.
- Use **logical sections** with headings and short helper text.
- Keep helper text under ~1–2 lines; link to docs for details.

---

## 10) Safe, consistent destructive actions

- Use a **danger zone** section for delete/archive/disable.
- Confirm with **what will happen**:
  - “Deleting will remove this record from active lists and revoke access.”
- Prefer **undo** (toast with “Undo”) for soft deletes.
- Log who did it and when.

---

## 11) Security and privacy for internal apps

- **Server-side authorization on every write** (create/update/delete), not just UI gating.
- **CSRF protection** (if using cookies) and proper session management.
- **Audit logs** for write operations: actor, timestamp, changed fields (as permissible).
- **Least privilege UI**: hide or disable actions the user can’t perform.
- **Sensitive fields**: mask by default (SSN-like, tokens) and require re-auth if needed.

---

## 12) Data quality and domain-specific guardrails

- Use **reference data** and controlled vocabularies where possible.
- Normalize with user help:
  - Address validation / standardization
  - Phone formatting
- When importing/copy-pasting:
  - Support bulk paste
  - Detect common issues and offer fixes (“We split 20 lines into 20 items.”)

---

## 13) Make forms observable and supportable

- Capture **form errors** (client + server) with correlation IDs.
- Log server validation failures with context (not PII).
- Provide user-visible **request IDs** for support tickets.
- Track drop-off points in long forms (internal analytics).

---

## 14) Internationalization and formatting (if relevant)

- Don’t assume:
  - Name formats
  - Address formats
  - Decimal separators
- Store canonical formats; display localized.

---

## 15) Performance for “enterprise-sized” datasets

- For large relational data:
  - Use **typeahead** with server-side search rather than giant dropdowns.
  - Cache reference lists client-side with invalidation (ETags/versioning).
- Avoid fetching everything “just in case.”

---

## 16) Recommended UX patterns by scenario

### High-throughput data entry
- Minimal create form
- Strong defaults
- “Create another”
- Keyboard shortcuts (document them)

### High-risk edits (billing, compliance, permissions)
- Review step before save
- Change summaries (“You changed: status, owner, effective date”)
- Approval workflow if needed
- Mandatory comment / reason for change

### Multi-entity edits (line items)
- Inline row validation
- Totals computed live
- Save-as-draft + finalize action

---

## 17) A practical “golden path” implementation checklist

### Structure
- [ ] Task-ordered sections with clear headings
- [ ] Primary CTA at top and bottom (“Save” / “Create”)
- [ ] Secondary actions separated (“Cancel”, “Reset”, “Delete”)

### Validation
- [ ] Inline field errors + top summary
- [ ] Server errors shown without losing input
- [ ] Uniqueness and cross-field checks handled

### State safety
- [ ] Unsaved changes prompt
- [ ] Optimistic locking / conflict handling
- [ ] Soft delete + undo where feasible

### Accessibility
- [ ] Labels, focus management, keyboard support
- [ ] Error announcements via ARIA

### Security
- [ ] Server-side authz on writes
- [ ] Audit logging and data masking

### Performance
- [ ] Typeahead for large datasets
- [ ] Reference data caching with invalidation

---

## 18) Suggested form API shape (backend-friendly)

Even if your UI framework changes, keep backend contracts stable:

- **Create**: `POST /records`
- **Read**: `GET /records/{id}`
- **Update**: `PATCH /records/{id}`
- **Delete (soft)**: `DELETE /records/{id}` (or `POST /records/{id}:archive`)
- **Concurrency**: include `If-Match: <etag>` or a `version` field
- **Idempotency**: `Idempotency-Key` for create actions (optional but helpful)

---

## 19) Common anti-patterns to avoid

- Giant dropdowns with thousands of options
- Placeholder text used as the only label
- Errors shown only after submit
- Resetting the whole form on a single-field error
- “Are you sure?” confirmations without context
- Deleting without undo/audit trail
- Client-side-only authorization

---

## 20) What to standardize across your internal CRUD apps

- Form layout and spacing
- Error message style and placement
- Loading/saving states
- Confirmation + undo patterns
- Audit log visibility
- Date/time formatting rules
- Permission-based UI behavior

---

### Optional: “definition of done” for a new CRUD form

A form is production-ready when:
- Users can complete core flows quickly (create/edit) without training
- Validation is clear and fast, and never loses input
- Conflicts, deletes, and partial failures are safely handled
- The UI is accessible and keyboard-friendly
- Authorization and auditing are enforced server-side
