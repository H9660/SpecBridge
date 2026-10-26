# Code search scores - method: keyword

Run 2026-10-27 02:33. Index: 2322 code files (1755 non-test), 3827 pieces; already up to date; search 10.5 ms per ticket.

hit@k = share of tickets with at least one really-changed file in the top k; recall@k = share of each ticket's changed files found in the top k (averaged); mrr = average of 1 / rank of the first changed file found.

| Tickets | tickets | hit@5 | hit@10 | hit@20 | recall@5 | recall@10 | recall@20 | mrr |
|---|---|---|---|---|---|---|---|---|
| all | 61 | 0.69 | 0.79 | 0.89 | 0.44 | 0.54 | 0.63 | 0.46 |
| no file names in ticket | 43 | 0.63 | 0.70 | 0.84 | 0.38 | 0.47 | 0.57 | 0.43 |
| file names in ticket (mentions-files) | 18 | 0.83 | 1.00 | 1.00 | 0.57 | 0.73 | 0.79 | 0.52 |
| group: clear | 23 | 0.74 | 0.83 | 0.96 | 0.58 | 0.64 | 0.75 | 0.54 |
| group: cross-repo | 6 | 0.67 | 0.83 | 1.00 | 0.11 | 0.26 | 0.32 | 0.40 |
| group: normal | 14 | 0.79 | 0.86 | 0.93 | 0.44 | 0.58 | 0.67 | 0.55 |
| group: security | 1 | 1.00 | 1.00 | 1.00 | 0.25 | 0.25 | 0.75 | 0.25 |
| group: vague | 17 | 0.53 | 0.65 | 0.71 | 0.37 | 0.49 | 0.54 | 0.31 |

Not scored (no changed file existed at the frozen version): O3-5742, O3-5729

## Per ticket

| Ticket | Group | Files | First found at | Top result |
|---|---|---|---|---|
| SPEC-1 (O3-5714) | cross-repo * | 10 | 2 | core/packages/shell/esm-app-shell/src/run.ts |
| SPEC-2 (O3-5836) | cross-repo * | 2 | 8 | core/packages/framework/esm-styleguide/src/workspaces2/workspace2.ts |
| SPEC-3 (O3-6020) | cross-repo | 4 | 5 | patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts |
| SPEC-4 (O3-5986) | cross-repo | 13 | 11 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx |
| SPEC-5 (O3-5823) | cross-repo * | 11 | 2 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx |
| SPEC-6 (O3-5763) | cross-repo | 27 | 1 | patient-chart/packages/esm-patient-chart-app/src/visit/visits-widget/past-visits-components/visit-summary.component.tsx |
| SPEC-7 (O3-6028) | clear | 3 | 2 | core/packages/framework/esm-styleguide/src/location-picker/location-picker.component.tsx |
| SPEC-8 (O3-5981) | clear * | 1 | 1 | core/packages/framework/esm-error-handling/src/index.ts |
| SPEC-9 (O3-5849) | clear | 3 | 1 | core/packages/framework/esm-translations/src/translations.ts |
| SPEC-10 (O3-6026) | clear | 2 | 1 | patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx |
| SPEC-11 (O3-6019) | clear | 2 | 3 | dispensing-app/src/forms/dispense-form.workspace.tsx |
| SPEC-12 (O3-5969) | clear | 4 | 1 | patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx |
| SPEC-13 (O3-5798) | clear | 2 | - | patient-chart/packages/esm-patient-chart-app/src/visit/visit-form/exported-visit-form.workspace.tsx |
| SPEC-14 (O3-5850) | clear | 4 | 12 | patient-chart/packages/esm-patient-vitals-app/src/common/data.resource.ts |
| SPEC-15 (O3-4444) | clear | 10 | 1 | patient-chart/packages/esm-patient-common-lib/src/orders/types/order.ts |
| SPEC-16 (O3-5817) | clear | 1 | 3 | core/packages/framework/esm-react-utils/src/useEmrConfiguration.ts |
| SPEC-17 (O3-5889) | clear | 2 | 13 | core/packages/framework/esm-globals/src/types.ts |
| SPEC-18 (O3-5665) | clear | 6 | 6 | patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx |
| SPEC-19 (O3-5910) | clear | 1 | 2 | patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts |
| SPEC-20 (O3-5912) | clear | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-hierarchy.resource.tsx |
| SPEC-21 (O3-5913) | clear | 1 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts |
| SPEC-22 (O3-5918) | clear * | 1 | 4 | patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx |
| SPEC-23 (O3-6098) | clear * | 4 | 9 | patient-management/packages/esm-appointments-app/src/types/index.ts |
| SPEC-24 (O3-5917) | clear * | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/section/patient-relationships/relationships-section.component.tsx |
| SPEC-25 (O3-5919) | clear * | 2 | 5 | patient-chart/packages/esm-patient-chart-app/src/mark-patient-deceased/mark-patient-deceased-form.workspace.tsx |
| SPEC-26 (O3-5914) | clear * | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx |
| SPEC-27 (O3-5666) | clear | 3 | 20 | core/packages/framework/esm-api/src/openmrs-fetch.ts |
| SPEC-28 (O3-5916) | clear * | 2 | 2 | patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts |
| SPEC-29 (O3-5680) | clear * | 6 | 4 | patient-management/packages/esm-service-queues-app/src/types/index.ts |
| SPEC-30 (O3-6112) | normal * | 1 | 5 | billing-app/src/bill-history/bill-history.component.tsx |
| SPEC-31 (O3-5411) | normal | 4 | 5 | billing-app/src/config-schema.ts |
| SPEC-32 (O3-5413) | normal | 8 | 2 | core/packages/framework/esm-emr-api/src/types/fhir.ts |
| SPEC-33 (O3-5417) | normal | 14 | 1 | billing-app/src/invoice/payments/payments.component.tsx |
| SPEC-34 (O3-5708) | normal | 1 | - | dispensing-app/src/forms/dispense-form.workspace.tsx |
| SPEC-35 (O3-5743) | normal | 2 | 1 | billing-app/src/invoice/payments/payments.component.tsx |
| SPEC-36 (O3-5816) | normal * | 1 | 4 | core/packages/apps/esm-login-app/src/config-schema.ts |
| SPEC-37 (O3-5874) | normal * | 7 | 1 | core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.modal.tsx |
| SPEC-38 (O3-5588) | normal * | 1 | 6 | core/packages/framework/esm-styleguide/src/location-picker/location-picker.resource.ts |
| SPEC-39 (O3-5838) | normal | 2 | 1 | core/packages/apps/esm-login-app/src/login/login.component.tsx |
| SPEC-40 (O3-5449) | normal | 4 | 19 | core/packages/framework/esm-styleguide/src/workspaces2/workspace-windows-and-menu.component.tsx |
| SPEC-41 (O3-5650) | normal * | 5 | 1 | dispensing-app/src/config-schema.ts |
| SPEC-42 (O3-5632) | normal * | 1 | 1 | dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx |
| SPEC-43 (O3-4692) | normal | 2 | 3 | dispensing-app/src/history/history-and-comments.component.tsx |
| SPEC-44 (O3-5705) | vague | 2 | 1 | billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx |
| SPEC-45 (O3-5706) | vague | 1 | 2 | billing-app/src/config-schema.ts |
| SPEC-46 (O3-5202) | vague | 13 | 4 | core/packages/apps/esm-implementer-tools-app/src/implementer-tools.component.tsx |
| SPEC-47 (O3-5027) | vague | 2 | 4 | core/packages/framework/esm-emr-api/src/types/fhir.ts |
| SPEC-48 (O3-5630) | vague | 3 | 1 | dispensing-app/src/forms/medication-dispense-review.component.tsx |
| SPEC-49 (O3-5610) | vague | 3 | 9 | patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/test-order-form.component.tsx |
| SPEC-50 (O3-4578) | vague | 3 | 3 | patient-chart/packages/esm-patient-immunizations-app/src/immunizations/delete-immunization.modal.tsx |
| SPEC-51 (O3-5677) | vague | 2 | - | patient-chart/packages/esm-patient-attachments-app/src/attachments/attachments-overview.component.tsx |
| SPEC-52 (O3-5078) | vague | 2 | - | patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes-action-button.component.tsx |
| SPEC-53 (O3-5801) | vague | 1 | - | patient-management/packages/esm-ward-app/src/ward-workspace/patient-transfer-bed-swap/patient-admit-or-transfer-request-form.component.tsx |
| SPEC-54 (O3-5436) | vague | 2 | - | patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/reference-range-helpers.ts |
| SPEC-55 (O3-5452) | vague | 6 | - | patient-chart/packages/esm-patient-orders-app/src/config-schema.ts |
| SPEC-56 (O3-5534) | vague | 1 | 7 | patient-management/packages/esm-patient-registration-app/src/patient-registration/input/combo-input/combo-input.component.tsx |
| SPEC-57 (O3-5545) | vague | 6 | 1 | patient-management/packages/esm-appointments-app/src/calendar/monthly/monthly-header.component.tsx |
| SPEC-58 (O3-5592) | vague | 4 | 11 | patient-management/packages/esm-appointments-app/src/appointments/scheduled/early-appointments.component.tsx |
| SPEC-59 (O3-5742) | vague | 0 | n/a | patient-management/packages/esm-appointments-app/src/workload/monthly-view-workload/monthly-view.component.tsx |
| SPEC-60 (O3-5737) | vague | 1 | 5 | core/packages/framework/esm-styleguide/src/icons/icon-registration.ts |
| SPEC-61 (O3-5729) | vague | 0 | n/a | patient-management/packages/esm-appointments-app/src/hooks/useAppointmentsCalendar.ts |
| SPEC-62 (O3-5624) | vague | 2 | 3 | patient-management/packages/esm-ward-app/src/ward-workspace/patient-discharge/patient-discharge.workspace.tsx |
| SPEC-63 (O3-5645) | security * | 4 | 4 | core/packages/framework/esm-api/src/openmrs-fetch.ts |

\* ticket names code files (scored separately).
