# UAT SPEC-66: Allergies widget: list the most severe allergies first

> **Ready for PM review**
>
> Every acceptance criterion passed the review.

Draft written by SpecBridge from the code at the frozen version, for [SPEC-66](https://rooks101.atlassian.net/browse/SPEC-66). Please review it before use. The Actual result and Pass/Fail columns are for the tester.

## 1. Summary

**What the ticket asks:** Sort allergies in the patient chart by severity (severe first, then moderate, then mild) and then by recency.

**Test scope:** Full: new or changed behaviour on screen.

### Affected screens

| Screen | New or existing | Changed or used | Where in the code |
|---|---|---|---|
| Allergies widget | existing | changed | registered: allergies-list |
| patient summary | existing | used | registered: allergies-summary-dashboard |
| full Allergies page | existing | used | registered: allergies-details-widget |

## 2. Before you start

- Logged in as a clinician

## 3. Test cases by acceptance criterion

### AC1: Allergies are listed by severity: severe first, then moderate, then mild.

**[OK]**

*Ticket: “Allergies are listed by severity: severe first, then moderate, then mild.”*

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-01** · happy path<br>Verify allergies are sorted by severity (severe first, then moderate, then mild) in the Allergies widget<br>*Code: EV-05, EV-02* | • A patient chart exists with recorded allergies across severe, moderate, and mild severities (\<patient with mixed severity allergies\>) | 1. Navigate to the patient chart for \<patient with mixed severity allergies\>.<br>2. Locate the Allergies widget on the page.<br>3. Observe the sequence of allergy tags displayed under the Allergies section. | Allergies are displayed in order of severity: severe allergies appear first, followed by moderate allergies, and mild allergies appear last. |   |   |
| **TC-02** · edge case<br>Verify allergies with moderate and mild severities sort moderate before mild when severe is absent<br>*Code: EV-05, EV-02* | • A patient chart exists with only moderate and mild allergies recorded (\<patient with moderate and mild allergies\>) | 1. Navigate to the patient chart for \<patient with moderate and mild allergies\>.<br>2. Locate the Allergies widget.<br>3. Observe the ordering of the displayed allergy tags. | Moderate allergies are listed before mild allergies. |   |   |

### AC2: Allergies with the same severity are listed most recent first.

**[OK]**

*Ticket: “Allergies with the same severity are listed most recent first.”*

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-03** · happy path<br>Verify allergies with the same severity are sorted most recent first<br>*Code: EV-05, EV-02, EV-04* | • A patient chart exists with multiple severe allergies recorded at different times (\<patient with multiple severe allergies\>) | 1. Navigate to the patient chart for \<patient with multiple severe allergies\>.<br>2. Locate the Allergies widget.<br>3. Observe the relative order of the severe allergies. | The most recently updated severe allergy is displayed before older severe allergies. |   |   |
| **TC-04** · edge case<br>Verify recency ordering within moderate severity group<br>*Code: EV-05, EV-02, EV-04* | • A patient chart exists with multiple moderate allergies updated at different dates (\<patient with multiple moderate allergies\>) | 1. Navigate to the patient chart for \<patient with multiple moderate allergies\>.<br>2. Locate the Allergies widget.<br>3. Observe the relative order of the moderate allergies. | The moderate allergy with the most recent lastUpdated date is listed first among the moderate allergies. |   |   |

### AC3: The ordering of allergies is consistent across both the patient summary and the full Allergies page.

**[OK]**

*Ticket: “The order is the same on the patient summary and on the full Allergies page.”*

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-05** · happy path<br>Verify ordering consistency between patient summary and full Allergies page<br>*Code: EV-03, EV-02, EV-01, EV-04* | • A patient chart exists with multiple allergies of varying severities and update dates (\<patient with diverse allergies\>) | 1. Navigate to the patient summary page for \<patient with diverse allergies\>.<br>2. Observe the list order of allergies in the patient summary view.<br>3. Navigate to the full Allergies page (allergies-details-widget).<br>4. Compare the list order of allergies on the full Allergies page table with the order on the patient summary. | The ordering of allergies (severe first, then moderate, then mild; ordered by recency within each severity) is identical on both the patient summary and the full Allergies page. |   |   |
| **TC-06** · empty-state<br>Verify empty state consistency across patient summary and full Allergies page<br>*Code: EV-03, EV-02, EV-01* | • A patient chart exists with no recorded allergies (\<patient with no allergies\>) | 1. Navigate to the patient summary for \<patient with no allergies\>.<br>2. Observe the Allergies section on the summary page.<br>3. Navigate to the full Allergies page.<br>4. Observe the display on the full Allergies page. | Both the summary view and full Allergies page present consistent empty/unknown state messages ('Unknown' on tile/list and empty state with 'allergy intolerances' display text on full page). |   |   |

## 5. Open questions for the PM

1. Should severity sorting logic be centralized inside the \`useAllergies\` hook (\`allergy-intolerance.resource.ts\`) so that all widgets (tile, list, detailed summary) share the exact same severity-first recency-second sorting order?

## 6. Notes from the code

<details><summary>Show the notes</summary>

What the writers noticed in the code:

- Code Implementation Discrepancy: \`allergies-list.extension.tsx\` (E3) applies \`severityOrder\` sorting to \`sortedAllergies\`, but \`allergies-tile.extension.tsx\` (E2) and \`allergies-detailed-summary.component.tsx\` (E4) directly render \`allergies\` from \`useAllergies\` (E5) without sorting by \`severityOrder\`. Consequently, the full Allergies page and summary tile currently display allergies ordered solely by recency (\`lastUpdated\`), failing AC3 consistency across screens.

</details>

## 7. Review report

**Criteria ok:** 3/3 · **Cases fully grounded:** 100% · **Review rounds:** 1

| Criterion | Verdict | Problems | Checked by |
|---|---|---|---|
| AC1 | **[OK]** | 0 | AI and code checks |
| AC2 | **[OK]** | 0 | AI and code checks |
| AC3 | **[OK]** | 1 | AI and code checks |

## 8. Code the test cases cite

| ID | File | Lines | Link |
|---|---|---|---|
| **EV-01** | `patient-chart/packages/esm-patient-allergies-app/src/allergies/allergies-detailed-summary.component.tsx` | 1-130 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-allergies-app/src/allergies/allergies-detailed-summary.component.tsx#L1-L130) |
| **EV-02** | `patient-chart/packages/esm-patient-allergies-app/src/allergies/allergies-list.extension.tsx` | 1-60 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-allergies-app/src/allergies/allergies-list.extension.tsx#L1-L60) |
| **EV-03** | `patient-chart/packages/esm-patient-allergies-app/src/allergies/allergies-tile.extension.tsx` | 1-38 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-allergies-app/src/allergies/allergies-tile.extension.tsx#L1-L38) |
| **EV-04** | `patient-chart/packages/esm-patient-allergies-app/src/allergies/allergy-intolerance.resource.ts` | 1-100 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-allergies-app/src/allergies/allergy-intolerance.resource.ts#L1-L100) |
| **EV-05** | `patient-chart/packages/esm-patient-allergies-app/src/utils.ts` | 1-5 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-allergies-app/src/utils.ts#L1-L5) |

## 9. Run details

<details><summary>Show the run details</summary>

**Run:** `20261111-212317-4d465c` · mode dry-run

**Started:** 2026-11-11 15:53 UTC · about 13.7 min to this page

**Cost:** $0.073 (estimated from list prices) · 57,188 tokens

**Rounds:** 1 · **Worker runs:** 1

**Models:** gemini-3.5-flash-lite, gemini-3.6-flash

**Prompts:** orchestrator-v1 (2026-11-10), reviewer-v3 (2026-11-11), understand-v3 (2026-11-09), worker\_agent-v1 (2026-11-11), write\_cases-v1 (2026-11-11), render-v1

**Limits:** $0.25 per ticket, 2 rounds, 8 tool calls per worker

**Code version (frozen):** billing-app @ 6a0f8098, core @ cf088d52, dispensing-app @ 7f604ab7, patient-chart @ 8ede2e3a, patient-management @ 37d3c1bc

</details>
