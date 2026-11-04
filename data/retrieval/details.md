# Code search - per-ticket details

For each golden ticket: the files the real fix changed (targets) and where each search put them, then the hybrid top 20 with targets marked **<- target**.
Combined = keywords + links (no embeddings). Hybrid = keywords + meaning (nomic-embed-text) + links. Rank `-` = not in the top 20. `*` after the group = ticket names code files.

## Summary

| Ticket | Group | Title | Targets | Best rank combined | Best rank hybrid |
|---|---|---|---|---|---|
| SPEC-1 (O3-5714) | cross-repo * | Patient search results unmount and remount on every keystroke, causing | 10 | 1 | 1 |
| SPEC-2 (O3-5836) | cross-repo * | Starting a visit from a patient search result throws because the patie | 2 | 6 | 3 |
| SPEC-3 (O3-6020) | cross-repo | Visit Notes workspace should accept a Encounter object for editing | 4 | 2 | 1 |
| SPEC-4 (O3-5986) | cross-repo | Saved image attachments are missing when editing a visit note | 13 | 6 | 2 |
| SPEC-5 (O3-5823) | cross-repo * | Capture and surface diagnosis certainty (confirmed / provisional) | 11 | 1 | 1 |
| SPEC-6 (O3-5763) | cross-repo | Unify the Current visit and Previous visit views | 27 | 1 | 1 |
| SPEC-7 (O3-6028) | clear | Login location picker ignores the configured number of locations to lo | 3 | 1 | 1 |
| SPEC-8 (O3-5981) | clear * | Unhandled rejections pass a raw Error into the toast description, whic | 1 | - | - |
| SPEC-9 (O3-5849) | clear | Improve the Workspace2 unsaved-changes confirmation modal | 3 | 1 | 3 |
| SPEC-10 (O3-6026) | clear | Vitals and biometrics chart view shows a loading spinner and causes la | 2 | 1 | 5 |
| SPEC-11 (O3-6019) | clear | Prevent loss of unsaved medication dosage entries when switching dosag | 2 | 2 | 2 |
| SPEC-12 (O3-5969) | clear | Improve keyboard access and edit wording in the conditions form | 4 | 1 | 1 |
| SPEC-13 (O3-5798) | clear | Add the current past visit context to the patient header so users can  | 2 | - | - |
| SPEC-14 (O3-5850) | clear | Support concept reference ranges in the Angular form engine | 4 | 17 | 19 |
| SPEC-15 (O3-4444) | clear | Persist user-selected start date on medication orders | 10 | 1 | 4 |
| SPEC-16 (O3-5817) | clear | Add a schema-configurable searchable dropdown backed by a live REST en | 1 | 1 | 1 |
| SPEC-17 (O3-5889) | clear | Support fullWidth configuration for obs-by-encounter-widget | 2 | 5 | 4 |
| SPEC-18 (O3-5665) | clear | Vitals form button has broken template literal and missing import | 6 | 1 | 1 |
| SPEC-19 (O3-5910) | clear | Patient registration: Preserve local-language names when editing a pat | 1 | 1 | 2 |
| SPEC-20 (O3-5912) | clear | Regression: Address hierarchy does not clear dependent fields | 2 | 2 | 2 |
| SPEC-21 (O3-5913) | clear | Patient registration: Wait for deletions before reporting a successful | 1 | 2 | 1 |
| SPEC-22 (O3-5918) | clear * | Allow birth and death on the same calendar day | 1 | 4 | 4 |
| SPEC-23 (O3-6098) | clear * | Service Queues always shows “Scheduled for today” and “On time” | 4 | 2 | 2 |
| SPEC-24 (O3-5917) | clear * | Keep newly added relationship rows correctly associated | 2 | 1 | 4 |
| SPEC-25 (O3-5919) | clear * | Clear stale death metadata when marking a patient alive | 2 | 4 | 4 |
| SPEC-26 (O3-5914) | clear * | Preserve existing location attributes while searching | 2 | 1 | 1 |
| SPEC-27 (O3-5666) | clear | "Call" action crashes the page when the API request fails | 3 | 10 | 2 |
| SPEC-28 (O3-5916) | clear * | Make automatically generated patient identifiers retry-safe | 2 | 3 | 3 |
| SPEC-29 (O3-5680) | clear * | Make calling status and drug order type filters configurable | 6 | 2 | 1 |
| SPEC-30 (O3-6112) | normal * | Billing "Create bill / Add bill items" workspace doesn't show which pa | 1 | 1 | 1 |
| SPEC-31 (O3-5411) | normal | Automatically Waive Consultation Fees for Return Visits Within 7 Days | 4 | 2 | 1 |
| SPEC-32 (O3-5413) | normal | Enable Refund Requests and Approval for Paid Bills | 8 | 3 | 4 |
| SPEC-33 (O3-5417) | normal | Bill Discount Management with Audit Trail | 14 | 3 | 2 |
| SPEC-34 (O3-5708) | normal | Review discounts modal closes after first action even when multiple di | 1 | - | - |
| SPEC-35 (O3-5743) | normal | UI doesn't make it clear bill must be finalized before payment | 2 | 2 | 3 |
| SPEC-36 (O3-5816) | normal * | Login crashes with uncaught TypeError when no Login Locations are conf | 1 | 3 | 2 |
| SPEC-37 (O3-5874) | normal * | Change language modal and user menu language item crash with RangeErro | 7 | 1 | 1 |
| SPEC-38 (O3-5588) | normal * | fix(login-app): Login Location tag filter silently ignored in useLocat | 1 | 1 | 2 |
| SPEC-39 (O3-5838) | normal | Implement the Two-Factor Verification Page (TOTP) | 2 | 2 | 1 |
| SPEC-40 (O3-5449) | normal | Integrate Chart Line Icon for Growth Chart in Left Navigation | 4 | - | 1 |
| SPEC-41 (O3-5650) | normal * | Dispensing: Support limiting prescriptions shown to locations under se | 5 | 1 | 1 |
| SPEC-42 (O3-5632) | normal * | Dispensing modal: "Dispense all prescriptions" fires before medication | 1 | 1 | 3 |
| SPEC-43 (O3-4692) | normal | Display "Dispensed" Status in Prescription Details Section (Consistent | 2 | 10 | 11 |
| SPEC-44 (O3-5705) | vague | Receipt shows discount as outstanding balance on fully paid bills | 2 | 1 | 5 |
| SPEC-45 (O3-5706) | vague | "Paying" option is unselectable when patient has a recent prior visit  | 1 | 1 | 2 |
| SPEC-46 (O3-5202) | vague | Add a UI button to "finalize" a bill | 13 | 18 | 1 |
| SPEC-47 (O3-5027) | vague | Beautiful + Configurable Login Page | 2 | 2 | 1 |
| SPEC-48 (O3-5630) | vague | Dispensing: Bug when editing substitution reason of an old order | 3 | 1 | 1 |
| SPEC-49 (O3-5610) | vague | Add result date column to lab order result | 3 | 13 | - |
| SPEC-50 (O3-4578) | vague | Duplicate Dose Entries in Immunization Module | 3 | 1 | 3 |
| SPEC-51 (O3-5677) | vague | Frontend print button for visit summary in O3 patient chart | 2 | - | 6 |
| SPEC-52 (O3-5078) | vague | Sticky Note in O3 | 2 | 11 | 8 |
| SPEC-53 (O3-5801) | vague | Location obs should display location name not the location id | 1 | - | - |
| SPEC-54 (O3-5436) | vague | Align test result values and reference range columns in the Tests tab | 2 | - | 12 |
| SPEC-55 (O3-5452) | vague | Printing encounters based on O3-forms | 6 | - | 16 |
| SPEC-56 (O3-5534) | vague | Fix index-based keys in address search suggestions causing incorrect s | 1 | 8 | 1 |
| SPEC-57 (O3-5545) | vague |  Prev/Next navigation in appointments calendar monthly view is not wor | 6 | 1 | 1 |
| SPEC-58 (O3-5592) | vague | Appointment Services should be sorted alphabetically | 4 | 9 | 11 |
| SPEC-59 (O3-5742) | vague | Build DailyCalendarView with compact appointment card list | 0 | - | - |
| SPEC-60 (O3-5737) | vague | Appointments: Download button is oversized with more padding | 1 | 3 | 8 |
| SPEC-61 (O3-5729) | vague | Build WeeklyCalendarView with CSS Grid time-slot layout | 0 | - | - |
| SPEC-62 (O3-5624) | vague | Ward App: add way to show the discharge workspace only in certain loca | 2 | 2 | 1 |
| SPEC-63 (O3-5645) | security * | Prevent open redirect via unvalidated returnToUrl | 4 | 5 | 5 |

## SPEC-1 (O3-5714) - cross-repo (names code files)

**Patient search results unmount and remount on every keystroke, causing multi-second UI stalls and heap growth**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-search-app/src/compact-patient-search.extension.tsx` | 3 | 4 |
| `patient-management/packages/esm-patient-search-app/src/compact-patient-search/compact-patient-banner.component.tsx` | 10 | - |
| `patient-management/packages/esm-patient-search-app/src/compact-patient-search/compact-patient-search.component.tsx` | 6 | 5 |
| `patient-management/packages/esm-patient-search-app/src/compact-patient-search/loader.component.tsx` | - | - |
| `patient-management/packages/esm-patient-search-app/src/compact-patient-search/patient-search.component.tsx` | 14 | 3 |
| `patient-management/packages/esm-patient-search-app/src/compact-patient-search/recently-searched-patients.component.tsx` | - | 12 |
| `patient-management/packages/esm-patient-search-app/src/hooks/useArrowNavigation.tsx` | - | 6 |
| `patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-search-lg.component.tsx` | 9 | 13 |
| `patient-management/packages/esm-patient-search-app/src/patient-search.resource.tsx` | 1 | 1 |
| `patient-management/packages/esm-service-queues-app/src/patient-banner-extension/patient-banner-queue-entry-status.extension.tsx` | - | 8 |

(1 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-management/packages/esm-patient-search-app/src/patient-search.resource.tsx` **<- target**
2. `patient-management/packages/esm-patient-search-app/src/patient-search-bar/patient-search-bar.component.tsx`
3. `patient-management/packages/esm-patient-search-app/src/compact-patient-search/patient-search.component.tsx` **<- target**
4. `patient-management/packages/esm-patient-search-app/src/compact-patient-search.extension.tsx` **<- target**
5. `patient-management/packages/esm-patient-search-app/src/compact-patient-search/compact-patient-search.component.tsx` **<- target**
6. `patient-management/packages/esm-patient-search-app/src/hooks/useArrowNavigation.tsx` **<- target**
7. `patient-management/packages/esm-patient-search-app/src/patient-search-page/advanced-patient-search.component.tsx`
8. `patient-management/packages/esm-service-queues-app/src/patient-banner-extension/patient-banner-queue-entry-status.extension.tsx` **<- target**
9. `patient-management/packages/esm-patient-search-app/src/patient-search-icon/patient-search-icon.component.tsx`
10. `patient-management/packages/esm-patient-list-management-app/src/list-details-table/list-details-table.component.tsx`
11. `patient-management/packages/esm-service-queues-app/src/hooks/useQueueEntries.ts`
12. `patient-management/packages/esm-patient-search-app/src/compact-patient-search/recently-searched-patients.component.tsx` **<- target**
13. `patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-search-lg.component.tsx` **<- target**
14. `patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-banner/banner/patient-banner.component.tsx`
15. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/refine-search.component.tsx`
16. `patient-management/packages/esm-service-queues-app/src/queue-patient-linelists/queue-linelist-base-table.component.tsx`
17. `patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-search-page.component.tsx`
18. `core/packages/framework/esm-styleguide/src/patient-banner/actions-menu/patient-banner-actions-menu.component.tsx`
19. `patient-chart/packages/esm-patient-banner-app/src/hooks/useCauseOfDeath.ts`
20. `core/packages/apps/esm-devtools-app/src/devtools/import-map-list/list.component.tsx`

## SPEC-2 (O3-5836) - cross-repo (names code files)

**Starting a visit from a patient search result throws because the patient-chart workspace group is launched without group props**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-chart-app/src/visit/start-visit-button.component.tsx` | 6 | 3 |
| `patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-banner/banner/patient-banner.component.tsx` | 10 | - |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/visit-form.workspace.tsx`
2. `patient-chart/packages/esm-patient-chart-app/src/actions-buttons/start-visit.component.tsx`
3. `patient-chart/packages/esm-patient-chart-app/src/visit/start-visit-button.component.tsx` **<- target**
4. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-prompt/start-visit-dialog.modal.tsx`
5. `patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-banner/banner/start-visit-button2.component.tsx`
6. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
7. `patient-chart/packages/esm-patient-common-lib/src/workspaces.ts`
8. `patient-management/packages/esm-patient-list-management-app/src/root.component.tsx`
9. `patient-management/packages/esm-service-queues-app/src/create-queue-entry/create-queue-entry.workspace.tsx`
10. `patient-management/packages/esm-patient-search-app/src/patient-search-button/patient-search-button.component.tsx`
11. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-action-items/edit-visit-details.component.tsx`
12. `patient-chart/packages/esm-patient-forms-app/src/forms/form-entry.component.tsx`
13. `patient-chart/packages/esm-patient-common-lib/src/form-entry/form-entry.ts`
14. `patient-management/packages/esm-patient-search-app/src/patient-search-context.ts`
15. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/utils/helpers.ts`
16. `patient-management/packages/esm-patient-search-app/src/patient-search-icon/patient-search-icon.component.tsx`
17. `patient-management/packages/esm-ward-app/src/ward-workspace/create-admission-encounter/create-admission-encounter.workspace.tsx`
18. `patient-management/packages/esm-service-queues-app/src/create-queue-entry/existing-visit-form/existing-visit-form.component.tsx`
19. `core/packages/framework/esm-styleguide/src/workspaces2/workspace2.ts`
20. `patient-chart/packages/esm-patient-chart-app/src/index.ts`

## SPEC-3 (O3-6020) - cross-repo

**Visit Notes workspace should accept a Encounter object for editing**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx` | 2 | 1 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` | 3 | 3 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/single-visit-details/visit-timeline/visit-timeline.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit.resource.tsx` | - | - |

(3 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx` **<- target**
2. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx`
3. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` **<- target**
4. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/encounter-list.component.tsx`
5. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts`
6. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.resource.ts`
7. `patient-management/packages/esm-service-queues-app/src/service-queues.resource.ts`
8. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes.resource.ts`
9. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/history/note.component.tsx`
10. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
11. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/types.ts`
12. `patient-chart/packages/esm-patient-common-lib/src/form-entry/form-entry.ts`
13. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/visit-encounters-table.component.tsx`
14. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/types.ts`
15. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
16. `dispensing-app/src/utils.ts`
17. `patient-management/packages/esm-ward-app/src/types/index.ts`
18. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
19. `patient-management/packages/esm-service-queues-app/src/admin/queue-rooms/queue-room-form.workspace.tsx`
20. `core/packages/framework/esm-routes/src/loaders/components.ts`

## SPEC-4 (O3-5986) - cross-repo

**Saved image attachments are missing when editing a visit note**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/framework/esm-emr-api/mock-jest.ts` | - | - |
| `core/packages/framework/esm-emr-api/mock.ts` | - | - |
| `core/packages/framework/esm-emr-api/src/attachments.ts` | 20 | 18 |
| `core/packages/framework/esm-react-utils/src/useAttachments.ts` | - | - |
| `core/packages/tooling/storybook/mocks/esm-emr-api.ts` | - | - |
| `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachment-preview.component.tsx` | 6 | 2 |
| `patient-chart/packages/esm-patient-attachments-app/src/index.ts` | - | - |
| `patient-chart/packages/esm-patient-attachments-app/src/utils.ts` | - | 16 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/encounter-observations/encounter-observations.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit.resource.tsx` | - | - |
| `patient-chart/packages/esm-patient-common-lib/src/index.ts` | - | - |
| `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes.resource.ts` | - | 8 |

(5 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/camera-media-uploader.component.tsx`
2. `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachment-preview.component.tsx` **<- target**
3. `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachments-grid-overview.component.tsx`
4. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx`
5. `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachments-overview.component.tsx`
6. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/file-review.component.tsx`
7. `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachments-table-overview.component.tsx`
8. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes.resource.ts` **<- target**
9. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts`
10. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/history/note.component.tsx`
11. `patient-chart/packages/esm-form-engine-app/src/index.ts`
12. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/capture-photo.component.tsx`
13. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/upload-status.component.tsx`
14. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
15. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.resource.ts`
16. `patient-chart/packages/esm-patient-attachments-app/src/utils.ts` **<- target**
17. `patient-chart/packages/esm-patient-notes-app/src/notes/notes-overview.extension.tsx`
18. `core/packages/framework/esm-emr-api/src/attachments.ts` **<- target**
19. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/history/notes-container.component.tsx`
20. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-note-config-schema.ts`

## SPEC-5 (O3-5823) - cross-repo (names code files)

**Capture and surface diagnosis certainty (confirmed / provisional)**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/framework/esm-styleguide/mock-jest.tsx` | - | - |
| `core/packages/framework/esm-styleguide/mock.tsx` | - | - |
| `core/packages/framework/esm-styleguide/src/config-schema.ts` | 14 | - |
| `core/packages/framework/esm-styleguide/src/diagnosis-tags/diagnosis-tags.component.tsx` | 12 | 7 |
| `core/packages/framework/esm-styleguide/src/diagnosis-tags/diagnosis-tags.stories.tsx` | - | 12 |
| `core/packages/framework/esm-translations/src/translations.ts` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visit-history-table/visit-diagnoses-cell.component.tsx` | - | 9 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` | 4 | 18 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx` | 11 | - |
| `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes.resource.ts` | 2 | 2 |
| `patient-chart/packages/esm-patient-notes-app/src/types/index.ts` | 1 | 1 |

(3 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts` **<- target**
2. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes.resource.ts` **<- target**
3. `patient-chart/packages/esm-patient-notes-app/src/config-schema.ts`
4. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx`
5. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-note-config-schema.ts`
6. `patient-chart/packages/esm-form-entry-app/src/app/types/index.ts`
7. `core/packages/framework/esm-styleguide/src/diagnosis-tags/diagnosis-tags.component.tsx` **<- target**
8. `patient-chart/packages/esm-form-entry-app/src/app/form-submission/form-submission.service.ts`
9. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-history-table/visit-diagnoses-cell.component.tsx` **<- target**
10. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit.resource.tsx`
11. `dispensing-app/src/diagnoses/diagnoses.resource.ts`
12. `core/packages/framework/esm-styleguide/src/diagnosis-tags/diagnosis-tags.stories.tsx` **<- target**
13. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/history/note.component.tsx`
14. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
15. `patient-management/packages/esm-ward-app/src/ward-patient-card/row-elements/ward-patient-coded-obs-tags.component.tsx`
16. `patient-management/packages/esm-ward-app/src/ward-patient-card/card-rows/coded-obs-tags-row.component.tsx`
17. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.component.tsx`
18. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` **<- target**
19. `patient-management/packages/esm-active-visits-app/src/visits-summary/visits-components/visit-summary.component.tsx`
20. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.workspace.tsx`

## SPEC-6 (O3-5763) - cross-repo

**Unify the Current visit and Previous visit views**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-chart-app/src/index.ts` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx` | - | 11 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/visit-encounters-table.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx` | 3 | 4 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/single-visit-details/visit-timeline/visit-timeline.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-notes-app/src/index.ts` | - | - |
| `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx` | 13 | 8 |
| `patient-management/packages/esm-service-queues-app/src/config-schema.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/constants.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/create-queue-entry/existing-visit-form/existing-visit-form.component.tsx` | 17 | 6 |
| `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit-summary.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit.resource.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/hooks/useVitalsConceptMetadata.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/biometrics-config-schema.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/current-visit-details.component.tsx` | 7 | 10 |
| `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/vitals-config-schema.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/vitals.component.tsx` | 9 | - |
| `patient-management/packages/esm-service-queues-app/src/modals/add-or-move-modal/add-patient-to-queue.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/encounter-list.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/medications-list.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/notes-list.component.tsx` | 12 | - |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/past-visit-summary.component.tsx` | 4 | 5 |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit.component.tsx` | 1 | 1 |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit.resource.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx` | 8 | 2 |
| `patient-management/packages/esm-service-queues-app/src/types/index.ts` | - | 15 |

(11 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit.component.tsx` **<- target**
2. `patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx` **<- target**
3. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-history-table/visit-history-table.component.tsx`
4. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx` **<- target**
5. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/past-visit-summary.component.tsx` **<- target**
6. `patient-management/packages/esm-service-queues-app/src/create-queue-entry/existing-visit-form/existing-visit-form.component.tsx` **<- target**
7. `patient-chart/packages/esm-patient-notes-app/src/notes/notes-overview.extension.tsx`
8. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx` **<- target**
9. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-header.extension.tsx`
10. `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/current-visit-details.component.tsx` **<- target**
11. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx` **<- target**
12. `patient-management/packages/esm-active-visits-app/src/visits-summary/visits-components/visit-summary.component.tsx`
13. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-detail-overview.component.tsx`
14. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`
15. `patient-management/packages/esm-service-queues-app/src/types/index.ts` **<- target**
16. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/encounter-list/encounter-list-tabs.extension.tsx`
17. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/current-visit-summary.extension.tsx`
18. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions.resource.ts`
19. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/active-visit-buttons/active-visit-buttons.tsx`
20. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts`

## SPEC-7 (O3-6028) - clear

**Login location picker ignores the configured number of locations to load**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-login-app/src/config-schema.ts` | 1 | 1 |
| `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx` | 3 | 2 |
| `core/packages/apps/esm-login-app/src/login.resource.ts` | 20 | 7 |

Hybrid top 20:

1. `core/packages/apps/esm-login-app/src/config-schema.ts` **<- target**
2. `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx` **<- target**
3. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.component.tsx`
4. `core/packages/apps/esm-login-app/src/login/login.component.tsx`
5. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts`
6. `core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts`
7. `core/packages/apps/esm-login-app/src/login.resource.ts` **<- target**
8. `patient-management/packages/esm-ward-app/src/location-selector/location-selector.component.tsx`
9. `core/packages/apps/esm-login-app/src/index.ts`
10. `billing-app/tools/i18next-parser.config.js`
11. `dispensing-app/tools/i18next-parser.config.js`
12. `patient-management/packages/esm-ward-app/src/config-schema.ts`
13. `patient-management/tools/i18next-parser.config.js`
14. `patient-chart/tools/i18next-parser.config.js`
15. `core/packages/apps/esm-implementer-tools-app/src/configuration/json-editor/json-editor.component.tsx`
16. `patient-chart/packages/esm-patient-programs-app/src/programs/programs-form.workspace.tsx`
17. `core/packages/framework/esm-styleguide/mock.tsx`
18. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
19. `core/packages/framework/esm-styleguide/mock-jest.tsx`
20. `patient-management/packages/esm-appointments-app/src/appointments/common-components/location-select-option.component.tsx`

## SPEC-8 (O3-5981) - clear (names code files)

**Unhandled rejections pass a raw Error into the toast description, which React cannot render**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/framework/esm-error-handling/src/index.ts` | - | - |

Hybrid top 20:

1. `core/packages/framework/esm-styleguide/src/toasts/active-toasts.component.tsx`
2. `patient-chart/packages/esm-form-engine-app/src/form-renderer/form-error.component.tsx`
3. `core/packages/framework/esm-styleguide/src/toasts/toast.stories.tsx`
4. `core/packages/framework/esm-styleguide/src/toasts/index.tsx`
5. `core/packages/framework/esm-globals/src/events.ts`
6. `core/packages/shell/esm-app-shell/src/routing-events.ts`
7. `patient-chart/packages/esm-form-engine-app/src/form-renderer/repeat/delete-question.modal.tsx`
8. `core/packages/shell/esm-app-shell/src/run.ts`
9. `core/packages/framework/esm-styleguide/src/toasts/toast.component.tsx`
10. `core/packages/framework/esm-api/src/openmrs-fetch.ts`
11. `patient-chart/packages/esm-form-engine-app/src/form-renderer/form-renderer.component.tsx`
12. `core/packages/shell/esm-app-shell/src/service-worker/message.ts`
13. `core/packages/framework/esm-styleguide/src/notifications/actionable-notification.stories.tsx`
14. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts`
15. `core/packages/apps/esm-implementer-tools-app/src/implementer-tools.component.tsx`
16. `core/packages/framework/esm-react-utils/src/OpenmrsContext.ts`
17. `patient-chart/packages/esm-form-engine-app/src/index.ts`
18. `core/packages/framework/esm-styleguide/src/notifications/notification.stories.tsx`
19. `core/packages/framework/esm-dynamic-loading/src/dynamic-loading.ts`
20. `core/packages/framework/esm-styleguide/src/notifications/index.tsx`

## SPEC-9 (O3-5849) - clear

**Improve the Workspace2 unsaved-changes confirmation modal**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/framework/esm-styleguide/src/workspaces2/workspace2-close-prompt.modal.tsx` | 1 | 3 |
| `core/packages/framework/esm-styleguide/src/workspaces2/workspace2.ts` | 9 | 8 |
| `core/packages/framework/esm-translations/src/translations.ts` | 5 | 4 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/before-save-prompt.component.tsx`
2. `core/packages/framework/esm-styleguide/src/workspaces/notification/workspace-notification.component.tsx`
3. `core/packages/framework/esm-styleguide/src/workspaces2/workspace2-close-prompt.modal.tsx` **<- target**
4. `core/packages/framework/esm-translations/src/translations.ts` **<- target**
5. `core/packages/framework/esm-styleguide/src/workspaces2/workspace2.component.tsx`
6. `patient-management/packages/esm-patient-registration-app/src/widgets/cancel-patient-edit.modal.tsx`
7. `core/packages/framework/esm-styleguide/src/workspaces/workspaces.ts`
8. `core/packages/framework/esm-styleguide/src/workspaces2/workspace2.ts` **<- target**
9. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/history/delete-note.modal.tsx`
10. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments-cancel.modal.tsx`
11. `dispensing-app/src/forms/close-dispense-form.workspace.tsx`
12. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-confirm-action.modal.tsx`
13. `patient-management/packages/esm-appointments-app/src/appointments/common-components/batch-change-appointment-statuses.modal.tsx`
14. `patient-management/packages/esm-ward-app/src/ward-workspace/cancel-admission-request-workspace/cancel-admission-request.component.tsx`
15. `patient-chart/packages/esm-patient-tests-app/src/edit-test-results/modal/edit-lab-results.modal.tsx`
16. `core/packages/framework/esm-styleguide/src/modals/index.tsx`
17. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-prompt/modify-visit-date.modal.tsx`
18. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/delete-encounter.modal.tsx`
19. `dispensing-app/src/types.ts`
20. `core/packages/framework/esm-styleguide/src/workspaces2/action-menu2/action-menu-button2.component.tsx`

## SPEC-10 (O3-6026) - clear

**Vitals and biometrics chart view shows a loading spinner and causes layout jump on first switch**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-vitals-app/src/biometrics/biometrics-base.component.tsx` | 2 | 6 |
| `patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx` | 1 | 5 |

Hybrid top 20:

1. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table/obs-table.component.tsx`
2. `patient-chart/packages/esm-patient-vitals-app/src/common/helpers.ts`
3. `patient-chart/packages/esm-generic-patient-widgets-app/src/config-schema-obs-switchable.ts`
4. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-switchable/obs-switchable.component.tsx`
5. `patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx` **<- target**
6. `patient-chart/packages/esm-patient-vitals-app/src/biometrics/biometrics-base.component.tsx` **<- target**
7. `patient-chart/packages/esm-patient-vitals-app/src/biometrics/biometrics-overview.component.tsx`
8. `patient-chart/packages/esm-patient-vitals-app/src/biometrics/paginated-biometrics.component.tsx`
9. `patient-chart/packages/esm-patient-vitals-app/src/vitals-and-biometrics-header/vitals-header.extension.tsx`
10. `patient-chart/packages/esm-patient-vitals-app/src/vitals/paginated-vitals.component.tsx`
11. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.component.tsx`
12. `patient-chart/packages/esm-patient-vitals-app/src/vitals-and-biometrics-header/vitals-header-item.component.tsx`
13. `patient-chart/packages/esm-patient-vitals-app/src/common/index.ts`
14. `patient-chart/packages/esm-patient-vitals-app/src/config-schema.ts`
15. `patient-chart/packages/esm-patient-vitals-app/src/common/data.resource.ts`
16. `patient-chart/packages/esm-patient-vitals-app/src/biometrics/biometrics-main.component.tsx`
17. `patient-chart/packages/esm-patient-vitals-app/src/vitals-biometrics-form/vitals-biometrics-input.component.tsx`
18. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-overview.component.tsx`
19. `patient-chart/packages/esm-patient-vitals-app/src/biometrics/biometrics-chart.component.tsx`
20. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-detailed-summary.component.tsx`

## SPEC-11 (O3-6019) - clear

**Prevent loss of unsaved medication dosage entries when switching dosage modes**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/add-drug-order.component.tsx` | 17 | 14 |
| `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.component.tsx` | 2 | 2 |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.resource.ts`
2. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.component.tsx` **<- target**
3. `patient-chart/packages/esm-patient-common-lib/src/orders/types/order.ts`
4. `dispensing-app/src/medication-dispense/medication-dispense.resource.tsx`
5. `dispensing-app/src/forms/medication-dispense-review.component.tsx`
6. `patient-chart/packages/esm-patient-medications-app/src/api/order-config.ts`
7. `patient-chart/packages/esm-patient-common-lib/src/orders/useOrders.ts`
8. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
9. `patient-chart/packages/esm-patient-orders-app/src/order-basket/general-order-type/general-order-form/general-order-form.component.tsx`
10. `patient-chart/packages/esm-patient-medications-app/src/api/api.ts`
11. `patient-chart/packages/esm-patient-orders-app/src/components/medication-record.component.tsx`
12. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/medications-summary.component.tsx`
13. `patient-chart/packages/esm-patient-medications-app/src/config-schema.ts`
14. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/add-drug-order.component.tsx` **<- target**
15. `dispensing-app/src/utils.ts`
16. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/medications-list.component.tsx`
17. `dispensing-app/src/forms/dispense-form.workspace.tsx`
18. `patient-management/packages/esm-active-visits-app/src/types/index.ts`
19. `patient-chart/packages/esm-form-entry-app/src/app/types/index.ts`
20. `patient-management/packages/esm-active-visits-app/src/visits-summary/visits-components/medications-summary.component.tsx`

## SPEC-12 (O3-5969) - clear

**Improve keyboard access and edit wording in the conditions form**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-action-menu.component.tsx` | 9 | 8 |
| `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-form.workspace.tsx` | 2 | 1 |
| `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx` | 1 | 2 |
| `patient-chart/packages/esm-patient-conditions-app/src/index.ts` | - | 4 |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-form.workspace.tsx` **<- target**
2. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx` **<- target**
3. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions.resource.ts`
4. `patient-chart/packages/esm-patient-conditions-app/src/index.ts` **<- target**
5. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-overview.component.tsx`
6. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-detailed-summary.component.tsx`
7. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx`
8. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-action-menu.component.tsx` **<- target**
9. `patient-management/packages/esm-patient-search-app/src/patient-search-context.ts`
10. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes.resource.ts`
11. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
12. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-switcher.modal.tsx`
13. `patient-management/packages/esm-patient-search-app/src/patient-search-workspace/patient-search.workspace.tsx`
14. `patient-chart/packages/esm-patient-tests-app/src/edit-test-results/modal/edit-lab-results.modal.tsx`
15. `patient-management/packages/esm-patient-search-app/src/patient-search-overlay/patient-search-overlay.component.tsx`
16. `patient-management/packages/esm-patient-list-management-app/src/list-details-table/list-details-table.component.tsx`
17. `patient-chart/packages/esm-patient-allergies-app/src/allergies/allergies-form/allergy-form.workspace.tsx`
18. `dispensing-app/src/history/history-and-comments.component.tsx`
19. `patient-chart/packages/esm-patient-vitals-app/src/vitals-biometrics-form/exported-vitals-biometrics-form.workspace.tsx`
20. `patient-chart/packages/esm-patient-common-lib/src/form-entry/form-entry.ts`

## SPEC-13 (O3-5798) - clear

**Add the current past visit context to the patient header so users can easily identify the visit they are currently working in.**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-banner-app/src/banner-tags/visit-tag.extension.tsx` | - | - |
| `patient-chart/packages/esm-patient-banner-app/src/index.ts` | - | - |

(1 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
2. `patient-chart/packages/esm-patient-medications-app/src/api/api.ts`
3. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/past-visit-summary.component.tsx`
4. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/visit-form.resource.ts`
5. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-header.extension.tsx`
6. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx`
7. `patient-management/packages/esm-service-queues-app/src/metrics/metrics.resource.ts`
8. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit.component.tsx`
9. `patient-management/packages/esm-active-visits-app/src/active-visits-widget/active-visits.resource.ts`
10. `patient-chart/packages/esm-patient-chart-app/src/patient-chart/patient-chart.resources.ts`
11. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-info.component.tsx`
12. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-switcher.modal.tsx`
13. `patient-management/packages/esm-ward-app/src/hooks/useInpatientAdmission.ts`
14. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts`
15. `patient-chart/packages/esm-patient-chart-app/src/index.ts`
16. `patient-management/packages/esm-active-visits-app/src/types/index.ts`
17. `patient-management/packages/esm-active-visits-app/src/active-visits-widget/active-visits.component.tsx`
18. `patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts`
19. `core/packages/framework/esm-react-utils/src/useVisit.ts`
20. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/medications-list.component.tsx`

## SPEC-14 (O3-5850) - clear

**Support concept reference ranges in the Angular form engine**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts` | 17 | 19 |
| `patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts` | - | - |
| `patient-chart/packages/esm-form-entry-app/src/app/openmrs-api/openmrs-api.module.ts` | - | - |
| `patient-chart/packages/esm-form-entry-app/src/app/types/index.ts` | - | - |

(2 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `core/packages/framework/esm-styleguide/src/numeric-observation/interpretation-utils.ts`
2. `patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/reference-range-helpers.ts`
3. `core/packages/framework/esm-styleguide/src/numeric-observation/use-concept-reference-range.ts`
4. `patient-chart/packages/esm-patient-tests-app/src/test-results/loadPatientTestData/helpers.ts`
5. `core/packages/framework/esm-styleguide/src/numeric-observation/numeric-observation.component.tsx`
6. `patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/useObstreeData.ts`
7. `patient-chart/packages/esm-patient-common-lib/src/results/useReferenceRanges.ts`
8. `patient-chart/packages/esm-patient-vitals-app/src/common/data.resource.ts`
9. `patient-chart/packages/esm-patient-tests-app/src/test-results/loadPatientTestData/loadPatientData.ts`
10. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
11. `patient-chart/packages/esm-patient-tests-app/src/types.ts`
12. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results-form-field.component.tsx`
13. `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table-tablet/helper.tsx`
14. `patient-chart/packages/esm-patient-common-lib/src/results/helpers.ts`
15. `patient-chart/packages/esm-patient-orders-app/src/utils/index.ts`
16. `patient-chart/packages/esm-patient-vitals-app/src/vitals-biometrics-form/vitals-biometrics-form.utils.ts`
17. `patient-chart/packages/esm-patient-tests-app/src/test-results/trendline/trendline-resource.tsx`
18. `patient-chart/packages/esm-patient-vitals-app/src/common/helpers.ts`
19. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts` **<- target**
20. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results-schema.resource.tsx`

## SPEC-15 (O3-4444) - clear

**Persist user-selected start date on medication orders**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-common-lib/src/orders/postOrders.ts` | 9 | 4 |
| `patient-chart/packages/esm-patient-common-lib/src/orders/types/order.ts` | - | 14 |
| `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/add-drug-order.component.tsx` | 3 | 5 |
| `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.component.tsx` | 12 | 13 |
| `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.resource.ts` | - | 12 |
| `patient-chart/packages/esm-patient-medications-app/src/api/api.ts` | 1 | 6 |
| `patient-chart/packages/esm-patient-medications-app/src/config-schema.ts` | - | - |
| `patient-chart/packages/esm-patient-orders-app/src/order-basket/order-basket.component.tsx` | 10 | - |
| `patient-chart/packages/esm-patient-orders-app/src/order-basket/order-basket.utils.ts` | - | - |
| `patient-chart/packages/esm-patient-orders-app/src/utils/index.ts` | - | - |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-orders-app/src/order-basket/general-order-type/general-order-form/general-order-form.component.tsx`
2. `patient-chart/packages/esm-patient-orders-app/src/order-basket/general-order-type/resources.ts`
3. `patient-chart/packages/esm-form-entry-app/src/app/types/index.ts`
4. `patient-chart/packages/esm-patient-common-lib/src/orders/postOrders.ts` **<- target**
5. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/add-drug-order.component.tsx` **<- target**
6. `patient-chart/packages/esm-patient-medications-app/src/api/api.ts` **<- target**
7. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/retrospective-data-date-time-picker/retrospective-date-time-picker.component.tsx`
8. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts`
9. `patient-chart/packages/esm-patient-orders-app/src/components/order-details-table.component.tsx`
10. `dispensing-app/src/utils.ts`
11. `patient-chart/packages/esm-form-entry-app/src/app/form-submission/form-submission.service.ts`
12. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.resource.ts` **<- target**
13. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.component.tsx` **<- target**
14. `patient-chart/packages/esm-patient-common-lib/src/orders/types/order.ts` **<- target**
15. `patient-chart/packages/esm-patient-medications-app/src/drug-order-basket-panel/drug-order-basket-panel.extension.tsx`
16. `patient-chart/packages/esm-patient-tests-app/src/test-orders/api.ts`
17. `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx`
18. `patient-chart/packages/esm-form-entry-app/src/app/openmrs-api/patient-previous-encounter.service.ts`
19. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results.resource.ts`
20. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`

## SPEC-16 (O3-5817) - clear

**Add a schema-configurable searchable dropdown backed by a live REST endpoint**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts` | 1 | 1 |

Hybrid top 20:

1. `patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts` **<- target**
2. `patient-chart/packages/esm-form-entry-app/src/app/form-data-source/form-data-source.service.ts`
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
4. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
5. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts`
6. `patient-chart/packages/esm-form-engine-app/src/index.ts`
7. `billing-app/src/config-schema.ts`
8. `patient-management/packages/esm-patient-list-management-app/src/list-details-table/list-details-table.component.tsx`
9. `patient-chart/packages/esm-patient-forms-app/src/offline.ts`
10. `patient-chart/packages/esm-form-entry-app/src/app/offline/caching.ts`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/id/identifier-selection-overlay.component.tsx`
12. `patient-chart/packages/esm-patient-orders-app/src/config-schema.ts`
13. `patient-chart/packages/esm-form-engine-app/src/config-schema.ts`
14. `patient-management/packages/esm-service-queues-app/src/config-schema.ts`
15. `patient-chart/packages/esm-form-entry-app/src/app/openmrs-api/patient-resource.service.ts`
16. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-note-config-schema.ts`
17. `patient-management/packages/esm-patient-search-app/src/config-schema.ts`
18. `billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx`
19. `core/packages/tooling/openmrs/src/utils/importmap.ts`
20. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`

## SPEC-17 (O3-5889) - clear

**Support fullWidth configuration for obs-by-encounter-widget**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-generic-patient-widgets-app/src/config-schema-obs-switchable.ts` | 5 | 4 |
| `patient-chart/packages/esm-patient-chart-app/src/patient-chart/chart-review/dashboard-view.component.tsx` | - | - |

Hybrid top 20:

1. `patient-chart/packages/esm-generic-patient-widgets-app/src/index.ts`
2. `patient-chart/packages/esm-generic-patient-widgets-app/src/resources/useObs.ts`
3. `patient-chart/packages/esm-generic-patient-widgets-app/src/config-schema-obs-horizontal.ts`
4. `patient-chart/packages/esm-generic-patient-widgets-app/src/config-schema-obs-switchable.ts` **<- target**
5. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-switchable/obs-switchable.component.tsx`
6. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.component.tsx`
7. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table/obs-table.component.tsx`
8. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.resource.ts`
9. `patient-management/packages/esm-active-visits-app/src/config-schema.ts`
10. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-graph/obs-graph.component.tsx`
11. `core/packages/framework/esm-globals/src/types.ts`
12. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/utils/encounter-list-config-builder.ts`
13. `patient-management/packages/esm-active-visits-app/src/visits-summary/visits-components/encounter-list.component.tsx`
14. `patient-chart/packages/esm-generic-patient-widgets-app/src/resources/useEncounterTypes.ts`
15. `core/packages/apps/esm-primary-navigation-app/src/components/dashboard/dashboard.component.tsx`
16. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/types.ts`
17. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx`
18. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
19. `patient-management/packages/esm-ward-app/src/config-schema.ts`
20. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/media-uploader.component.tsx`

## SPEC-18 (O3-5665) - clear

**Vitals form button has broken template literal and missing import**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-service-queues-app/src/config-schema.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/constants.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit-summary.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit.resource.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/current-visit-details.component.tsx` | 4 | 1 |
| `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/vitals.component.tsx` | 1 | 2 |

(1 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/current-visit-details.component.tsx` **<- target**
2. `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/vitals.component.tsx` **<- target**
3. `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/triage-note.component.tsx`
4. `patient-management/packages/esm-service-queues-app/src/create-queue-entry/existing-visit-form/existing-visit-form.component.tsx`
5. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
6. `patient-chart/packages/esm-patient-vitals-app/src/vitals-and-biometrics-header/vitals-header.extension.tsx`
7. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/past-visit-summary.component.tsx`
8. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/active-visit-buttons/active-visit-buttons.tsx`
9. `patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx`
10. `patient-management/packages/esm-service-queues-app/src/create-queue-entry/queue-fields/visit-form-queue-fields.extension.tsx`
11. `patient-management/packages/esm-service-queues-app/src/queue-table/components/add-patient-to-queue-button.component.tsx`
12. `patient-chart/packages/esm-patient-vitals-app/src/common/helpers.ts`
13. `patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx`
14. `patient-chart/packages/esm-patient-vitals-app/src/vitals-biometrics-form/exported-vitals-biometrics-form.workspace.tsx`
15. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
16. `patient-management/packages/esm-active-visits-app/src/active-visits-widget/active-visits.component.tsx`
17. `patient-chart/packages/esm-patient-vitals-app/src/utils.ts`
18. `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-workload-view-expanded.component.tsx`
19. `core/packages/framework/esm-react-utils/src/ConfigurableLink.tsx`
20. `patient-management/packages/esm-service-queues-app/src/admin/admin-page/admin-page.component.tsx`

## SPEC-19 (O3-5910) - clear

**Patient registration: Preserve local-language names when editing a patient**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` | 1 | 2 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` **<- target**
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx`
4. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.resource.ts`
6. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/custom-input/identifier/utils.ts`
7. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
8. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/custom-input/identifier/identifier-input.component.tsx`
9. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/dummy-data/dummy-data-input.component.tsx`
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/id/identifier-selection-overlay.component.tsx`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-utils.ts`
12. `patient-chart/packages/esm-form-engine-app/src/index.ts`
13. `patient-management/packages/esm-patient-registration-app/src/offline.resources.ts`
14. `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.resource.ts`
15. `patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships-section.component.tsx`
16. `patient-management/packages/esm-patient-registration-app/src/index.ts`
17. `patient-management/packages/esm-patient-registration-app/src/widgets/delete-identifier-confirmation.modal.tsx`
18. `dispensing-app/src/forms/dispense-form.workspace.tsx`
19. `dispensing-app/src/history/history-and-comments.component.tsx`
20. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/id/id-field.component.tsx`

## SPEC-20 (O3-5912) - clear

**Regression: Address hierarchy does not clear dependent fields**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-field.component.tsx` | 4 | 4 |
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy.resource.tsx` | 2 | 2 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy-levels.component.tsx`
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy.resource.tsx` **<- target**
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-search.component.tsx`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-field.component.tsx` **<- target**
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
6. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
7. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
8. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
9. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/cause-of-death/cause-of-death.component.tsx`
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/custom-address-field.component.tsx`
12. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/obs/obs-field.component.tsx`
13. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-utils.ts`
14. `patient-management/packages/esm-ward-app/src/config-schema.ts`
15. `patient-management/packages/esm-patient-registration-app/src/offline.resources.ts`
16. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/id/id-field.component.tsx`
17. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attribute-field.component.tsx`
18. `patient-chart/packages/esm-patient-tests-app/src/test-results/filter/filter-reducer.ts`
19. `patient-management/packages/esm-service-queues-app/src/create-queue-entry/queue-fields/queue-fields.component.tsx`
20. `patient-chart/packages/esm-form-engine-app/src/config-schema.ts`

## SPEC-21 (O3-5913) - clear

**Patient registration: Wait for deletions before reporting a successful save**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` | 2 | 1 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` **<- target**
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx`
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.resource.ts`
6. `patient-management/packages/esm-patient-registration-app/src/patient-registration/before-save-prompt.component.tsx`
7. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-utils.ts`
8. `patient-chart/packages/esm-form-engine-app/src/index.ts`
9. `patient-management/packages/esm-patient-registration-app/src/offline.ts`
10. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/history/delete-note.modal.tsx`
11. `core/packages/apps/esm-offline-tools-app/src/offline-patients/offline-patient-table.component.tsx`
12. `patient-chart/packages/esm-patient-flags-app/src/flags/flags-workspace/flags.workspace.tsx`
13. `core/packages/shell/esm-app-shell/src/service-worker/caching.ts`
14. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
15. `core/packages/shell/esm-app-shell/src/run.ts`
16. `patient-management/packages/esm-patient-registration-app/src/index.ts`
17. `core/packages/framework/esm-error-handling/src/index.ts`
18. `core/packages/framework/esm-offline/src/dynamic-offline-data.ts`
19. `patient-management/packages/esm-patient-registration-app/src/constants.ts`
20. `core/packages/apps/esm-implementer-tools-app/src/backend-dependencies/openmrs-backend-dependencies.ts`

## SPEC-22 (O3-5918) - clear (names code files)

**Allow birth and death on the same calendar day**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/validation/patient-registration-validation.ts` | 4 | 4 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
2. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
3. `patient-chart/packages/esm-patient-chart-app/src/data.resource.ts`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/validation/patient-registration-validation.ts` **<- target**
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/basic-input/input/input.component.tsx`
6. `patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx`
7. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
8. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/obs/obs-field.component.tsx`
9. `patient-chart/packages/esm-form-engine-app/src/index.ts`
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.resource.ts`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx`
12. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/date-and-time-of-death/date-and-time-of-death.component.tsx`
13. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/visit-form.resource.ts`
14. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
15. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/dummy-data/dummy-data-input.component.tsx`
16. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/dob/dob.component.tsx`
17. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/cause-of-death/cause-of-death.component.tsx`
18. `patient-chart/packages/esm-patient-banner-app/src/banner-tags/deceased-patient-tag.extension.tsx`
19. `patient-chart/packages/esm-patient-chart-app/src/actions-buttons/mark-patient-deceased.component.tsx`
20. `patient-management/packages/esm-patient-registration-app/src/constants.ts`

## SPEC-23 (O3-6098) - clear (names code files)

**Service Queues always shows “Scheduled for today” and “On time”**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-service-queues-app/src/config-schema.ts` | - | 10 |
| `patient-management/packages/esm-service-queues-app/src/constants.ts` | - | - |
| `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit-summary.component.tsx` | 2 | 2 |
| `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit.resource.ts` | 7 | 14 |

Hybrid top 20:

1. `patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx`
2. `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit-summary.component.tsx` **<- target**
3. `patient-management/packages/esm-service-queues-app/src/queue-patient-linelists/queue-linelist.resource.ts`
4. `patient-management/packages/esm-service-queues-app/src/metrics/metrics.resource.ts`
5. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-upcoming-appointments-card.component.tsx`
6. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
7. `patient-management/packages/esm-appointments-app/src/appointments/scheduled/scheduled-appointments.component.tsx`
8. `patient-management/packages/esm-appointments-app/src/types/index.ts`
9. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit.component.tsx`
10. `patient-management/packages/esm-service-queues-app/src/config-schema.ts` **<- target**
11. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/encounter-list.component.tsx`
12. `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx`
13. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`
14. `patient-management/packages/esm-service-queues-app/src/current-visit/current-visit.resource.ts` **<- target**
15. `patient-management/packages/esm-service-queues-app/src/queue-patient-linelists/queue-services-table.component.tsx`
16. `patient-management/packages/esm-appointments-app/src/config-schema.ts`
17. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments-detailed-summary.extension.tsx`
18. `patient-management/packages/esm-service-queues-app/src/metrics/metrics-cards/waiting-patients.extension.tsx`
19. `patient-management/packages/esm-service-queues-app/src/service-queues.resource.ts`
20. `patient-management/packages/esm-appointments-app/src/hooks/useTodaysVisits.ts`

## SPEC-24 (O3-5917) - clear (names code files)

**Keep newly added relationship rows correctly associated**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts` | 1 | 5 |
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships-section.component.tsx` | 9 | 4 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships.resource.tsx`
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.resource.ts`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships-section.component.tsx` **<- target**
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts` **<- target**
6. `patient-management/packages/esm-patient-registration-app/src/constants.ts`
7. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx`
8. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
9. `patient-management/packages/esm-patient-registration-app/src/offline.resources.ts`
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/dummy-data/dummy-data-input.component.tsx`
11. `patient-management/packages/esm-patient-registration-app/src/root.component.tsx`
12. `patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/timeline-data-group.component.tsx`
13. `core/packages/framework/esm-styleguide/src/patient-banner/contact-details/useRelationships.ts`
14. `patient-management/packages/esm-patient-registration-app/src/patient-registration/validation/patient-registration-validation.ts`
15. `core/packages/framework/esm-styleguide/src/patient-banner/contact-details/patient-banner-contact-details.component.tsx`
16. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
17. `patient-management/packages/esm-patient-list-management-app/src/list-details-table/list-details-table.component.tsx`
18. `patient-management/packages/esm-patient-registration-app/src/offline.ts`
19. `patient-chart/packages/esm-patient-tests-app/src/test-results/tree-view/tree-view.component.tsx`
20. `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table/individual-results-table.component.tsx`

## SPEC-25 (O3-5919) - clear (names code files)

**Clear stale death metadata when marking a patient alive**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` | 4 | 6 |
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts` | 6 | 4 |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-chart-app/src/data.resource.ts`
2. `patient-chart/packages/esm-patient-chart-app/src/actions-buttons/mark-patient-deceased.component.tsx`
3. `patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts` **<- target**
5. `patient-chart/packages/esm-patient-chart-app/src/mark-patient-alive/mark-patient-alive.modal.tsx`
6. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` **<- target**
7. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
8. `patient-chart/packages/esm-form-engine-app/src/index.ts`
9. `patient-chart/packages/esm-patient-banner-app/src/banner-tags/deceased-patient-tag.extension.tsx`
10. `patient-chart/packages/esm-patient-chart-app/src/actions-buttons/mark-patient-alive.component.tsx`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/validation/patient-registration-validation.ts`
12. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.resource.ts`
13. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/cause-of-death/cause-of-death.component.tsx`
14. `patient-chart/packages/esm-patient-banner-app/src/hooks/useCauseOfDeath.ts`
15. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/date-and-time-of-death/date-and-time-of-death.component.tsx`
16. `core/packages/framework/esm-api/src/types/person-resource.ts`
17. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
18. `patient-management/packages/esm-patient-registration-app/src/patient-registration/section/death-info/death-info-section.component.tsx`
19. `patient-chart/tools/test-utils.tsx`
20. `core/packages/framework/esm-styleguide/src/patient-banner/contact-details/usePatientAttributes.ts`

## SPEC-26 (O3-5914) - clear (names code files)

**Preserve existing location attributes while searching**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx` | 1 | 1 |
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` | 9 | 4 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx` **<- target**
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.resource.tsx`
3. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attributes.resource.ts`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` **<- target**
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx`
6. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attribute-field.component.tsx`
7. `patient-management/packages/esm-patient-registration-app/src/root.component.tsx`
8. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-search.component.tsx`
9. `core/packages/apps/esm-implementer-tools-app/src/configuration/interactive-editor/value-editors/person-attribute-search.tsx`
10. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/location-selector.component.tsx`
11. `core/packages/apps/esm-implementer-tools-app/src/configuration/interactive-editor/value-editors/patient-identifier-type-search.tsx`
12. `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx`
13. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
14. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/custom-input/autosuggest/autosuggest.component.tsx`
15. `patient-management/packages/esm-patient-search-app/src/config-schema.ts`
16. `patient-chart/packages/esm-form-engine-app/src/index.ts`
17. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
18. `core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts`
19. `patient-management/packages/esm-patient-registration-app/src/patient-registration/before-save-prompt.component.tsx`
20. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.component.tsx`

## SPEC-27 (O3-5666) - clear

**"Call" action crashes the page when the API request fails**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-service-queues-app/src/modals/call-modal/call-queue-entry.modal.tsx` | 10 | 3 |
| `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-error.utils.ts` | - | 2 |
| `patient-management/packages/esm-service-queues-app/src/queue-table/cells/queue-table-action-cell.component.tsx` | 14 | 4 |

Hybrid top 20:

1. `patient-management/packages/esm-service-queues-app/src/hooks/useQueueEntries.ts`
2. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-error.utils.ts` **<- target**
3. `patient-management/packages/esm-service-queues-app/src/modals/call-modal/call-queue-entry.modal.tsx` **<- target**
4. `patient-management/packages/esm-service-queues-app/src/queue-table/cells/queue-table-action-cell.component.tsx` **<- target**
5. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-confirm-action.modal.tsx`
6. `patient-management/packages/esm-service-queues-app/src/modals/call-modal/call-queue-entry.resource.ts`
7. `core/packages/framework/esm-styleguide/src/toasts/toast.stories.tsx`
8. `patient-management/packages/esm-service-queues-app/src/service-queues.resource.ts`
9. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`
10. `patient-management/packages/esm-service-queues-app/src/queue-table/default-queue-table.component.tsx`
11. `core/packages/framework/esm-api/src/current-user.ts`
12. `patient-management/packages/esm-ward-app/src/ward-workspace/admit-patient-button.component.tsx`
13. `patient-management/packages/esm-service-queues-app/src/admin/admin-page/admin-page.component.tsx`
14. `core/packages/tooling/openmrs/src/cli.ts`
15. `core/packages/shell/esm-app-shell/src/index.ts`
16. `core/packages/framework/esm-api/src/openmrs-fetch.ts`
17. `patient-management/packages/esm-patient-list-management-app/src/api/patient-list.resource.ts`
18. `core/packages/framework/esm-translations/src/translations.ts`
19. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
20. `core/packages/tooling/openmrs/src/commands/debug.ts`

## SPEC-28 (O3-5916) - clear (names code files)

**Make automatically generated patient identifiers retry-safe**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` | 3 | 3 |
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx` | 6 | 9 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/custom-input/identifier/identifier-input.component.tsx`
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts` **<- target**
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/id/identifier-selection-overlay.component.tsx`
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-utils.ts`
6. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/custom-input/identifier/utils.ts`
7. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/dummy-data/dummy-data-input.component.tsx`
8. `patient-management/packages/esm-patient-registration-app/src/patient-registration/validation/patient-registration-validation.ts`
9. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.component.tsx` **<- target**
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-hooks.ts`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.resource.ts`
12. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/id/id-field.component.tsx`
13. `patient-management/packages/esm-patient-registration-app/src/offline.ts`
14. `patient-management/packages/esm-patient-registration-app/src/offline.resources.ts`
15. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
16. `patient-management/packages/esm-patient-registration-app/src/root.component.tsx`
17. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration-context.ts`
18. `core/packages/framework/esm-utils/src/retry.ts`
19. `patient-chart/packages/esm-form-engine-app/src/index.ts`
20. `patient-management/packages/esm-patient-registration-app/src/patient-registration/before-save-prompt.component.tsx`

## SPEC-29 (O3-5680) - clear (names code files)

**Make calling status and drug order type filters configurable**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-active-visits-app/src/config-schema.ts` | - | - |
| `patient-management/packages/esm-active-visits-app/src/visits-summary/visits-components/medications-summary.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/config-schema.ts` | 6 | 7 |
| `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/medications-list.component.tsx` | 3 | 1 |
| `patient-management/packages/esm-service-queues-app/src/queue-screen/queue-screen.component.tsx` | - | - |
| `patient-management/packages/esm-service-queues-app/src/queue-table/cells/queue-table-action-cell.component.tsx` | 2 | 6 |

Hybrid top 20:

1. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/medications-list.component.tsx` **<- target**
2. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
3. `patient-management/packages/esm-service-queues-app/src/modals/call-modal/call-queue-entry.modal.tsx`
4. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`
5. `patient-management/packages/esm-service-queues-app/src/hooks/useQueueEntries.ts`
6. `patient-management/packages/esm-service-queues-app/src/queue-table/cells/queue-table-action-cell.component.tsx` **<- target**
7. `patient-management/packages/esm-service-queues-app/src/config-schema.ts` **<- target**
8. `patient-chart/packages/esm-patient-medications-app/src/api/api.ts`
9. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-search/order-basket-search-results.component.tsx`
10. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/add-drug-order.component.tsx`
11. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.component.tsx`
12. `patient-chart/packages/esm-patient-orders-app/src/utils/index.ts`
13. `dispensing-app/src/utils.ts`
14. `patient-chart/packages/esm-patient-common-lib/src/orders/types/order.ts`
15. `patient-chart/packages/esm-patient-orders-app/src/components/order-details-table.component.tsx`
16. `patient-management/packages/esm-service-queues-app/src/queue-table/default-queue-table.component.tsx`
17. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/past-visit-summary.component.tsx`
18. `patient-chart/packages/esm-patient-orders-app/src/order-basket/general-order-type/add-general-order/add-general-order.component.tsx`
19. `patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx`
20. `patient-chart/packages/esm-patient-orders-app/src/config-schema.ts`

## SPEC-30 (O3-6112) - normal (names code files)

**Billing "Create bill / Add bill items" workspace doesn't show which patient is being billed**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/billing-form/billing-form.workspace.tsx` | 1 | 1 |

Hybrid top 20:

1. `billing-app/src/billing-form/billing-form.workspace.tsx` **<- target**
2. `billing-app/src/bill-history/bill-history.component.tsx`
3. `billing-app/src/billing.resource.ts`
4. `billing-app/src/invoice/invoice-table.component.tsx`
5. `billing-app/src/types/index.ts`
6. `billing-app/src/invoice/printable-invoice/printable-invoice-header.component.tsx`
7. `billing-app/src/bills-table/bills-table.component.tsx`
8. `billing-app/src/config-schema.ts`
9. `billing-app/src/billable-services/bill-waiver/patient-bills.component.tsx`
10. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
11. `billing-app/src/invoice/invoice.component.tsx`
12. `billing-app/src/billable-services/billable-service-form/billable-service-form.workspace.tsx`
13. `billing-app/src/modal/require-payment.modal.tsx`
14. `billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx`
15. `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx`
16. `billing-app/src/invoice/payments/payment-history/payment-history.component.tsx`
17. `billing-app/src/invoice/line-item-action-menu.component.tsx`
18. `billing-app/src/billing-form/billing-checkin-form.component.tsx`
19. `billing-app/src/dashboard.meta.ts`
20. `billing-app/src/helpers/functions.ts`

## SPEC-31 (O3-5411) - normal

**Automatically Waive Consultation Fees for Return Visits Within 7 Days**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/billing-form/billing-checkin-form.component.tsx` | 5 | 1 |
| `billing-app/src/billing-form/billing-form.resource.ts` | - | - |
| `billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx` | 2 | 2 |
| `billing-app/tools/setup-tests.ts` | - | - |

Hybrid top 20:

1. `billing-app/src/billing-form/billing-checkin-form.component.tsx` **<- target**
2. `billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx` **<- target**
3. `billing-app/src/billing-form/billing-form.workspace.tsx`
4. `billing-app/src/index.ts`
5. `dispensing-app/src/utils.ts`
6. `billing-app/src/invoice/payments/payments.component.tsx`
7. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts`
8. `billing-app/src/billable-services/bill-waiver/patient-bills.component.tsx`
9. `billing-app/src/config-schema.ts`
10. `billing-app/src/types/index.ts`
11. `billing-app/src/modal/require-payment.modal.tsx`
12. `billing-app/src/bills-table/bills-table.component.tsx`
13. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx`
14. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts`
15. `dispensing-app/src/forms/dispense-form.workspace.tsx`
16. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/visit-form.resource.ts`
17. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
18. `core/packages/framework/esm-emr-api/src/types/fhir.ts`
19. `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx`
20. `patient-management/packages/esm-appointments-app/src/types/index.ts`

## SPEC-32 (O3-5413) - normal

**Enable Refund Requests and Approval for Paid Bills**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/billable-services/billable-services-home.component.tsx` | - | - |
| `billing-app/src/bills-table/bills-table.component.tsx` | 9 | 12 |
| `billing-app/src/index.ts` | 5 | 6 |
| `billing-app/src/invoice/invoice-table.component.tsx` | - | - |
| `billing-app/src/invoice/invoice.component.tsx` | - | - |
| `billing-app/src/invoice/line-item-action-menu.component.tsx` | - | - |
| `billing-app/src/invoice/payments/payments.component.tsx` | 4 | 8 |
| `billing-app/src/types/index.ts` | 3 | 4 |

(15 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `billing-app/src/modal/require-payment.modal.tsx`
2. `billing-app/src/billing.resource.ts`
3. `billing-app/src/billing-form/billing-form.workspace.tsx`
4. `billing-app/src/types/index.ts` **<- target**
5. `billing-app/src/billable-services/billable-service-form/billable-service-form.workspace.tsx`
6. `billing-app/src/index.ts` **<- target**
7. `billing-app/src/billable-services/bill-waiver/bill-waiver.component.tsx`
8. `billing-app/src/invoice/payments/payments.component.tsx` **<- target**
9. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
10. `billing-app/src/billing-form/billing-checkin-form.component.tsx`
11. `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx`
12. `billing-app/src/bills-table/bills-table.component.tsx` **<- target**
13. `billing-app/src/invoice/payments/payment-form/payment-form.component.tsx`
14. `billing-app/src/billable-services/payment-modes/payment-mode-form.modal.tsx`
15. `billing-app/src/billable-services/billable-service.resource.ts`
16. `dispensing-app/src/utils.ts`
17. `billing-app/src/billable-services/billable-services.component.tsx`
18. `billing-app/src/config-schema.ts`
19. `dispensing-app/src/types.ts`
20. `billing-app/src/billable-services-admin-card-link.component.tsx`

## SPEC-33 (O3-5417) - normal

**Bill Discount Management with Audit Trail**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/billable-services/bill-waiver/bill-selection.component.tsx` | - | 13 |
| `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx` | - | 12 |
| `billing-app/src/billable-services/bill-waiver/bill-waiver.component.tsx` | 10 | 10 |
| `billing-app/src/billable-services/bill-waiver/patient-bills.component.tsx` | - | 8 |
| `billing-app/src/billable-services/billable-services-home.component.tsx` | - | - |
| `billing-app/src/billing.resource.ts` | - | 2 |
| `billing-app/src/config-schema.ts` | - | 7 |
| `billing-app/src/index.ts` | 11 | 4 |
| `billing-app/src/invoice/invoice-table.component.tsx` | - | - |
| `billing-app/src/invoice/invoice.component.tsx` | 6 | 5 |
| `billing-app/src/invoice/line-item-action-menu.component.tsx` | - | - |
| `billing-app/src/invoice/payments/payments.component.tsx` | 3 | 9 |
| `billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx` | 7 | 3 |
| `billing-app/src/types/index.ts` | - | 20 |

(17 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `billing-app/src/billable-services-admin-card-link.component.tsx`
2. `billing-app/src/billing.resource.ts` **<- target**
3. `billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx` **<- target**
4. `billing-app/src/index.ts` **<- target**
5. `billing-app/src/invoice/invoice.component.tsx` **<- target**
6. `billing-app/src/invoice/printable-invoice/printable-invoice-header.component.tsx`
7. `billing-app/src/config-schema.ts` **<- target**
8. `billing-app/src/billable-services/bill-waiver/patient-bills.component.tsx` **<- target**
9. `billing-app/src/invoice/payments/payments.component.tsx` **<- target**
10. `billing-app/src/billable-services/bill-waiver/bill-waiver.component.tsx` **<- target**
11. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
12. `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx` **<- target**
13. `billing-app/src/billable-services/bill-waiver/bill-selection.component.tsx` **<- target**
14. `billing-app/src/billable-services/billable-service-form/billable-service-form.workspace.tsx`
15. `billing-app/src/modal/require-payment.modal.tsx`
16. `billing-app/src/billing-form/billing-form.workspace.tsx`
17. `billing-app/src/billing-form/billing-checkin-form.component.tsx`
18. `billing-app/src/bills-table/bills-table.component.tsx`
19. `billing-app/src/invoice/payments/payment-form/payment-form.component.tsx`
20. `billing-app/src/types/index.ts` **<- target**

## SPEC-34 (O3-5708) - normal

**Review discounts modal closes after first action even when multiple discounts are pending**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/billing.resource.ts` | - | - |

(2 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx`
2. `dispensing-app/src/types.ts`
3. `core/packages/apps/esm-offline-tools-app/src/components/confirmation.modal.tsx`
4. `billing-app/src/modal/require-payment.modal.tsx`
5. `dispensing-app/src/forms/medication-dispense-review.component.tsx`
6. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
7. `billing-app/src/invoice/line-item-action-menu.component.tsx`
8. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`
9. `dispensing-app/src/print-prescription/prescription-print-preview.modal.tsx`
10. `dispensing-app/src/forms/dispense-form.workspace.tsx`
11. `dispensing-app/src/components/prescription-actions/dispense-action-button.component.tsx`
12. `dispensing-app/src/components/action-buttons.component.tsx`
13. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-confirm-action.modal.tsx`
14. `dispensing-app/src/utils.ts`
15. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/file-review.component.tsx`
16. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments-cancel.modal.tsx`
17. `patient-chart/packages/esm-patient-chart-app/src/patient-chart/chart-review/chart-review.component.tsx`
18. `dispensing-app/src/history/history-and-comments.component.tsx`
19. `patient-management/packages/esm-appointments-app/src/appointments/common-components/batch-change-appointment-statuses.modal.tsx`
20. `patient-management/packages/esm-patient-registration-app/src/widgets/cancel-patient-edit.modal.tsx`

## SPEC-35 (O3-5743) - normal

**UI doesn't make it clear bill must be finalized before payment**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/invoice/invoice.component.tsx` | - | 20 |
| `billing-app/src/invoice/payments/payments.component.tsx` | 2 | 3 |

(1 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `billing-app/src/billing.resource.ts`
2. `billing-app/src/invoice/payments/payment-form/payment-form.component.tsx`
3. `billing-app/src/invoice/payments/payments.component.tsx` **<- target**
4. `billing-app/src/billing-form/billing-form.workspace.tsx`
5. `billing-app/src/types/index.ts`
6. `billing-app/src/modal/require-payment.modal.tsx`
7. `billing-app/src/bills-table/bills-table.component.tsx`
8. `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx`
9. `billing-app/src/invoice/payments/payment-history/payment-history.component.tsx`
10. `billing-app/src/modal/delete-line-item-confirmation.modal.tsx`
11. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
12. `billing-app/src/helpers/functions.ts`
13. `billing-app/src/billable-services/billable-service-form/billable-service-form.workspace.tsx`
14. `billing-app/src/index.ts`
15. `billing-app/src/invoice/payments/invoice-breakdown/invoice-breakdown.component.tsx`
16. `billing-app/src/invoice/line-item-action-menu.component.tsx`
17. `billing-app/src/bill-history/bill-history.component.tsx`
18. `billing-app/src/billing-form/billing-checkin-form.component.tsx`
19. `billing-app/src/billable-services/payment-modes/payment-mode-form.modal.tsx`
20. `billing-app/src/invoice/invoice.component.tsx` **<- target**

## SPEC-36 (O3-5816) - normal (names code files)

**Login crashes with uncaught TypeError when no Login Locations are configured, user stuck on location picker**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx` | 3 | 2 |

Hybrid top 20:

1. `core/packages/apps/esm-login-app/src/config-schema.ts`
2. `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx` **<- target**
3. `core/packages/apps/esm-login-app/src/login/login.component.tsx`
4. `core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts`
5. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts`
6. `core/packages/framework/esm-api/src/current-user.ts`
7. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.component.tsx`
8. `patient-chart/packages/esm-patient-programs-app/src/programs/programs-form.workspace.tsx`
9. `core/packages/apps/esm-login-app/src/login.resource.ts`
10. `patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx`
11. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.workspace.tsx`
12. `core/packages/framework/esm-styleguide/mock.tsx`
13. `core/packages/framework/esm-api/src/types/user-resource.ts`
14. `core/packages/framework/esm-styleguide/mock-jest.tsx`
15. `core/packages/framework/esm-api/src/openmrs-fetch.ts`
16. `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.modal.tsx`
17. `patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/file-review.component.tsx`
18. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attributes.resource.ts`
19. `patient-management/packages/esm-bed-management-app/src/bed-tag/delete-bed-tag-form.modal.tsx`
20. `core/packages/framework/esm-styleguide/src/datepicker/hooks.ts`

## SPEC-37 (O3-5874) - normal (names code files)

**Change language modal and user menu language item crash with RangeError when allowed locales include a region**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language-link.extension.tsx` | 3 | 3 |
| `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.modal.tsx` | 1 | 1 |
| `core/packages/framework/esm-api/src/current-user.ts` | 6 | 6 |
| `core/packages/framework/esm-framework/mock-jest.tsx` | - | - |
| `core/packages/framework/esm-framework/mock.tsx` | - | - |
| `core/packages/framework/esm-utils/src/get-locale.ts` | - | 11 |
| `core/packages/framework/esm-utils/src/index.ts` | - | - |

(2 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.modal.tsx` **<- target**
2. `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.resource.ts`
3. `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language-link.extension.tsx` **<- target**
4. `core/packages/apps/esm-primary-navigation-app/src/index.ts`
5. `core/packages/framework/esm-utils/src/dates/date-util.ts`
6. `core/packages/framework/esm-api/src/current-user.ts` **<- target**
7. `core/packages/shell/esm-app-shell/src/locale.ts`
8. `core/packages/framework/esm-styleguide/src/datepicker/hooks.ts`
9. `core/packages/apps/esm-primary-navigation-app/src/components/navbar/user-menu-button.component.tsx`
10. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-actions-modal.component.tsx`
11. `core/packages/framework/esm-utils/src/get-locale.ts` **<- target**
12. `core/packages/apps/esm-implementer-tools-app/src/store.ts`
13. `core/packages/framework/esm-translations/src/translations.ts`
14. `patient-management/packages/esm-service-queues-app/src/modals/queue-entry-error.utils.ts`
15. `core/packages/tooling/storybook/.storybook/preview.tsx`
16. `core/packages/apps/esm-primary-navigation-app/src/components/navbar/navbar.component.tsx`
17. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts`
18. `patient-management/tools/i18next-parser.config.js`
19. `patient-chart/tools/i18next-parser.config.js`
20. `core/packages/framework/esm-api/src/types/user-resource.ts`

## SPEC-38 (O3-5588) - normal (names code files)

**fix(login-app): Login Location tag filter silently ignored in useLocationCount**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts` | 1 | 2 |

Hybrid top 20:

1. `core/packages/apps/esm-login-app/src/types.ts`
2. `core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts` **<- target**
3. `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx`
4. `core/packages/apps/esm-login-app/src/login.resource.ts`
5. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts`
6. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.component.tsx`
7. `patient-management/packages/esm-ward-app/src/hooks/useLocations.ts`
8. `core/packages/apps/esm-login-app/src/config-schema.ts`
9. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attributes.resource.ts`
10. `patient-management/packages/esm-ward-app/src/location-selector/location-selector.component.tsx`
11. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.resource.tsx`
12. `patient-chart/packages/esm-patient-chart-app/src/visit/hooks/useDefaultVisitLocation.tsx`
13. `patient-management/packages/esm-bed-management-app/src/summary/summary.resource.ts`
14. `core/packages/framework/esm-api/src/config-schema.ts`
15. `core/packages/apps/esm-login-app/src/change-location-link/change-location-link.extension.tsx`
16. `patient-management/packages/esm-ward-app/src/config-schema.ts`
17. `dispensing-app/src/location/location.resource.tsx`
18. `patient-management/packages/esm-ward-app/src/ward-view/ward-view.resource.ts`
19. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/location-selector.component.tsx`
20. `patient-management/packages/esm-patient-search-app/src/config-schema.ts`

## SPEC-39 (O3-5838) - normal

**Implement the Two-Factor Verification Page (TOTP)**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-login-app/src/login/login.component.tsx` | 2 | 4 |
| `core/packages/apps/esm-login-app/src/root.component.tsx` | 11 | 1 |

(3 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `core/packages/apps/esm-login-app/src/root.component.tsx` **<- target**
2. `core/packages/apps/esm-login-app/src/change-password/change-password.component.tsx`
3. `core/packages/apps/esm-login-app/src/change-password/change-password.resource.ts`
4. `core/packages/apps/esm-login-app/src/login/login.component.tsx` **<- target**
5. `core/packages/framework/esm-styleguide/src/pagination/pagination.component.tsx`
6. `patient-chart/tools/test-utils.tsx`
7. `patient-chart/packages/esm-patient-programs-app/src/types/index.ts`
8. `core/packages/framework/esm-api/src/current-user.ts`
9. `core/packages/framework/esm-styleguide/mock-jest.tsx`
10. `core/packages/framework/esm-expression-evaluator/src/evaluator.ts`
11. `core/packages/apps/esm-login-app/src/change-password/change-password.modal.tsx`
12. `core/packages/framework/esm-styleguide/src/icons/icons.tsx`
13. `core/packages/framework/esm-api/src/openmrs-fetch.ts`
14. `core/packages/apps/esm-login-app/src/index.ts`
15. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/basic-input/input/input.component.tsx`
16. `core/packages/framework/esm-styleguide/src/custom-overflow-menu/custom-overflow-menu.component.tsx`
17. `core/packages/framework/esm-styleguide/mock.tsx`
18. `core/packages/apps/esm-login-app/src/login.resource.ts`
19. `billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx`
20. `core/packages/framework/esm-feature-flags/src/feature-flags.ts`

## SPEC-40 (O3-5449) - normal

**Integrate Chart Line Icon for Growth Chart in Left Navigation**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/framework/esm-styleguide/mock-jest.tsx` | - | - |
| `core/packages/framework/esm-styleguide/mock.tsx` | - | - |
| `core/packages/framework/esm-styleguide/src/icons/icon-registration.ts` | - | 1 |
| `core/packages/framework/esm-styleguide/src/icons/icons.tsx` | - | 7 |

Hybrid top 20:

1. `core/packages/framework/esm-styleguide/src/icons/icon-registration.ts` **<- target**
2. `core/packages/framework/esm-styleguide/src/left-nav/index.tsx`
3. `core/packages/apps/esm-primary-navigation-app/src/components/navbar-header-panels/side-menu-panel.component.tsx`
4. `patient-chart/packages/esm-patient-vitals-app/src/index.ts`
5. `core/packages/shell/esm-app-shell/src/service-worker/routing.ts`
6. `patient-chart/packages/esm-patient-vitals-app/src/dashboard.meta.ts`
7. `core/packages/framework/esm-styleguide/src/icons/icons.tsx` **<- target**
8. `core/packages/framework/esm-styleguide/src/workspaces2/workspace-windows-and-menu.component.tsx`
9. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-graph/obs-graph.component.tsx`
10. `core/packages/framework/esm-styleguide/src/workspaces2/action-menu2/action-menu-button2.component.tsx`
11. `patient-chart/packages/esm-patient-tests-app/src/test-results/trendline/trendline.component.tsx`
12. `billing-app/src/billable-services/billable-services-left-panel-menu.component.tsx`
13. `core/packages/framework/esm-routes/src/loaders/pages.ts`
14. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.component.tsx`
15. `patient-management/packages/esm-patient-search-app/src/hooks/useArrowNavigation.tsx`
16. `patient-management/packages/esm-service-queues-app/src/side-menu/nav-group/nav-group.component.tsx`
17. `patient-chart/prettier.config.js`
18. `core/packages/framework/esm-extensions/src/public.ts`
19. `core/packages/framework/esm-styleguide/src/icons/icons.stories.tsx`
20. `patient-chart/packages/esm-patient-chart-app/src/dashboard.meta.ts`

## SPEC-41 (O3-5650) - normal (names code files)

**Dispensing: Support limiting prescriptions shown to locations under session's visit location**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `dispensing-app/src/config-schema.ts` | 3 | 3 |
| `dispensing-app/src/location/location.resource.tsx` | 6 | 4 |
| `dispensing-app/src/prescriptions/patient-search-tab-panel.component.tsx` | - | 7 |
| `dispensing-app/src/prescriptions/prescription-tab-lists.component.tsx` | 1 | 2 |
| `dispensing-app/src/prescriptions/prescription-tab-panel.component.tsx` | 2 | 1 |

Hybrid top 20:

1. `dispensing-app/src/prescriptions/prescription-tab-panel.component.tsx` **<- target**
2. `dispensing-app/src/prescriptions/prescription-tab-lists.component.tsx` **<- target**
3. `dispensing-app/src/config-schema.ts` **<- target**
4. `dispensing-app/src/location/location.resource.tsx` **<- target**
5. `dispensing-app/src/dashboard/dispensing-dashboard.component.tsx`
6. `dispensing-app/src/prescriptions/prescriptions-table.component.tsx`
7. `dispensing-app/src/prescriptions/patient-search-tab-panel.component.tsx` **<- target**
8. `dispensing-app/src/types.ts`
9. `patient-management/packages/esm-ward-app/src/location-selector/location-selector.component.tsx`
10. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/location-selector.component.tsx`
11. `patient-management/packages/esm-ward-app/src/hooks/useLocations.ts`
12. `patient-management/packages/esm-patient-list-management-app/src/lists-table/lists-table.component.tsx`
13. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx`
14. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attribute-field.component.tsx`
15. `patient-management/packages/esm-ward-app/src/hooks/useEmrConfiguration.ts`
16. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
17. `patient-management/packages/esm-ward-app/src/config-schema.ts`
18. `patient-management/packages/esm-patient-search-app/src/config-schema.ts`
19. `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx`
20. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts`

## SPEC-42 (O3-5632) - normal (names code files)

**Dispensing modal: "Dispense all prescriptions" fires before medication request data has loaded**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx` | 1 | 3 |

Hybrid top 20:

1. `dispensing-app/src/print-prescription/printable-prescriptions.component.tsx`
2. `dispensing-app/src/medication-request/medication-request.resource.tsx`
3. `dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx` **<- target**
4. `dispensing-app/src/utils.ts`
5. `dispensing-app/src/prescriptions/prescription-details.component.tsx`
6. `dispensing-app/src/types.ts`
7. `dispensing-app/src/print-prescription/prescription-printout.component.tsx`
8. `dispensing-app/src/fill-prescription/fill-prescription-button.component.tsx`
9. `dispensing-app/src/constants.ts`
10. `dispensing-app/src/forms/dispense-form.workspace.tsx`
11. `dispensing-app/src/medication-dispense/medication-dispense.resource.tsx`
12. `dispensing-app/src/components/medication-event.component.tsx`
13. `dispensing-app/src/print-prescription/prescription-print-preview.modal.tsx`
14. `dispensing-app/src/forms/medication-dispense-review.component.tsx`
15. `dispensing-app/src/forms/duplicate-dispense.modal.tsx`
16. `dispensing-app/src/index.ts`
17. `dispensing-app/src/prescriptions/prescriptions-table.component.tsx`
18. `dispensing-app/src/history/history-and-comments.component.tsx`
19. `dispensing-app/src/print-prescription/prescription-print-action.component.tsx`
20. `dispensing-app/src/components/prescription-actions/dispense-action-button.component.tsx`

## SPEC-43 (O3-4692) - normal

**Display "Dispensed" Status in Prescription Details Section (Consistent with "Cancelled" and "Paused")**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `dispensing-app/src/prescriptions/prescription-details.component.tsx` | 10 | 11 |
| `dispensing-app/src/prescriptions/prescriptions-table.component.tsx` | 20 | - |

Hybrid top 20:

1. `dispensing-app/src/forms/pause-dispense-form.workspace.tsx`
2. `dispensing-app/src/history/history-and-comments.component.tsx`
3. `dispensing-app/src/components/prescription-actions/pause-action-button.component.tsx`
4. `dispensing-app/src/types.ts`
5. `dispensing-app/src/forms/close-dispense-form.workspace.tsx`
6. `dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx`
7. `dispensing-app/src/medication-dispense/medication-dispense.resource.tsx`
8. `dispensing-app/src/utils.ts`
9. `dispensing-app/src/forms/dispense-form.workspace.tsx`
10. `dispensing-app/src/medication-request/medication-request.resource.tsx`
11. `dispensing-app/src/prescriptions/prescription-details.component.tsx` **<- target**
12. `dispensing-app/src/components/medication-event.component.tsx`
13. `dispensing-app/src/config-schema.ts`
14. `dispensing-app/src/forms/medication-dispense-review.component.tsx`
15. `dispensing-app/src/constants.ts`
16. `dispensing-app/src/components/prescription-actions/dispense-action-button.component.tsx`
17. `dispensing-app/src/history/delete-confirm.modal.tsx`
18. `dispensing-app/src/components/action-buttons.component.tsx`
19. `dispensing-app/src/index.ts`
20. `dispensing-app/src/print-prescription/printable-prescriptions.component.tsx`

## SPEC-44 (O3-5705) - vague

**Receipt shows discount as outstanding balance on fully paid bills**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/invoice/printable-invoice/printable-invoice-header.component.tsx` | 5 | 5 |
| `billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx` | 1 | 6 |

Hybrid top 20:

1. `billing-app/src/types/index.ts`
2. `billing-app/src/invoice/invoice.component.tsx`
3. `billing-app/src/invoice/payments/invoice-breakdown/invoice-breakdown.component.tsx`
4. `billing-app/src/invoice/payments/payment-form/payment-form.component.tsx`
5. `billing-app/src/invoice/printable-invoice/printable-invoice-header.component.tsx` **<- target**
6. `billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx` **<- target**
7. `billing-app/src/helpers/functions.ts`
8. `billing-app/src/invoice/payments/payments.component.tsx`
9. `billing-app/src/billable-services/bill-waiver/bill-selection.component.tsx`
10. `billing-app/src/invoice/printable-invoice/print-receipt.component.tsx`
11. `billing-app/src/billable-services/bill-waiver/patient-bills.component.tsx`
12. `billing-app/src/billing.resource.ts`
13. `billing-app/src/billing-form/billing-form.workspace.tsx`
14. `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx`
15. `billing-app/src/metrics-cards/metrics.resource.ts`
16. `billing-app/src/invoice/payments/payment-history/payment-history.component.tsx`
17. `billing-app/src/billable-services/bill-waiver/bill-waiver.component.tsx`
18. `billing-app/src/metrics-cards/metrics-cards.component.tsx`
19. `billing-app/src/invoice/payments/payment.resource.ts`
20. `billing-app/src/helpers/index.ts`

## SPEC-45 (O3-5706) - vague

**"Paying" option is unselectable when patient has a recent prior visit - should be selectable**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx` | 1 | 2 |

Hybrid top 20:

1. `billing-app/src/billing-form/billing-checkin-form.component.tsx`
2. `billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx` **<- target**
3. `billing-app/src/billing-form/billing-form.workspace.tsx`
4. `billing-app/src/types/index.ts`
5. `billing-app/src/invoice/payments/visit-tags/visit-attribute.component.tsx`
6. `billing-app/src/billing.resource.ts`
7. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-switcher.modal.tsx`
8. `billing-app/src/billable-services/billable-service-form/billable-service-form.workspace.tsx`
9. `billing-app/src/invoice/payments/payments.component.tsx`
10. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/visit-form.resource.ts`
11. `billing-app/src/index.ts`
12. `billing-app/src/modal/require-payment.modal.tsx`
13. `core/packages/framework/esm-react-utils/src/useVisit.ts`
14. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
15. `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx`
16. `billing-app/src/invoice/payments/payment-form/payment-form.component.tsx`
17. `core/packages/framework/esm-emr-api/src/visit-utils.ts`
18. `billing-app/src/billable-services/payment-modes/payment-modes-config.component.tsx`
19. `billing-app/src/config-schema.ts`
20. `patient-management/packages/esm-ward-app/src/ward-patient-card/card-rows/incorrect-admission-warning-row.component.tsx`

## SPEC-46 (O3-5202) - vague

**Add a UI button to "finalize" a bill**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `billing-app/src/bill-history/bill-history.component.tsx` | - | 12 |
| `billing-app/src/billable-services/bill-waiver/bill-waiver.component.tsx` | - | 15 |
| `billing-app/src/billing-form/billing-checkin-form.component.tsx` | - | 9 |
| `billing-app/src/billing-form/billing-form.workspace.tsx` | 18 | 4 |
| `billing-app/src/billing.resource.ts` | - | 11 |
| `billing-app/src/bills-table/bills-table.component.tsx` | - | - |
| `billing-app/src/index.ts` | - | 1 |
| `billing-app/src/invoice/invoice.component.tsx` | - | - |
| `billing-app/src/invoice/line-item-action-menu.component.tsx` | - | 19 |
| `billing-app/src/invoice/payments/payments.component.tsx` | - | - |
| `billing-app/src/metrics-cards/metrics.resource.ts` | - | - |
| `billing-app/src/modal/require-payment.modal.tsx` | - | - |
| `billing-app/src/types/index.ts` | - | 7 |

(5 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `billing-app/src/index.ts` **<- target**
2. `billing-app/src/billable-services/billable-service.resource.ts`
3. `billing-app/src/bill-item-actions/edit-bill-item.modal.tsx`
4. `billing-app/src/billing-form/billing-form.workspace.tsx` **<- target**
5. `billing-app/src/billable-services/bill-waiver/bill-waiver-form.component.tsx`
6. `billing-app/src/billable-services/billable-services.component.tsx`
7. `billing-app/src/types/index.ts` **<- target**
8. `billing-app/src/billable-services/billable-service-form/billable-service-form.workspace.tsx`
9. `billing-app/src/billing-form/billing-checkin-form.component.tsx` **<- target**
10. `billing-app/src/billing-form/billing-form.resource.ts`
11. `billing-app/src/billing.resource.ts` **<- target**
12. `billing-app/src/bill-history/bill-history.component.tsx` **<- target**
13. `billing-app/src/billable-services/billable-services-left-panel-menu.component.tsx`
14. `billing-app/src/billable-services/bill-waiver/bill-selection.component.tsx`
15. `billing-app/src/billable-services/bill-waiver/bill-waiver.component.tsx` **<- target**
16. `billing-app/src/billable-services/cash-point/add-cash-point.modal.tsx`
17. `billing-app/src/billable-services/billable-services-left-panel-link.component.tsx`
18. `billing-app/src/billing-dashboard/billing-dashboard.component.tsx`
19. `billing-app/src/invoice/line-item-action-menu.component.tsx` **<- target**
20. `core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.resource.ts`

## SPEC-47 (O3-5027) - vague

**Beautiful + Configurable Login Page**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-login-app/src/config-schema.ts` | 2 | 3 |
| `core/packages/apps/esm-login-app/src/login/login.component.tsx` | 3 | 1 |

Hybrid top 20:

1. `core/packages/apps/esm-login-app/src/login/login.component.tsx` **<- target**
2. `core/packages/apps/esm-login-app/src/redirect-logout/redirect-logout.component.tsx`
3. `core/packages/apps/esm-login-app/src/config-schema.ts` **<- target**
4. `core/packages/apps/esm-login-app/src/root.component.tsx`
5. `core/packages/apps/esm-login-app/src/footer.component.tsx`
6. `core/packages/framework/esm-config/src/module-config/module-config.ts`
7. `patient-management/packages/esm-ward-app/src/ward-view/ward-view.resource.ts`
8. `core/packages/apps/esm-login-app/src/login.resource.ts`
9. `core/packages/framework/esm-react-utils/src/ConfigurableLink.tsx`
10. `patient-management/prettier.config.js`
11. `core/packages/apps/esm-login-app/src/change-password/change-password.component.tsx`
12. `core/packages/framework/esm-error-handling/src/index.ts`
13. `core/packages/framework/esm-emr-api/src/types/fhir.ts`
14. `patient-chart/prettier.config.js`
15. `billing-app/prettier.config.js`
16. `core/packages/apps/esm-primary-navigation-app/src/config-schema.ts`
17. `core/packages/framework/esm-react-utils/src/useEmrConfiguration.ts`
18. `patient-management/packages/esm-ward-app/src/hooks/useEmrConfiguration.ts`
19. `patient-management/packages/esm-home-app/src/config-schema.ts`
20. `patient-management/packages/esm-ward-app/src/ward-workspace/patient-discharge/patient-discharge.workspace.tsx`

## SPEC-48 (O3-5630) - vague

**Dispensing: Bug when editing substitution reason of an old order**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `dispensing-app/src/forms/dispense-form.workspace.tsx` | 2 | 2 |
| `dispensing-app/src/forms/medication-dispense-review.component.tsx` | 1 | 1 |
| `dispensing-app/src/medication-request/medication-request.resource.tsx` | - | - |

Hybrid top 20:

1. `dispensing-app/src/forms/medication-dispense-review.component.tsx` **<- target**
2. `dispensing-app/src/forms/dispense-form.workspace.tsx` **<- target**
3. `dispensing-app/src/history/history-and-comments.component.tsx`
4. `dispensing-app/src/types.ts`
5. `dispensing-app/src/utils.ts`
6. `dispensing-app/src/medication-dispense/medication-dispense.resource.tsx`
7. `dispensing-app/src/config-schema.ts`
8. `dispensing-app/src/forms/pause-dispense-form.workspace.tsx`
9. `dispensing-app/src/constants.ts`
10. `dispensing-app/src/components/medication-card.component.tsx`
11. `dispensing-app/src/forms/close-dispense-form.workspace.tsx`
12. `dispensing-app/src/forms/stock-dispense/stock-dispense.component.tsx`
13. `dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx`
14. `dispensing-app/src/forms/duplicate-dispense.modal.tsx`
15. `dispensing-app/src/prescriptions/prescriptions-table.component.tsx`
16. `dispensing-app/playwright.config.ts`
17. `dispensing-app/src/dashboard/dispensing-dashboard.component.tsx`
18. `dispensing-app/src/dispensing-tiles/dispensing-tiles.component.tsx`
19. `patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.component.tsx`
20. `patient-chart/packages/esm-patient-common-lib/src/orders/useOrders.ts`

## SPEC-49 (O3-5610) - vague

**Add result date column to lab order result**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-tests-app/src/test-results/helpers.ts` | - | - |
| `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table-tablet/lab-set-panel.component.tsx` | 13 | - |
| `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table/individual-results-table.component.tsx` | - | - |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results-schema.resource.tsx`
2. `patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/add-test-order.workspace.tsx`
3. `patient-chart/packages/esm-patient-orders-app/src/lab-results/exported-lab-results-form.workspace.tsx`
4. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results-form.workspace.tsx`
5. `patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/add-test-order.component.tsx`
6. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-result.component.tsx`
7. `patient-chart/packages/esm-patient-tests-app/src/test-orders/lab-order-basket-panel/lab-order-basket-panel.extension.tsx`
8. `patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/test-order-form.component.tsx`
9. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results.resource.ts`
10. `patient-chart/packages/esm-patient-orders-app/src/index.ts`
11. `patient-chart/packages/esm-patient-orders-app/src/lab-results/lab-results-form-field.component.tsx`
12. `patient-chart/packages/esm-patient-tests-app/src/edit-test-results/modal/edit-lab-results.modal.tsx`
13. `patient-chart/packages/esm-patient-orders-app/src/utils/index.ts`
14. `patient-chart/packages/esm-patient-tests-app/src/config-schema.ts`
15. `patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/test-order.ts`
16. `patient-chart/packages/esm-patient-orders-app/src/order-basket/general-order-type/general-order-form/general-order-form.component.tsx`
17. `patient-chart/packages/esm-patient-tests-app/src/test-orders/lab-order-basket-panel/lab-icon.component.tsx`
18. `patient-chart/packages/esm-patient-common-lib/src/orders/useOrders.ts`
19. `patient-chart/packages/esm-patient-tests-app/src/test-orders/api.ts`
20. `patient-chart/packages/esm-patient-orders-app/src/components/order-details-table.component.tsx`

## SPEC-50 (O3-4578) - vague

**Duplicate Dose Entries in Immunization Module**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/components/dose-input.component.tsx` | 10 | 4 |
| `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/components/immunizations-sequence-table.component.tsx` | 1 | 12 |
| `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunizations-form.workspace.tsx` | 2 | 3 |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-immunizations-app/src/types/index.ts`
2. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunization-mapper.ts`
3. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunizations-form.workspace.tsx` **<- target**
4. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/components/dose-input.component.tsx` **<- target**
5. `patient-chart/packages/esm-patient-immunizations-app/src/types/fhir-immunization-domain.ts`
6. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/utils.ts`
7. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunization-history-card.component.tsx`
8. `patient-chart/packages/esm-patient-immunizations-app/src/config-schema.ts`
9. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunizations-detailed-summary.component.tsx`
10. `patient-chart/packages/esm-patient-immunizations-app/src/hooks/useImmunizations.ts`
11. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunizations-overview.component.tsx`
12. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/components/immunizations-sequence-table.component.tsx` **<- target**
13. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunization-history-dashboard.component.tsx`
14. `patient-chart/packages/esm-patient-immunizations-app/src/index.ts`
15. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/delete-immunization.modal.tsx`
16. `patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunizations.resource.ts`
17. `patient-chart/packages/esm-patient-immunizations-app/src/hooks/useImmunizationsConceptSet.ts`
18. `dispensing-app/src/types.ts`
19. `dispensing-app/src/components/medication-event.component.tsx`
20. `dispensing-app/src/forms/duplicate-dispense.modal.tsx`

## SPEC-51 (O3-5677) - vague

**Frontend print button for visit summary in O3 patient chart**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-label-printing-app/src/config-schema.ts` | - | - |
| `patient-chart/packages/esm-patient-label-printing-app/src/index.ts` | - | 6 |

(3 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-chart/packages/esm-patient-label-printing-app/src/hooks/useStickerPdfPrinter.tsx`
2. `patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx`
3. `patient-chart/packages/esm-patient-orders-app/src/components/order-details-table.component.tsx`
4. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx`
5. `patient-chart/packages/esm-patient-chart-app/src/visit/visit-prompt/end-visit-dialog.modal.tsx`
6. `patient-chart/packages/esm-patient-label-printing-app/src/index.ts` **<- target**
7. `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachment-preview.component.tsx`
8. `patient-chart/packages/esm-patient-label-printing-app/src/print-identifier-sticker/print-identifier-sticker-action-button.component.tsx`
9. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx`
10. `dispensing-app/src/print-prescription/prescription-print-preview.modal.tsx`
11. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/current-visit-summary.extension.tsx`
12. `patient-chart/packages/esm-patient-attachments-app/src/attachments/attachments-overview.component.tsx`
13. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-context/visit-context-header.extension.tsx`
14. `core/packages/tooling/storybook/.storybook/preview.tsx`
15. `patient-chart/packages/esm-patient-notes-app/src/notes/notes-overview.extension.tsx`
16. `dispensing-app/src/index.ts`
17. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/active-visit-buttons/active-visit-buttons.tsx`
18. `patient-chart/packages/esm-patient-chart-app/src/index.ts`
19. `patient-chart/packages/esm-patient-tests-app/src/test-results/overview/useOverviewData.ts`
20. `patient-chart/packages/esm-patient-orders-app/src/orders-summary/orders-summary.component.tsx`

## SPEC-52 (O3-5078) - vague

**Sticky Note in O3**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-notes-app/src/config-schema.ts` | 11 | 19 |
| `patient-chart/packages/esm-patient-notes-app/src/index.ts` | - | 8 |

(7 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes-action-button.component.tsx`
2. `core/packages/framework/esm-styleguide/src/icons/icons.tsx`
3. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.workspace.tsx`
4. `core/packages/framework/esm-styleguide/mock-jest.tsx`
5. `patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx`
6. `core/packages/framework/esm-styleguide/mock.tsx`
7. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts`
8. `patient-chart/packages/esm-patient-notes-app/src/index.ts` **<- target**
9. `core/packages/apps/esm-help-menu-app/src/help-menu/components/release-notes.component.tsx`
10. `patient-management/packages/esm-patient-registration-app/src/config-schema.ts`
11. `core/packages/shell/esm-app-shell/src/run.ts`
12. `patient-management/packages/esm-service-queues-app/src/past-visit/past-visit-details/notes-list.component.tsx`
13. `core/packages/apps/esm-implementer-tools-app/src/backend-dependencies/openmrs-backend-dependencies.ts`
14. `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/triage-note.component.tsx`
15. `core/packages/apps/esm-help-menu-app/src/help-menu/components/docs.component.tsx`
16. `core/packages/apps/esm-offline-tools-app/src/components/confirmation.modal.tsx`
17. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-detailed-summary.component.tsx`
18. `patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/current-visit-details.component.tsx`
19. `patient-chart/packages/esm-patient-notes-app/src/config-schema.ts` **<- target**
20. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx`

## SPEC-53 (O3-5801) - vague

**Location obs should display location name not the location id**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/encounter-observations/encounter-observations.component.tsx` | - | - |

Hybrid top 20:

1. `patient-management/packages/esm-ward-app/src/ward-patient-card/row-elements/ward-patient-location.component.tsx`
2. `patient-management/packages/esm-ward-app/src/ward-patient-card/row-elements/ward-patient-obs.resource.ts`
3. `patient-management/packages/esm-ward-app/src/hooks/useInpatientAdmission.ts`
4. `patient-management/packages/esm-ward-app/src/types/index.ts`
5. `patient-management/packages/esm-ward-app/src/ward-patient-card/card-rows/incorrect-admission-warning-row.component.tsx`
6. `patient-management/packages/esm-ward-app/src/ward-patient-card/row-elements/ward-patient-coded-obs-tags.component.tsx`
7. `patient-management/packages/esm-ward-app/src/ward-view/ward-view.resource.ts`
8. `patient-management/packages/esm-ward-app/src/hooks/useInpatientAdmissionByPatients.ts`
9. `patient-management/packages/esm-ward-app/src/ward-patient-card/card-rows/coded-obs-tags-row.component.tsx`
10. `patient-management/packages/esm-ward-app/src/ward.resource.ts`
11. `patient-management/packages/esm-ward-app/src/hooks/useAdmissionLocation.ts`
12. `patient-management/packages/esm-ward-app/src/hooks/useInpatientRequest.ts`
13. `patient-management/packages/esm-ward-app/src/config-schema.ts`
14. `patient-management/packages/esm-ward-app/src/hooks/useInpatientRequestByPatients.ts`
15. `patient-management/packages/esm-ward-app/src/ward-view/maternal-ward/maternal-ward-patient-card-header.component.tsx`
16. `patient-management/packages/esm-ward-app/src/ward-view/ward.component.tsx`
17. `patient-management/packages/esm-ward-app/src/hooks/useWardLocation.ts`
18. `patient-chart/packages/esm-patient-notes-app/src/types/index.ts`
19. `patient-management/packages/esm-ward-app/src/ward-workspace/cancel-admission-request-workspace/cancel-admission-request.component.tsx`
20. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/obs/obs-field.component.tsx`

## SPEC-54 (O3-5436) - vague

**Align test result values and reference range columns in the Tests tab**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-tests-app/src/test-results/overview/common-datatable.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-tests-app/src/test-results/overview/useOverviewData.ts` | - | 12 |

Hybrid top 20:

1. `patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/reference-range-helpers.ts`
2. `patient-chart/packages/esm-patient-tests-app/src/test-results/loadPatientTestData/helpers.ts`
3. `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table-tablet/lab-set-panel.component.tsx`
4. `patient-chart/packages/esm-patient-tests-app/src/test-results/results-viewer/results-viewer-router.tsx`
5. `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table/individual-results-table.component.tsx`
6. `patient-chart/packages/esm-patient-tests-app/src/test-results/trendline/trendline.component.tsx`
7. `patient-chart/packages/esm-patient-tests-app/src/test-results/dashboard.meta.ts`
8. `patient-chart/packages/esm-patient-tests-app/src/test-results/results-viewer/index.ts`
9. `patient-chart/packages/esm-patient-tests-app/src/types.ts`
10. `patient-chart/packages/esm-patient-tests-app/src/test-results/trendline/range-selector.component.tsx`
11. `patient-chart/packages/esm-patient-tests-app/src/index.ts`
12. `patient-chart/packages/esm-patient-tests-app/src/test-results/overview/useOverviewData.ts` **<- target**
13. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.component.tsx`
14. `patient-chart/packages/esm-patient-tests-app/src/test-results/results-viewer/results-viewer.extension.tsx`
15. `patient-chart/packages/esm-patient-tests-app/src/test-results/overview/common-overview.component.tsx`
16. `patient-chart/packages/esm-patient-common-lib/src/types/test-results.ts`
17. `patient-chart/packages/esm-patient-tests-app/src/test-results/filter/filter-types.ts`
18. `patient-chart/packages/esm-patient-tests-app/src/test-results/trendline/trendline-resource.tsx`
19. `patient-chart/packages/esm-patient-tests-app/src/test-results/individual-results-table-tablet/individual-results-table-tablet.component.tsx`
20. `patient-chart/packages/esm-patient-orders-app/src/lab-results/print-results/print-preview/print-preview.component.tsx`

## SPEC-55 (O3-5452) - vague

**Printing encounters based on O3-forms**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/all-encounters-table.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx` | - | 16 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` | - | 18 |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/visit-encounters-table.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx` | - | - |
| `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/visit-detail-overview.component.tsx` | - | - |

(3 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts`
2. `patient-chart/packages/esm-form-entry-app/src/app/fe-wrapper/fe-wrapper.component.ts`
3. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/encounter-list/encounter-list.component.tsx`
4. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/utils/helpers.ts`
5. `patient-chart/packages/esm-patient-forms-app/src/offline.ts`
6. `patient-chart/packages/esm-patient-forms-app/src/types/index.ts`
7. `patient-chart/packages/esm-patient-forms-app/src/hooks/use-forms.ts`
8. `patient-chart/packages/esm-patient-forms-app/src/offline-forms/offline-form-helpers.ts`
9. `patient-chart/packages/esm-patient-forms-app/src/constants.ts`
10. `patient-chart/packages/esm-patient-vitals-app/src/common/data.resource.ts`
11. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/types.ts`
12. `patient-chart/packages/esm-form-entry-app/src/app/types/index.ts`
13. `patient-chart/packages/esm-patient-common-lib/src/orders/postOrders.ts`
14. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/utils/encounter-list-config-builder.ts`
15. `patient-chart/packages/esm-form-entry-app/src/app/form-submission/form-submission.service.ts`
16. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.component.tsx` **<- target**
17. `patient-chart/packages/esm-form-engine-app/src/hooks/useFormSchema.tsx`
18. `patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/encounters-table/encounters-table.resource.ts` **<- target**
19. `patient-chart/packages/esm-generic-patient-widgets-app/src/obs-table-horizontal/obs-table-horizontal.resource.ts`
20. `patient-chart/packages/esm-patient-chart-app/src/clinical-views/hooks/useEncounterRows.ts`

## SPEC-56 (O3-5534) - vague

**Fix index-based keys in address search suggestions causing incorrect selection behavior**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-search.component.tsx` | 8 | 1 |

Hybrid top 20:

1. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-search.component.tsx` **<- target**
2. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy-levels.component.tsx`
3. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy.resource.tsx`
4. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-field.component.tsx`
5. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/custom-input/autosuggest/autosuggest.component.tsx`
6. `patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts`
7. `patient-management/packages/esm-patient-search-app/src/index.ts`
8. `patient-management/packages/esm-patient-list-management-app/src/list-details-table/list-details-table.component.tsx`
9. `core/packages/framework/esm-styleguide/src/patient-banner/contact-details/patient-banner-contact-details.component.tsx`
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships-section.component.tsx`
11. `patient-management/packages/esm-patient-list-management-app/src/lists-table/lists-table.component.tsx`
12. `patient-management/packages/esm-patient-list-management-app/src/lists-dashboard/lists-dashboard.component.tsx`
13. `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx`
14. `core/packages/apps/esm-devtools-app/src/devtools/import-map-list/list.component.tsx`
15. `patient-management/packages/esm-patient-registration-app/src/patient-registration/input/combo-input/combo-input.component.tsx`
16. `patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx`
17. `patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts`
18. `patient-management/packages/esm-patient-search-app/src/types/index.ts`
19. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/cause-of-death/cause-of-death.component.tsx`
20. `patient-management/packages/esm-ward-app/src/hooks/useLocations.ts`

## SPEC-57 (O3-5545) - vague

** Prev/Next navigation in appointments calendar monthly view is not working as intenional**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-appointments-app/src/calendar/appointments-calendar-view.component.tsx` | 10 | 6 |
| `patient-management/packages/esm-appointments-app/src/calendar/monthly/days-of-week.component.tsx` | 1 | 5 |
| `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-calendar-view.component.tsx` | 3 | 1 |
| `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-header.component.tsx` | 8 | 4 |
| `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-workload-view-expanded.component.tsx` | 13 | 2 |
| `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-workload-view.component.tsx` | 12 | 9 |

Hybrid top 20:

1. `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-calendar-view.component.tsx` **<- target**
2. `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-workload-view-expanded.component.tsx` **<- target**
3. `patient-management/packages/esm-appointments-app/src/hooks/useSelectedDate.ts`
4. `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-header.component.tsx` **<- target**
5. `patient-management/packages/esm-appointments-app/src/calendar/monthly/days-of-week.component.tsx` **<- target**
6. `patient-management/packages/esm-appointments-app/src/calendar/appointments-calendar-view.component.tsx` **<- target**
7. `patient-management/packages/esm-appointments-app/src/workload/monthly-view-workload/monthlyWorkCard.tsx`
8. `patient-management/packages/esm-appointments-app/src/calendar/header/calendar-header.component.tsx`
9. `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-workload-view.component.tsx` **<- target**
10. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentsCalendar.ts`
11. `patient-management/packages/esm-appointments-app/src/header/appointments-header.component.tsx`
12. `patient-management/packages/esm-appointments-app/src/workload/monthly-view-workload/monthly-view.component.tsx`
13. `patient-management/packages/esm-appointments-app/src/workload/workload.resource.ts`
14. `patient-management/packages/esm-appointments-app/src/workload/workload.component.tsx`
15. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments.resource.ts`
16. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-upcoming-appointments-card.component.tsx`
17. `patient-management/packages/esm-appointments-app/src/metrics/metrics-header.component.tsx`
18. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentList.ts`
19. `patient-management/packages/esm-appointments-app/src/appointments/common-components/appointments-table.component.tsx`
20. `patient-management/packages/esm-appointments-app/src/types/index.ts`

## SPEC-58 (O3-5592) - vague

**Appointment Services should be sorted alphabetically**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-appointments-app/src/form/appointments-form.resource.ts` | - | 19 |
| `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx` | 9 | 20 |
| `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentService.ts` | - | 11 |
| `patient-management/packages/esm-appointments-app/src/workload/workload.component.tsx` | 20 | - |

Hybrid top 20:

1. `patient-management/packages/esm-appointments-app/src/appointments/utils.tsx`
2. `patient-management/packages/esm-service-queues-app/src/queue-patient-linelists/queue-linelist.resource.ts`
3. `patient-management/packages/esm-appointments-app/src/store.ts`
4. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentList.ts`
5. `patient-management/packages/esm-appointments-app/src/appointments/scheduled/early-appointments.component.tsx`
6. `patient-management/packages/esm-appointments-app/src/appointments/scheduled/scheduled-appointments.component.tsx`
7. `patient-management/packages/esm-appointments-app/src/types/index.ts`
8. `patient-management/packages/esm-appointments-app/src/index.ts`
9. `patient-management/packages/esm-appointments-app/src/appointments/common-components/batch-change-appointment-statuses.modal.tsx`
10. `patient-management/packages/esm-appointments-app/src/workload/workload.resource.ts`
11. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentService.ts` **<- target**
12. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments.resource.ts`
13. `patient-management/packages/esm-appointments-app/src/helpers/excel.ts`
14. `patient-management/packages/esm-service-queues-app/src/types/index.ts`
15. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentsAppContext.ts`
16. `patient-management/packages/esm-appointments-app/src/appointments.component.tsx`
17. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentsCalendar.ts`
18. `patient-management/packages/esm-appointments-app/src/home/home-appointments.component.tsx`
19. `patient-management/packages/esm-appointments-app/src/form/appointments-form.resource.ts` **<- target**
20. `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx` **<- target**

## SPEC-59 (O3-5742) - vague

**Build DailyCalendarView with compact appointment card list**

Not scored: none of the changed files existed at the frozen version (1 skipped).

## SPEC-60 (O3-5737) - vague

**Appointments: Download button is oversized with more padding**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-appointments-app/src/appointments/common-components/appointments-table.component.tsx` | 3 | 8 |

Hybrid top 20:

1. `patient-management/packages/esm-appointments-app/src/appointments/common-components/batch-change-appointment-statuses.modal.tsx`
2. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments-table.component.tsx`
3. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments-detailed-summary.extension.tsx`
4. `patient-management/packages/esm-appointments-app/src/types/index.ts`
5. `patient-management/packages/esm-appointments-app/src/form/appointments-form.workspace.tsx`
6. `patient-management/packages/esm-appointments-app/src/appointments/scheduled/scheduled-appointments.component.tsx`
7. `patient-management/packages/esm-appointments-app/src/appointments/common-components/appointments-actions.component.tsx`
8. `patient-management/packages/esm-appointments-app/src/appointments/common-components/appointments-table.component.tsx` **<- target**
9. `patient-management/packages/esm-appointments-app/src/home/home-appointments.component.tsx`
10. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentList.ts`
11. `patient-management/packages/esm-appointments-app/src/helpers/excel.ts`
12. `patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-workload-view-expanded.component.tsx`
13. `patient-management/packages/esm-appointments-app/src/hooks/useUnscheduledAppointments.ts`
14. `patient-management/packages/esm-appointments-app/src/hooks/useAppointmentsAppContext.ts`
15. `patient-management/packages/esm-appointments-app/src/config-schema.ts`
16. `patient-management/packages/esm-appointments-app/src/store.ts`
17. `patient-management/packages/esm-appointments-app/src/appointments/scheduled/early-appointments.component.tsx`
18. `patient-management/packages/esm-appointments-app/src/metrics/metrics-header.component.tsx`
19. `patient-management/packages/esm-appointments-app/src/patient-appointments/patient-appointments-action-menu.component.tsx`
20. `patient-management/packages/esm-appointments-app/src/calendar/appointments-calendar-view.component.tsx`

## SPEC-61 (O3-5729) - vague

**Build WeeklyCalendarView with CSS Grid time-slot layout**

Not scored: none of the changed files existed at the frozen version (3 skipped).

## SPEC-62 (O3-5624) - vague

**Ward App: add way to show the discharge workspace only in certain locations**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `patient-management/packages/esm-ward-app/src/action-menu-buttons/discharge-workspace-siderail.component.tsx` | 2 | 1 |
| `patient-management/packages/esm-ward-app/src/index.ts` | 8 | 4 |

(1 other changed files were tests or did not exist yet; not counted.)

Hybrid top 20:

1. `patient-management/packages/esm-ward-app/src/action-menu-buttons/discharge-workspace-siderail.component.tsx` **<- target**
2. `patient-management/packages/esm-ward-app/src/ward-workspace/patient-discharge/patient-discharge.workspace.tsx`
3. `patient-management/packages/esm-ward-app/src/action-menu-buttons/clinical-forms-workspace-siderail.component.tsx`
4. `patient-management/packages/esm-ward-app/src/index.ts` **<- target**
5. `patient-management/packages/esm-ward-app/src/action-menu-buttons/order-basket-action-button.component.tsx`
6. `patient-management/packages/esm-ward-app/src/ward-workspace/admission-request-workspace/admission-requests.workspace.tsx`
7. `patient-management/packages/esm-ward-app/src/ward.resource.ts`
8. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.workspace.tsx`
9. `patient-management/packages/esm-ward-app/src/ward-workspace/create-admission-encounter/create-admission-encounter.workspace.tsx`
10. `patient-management/packages/esm-ward-app/src/types/index.ts`
11. `patient-management/packages/esm-ward-app/src/config-schema.ts`
12. `patient-management/packages/esm-ward-app/src/hooks/useEmrConfiguration.ts`
13. `patient-management/packages/esm-ward-app/src/ward-workspace/cancel-admission-request-workspace/ward-patient-cancel-admission-request.workspace.tsx`
14. `patient-management/packages/esm-ward-app/src/ward-workspace/patient-details/ward-patient.workspace.tsx`
15. `patient-management/packages/esm-ward-app/src/ward-workspace/admit-patient-form-workspace/admit-patient-form.workspace.tsx`
16. `patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes-action-button.component.tsx`
17. `patient-management/packages/esm-ward-app/src/ward-view/ward-view.resource.ts`
18. `patient-management/packages/esm-ward-app/src/ward-workspace/patient-banner/patient-banner.component.tsx`
19. `patient-management/packages/esm-ward-app/src/ward-workspace/cancel-admission-request-workspace/cancel-admission-request.workspace.tsx`
20. `patient-management/packages/esm-ward-app/src/ward-workspace/patient-details/ward-patient-action-button.component.tsx`

## SPEC-63 (O3-5645) - security (names code files)

**Prevent open redirect via unvalidated returnToUrl**

| Changed file (target) | Rank combined | Rank hybrid |
|---|---|---|
| `core/packages/apps/esm-login-app/src/change-location-link/change-location-link.extension.tsx` | 9 | 12 |
| `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx` | 12 | 9 |
| `core/packages/apps/esm-login-app/src/login/login.component.tsx` | 5 | 5 |
| `core/packages/apps/esm-login-app/vitest.config.ts` | - | - |

Hybrid top 20:

1. `core/packages/apps/esm-login-app/src/redirect-logout/redirect-logout.component.tsx`
2. `core/packages/apps/esm-login-app/src/config-schema.ts`
3. `core/packages/apps/esm-login-app/src/redirect-logout/logout.resource.ts`
4. `core/packages/framework/esm-api/src/config-schema.ts`
5. `core/packages/apps/esm-login-app/src/login/login.component.tsx` **<- target**
6. `core/packages/apps/esm-login-app/src/root.component.tsx`
7. `core/packages/apps/esm-login-app/src/login.resource.ts`
8. `core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts`
9. `core/packages/apps/esm-login-app/src/location-picker/location-picker-view.component.tsx` **<- target**
10. `patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.resource.tsx`
11. `patient-management/packages/esm-patient-search-app/src/patient-search-page/refine-search/person-attributes.resource.ts`
12. `core/packages/apps/esm-login-app/src/change-location-link/change-location-link.extension.tsx` **<- target**
13. `core/packages/apps/esm-primary-navigation-app/src/index.ts`
14. `core/packages/framework/esm-api/src/openmrs-fetch.ts`
15. `patient-management/packages/esm-patient-search-app/src/patient-search.resource.tsx`
16. `core/packages/apps/esm-primary-navigation-app/src/config-schema.ts`
17. `core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts`
18. `patient-chart/packages/esm-patient-chart-app/src/visit/hooks/useDefaultVisitLocation.tsx`
19. `core/packages/shell/esm-app-shell/src/service-worker/routing.ts`
20. `patient-management/packages/esm-patient-registration-app/src/patient-registration/before-save-prompt.component.tsx`
