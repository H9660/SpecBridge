# Code search scores - method: combined

Run 2026-10-27 11:48. Index: 2322 code files (1755 non-test), 3827 pieces; built now in 3.2 s; search 26.6 ms per ticket.

hit@k = share of tickets with at least one really-changed file in the top k; recall@k = share of each ticket's changed files found in the top k (averaged); mrr = average of 1 / rank of the first changed file found.

| Tickets | tickets | hit@5 | hit@10 | hit@20 | recall@5 | recall@10 | recall@20 | mrr |
|---|---|---|---|---|---|---|---|---|
| all | 61 | 0.70 | 0.80 | 0.87 | 0.43 | 0.58 | 0.66 | 0.53 |
| no file names in ticket | 43 | 0.63 | 0.74 | 0.84 | 0.40 | 0.50 | 0.60 | 0.48 |
| file names in ticket (mentions-files) | 18 | 0.89 | 0.94 | 0.94 | 0.51 | 0.75 | 0.78 | 0.64 |
| group: clear | 23 | 0.83 | 0.87 | 0.91 | 0.52 | 0.67 | 0.74 | 0.60 |
| group: cross-repo | 6 | 0.67 | 1.00 | 1.00 | 0.18 | 0.43 | 0.52 | 0.64 |
| group: normal | 14 | 0.79 | 0.86 | 0.86 | 0.49 | 0.57 | 0.65 | 0.54 |
| group: security | 1 | 1.00 | 1.00 | 1.00 | 0.25 | 0.50 | 0.75 | 0.20 |
| group: vague | 17 | 0.47 | 0.59 | 0.76 | 0.36 | 0.50 | 0.59 | 0.40 |

Not scored (no changed file existed at the frozen version): O3-5742, O3-5729

## Per ticket

| Ticket | Group | Files | First found at | Top result |
|---|---|---|---|---|
| SPEC-1 (O3-5714) | cross-repo * | 10 | 1 | patient-management/packages/esm-patient-search-app/src/patient-search.resource.tsx |
| SPEC-2 (O3-5836) | cross-repo * | 2 | 6 | patient-management/packages/esm-patient-search-app/src/patient-search-page/patient-banner/banner/start-visit-button2.component.tsx |
| SPEC-3 (O3-6020) | cross-repo | 4 | 2 | patient-chart/packages/esm-patient-notes-app/src/notes/visit-notes-form.workspace.tsx |
| SPEC-4 (O3-5986) | cross-repo | 13 | 6 | patient-chart/packages/esm-patient-attachments-app/src/camera-media-uploader/camera-media-uploader.component.tsx |
| SPEC-5 (O3-5823) | cross-repo * | 11 | 1 | patient-chart/packages/esm-patient-notes-app/src/types/index.ts |
| SPEC-6 (O3-5763) | cross-repo | 27 | 1 | patient-management/packages/esm-service-queues-app/src/past-visit/past-visit.component.tsx |
| SPEC-7 (O3-6028) | clear | 3 | 1 | core/packages/apps/esm-login-app/src/config-schema.ts |
| SPEC-8 (O3-5981) | clear * | 1 | - | patient-chart/packages/esm-form-engine-app/src/form-renderer/repeat/delete-question.modal.tsx |
| SPEC-9 (O3-5849) | clear | 3 | 1 | core/packages/framework/esm-styleguide/src/workspaces2/workspace2-close-prompt.modal.tsx |
| SPEC-10 (O3-6026) | clear | 2 | 1 | patient-chart/packages/esm-patient-vitals-app/src/vitals/vitals-overview.component.tsx |
| SPEC-11 (O3-6019) | clear | 2 | 2 | patient-chart/packages/esm-patient-medications-app/src/add-drug-order/drug-order-form.resource.ts |
| SPEC-12 (O3-5969) | clear | 4 | 1 | patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-widget.component.tsx |
| SPEC-13 (O3-5798) | clear | 2 | - | patient-management/packages/esm-active-visits-app/src/active-visits-widget/active-visits.resource.ts |
| SPEC-14 (O3-5850) | clear | 4 | 17 | core/packages/framework/esm-styleguide/src/numeric-observation/numeric-observation.component.tsx |
| SPEC-15 (O3-4444) | clear | 10 | 1 | patient-chart/packages/esm-patient-medications-app/src/api/api.ts |
| SPEC-16 (O3-5817) | clear | 1 | 1 | patient-chart/packages/esm-form-entry-app/src/app/form-creation/form-creation.service.ts |
| SPEC-17 (O3-5889) | clear | 2 | 5 | patient-chart/packages/esm-generic-patient-widgets-app/src/obs-switchable/obs-switchable.component.tsx |
| SPEC-18 (O3-5665) | clear | 6 | 1 | patient-management/packages/esm-service-queues-app/src/current-visit/visit-details/vitals.component.tsx |
| SPEC-19 (O3-5910) | clear | 1 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/form-manager.ts |
| SPEC-20 (O3-5912) | clear | 2 | 2 | patient-management/packages/esm-patient-registration-app/src/patient-registration/field/address/address-search.component.tsx |
| SPEC-21 (O3-5913) | clear | 1 | 2 | core/packages/shell/esm-app-shell/src/locale.ts |
| SPEC-22 (O3-5918) | clear * | 1 | 4 | patient-chart/packages/esm-patient-chart-app/src/data.resource.ts |
| SPEC-23 (O3-6098) | clear * | 4 | 2 | patient-management/packages/esm-service-queues-app/src/queue-table/queue-table-expanded-row.component.tsx |
| SPEC-24 (O3-5917) | clear * | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts |
| SPEC-25 (O3-5919) | clear * | 2 | 4 | patient-chart/packages/esm-patient-chart-app/src/data.resource.ts |
| SPEC-26 (O3-5914) | clear * | 2 | 1 | patient-management/packages/esm-patient-registration-app/src/patient-registration/field/person-attributes/location-person-attribute-field.component.tsx |
| SPEC-27 (O3-5666) | clear | 3 | 10 | core/packages/tooling/openmrs/src/cli.ts |
| SPEC-28 (O3-5916) | clear * | 2 | 3 | patient-management/packages/esm-patient-registration-app/src/patient-registration/patient-registration.types.ts |
| SPEC-29 (O3-5680) | clear * | 6 | 2 | patient-management/packages/esm-service-queues-app/src/modals/call-modal/call-queue-entry.modal.tsx |
| SPEC-30 (O3-6112) | normal * | 1 | 1 | billing-app/src/billing-form/billing-form.workspace.tsx |
| SPEC-31 (O3-5411) | normal | 4 | 2 | billing-app/src/config-schema.ts |
| SPEC-32 (O3-5413) | normal | 8 | 3 | billing-app/src/billing.resource.ts |
| SPEC-33 (O3-5417) | normal | 14 | 3 | billing-app/src/invoice/payments/payment-form/payment-form.component.tsx |
| SPEC-34 (O3-5708) | normal | 1 | - | dispensing-app/src/components/prescription-actions/dispense-action-button.component.tsx |
| SPEC-35 (O3-5743) | normal | 2 | 2 | billing-app/src/invoice/payments/invoice-breakdown/invoice-breakdown.component.tsx |
| SPEC-36 (O3-5816) | normal * | 1 | 3 | core/packages/apps/esm-login-app/src/login/login.component.tsx |
| SPEC-37 (O3-5874) | normal * | 7 | 1 | core/packages/apps/esm-primary-navigation-app/src/components/change-language/change-language.modal.tsx |
| SPEC-38 (O3-5588) | normal * | 1 | 1 | core/packages/apps/esm-login-app/src/location-picker/location-picker.resource.ts |
| SPEC-39 (O3-5838) | normal | 2 | 2 | core/packages/framework/esm-api/src/current-user.ts |
| SPEC-40 (O3-5449) | normal | 4 | - | core/packages/shell/esm-app-shell/src/service-worker/routing.ts |
| SPEC-41 (O3-5650) | normal * | 5 | 1 | dispensing-app/src/prescriptions/prescription-tab-lists.component.tsx |
| SPEC-42 (O3-5632) | normal * | 1 | 1 | dispensing-app/src/fill-prescription/on-prescription-filled.modal.tsx |
| SPEC-43 (O3-4692) | normal | 2 | 10 | dispensing-app/src/medication-request/medication-request.resource.tsx |
| SPEC-44 (O3-5705) | vague | 2 | 1 | billing-app/src/invoice/printable-invoice/printable-invoice.component.tsx |
| SPEC-45 (O3-5706) | vague | 1 | 1 | billing-app/src/billing-form/visit-attributes/visit-attributes-form.component.tsx |
| SPEC-46 (O3-5202) | vague | 13 | 18 | core/packages/apps/esm-implementer-tools-app/src/backend-dependencies/useBackendDependencies.ts |
| SPEC-47 (O3-5027) | vague | 2 | 2 | core/packages/apps/esm-login-app/src/footer.component.tsx |
| SPEC-48 (O3-5630) | vague | 3 | 1 | dispensing-app/src/forms/medication-dispense-review.component.tsx |
| SPEC-49 (O3-5610) | vague | 3 | 13 | patient-chart/packages/esm-patient-tests-app/src/test-orders/add-test-order/add-test-order.component.tsx |
| SPEC-50 (O3-4578) | vague | 3 | 1 | patient-chart/packages/esm-patient-immunizations-app/src/immunizations/components/immunizations-sequence-table.component.tsx |
| SPEC-51 (O3-5677) | vague | 2 | - | dispensing-app/src/print-prescription/prescription-print-action.component.tsx |
| SPEC-52 (O3-5078) | vague | 2 | 11 | patient-management/packages/esm-ward-app/src/ward-workspace/ward-patient-notes/notes.workspace.tsx |
| SPEC-53 (O3-5801) | vague | 1 | - | patient-management/packages/esm-ward-app/src/hooks/useInpatientAdmissionByPatients.ts |
| SPEC-54 (O3-5436) | vague | 2 | - | patient-chart/packages/esm-patient-tests-app/src/test-results/grouped-timeline/reference-range-helpers.ts |
| SPEC-55 (O3-5452) | vague | 6 | - | patient-chart/packages/esm-patient-chart-app/src/clinical-views/encounter-list/encounter-list.component.tsx |
| SPEC-56 (O3-5534) | vague | 1 | 8 | patient-chart/packages/esm-patient-chart-app/src/data.resource.ts |
| SPEC-57 (O3-5545) | vague | 6 | 1 | patient-management/packages/esm-appointments-app/src/calendar/monthly/days-of-week.component.tsx |
| SPEC-58 (O3-5592) | vague | 4 | 9 | patient-management/packages/esm-appointments-app/src/appointments/scheduled/early-appointments.component.tsx |
| SPEC-59 (O3-5742) | vague | 0 | n/a | patient-management/packages/esm-appointments-app/src/calendar/monthly/days-of-week.component.tsx |
| SPEC-60 (O3-5737) | vague | 1 | 3 | patient-management/packages/esm-appointments-app/src/helpers/excel.ts |
| SPEC-61 (O3-5729) | vague | 0 | n/a | patient-management/packages/esm-appointments-app/src/calendar/monthly/days-of-week.component.tsx |
| SPEC-62 (O3-5624) | vague | 2 | 2 | patient-management/packages/esm-ward-app/src/ward-workspace/patient-discharge/patient-discharge.workspace.tsx |
| SPEC-63 (O3-5645) | security * | 4 | 5 | core/packages/framework/esm-api/src/config-schema.ts |

\* ticket names code files (scored separately).
