# Golden dataset candidates (v0)

Real O3 tickets whose code was changed only after **2026-04-01**. The repos are pinned to their last
commit before that date (see `data/snapshots.json`), so for every ticket below the code SpecBridge
reads is the code *before* the ticket was built - exactly what a PM would have at ticket creation.

Dropped: 29 started before cutoff, 25 housekeeping, 22 no app code changed, 8 description too short, 3 not finished, 2 epic/test ticket.

| # | Ticket | Type | Tags | Repos | Files changed | Summary |
|---|---|---|---|---|---|---|
| 1 | [O3-1786](https://openmrs.atlassian.net/browse/O3-1786) | Bug | bug | patient-chart | 3 | Add notes to Vitals widget |
| 2 | [O3-1830](https://openmrs.atlassian.net/browse/O3-1830) | New Feature | feature | patient-management | 7 | Registration: Mark a patient identifier as preferred |
| 3 | [O3-4020](https://openmrs.atlassian.net/browse/O3-4020) | Bug | bug | core | 2 | Ward App - useAppContext does not work in AdmissionRequestsWorkspace |
| 4 | [O3-4444](https://openmrs.atlassian.net/browse/O3-4444) | Improvement | feature, has-acceptance-criteria | patient-chart | 10 | Persist user-selected start date on medication orders |
| 5 | [O3-4578](https://openmrs.atlassian.net/browse/O3-4578) | Bug | bug, vague | patient-chart | 3 | Duplicate Dose Entries in Immunization Module |
| 6 | [O3-4648](https://openmrs.atlassian.net/browse/O3-4648) | Bug | bug | patient-chart | 1 | Bad error "uuid is null" when adding drug order as admin with no current provider |
| 7 | [O3-4692](https://openmrs.atlassian.net/browse/O3-4692) | Bug | bug | dispensing-app | 2 | Display "Dispensed" Status in Prescription Details Section (Consistent with "Cancelled" and "Paused") |
| 8 | [O3-5027](https://openmrs.atlassian.net/browse/O3-5027) | New Feature | feature, vague | core | 2 | Beautiful + Configurable Login Page |
| 9 | [O3-5047](https://openmrs.atlassian.net/browse/O3-5047) | Task | feature | patient-management | 1 | A fieldset does not have a legend |
| 10 | [O3-5077](https://openmrs.atlassian.net/browse/O3-5077) | Story | feature | patient-chart | 17 | Support for recording clinical procedures |
| 11 | [O3-5078](https://openmrs.atlassian.net/browse/O3-5078) | New Feature | feature, vague | patient-chart | 9 | Sticky Note in O3 |
| 12 | [O3-5202](https://openmrs.atlassian.net/browse/O3-5202) | Enhancement | feature, vague | billing-app | 18 | Add a UI button to "finalize" a bill |
| 13 | [O3-5255](https://openmrs.atlassian.net/browse/O3-5255) | Improvement | feature | patient-management | 1 | Implement a free text field to allow entering a discharge note when discharging a patient |
| 14 | [O3-5401](https://openmrs.atlassian.net/browse/O3-5401) | New Feature | cross-repo, feature | dispensing-app, patient-chart | 10 | Able to show only required slot in the order basket workspace  |
| 15 | [O3-5411](https://openmrs.atlassian.net/browse/O3-5411) | New Feature | feature | billing-app | 4 | Automatically Waive Consultation Fees for Return Visits Within 7 Days |
| 16 | [O3-5413](https://openmrs.atlassian.net/browse/O3-5413) | New Feature | feature | billing-app | 23 | Enable Refund Requests and Approval for Paid Bills |
| 17 | [O3-5417](https://openmrs.atlassian.net/browse/O3-5417) | Enhancement | feature | billing-app | 31 | Bill Discount Management with Audit Trail |
| 18 | [O3-5432](https://openmrs.atlassian.net/browse/O3-5432) | Improvement | feature | patient-chart | 1 | Add inline validation when the completion date is before the enrollment date in the program enrollment form |
| 19 | [O3-5436](https://openmrs.atlassian.net/browse/O3-5436) | Improvement | feature, vague | patient-chart | 2 | Align test result values and reference range columns in the Tests tab |
| 20 | [O3-5444](https://openmrs.atlassian.net/browse/O3-5444) | Bug | bug | patient-chart | 1 | System allows identical condition to be saved twice with no duplicate warning |
| 21 | [O3-5449](https://openmrs.atlassian.net/browse/O3-5449) | Task | feature | core | 4 | Integrate Chart Line Icon for Growth Chart in Left Navigation |
| 22 | [O3-5452](https://openmrs.atlassian.net/browse/O3-5452) | Task | feature, vague | patient-chart | 9 | Printing encounters based on O3-forms |
| 23 | [O3-5479](https://openmrs.atlassian.net/browse/O3-5479) | Bug | bug | billing-app | 1 | fix(billing): implement safe patient display parsing with validation and fallbacks. |
| 24 | [O3-5488](https://openmrs.atlassian.net/browse/O3-5488) | Bug | bug | patient-management | 1 | Avoid unnecessary event listener re-registration in combo-input.component.tsx |
| 25 | [O3-5489](https://openmrs.atlassian.net/browse/O3-5489) | Improvement | feature | patient-management | 1 | Replace loose equality (==) with strict equality (===) in ward-view.resource.ts |
| 26 | [O3-5514](https://openmrs.atlassian.net/browse/O3-5514) | Bug | bug | patient-management | 1 | The iconDescription for the "Add Appointments" button is currently hardcoded. |
| 27 | [O3-5534](https://openmrs.atlassian.net/browse/O3-5534) | Bug | bug, vague | patient-management | 1 | Fix index-based keys in address search suggestions causing incorrect selection behavior |
| 28 | [O3-5536](https://openmrs.atlassian.net/browse/O3-5536) | Sub-task | feature | patient-management | 10 | Type-safe appointments app from `any` type declarations |
| 29 | [O3-5540](https://openmrs.atlassian.net/browse/O3-5540) | Improvement | feature | patient-chart | 1 | Add Allergy Quick-Add Link in Drug Order Basket |
| 30 | [O3-5541](https://openmrs.atlassian.net/browse/O3-5541) | Bug | bug | patient-chart | 1 | Implement RDE Feature Flag for Visit Note Datepicker |
| 31 | [O3-5545](https://openmrs.atlassian.net/browse/O3-5545) | Bug | bug, vague | patient-management | 6 |  Prev/Next navigation in appointments calendar monthly view is not working as intenional |
| 32 | [O3-5558](https://openmrs.atlassian.net/browse/O3-5558) | Bug | bug | patient-management | 1 | Service Queues table displays/shows negative wait times for patients |
| 33 | [O3-5559](https://openmrs.atlassian.net/browse/O3-5559) | Bug | bug | patient-management | 1 |  Edit queue entry time impossible to satisfy |
| 34 | [O3-5561](https://openmrs.atlassian.net/browse/O3-5561) | Improvement | feature | patient-chart | 1 | Display Vital Sign Reference Ranges on Hover/Tap |
| 35 | [O3-5565](https://openmrs.atlassian.net/browse/O3-5565) | Bug | bug | patient-management | 2 | showToast/showSnackbar called during render in service queues queue table components |
| 36 | [O3-5571](https://openmrs.atlassian.net/browse/O3-5571) | Bug | bug | patient-management | 1 | Service-queues: handle invalid time input format in queue entry transition modal |
| 37 | [O3-5573](https://openmrs.atlassian.net/browse/O3-5573) | Task | feature | patient-management | 9 | Appointments: add actions column to appointments table |
| 38 | [O3-5579](https://openmrs.atlassian.net/browse/O3-5579) | Bug | bug | patient-management | 3 | fix(esm-appointments-app): Isolate appointment cache per patient to prevent cross-patient data leakage. |
| 39 | [O3-5580](https://openmrs.atlassian.net/browse/O3-5580) | Improvement | feature | patient-chart | 1 | Set Default Clinical Status to "Active" When Adding a New Condition |
| 40 | [O3-5581](https://openmrs.atlassian.net/browse/O3-5581) | Bug | bug | core | 1 | `yarn serve` uses incorrect base URL for lazily compiled resources |
| 41 | [O3-5584](https://openmrs.atlassian.net/browse/O3-5584) | Improvement | feature | patient-management | 1 | fix(ward): un-awaited mutate() in patient transfer form causes UI race condition |
| 42 | [O3-5588](https://openmrs.atlassian.net/browse/O3-5588) | Bug | bug | core | 1 | fix(login-app): Login Location tag filter silently ignored in useLocationCount |
| 43 | [O3-5592](https://openmrs.atlassian.net/browse/O3-5592) | Improvement | feature, vague | patient-management | 4 | Appointment Services should be sorted alphabetically |
| 44 | [O3-5593](https://openmrs.atlassian.net/browse/O3-5593) | Bug | bug | patient-management | 3 | The sidebar doesn't behave sticky on scroll in Patient Registration App |
| 45 | [O3-5595](https://openmrs.atlassian.net/browse/O3-5595) | Bug | bug | patient-management | 4 | Service Queues: queue table incorrectly stuck in "validating" step sometimes |
| 46 | [O3-5597](https://openmrs.atlassian.net/browse/O3-5597) | Sub-task | feature, vague | patient-management | 4 | Type-safe ward app from `any` type declarations |
| 47 | [O3-5599](https://openmrs.atlassian.net/browse/O3-5599) | Story | feature | patient-chart | 33 | Standardize URL paths in the patient chart |
| 48 | [O3-5600](https://openmrs.atlassian.net/browse/O3-5600) | Story | feature | patient-management | 2 | Standardize URL paths in the patient management app |
| 49 | [O3-5601](https://openmrs.atlassian.net/browse/O3-5601) | Story | feature | billing-app | 1 | Standardize URL paths in the billing app |
| 50 | [O3-5610](https://openmrs.atlassian.net/browse/O3-5610) | Bug | bug, vague | patient-chart | 3 | Add result date column to lab order result |
| 51 | [O3-5614](https://openmrs.atlassian.net/browse/O3-5614) | Bug | bug | patient-chart | 2 | Restore delete-condition retry flow and stabilize form-entry test runner |
| 52 | [O3-5618](https://openmrs.atlassian.net/browse/O3-5618) | Bug | bug | patient-chart | 2 | Conditions form does not validate garbage text |
| 53 | [O3-5620](https://openmrs.atlassian.net/browse/O3-5620) | Task | feature | patient-management | 8 | Ward app: Show edit history for inpatient notes |
| 54 | [O3-5624](https://openmrs.atlassian.net/browse/O3-5624) | Task | feature, vague | patient-management | 3 | Ward App: add way to show the discharge workspace only in certain locations |
| 55 | [O3-5628](https://openmrs.atlassian.net/browse/O3-5628) | Bug | bug | patient-management | 1 | Ward App: inpatient notes does not show up after saving |
| 56 | [O3-5630](https://openmrs.atlassian.net/browse/O3-5630) | Bug | bug, vague | dispensing-app | 3 | Dispensing: Bug when editing substitution reason of an old order |
| 57 | [O3-5632](https://openmrs.atlassian.net/browse/O3-5632) | Bug | bug | dispensing-app | 1 | Dispensing modal: "Dispense all prescriptions" fires before medication request data has loaded |
| 58 | [O3-5633](https://openmrs.atlassian.net/browse/O3-5633) | Bug | bug | patient-management | 1 | Service Queue Line List: Patient chart link uses queue entry UUID instead of patient UUID |
| 59 | [O3-5634](https://openmrs.atlassian.net/browse/O3-5634) | Sub-task | feature | patient-management | 2 | Type-safe patient search app from `any` type declarations |
| 60 | [O3-5641](https://openmrs.atlassian.net/browse/O3-5641) | Improvement | feature | patient-management | 7 | Remove unused ServicesTable component from Service Queues App |
| 61 | [O3-5642](https://openmrs.atlassian.net/browse/O3-5642) | Improvement | feature, has-acceptance-criteria | patient-management | 35 | Replace loose equality with strict equality in Patient Management Repo |
| 62 | [O3-5645](https://openmrs.atlassian.net/browse/O3-5645) | Improvement | feature | core | 4 | Prevent open redirect via unvalidated returnToUrl |
| 63 | [O3-5650](https://openmrs.atlassian.net/browse/O3-5650) | Bug | bug | dispensing-app | 5 | Dispensing: Support limiting prescriptions shown to locations under session's visit location |
| 64 | [O3-5665](https://openmrs.atlassian.net/browse/O3-5665) | Bug | bug, has-acceptance-criteria | patient-management | 7 | Vitals form button has broken template literal and missing import |
| 65 | [O3-5666](https://openmrs.atlassian.net/browse/O3-5666) | Bug | bug, has-acceptance-criteria | patient-management | 3 | "Call" action crashes the page when the API request fails |
| 66 | [O3-5677](https://openmrs.atlassian.net/browse/O3-5677) | Task | feature, vague | patient-chart | 5 | Frontend print button for visit summary in O3 patient chart |
| 67 | [O3-5679](https://openmrs.atlassian.net/browse/O3-5679) | Bug | bug | patient-management | 1 | Patient notes appear duplicated in the Previous visit tab |
| 68 | [O3-5680](https://openmrs.atlassian.net/browse/O3-5680) | Improvement | feature, has-acceptance-criteria | patient-management | 6 | Make calling status and drug order type filters configurable |
| 69 | [O3-5681](https://openmrs.atlassian.net/browse/O3-5681) | Improvement | feature, has-acceptance-criteria | patient-management | 7 | Queue-screen widget polls regardless of user activity |
| 70 | [O3-5682](https://openmrs.atlassian.net/browse/O3-5682) | Bug | bug | patient-management | 1 | Call/Serve action flow is broken: queue-screen stays blank |
| 71 | [O3-5690](https://openmrs.atlassian.net/browse/O3-5690) | Improvement | feature | dispensing-app | 2 | Dispensing app:  Add extension slow in medication dispense overflow menu to add additional actions |
| 72 | [O3-5691](https://openmrs.atlassian.net/browse/O3-5691) | Task | feature, has-acceptance-criteria | patient-chart | 1 | Persist medication renewals with action=RENEW (not NEW) |
| 73 | [O3-5693](https://openmrs.atlassian.net/browse/O3-5693) | Story | feature | patient-management | 3 | Queues table over-fetches queue entry data on every load |
| 74 | [O3-5705](https://openmrs.atlassian.net/browse/O3-5705) | Improvement | feature, vague | billing-app | 2 | Receipt shows discount as outstanding balance on fully paid bills |
| 75 | [O3-5706](https://openmrs.atlassian.net/browse/O3-5706) | Improvement | feature, vague | billing-app | 1 | "Paying" option is unselectable when patient has a recent prior visit - should be selectable |
| 76 | [O3-5707](https://openmrs.atlassian.net/browse/O3-5707) | Bug | bug | patient-chart | 1 | Workspace group launch state updated even on failed launch |
| 77 | [O3-5708](https://openmrs.atlassian.net/browse/O3-5708) | Improvement | feature | billing-app | 3 | Review discounts modal closes after first action even when multiple discounts are pending |
| 78 | [O3-5709](https://openmrs.atlassian.net/browse/O3-5709) | Improvement | feature | patient-chart | 1 | Change Conditions icon to distinguish it from Task list icon |
| 79 | [O3-5714](https://openmrs.atlassian.net/browse/O3-5714) | Bug | cross-repo, bug | billing-app, patient-management | 11 | Patient search results unmount and remount on every keystroke, causing multi-second UI stalls and heap growth |
| 80 | [O3-5716](https://openmrs.atlassian.net/browse/O3-5716) | Task | feature | patient-management | 4 | Add Ability to Delete/Void Beds from Bed Management UI |
| 81 | [O3-5727](https://openmrs.atlassian.net/browse/O3-5727) | New Feature | feature | patient-management | 3 | Create useAppointmentsByDate SWR hook for per-date appointment fetching |
| 82 | [O3-5728](https://openmrs.atlassian.net/browse/O3-5728) | New Feature | feature | patient-management | 1 |  Extract hardcoded period string into named variable in orchestrator |
| 83 | [O3-5729](https://openmrs.atlassian.net/browse/O3-5729) | New Feature | feature, vague | patient-management | 3 | Build WeeklyCalendarView with CSS Grid time-slot layout |
| 84 | [O3-5730](https://openmrs.atlassian.net/browse/O3-5730) | Bug | bug | patient-management | 2 | Appointments App: Action button should change from "Check In" to "Check Out" after patient is checked in |
| 85 | [O3-5731](https://openmrs.atlassian.net/browse/O3-5731) | Bug | bug | patient-management | 1 | Appointment type duplicated in "Upcoming appointments" when checking in a patient via the Appointments App |
| 86 | [O3-5737](https://openmrs.atlassian.net/browse/O3-5737) | Improvement | feature, vague | patient-management | 1 | Appointments: Download button is oversized with more padding |
| 87 | [O3-5738](https://openmrs.atlassian.net/browse/O3-5738) | Bug | bug | patient-chart | 1 | "Close workspace(s)" confirmation modal appears even after the form has been saved |
| 88 | [O3-5739](https://openmrs.atlassian.net/browse/O3-5739) | Bug | bug | patient-chart | 3 | Sticky note: HTML entity codes (&lt;, &gt;) shown instead of < and > after saving |
| 89 | [O3-5742](https://openmrs.atlassian.net/browse/O3-5742) | New Feature | feature, vague | patient-management | 1 | Build DailyCalendarView with compact appointment card list |
| 90 | [O3-5743](https://openmrs.atlassian.net/browse/O3-5743) | Enhancement | feature | billing-app | 3 | UI doesn't make it clear bill must be finalized before payment |
| 91 | [O3-5753](https://openmrs.atlassian.net/browse/O3-5753) | Enhancement | feature | patient-chart | 2 | Defer drug search API calls until minimum character threshold is reached |
| 92 | [O3-5759](https://openmrs.atlassian.net/browse/O3-5759) | Improvement | feature | patient-management | 3 | Color queue wait time by configurable thresholds |
| 93 | [O3-5760](https://openmrs.atlassian.net/browse/O3-5760) | Improvement | feature | patient-management | 22 | Rework Service Queues dashboard to match design |
| 94 | [O3-5761](https://openmrs.atlassian.net/browse/O3-5761) | Improvement | feature | patient-management | 6 | List checked-in patients before search when adding to queue |
| 95 | [O3-5763](https://openmrs.atlassian.net/browse/O3-5763) | Improvement | cross-repo, feature | patient-chart, patient-management | 38 | Unify the Current visit and Previous visit views |
| 96 | [O3-5765](https://openmrs.atlassian.net/browse/O3-5765) | Story | feature | patient-management | 5 | Replace the "Clear queue entries" button with a scheduled clear |
| 97 | [O3-5767](https://openmrs.atlassian.net/browse/O3-5767) | Task | feature, vague | core | 1 | Redirect to Location header URL when session endpoint returns a redirect location |
| 98 | [O3-5769](https://openmrs.atlassian.net/browse/O3-5769) | Improvement | feature | patient-management | 6 | Combine the "Move" and "Transition" row actions into one |
| 99 | [O3-5770](https://openmrs.atlassian.net/browse/O3-5770) | Story | feature | patient-management | 21 | Build a Clinic Administrator screen |
| 100 | [O3-5798](https://openmrs.atlassian.net/browse/O3-5798) | Task | feature, has-acceptance-criteria | patient-chart | 3 | Add the current past visit context to the patient header so users can easily identify the visit they are currently working in. |
| 101 | [O3-5801](https://openmrs.atlassian.net/browse/O3-5801) | Task | feature, vague | patient-chart | 1 | Location obs should display location name not the location id |
| 102 | [O3-5802](https://openmrs.atlassian.net/browse/O3-5802) | Enhancement | feature | patient-management | 2 | Ward app - add extension slot for displaying visit attributes |
| 103 | [O3-5815](https://openmrs.atlassian.net/browse/O3-5815) | New Feature | feature | patient-chart | 2 | Show ICD-11 codes next to diagnoses in the diagnosis picker |
| 104 | [O3-5816](https://openmrs.atlassian.net/browse/O3-5816) | Bug | bug | core | 1 | Login crashes with uncaught TypeError when no Login Locations are configured, user stuck on location picker |
| 105 | [O3-5817](https://openmrs.atlassian.net/browse/O3-5817) | New Feature | feature, has-acceptance-criteria | patient-chart | 1 | Add a schema-configurable searchable dropdown backed by a live REST endpoint |
| 106 | [O3-5821](https://openmrs.atlassian.net/browse/O3-5821) | Bug | bug | patient-management | 1 | Cosmetic bugs on Ward app |
| 107 | [O3-5822](https://openmrs.atlassian.net/browse/O3-5822) | Bug | bug | patient-chart | 3 | Visit-level diagnosis rollups show duplicate tags when the same diagnosis is recorded in multiple encounters |
| 108 | [O3-5823](https://openmrs.atlassian.net/browse/O3-5823) | Enhancement | cross-repo, feature | core, patient-chart | 14 | Capture and surface diagnosis certainty (confirmed / provisional) |
| 109 | [O3-5825](https://openmrs.atlassian.net/browse/O3-5825) | Bug | bug | patient-chart | 1 | Patient banner does not rearrange its layout when resized to 520px or narrower |
| 110 | [O3-5833](https://openmrs.atlassian.net/browse/O3-5833) | Improvement | feature | patient-management | 1 | Use i18next pluralization for queue wait-time durations instead of "(s)" |
| 111 | [O3-5836](https://openmrs.atlassian.net/browse/O3-5836) | Bug | cross-repo, bug | patient-chart, patient-management | 2 | Starting a visit from a patient search result throws because the patient-chart workspace group is launched without group props |
| 112 | [O3-5838](https://openmrs.atlassian.net/browse/O3-5838) | Task | feature | core | 5 | Implement the Two-Factor Verification Page (TOTP) |
| 113 | [O3-5839](https://openmrs.atlassian.net/browse/O3-5839) | Enhancement | feature | patient-chart | 2 | Configurable/differentiated patient banner for deceased patients + always-visible header |
| 114 | [O3-5841](https://openmrs.atlassian.net/browse/O3-5841) | Bug | bug | patient-chart | 4 |  Vitals & Biometrics tables sort in the opposite direction to the sort arrow |
| 115 | [O3-5844](https://openmrs.atlassian.net/browse/O3-5844) | Bug | bug | patient-chart | 1 | Birth-day vaccinations rejected by the system |
| 116 | [O3-5845](https://openmrs.atlassian.net/browse/O3-5845) | Bug | bug | patient-chart | 1 | Task due date shifts one day earlier every time an existing task is edited and saved  |
| 117 | [O3-5846](https://openmrs.atlassian.net/browse/O3-5846) | Bug | bug | patient-management | 1 | Ward app - "admit elsewhere" should result in a new admission request instead of transfer request |
| 118 | [O3-5849](https://openmrs.atlassian.net/browse/O3-5849) | Improvement | feature, has-acceptance-criteria | core | 3 | Improve the Workspace2 unsaved-changes confirmation modal |
| 119 | [O3-5850](https://openmrs.atlassian.net/browse/O3-5850) | New Feature | feature, has-acceptance-criteria | patient-chart | 6 | Support concept reference ranges in the Angular form engine |
| 120 | [O3-5851](https://openmrs.atlassian.net/browse/O3-5851) | Improvement | feature | patient-chart | 7 | Make the visit summary Timeline expandable and retire the Encounters tab |
| 121 | [O3-5858](https://openmrs.atlassian.net/browse/O3-5858) | Task | feature, has-acceptance-criteria | patient-chart | 1 | Add @carbon/react to peerDependencies in openmrs-esm-patient-chart |
| 122 | [O3-5872](https://openmrs.atlassian.net/browse/O3-5872) | Task | feature, has-acceptance-criteria | core | 4 | Emit precompressed (gzip -9 and brotli) assets from openmrs build and serve them statically |
| 123 | [O3-5874](https://openmrs.atlassian.net/browse/O3-5874) | Bug | bug | core | 9 | Change language modal and user menu language item crash with RangeError when allowed locales include a region |
| 124 | [O3-5875](https://openmrs.atlassian.net/browse/O3-5875) | Bug | bug | patient-chart | 6 | Prevent render crashes on incomplete FHIR demographics/coding data across medications, orders, vitals, and tests |
| 125 | [O3-5877](https://openmrs.atlassian.net/browse/O3-5877) | Task | feature | patient-management | 6 | Patient Search should be clear about too few characters |
| 126 | [O3-5889](https://openmrs.atlassian.net/browse/O3-5889) | Enhancement | feature, has-acceptance-criteria | patient-chart | 2 | Support fullWidth configuration for obs-by-encounter-widget |
| 127 | [O3-5908](https://openmrs.atlassian.net/browse/O3-5908) | Bug | bug | patient-chart | 4 | Pinned drug orders skip the "Already prescribed" check, and the order form disables Save without saying why |
| 128 | [O3-5910](https://openmrs.atlassian.net/browse/O3-5910) | Bug | bug, has-acceptance-criteria | patient-management | 1 | Patient registration: Preserve local-language names when editing a patient |
| 129 | [O3-5911](https://openmrs.atlassian.net/browse/O3-5911) | Bug | bug, has-acceptance-criteria | patient-management | 1 | Patient registration: Validate the encounter type used by registration observations |
| 130 | [O3-5912](https://openmrs.atlassian.net/browse/O3-5912) | Bug | bug, has-acceptance-criteria | patient-management | 2 | Regression: Address hierarchy does not clear dependent fields |
| 131 | [O3-5913](https://openmrs.atlassian.net/browse/O3-5913) | Bug | bug, has-acceptance-criteria | patient-management | 1 | Patient registration: Wait for deletions before reporting a successful save |
| 132 | [O3-5914](https://openmrs.atlassian.net/browse/O3-5914) | Bug | bug, has-acceptance-criteria | patient-management | 2 | Preserve existing location attributes while searching |
| 133 | [O3-5916](https://openmrs.atlassian.net/browse/O3-5916) | Bug | bug, has-acceptance-criteria | patient-management | 2 | Make automatically generated patient identifiers retry-safe |
| 134 | [O3-5917](https://openmrs.atlassian.net/browse/O3-5917) | Bug | bug, has-acceptance-criteria | patient-management | 2 | Keep newly added relationship rows correctly associated |
| 135 | [O3-5918](https://openmrs.atlassian.net/browse/O3-5918) | Bug | bug, has-acceptance-criteria | patient-management | 1 | Allow birth and death on the same calendar day |
| 136 | [O3-5919](https://openmrs.atlassian.net/browse/O3-5919) | Bug | bug, has-acceptance-criteria | patient-management | 2 | Clear stale death metadata when marking a patient alive |
| 137 | [O3-5924](https://openmrs.atlassian.net/browse/O3-5924) | Task | cross-repo, feature | dispensing-app, patient-management | 5 | Land the React 18-safe migration prerequisites |
| 138 | [O3-5934](https://openmrs.atlassian.net/browse/O3-5934) | Enhancement | feature | patient-chart | 2 |  Expose person attributes on the form-entry patient object |
| 139 | [O3-5940](https://openmrs.atlassian.net/browse/O3-5940) | Bug | bug | patient-management | 7 | Don't offer queues a patient is already in |
| 140 | [O3-5953](https://openmrs.atlassian.net/browse/O3-5953) | Bug | bug | patient-chart | 3 | Renewing a medication files the renewal encounter in the original order's closed visit |
| 141 | [O3-5957](https://openmrs.atlassian.net/browse/O3-5957) | Bug | bug | patient-chart | 1 | MUAC color code not set for patients aged exactly 5, 10, or 18 |
| 142 | [O3-5958](https://openmrs.atlassian.net/browse/O3-5958) | Enhancement | feature | patient-management | 1 | Queue location is blank when the login location is not queue-tagged |
| 143 | [O3-5964](https://openmrs.atlassian.net/browse/O3-5964) | Task | feature, has-acceptance-criteria | patient-chart | 1 | Remove unreferenced SCSS files and the dead AllergyFormTab component from the patient chart |
| 144 | [O3-5967](https://openmrs.atlassian.net/browse/O3-5967) | Improvement | feature | patient-management | 1 | Show queue number instead of status in the default queue table |
| 145 | [O3-5969](https://openmrs.atlassian.net/browse/O3-5969) | Bug | bug, has-acceptance-criteria | patient-chart | 4 | Improve keyboard access and edit wording in the conditions form |
| 146 | [O3-5976](https://openmrs.atlassian.net/browse/O3-5976) | Bug | bug, has-acceptance-criteria | patient-chart | 1 | Form engine never loads Angular locale data: the locale import requests .mjs files that do not exist |
| 147 | [O3-5981](https://openmrs.atlassian.net/browse/O3-5981) | Bug | bug, has-acceptance-criteria | core | 1 | Unhandled rejections pass a raw Error into the toast description, which React cannot render |
| 148 | [O3-5983](https://openmrs.atlassian.net/browse/O3-5983) | Bug | bug | patient-management | 2 | Queues Actions for "In Service/Attending" patients |
| 149 | [O3-5984](https://openmrs.atlassian.net/browse/O3-5984) | Bug | bug | patient-management | 2 | Queues: In Service vs Attending language |
| 150 | [O3-5986](https://openmrs.atlassian.net/browse/O3-5986) | Bug | cross-repo, bug, has-acceptance-criteria | core, patient-chart | 18 | Saved image attachments are missing when editing a visit note |
| 151 | [O3-5987](https://openmrs.atlassian.net/browse/O3-5987) | Bug | bug | patient-chart | 6 | Attachment upload dialog ignores the caller's allowed extensions and reports "Upload complete" before anything is uploaded |
| 152 | [O3-5988](https://openmrs.atlassian.net/browse/O3-5988) | Bug | bug | patient-chart | 4 | Attachment upload dialog shows a file size limit that is unrelated to the backend's attachments.maxUploadFileSize |
| 153 | [O3-5989](https://openmrs.atlassian.net/browse/O3-5989) | Bug | bug | patient-chart | 1 | Visit note form leaves a saved note behind when an image upload is rejected, and saving again creates a duplicate |
| 154 | [O3-5990](https://openmrs.atlassian.net/browse/O3-5990) | Story | feature | patient-chart | 2 | Let users remove an image already saved on a visit note without deleting the note |
| 155 | [O3-5991](https://openmrs.atlassian.net/browse/O3-5991) | Bug | bug | patient-management | 1 | Registration - allow post-registration redirects to non-SPA URLs |
| 156 | [O3-5998](https://openmrs.atlassian.net/browse/O3-5998) | Bug | bug | patient-chart | 4 | Starting or selecting a visit from the visit prompt doesn't continue to the workspace that asked for it |
| 157 | [O3-6000](https://openmrs.atlassian.net/browse/O3-6000) | Task | feature | core | 13 | Allow extensions and workspaces to access their `meta` data |
| 158 | [O3-6004](https://openmrs.atlassian.net/browse/O3-6004) | Bug | bug | patient-chart | 2 | Retrying a failed lab result save creates duplicate results on the order |
| 159 | [O3-6007](https://openmrs.atlassian.net/browse/O3-6007) | Task | feature, vague | core | 13 | Create a way to render workspace as a component |
| 160 | [O3-6012](https://openmrs.atlassian.net/browse/O3-6012) | Task | feature | patient-management | 7 | (BREAKING) Remove the patient-search-button extension and v1 patient-search-workspace |
| 161 | [O3-6019](https://openmrs.atlassian.net/browse/O3-6019) | Bug | bug, has-acceptance-criteria | patient-chart | 2 | Prevent loss of unsaved medication dosage entries when switching dosage modes |
| 162 | [O3-6020](https://openmrs.atlassian.net/browse/O3-6020) | Bug | cross-repo, bug | patient-chart, patient-management | 7 | Visit Notes workspace should accept a Encounter object for editing |
| 163 | [O3-6025](https://openmrs.atlassian.net/browse/O3-6025) | Bug | bug, has-acceptance-criteria | patient-chart | 1 | Every form downloads WHO growth reference data even when it doesn't use it |
| 164 | [O3-6026](https://openmrs.atlassian.net/browse/O3-6026) | Bug | bug, has-acceptance-criteria | patient-chart | 2 | Vitals and biometrics chart view shows a loading spinner and causes layout jump on first switch |
| 165 | [O3-6028](https://openmrs.atlassian.net/browse/O3-6028) | Bug | bug, has-acceptance-criteria | core | 3 | Login location picker ignores the configured number of locations to load |
| 166 | [O3-6029](https://openmrs.atlassian.net/browse/O3-6029) | Task | feature, has-acceptance-criteria | core | 20 | Remove the legacy workspace (v1) system from the framework |
| 167 | [O3-6040](https://openmrs.atlassian.net/browse/O3-6040) | New Feature | feature | patient-management | 4 | Add Support date person attributes in the registration form |
| 168 | [O3-6043](https://openmrs.atlassian.net/browse/O3-6043) | New Feature | feature, vague | patient-chart | 2 | Remove showPrintVisitSummaryButton feature flag |
| 169 | [O3-6044](https://openmrs.atlassian.net/browse/O3-6044) | Bug | bug | patient-chart | 2 | Forms that calculate growth z-scores can't be saved in the Angular form engine |
| 170 | [O3-6047](https://openmrs.atlassian.net/browse/O3-6047) | Task | feature | patient-chart | 7 | Share one Back button across patient chart workspaces |
| 171 | [O3-6093](https://openmrs.atlassian.net/browse/O3-6093) | Bug | bug, has-acceptance-criteria | core | 1 | `extractVariableNames()` drops variables and returns nested arrays for expressions inside arrow functions |
| 172 | [O3-6096](https://openmrs.atlassian.net/browse/O3-6096) | Bug | bug | patient-management | 2 | Creating a new list from a patient's chart ("Add to list") doesn't take the user back to add the patient |
| 173 | [O3-6097](https://openmrs.atlassian.net/browse/O3-6097) | Bug | bug | patient-chart | 1 | "Free text dosage" toggle labels are inverted in the drug order form |
| 174 | [O3-6098](https://openmrs.atlassian.net/browse/O3-6098) | Bug | bug, has-acceptance-criteria | patient-management | 4 | Service Queues always shows “Scheduled for today” and “On time” |
| 175 | [O3-6100](https://openmrs.atlassian.net/browse/O3-6100) | Bug | bug | patient-chart | 1 | Double-clicking Save and close creates duplicate vitals encounters |
| 176 | [O3-6110](https://openmrs.atlassian.net/browse/O3-6110) | Bug | bug | patient-chart | 28 | Patient-chart workspaces don't show which patient you're working on when they fill the screen (tablet) |
| 177 | [O3-6112](https://openmrs.atlassian.net/browse/O3-6112) | Bug | bug | billing-app | 1 | Billing "Create bill / Add bill items" workspace doesn't show which patient is being billed |
| 178 | [O3-6127](https://openmrs.atlassian.net/browse/O3-6127) | Task | feature, vague | dispensing-app | 6 | Dispensing: Convert "Print labels" button to extension |
| 179 | [O3-6135](https://openmrs.atlassian.net/browse/O3-6135) | Bug | bug | core | 2 | Extension config keys are reported as unknown before their module has loaded |
