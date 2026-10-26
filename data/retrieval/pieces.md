# Code search scores - method: pieces

Run 2026-10-27 02:33. Index: 2322 code files (1755 non-test), 3827 pieces; already up to date; search 17.3 ms per ticket.

hit@k = share of tickets with at least one really-changed file in the top k; recall@k = share of each ticket's changed files found in the top k (averaged); mrr = average of 1 / rank of the first changed file found.

| Tickets | tickets | hit@5 | hit@10 | hit@20 | recall@5 | recall@10 | recall@20 | mrr |
|---|---|---|---|---|---|---|---|---|
| all | 61 | 0.70 | 0.79 | 0.87 | 0.42 | 0.54 | 0.63 | 0.50 |
| no file names in ticket | 43 | 0.65 | 0.74 | 0.84 | 0.38 | 0.51 | 0.58 | 0.49 |
| file names in ticket (mentions-files) | 18 | 0.83 | 0.89 | 0.94 | 0.53 | 0.60 | 0.75 | 0.51 |
| group: clear | 23 | 0.83 | 0.87 | 0.87 | 0.55 | 0.61 | 0.70 | 0.56 |
| group: cross-repo | 6 | 0.83 | 0.83 | 1.00 | 0.21 | 0.31 | 0.42 | 0.46 |
| group: normal | 14 | 0.79 | 0.79 | 0.86 | 0.43 | 0.52 | 0.61 | 0.57 |
| group: security | 1 | 0.00 | 1.00 | 1.00 | 0.00 | 0.50 | 0.75 | 0.17 |
| group: vague | 17 | 0.47 | 0.65 | 0.82 | 0.34 | 0.53 | 0.64 | 0.38 |

Not scored (no changed file existed at the frozen version): O3-5742, O3-5729

## Per ticket

| Ticket | Group | Files | First found at | Top result |
|---|---|---|---|---|
| SPEC-1 (O3-5714) | cross-repo * | 10 | 2 | patient-chart/packages/esm-patient-banner-app/src/hooks/useCauseOfDeath.ts |
| SPEC-2 (O3-5836) | cross-repo * | 2 | 5 | core/packages/framework/esm-styleguide/src/workspaces2/workspace2.ts |
| SPEC-3 (O3-6020) | cross-repo | 4 | 2 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx |
| SPEC-4 (O3-5986) | cross-repo | 13 | 15 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx |
| SPEC-5 (O3-5823) | cross-repo * | 11 | 2 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx |
| SPEC-6 (O3-5763) | cross-repo | 27 | 1 | patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx |
| SPEC-7 (O3-6028) | clear | 3 | 2 | core/packages/framework/esm-styleguide/src/location-picker/location-picker.component.tsx |
| SPEC-8 (O3-5981) | clear * | 1 | - | core/packages/framework/esm-dynamic-loading/src/dynamic-loading.ts |
| SPEC-9 (O3-5849) | clear | 3 | 1 | core/packages/framework/esm-styleguide/src/workspaces2/workspace2-close-prompt.modal.tsx |
| SPEC-10 (O3-6026) | clear | 2 | 1 | patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx |
| SPEC-11 (O3-6019) | clear | 2 | 4 | dispensing-app/src/forms/dispense-form.workspace.tsx |
| SPEC-12 (O3-5969) | clear | 4 | 1 | patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx |
| SPEC-13 (O3-5798) | clear | 2 | - | patient-management/packages/esm-active-visits-app/src/active-visits-widget/active-visits.resource.ts |
| SPEC-14 (O3-5850) | clear | 4 | - | core/packages/framework/esm-styleguide/src/numeric-observation/use-concept-reference-range.ts |
| SPEC-15 (O3-4444) | clear | 10 | 1 | patient-chart/packages/esm-patient-medications-app/src/add-drug-order/add-drug-order.component.tsx |
| SPEC-16 (O3-5817) | clear | 1 | 3 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-note-config-schema.ts |
| SPEC-17 (O3-5889) | clear | 2 | 4 | patient-management/packages/esm-patient-registration-app/src/config-schema.ts |
| SPEC-18 (O3-5665) | clear | 6 | 1 | patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/vitals.component.tsx |
| SPEC-19 (O3-5910) | clear | 1 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts |
| SPEC-20 (O3-5912) | clear | 2 | 2 | patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy-levels.component.tsx |
| SPEC-21 (O3-5913) | clear | 1 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts |
| SPEC-22 (O3-5918) | clear * | 1 | 2 | patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx |
| SPEC-23 (O3-6098) | clear * | 4 | 5 | patient-management/packages/esm-appointments-app/src/types/index.ts |
| SPEC-24 (O3-5917) | clear * | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships-section.component.tsx |
| SPEC-25 (O3-5919) | clear * | 2 | 3 | patient-chart/packages/esm-patient-chart-app/src/data.resource.ts |
| SPEC-26 (O3-5914) | clear * | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx |
| SPEC-27 (O3-5666) | clear | 3 | 10 | core/packages/tooling/openmrs/src/cli.ts |
| SPEC-28 (O3-5916) | clear * | 2 | 2 | patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts |
| SPEC-29 (O3-5680) | clear * | 6 | 2 | patient-management/packages/esm-service-queues-app/src/modals/call-modal/call-queue-entry.modal.tsx |
| SPEC-30 (O3-6112) | normal * | 1 | 12 | billing-app/src/bill-history/bill-history.component.tsx |
| SPEC-31 (O3-5411) | normal | 4 | 2 | billing-app/src/config-schema.ts |
| SPEC-32 (O3-5413) | normal | 8 | 2 | core/packages/framework/esm-emr-api/src/types/fhir.ts |
| SPEC-33 (O3-5417) | normal | 14 | 1 | billing-app/src/invoice/payments/payments.component.tsx |
| SPEC-34 (O3-5708) | normal | 1 | - | dispensing-app/src/forms/medication-dispense-review.component.tsx |
| SPEC-35 (O3-5743) | normal | 2 | 1 | billing-app/src/invoice/payments/payments.component.tsx |
| SPEC-36 (O3-5816) | normal * | 1 | 3 | core/packages/apps/esm-login-app/src/login/login.component.tsx |
| SPEC-37 (O3-5874) | normal * | 7 | 1 | core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.modal.tsx |
| SPEC-38 (O3-5588) | normal * | 1 | 3 | core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts |
| SPEC-39 (O3-5838) | normal | 2 | 1 | core/packages/apps/esm-login-app/src/login/login.component.tsx |
| SPEC-40 (O3-5449) | normal | 4 | - | core/packages/shell/esm-app-shell/src/service-worker/routing.ts |
| SPEC-41 (O3-5650) | normal * | 5 | 1 | dispensing-app/src/config-schema.ts |
| SPEC-42 (O3-5632) | normal * | 1 | 1 | dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx |
| SPEC-43 (O3-4692) | normal | 2 | 4 | dispensing-app/src/history/history-and-comments.component.tsx |
| SPEC-44 (O3-5705) | vague | 2 | 1 | billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx |
| SPEC-45 (O3-5706) | vague | 1 | 1 | billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx |
| SPEC-46 (O3-5202) | vague | 13 | 17 | core/packages/apps/esm-implementer-tools-app/src/implementer-tools.component.tsx |
| SPEC-47 (O3-5027) | vague | 2 | 4 | core/packages/framework/esm-config/src/module-config/module-config.ts |
| SPEC-48 (O3-5630) | vague | 3 | 1 | dispensing-app/src/forms/medication-dispense-review.component.tsx |
| SPEC-49 (O3-5610) | vague | 3 | 8 | patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/test-order-form.component.tsx |
| SPEC-50 (O3-4578) | vague | 3 | 3 | patient-chart/packages/esm-patient-immunizations-app/src/immunizations/immunization-mapper.ts |
| SPEC-51 (O3-5677) | vague | 2 | - | patient-chart/packages/esm-patient-attachments-app/src/attachments/attachment-preview.component.tsx |
| SPEC-52 (O3-5078) | vague | 2 | 11 | core/packages/framework/esm-styleguide/mock.tsx |
| SPEC-53 (O3-5801) | vague | 1 | - | patient-management/packages/esm-ward-app/src/hooks/useInpatientAdmissionByPatients.ts |
| SPEC-54 (O3-5436) | vague | 2 | 20 | patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/reference-range-helpers.ts |
| SPEC-55 (O3-5452) | vague | 6 | - | patient-chart/packages/esm-patient-chart-app/src/clinical-views/encounter-list/encounter-list.component.tsx |
| SPEC-56 (O3-5534) | vague | 1 | 6 | patient-management/packages/esm-patient-registration-app/src/patient-registration/input/combo-input/combo-input.component.tsx |
| SPEC-57 (O3-5545) | vague | 6 | 1 | patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-header.component.tsx |
| SPEC-58 (O3-5592) | vague | 4 | 9 | patient-management/packages/esm-appointments-app/src/appointments/scheduled/early-appointments.component.tsx |
| SPEC-59 (O3-5742) | vague | 0 | n/a | patient-management/packages/esm-appointments-app/src/workload/monthly-view-workload/monthly-view.component.tsx |
| SPEC-60 (O3-5737) | vague | 1 | 1 | patient-management/packages/esm-appointments-app/src/appointments/common-components/appointments-table.component.tsx |
| SPEC-61 (O3-5729) | vague | 0 | n/a | patient-management/packages/esm-appointments-app/src/hooks/useAppointmentsCalendar.ts |
| SPEC-62 (O3-5624) | vague | 2 | 4 | patient-management/packages/esm-ward-app/src/ward.resource.ts |
| SPEC-63 (O3-5645) | security * | 4 | 6 | core/packages/framework/esm-api/src/openmrs-fetch.ts |

\* ticket names code files (scored separately).
