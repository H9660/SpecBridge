# UAT SPEC-64: Show allergy alerts on the Dental Chart tab

> **Needs clarification: no UAT test cases yet**
>
> No UAT test cases yet: the ticket relies on a screen that is not in the app (Dental Chart tab).

Draft written by SpecBridge from the code at the frozen version, for [SPEC-64](https://rooks101.atlassian.net/browse/SPEC-64). Please review it before use.

## Why there are no test cases yet

the ticket talks about a screen that does not exist in the code: Dental Chart tab

## What SpecBridge understood

**Intent:** Display a red allergy banner listing allergen names at the top of the Dental Chart tab when a patient has recorded allergies.

- **AC1**: When opening the Dental Chart tab for a patient with at least one recorded allergy, a red allergy banner appears at the top of the tab.
- **AC2**: The allergy banner displays the names of the patient's allergens.
- **AC3**: No allergy banner is shown if the patient has no recorded allergies.

### Screens

| Screen | New or existing | Changed or used | Where in the code |
|---|---|---|---|
| Dental Chart tab | existing | changed | - |
| allergy banner | new | changed | - |

### Risks

- unknown-screen: not found in the code: Dental Chart tab

## Questions for the PM

1. "Dental Chart tab" does not exist in the code: is it a new screen to be built, and where should it appear?

## Next step

Say whether the screen is new (and where it goes), or name the existing screen that is meant.

## Run details

<details><summary>Show the run details</summary>

**Run:** `20261109-152155-13b864` · mode dry-run

**Started:** 2026-11-09 09:51 UTC · about 0.6 min to this page

**Cost:** $0.008 (estimated from list prices) · 3,793 tokens

**Rounds:** 0 · **Worker runs:** 0

**Models:** gemini-3.6-flash

**Prompts:** understand-v3 (2026-11-09), render-v1

**Limits:** $0.25 per ticket, 2 rounds, 8 tool calls per worker

**Code version (frozen):** billing-app @ 6a0f8098, core @ cf088d52, dispensing-app @ 7f604ab7, patient-chart @ 8ede2e3a, patient-management @ 37d3c1bc

</details>
