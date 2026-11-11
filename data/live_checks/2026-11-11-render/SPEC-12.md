# UAT SPEC-12: Improve keyboard access and edit wording in the conditions form

> **Needs attention**
>
> AC1, AC2, AC3, AC5, AC6 still weak (after the retry round)

Draft written by SpecBridge from the code at the frozen version, for **SPEC-12**. Please review it before use. The Actual result and Pass/Fail columns are for the tester.

## 1. Summary

**What the ticket asks:** Enable keyboard navigation and selection for condition search results and update the workspace title dynamically to show 'Record condition' or 'Edit condition'.

**Test scope:** Full: new or changed behaviour on screen.

### Affected screens

| Screen | New or existing | Changed or used | Where in the code |
|---|---|---|---|
| conditions form workspace | existing | changed | registered: conditions-form-workspace |

## 2. Before you start

- User is logged in to the application
- A patient chart is open

## 3. Test cases by acceptance criterion

### AC1: Condition search results support keyboard navigation and selection, with a visible focus indicator.

**[NEEDS ATTENTION]**

*Ticket: “Search results support keyboard navigation and selection, with a visible focus indicator.”*

> **May be ambiguous, please check**
>
> The reviewer found problems below.

- TC-01 (grounding): Cites conditions-form.workspace.tsx, which is a parent component that only renders ConditionsWidget, rather than the component where the search box and keyboard navigation logic are implemented.
- TC-02 (grounding): Cites conditions-form.workspace.tsx, which is a parent component that only renders ConditionsWidget, rather than the component where the search box and keyboard navigation logic are implemented.
- TC-14 (grounding): Cites conditions-form.workspace.tsx, which is a parent component that only renders ConditionsWidget, rather than the component where the search box and keyboard navigation logic are implemented.

**What is missing:** Find and cite the code in conditions-widget.component.tsx or the search component where the search input, search results list, and keyboard event handlers are implemented.

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-01** · happy path<br>Navigate condition search results using arrow keys and select with Enter<br>*Code: EV-01* | • The conditions form workspace is open with title 'Record condition' | 1. In the conditions form workspace, focus the search input inside the conditions widget (E1 line 95)<br>2. Type a search query to load condition search results<br>3. Press the Down Arrow key to navigate through the displayed search results list<br>4. Verify that each highlighted search result shows a visible focus indicator<br>5. Press the Enter key on a highlighted condition result | Each search result displays a visible focus indicator when navigated to with arrow keys, and pressing Enter selects the highlighted condition. |   |   |
| **TC-02** · edge case<br>Navigate condition search results upward using Up Arrow key<br>*Code: EV-01* | • The conditions form workspace is open | 1. In the conditions form workspace, focus the search input in the conditions widget (E1 line 95)<br>2. Type a search query to display search results<br>3. Press the Down Arrow key twice to move focus down the search results<br>4. Press the Up Arrow key to navigate back up through the search results | The visible focus indicator shifts upward to previous search results following the Up Arrow keypresses. |   |   |

Also tested in end-to-end flow TC-14.

### AC2: Focus returns to the search input after selecting a condition, and the selected condition's name remains displayed in the input.

**[NEEDS ATTENTION]**

*Ticket: “Focus returns to the search input after selection, and the selected condition’s name remains in the input.”*

> **May be ambiguous, please check**
>
> The reviewer found problems below.

- TC-03 (grounding): Cited code EV-01 is the parent workspace wrapper component that only renders ConditionsWidget and does not contain the search input or focus management logic for condition selection.
- TC-04 (grounding): Cited code EV-01 is the parent workspace wrapper component that only renders ConditionsWidget and does not contain the search input or focus management logic for replacing a condition.
- TC-14 (grounding): Cited code EV-01 is the parent workspace wrapper component that only renders ConditionsWidget and does not contain the search input or focus return logic.

**What is missing:** Find and cite the component handling the search input, dropdown search results, and selection/focus logic (such as ConditionsWidget or its concept search input subcomponent) rather than the parent workspace wrapper.

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-03** · happy path<br>Focus returns to search input and displays selected condition name after keyboard selection<br>*Code: EV-01* | • The conditions form workspace is open | 1. In the conditions form workspace, click or focus the search input in the conditions widget (E1 line 95)<br>2. Type a search query to open the condition search results<br>3. Press the Down Arrow key to focus a condition in the search results and press Enter to select it | Focus returns to the search input immediately upon selection, and the selected condition's name remains displayed in the search input. |   |   |
| **TC-04** · edge case<br>Replace an already selected condition and verify focus returns with updated condition name<br>*Code: EV-01* | • The conditions form workspace is open with a condition already selected in the search input | 1. Focus the search input in the conditions widget (E1 line 95)<br>2. Clear the existing condition name and type a new search query<br>3. Use the Down Arrow key to navigate to a different condition result and press Enter | Focus returns to the search input, and the newly selected condition's name replaces the previous one and remains displayed in the input. |   |   |

Also tested in end-to-end flow TC-14.

### AC3: Pressing Escape returns focus to the search input without selecting any condition result.

**[NEEDS ATTENTION]**

*Ticket: “Escape returns focus to the search input without selecting a result.”*

> **May be ambiguous, please check**
>
> The reviewer found problems below.

- TC-05 (grounding): EV-01 (conditions-form.workspace.tsx) is a parent wrapper component that only renders ConditionsWidget; it does not contain the search input or keyboard navigation event handling.
- TC-06 (grounding): EV-01 (conditions-form.workspace.tsx) is a parent wrapper component and does not contain the search input or Escape key handling.
- TC-14 (grounding): EV-01 (conditions-form.workspace.tsx) is a parent wrapper component and does not show the focus management or Escape/Enter keyboard handlers for the search widget.

**What is missing:** Cite the component where the condition search input and keyboard navigation/Escape key handling are implemented (e.g., ConditionsWidget or search component) rather than the parent workspace wrapper.

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-05** · happy path<br>Pressing Escape while focused on a search result dismisses results and returns focus to search input<br>*Code: EV-01* | • The conditions form workspace is open | 1. In the conditions form workspace, focus the search input in the conditions widget (E1 line 95)<br>2. Type a search query to open the search results<br>3. Press the Down Arrow key to move focus to a condition search result<br>4. Press the Escape key | The search results list is dismissed, no condition is selected, and focus returns directly to the search input. |   |   |
| **TC-06** · edge case<br>Pressing Escape while focused inside search input closes search results dropdown<br>*Code: EV-01* | • The conditions form workspace is open | 1. In the conditions form workspace, focus the search input in the conditions widget (E1 line 95)<br>2. Type a search query so that search results are displayed, keeping keyboard focus inside the search input<br>3. Press the Escape key | The search results list closes without selecting any condition, and focus remains in the search input. |   |   |

Also tested in end-to-end flow TC-14.

### AC4: The workspace displays 'Record condition' when creating a new condition and 'Edit condition' when editing an existing condition.

**[OK]**

*Ticket: “The workspace shows “Record condition” when creating and “Edit condition” when editing.”*

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-07** · happy path<br>Workspace title displays 'Record condition' when creating a new condition<br>*Code: EV-01, EV-02, EV-03, EV-04* | • User is logged into the OpenMRS 3 web app with privileges to access patient charts<br>• A patient chart is opened | 1. In the patient chart, click the 'Record conditions' button to open the conditions form workspace<br>2. Observe the workspace header title at the top of the workspace | The conditions form workspace opens and displays 'Record condition' (or 'Record a Condition' per current English locale) as the workspace title. |   |   |
| **TC-08** · edge case<br>Workspace title displays 'Edit condition' when editing an existing condition<br>*Code: EV-01* | • User is logged into the OpenMRS 3 web app with privileges to edit patient conditions<br>• A patient chart is opened for a patient with at least one existing condition recorded | 1. In the patient conditions section, choose an existing condition to edit and launch the conditions form workspace in editing mode<br>2. Observe the workspace header title at the top of the workspace | The conditions form workspace opens and displays 'Edit condition' as the workspace title. |   |   |

Also tested in end-to-end flow TC-14, TC-15.

### AC5: Mouse selection of search results continues to work as expected.

**[NEEDS ATTENTION]**

*Ticket: “Mouse selection continues to work.”*

> **May be ambiguous, please check**
>
> The reviewer found problems below.

- TC-09 (grounding): TC-09 cites EV-01 (conditions-form.workspace.tsx), which only renders \<ConditionsWidget /\> and does not contain the search input, search results list dropdown, or mouse selection handlers.
- TC-10 (grounding): TC-10 cites EV-01 (conditions-form.workspace.tsx), which does not contain the search results dropdown or the click-outside dismiss logic.
- TC-15 (grounding): TC-15 cites EV-01 (conditions-form.workspace.tsx) for search result mouse selection steps, but EV-01 does not implement the search results dropdown or item click handling.

**What is missing:** Cite the component containing the search input and search results dropdown (such as conditions-widget.component.tsx or the concept search component) where search results rendering and mouse click selection are implemented, rather than conditions-form.workspace.tsx.

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-09** · happy path<br>Select a condition search result by mouse click<br>*Code: EV-01* | • The conditions form workspace is open | 1. In the conditions form workspace, click the search input in the conditions widget (E1 line 95)<br>2. Type a search query to display search results<br>3. Click on a condition in the search results list using the mouse cursor | The clicked condition is selected, the search results dropdown closes, and the condition name is populated in the search input. |   |   |
| **TC-10** · negative<br>Click outside search results dropdown without selecting a condition<br>*Code: EV-01* | • The conditions form workspace is open | 1. In the conditions form workspace, click the search input in the conditions widget (E1 line 95)<br>2. Type a search query to display search results<br>3. Click with the mouse on an empty area of the form outside the search results list | The search results list closes and no condition from the list is selected. |   |   |

Also tested in end-to-end flow TC-15.

### AC6: Keyboard behavior and workspace titles function correctly on both desktop and tablet screen sizes.

**[NEEDS ATTENTION]**

*Ticket: “Keyboard behavior and titles are validated on desktop and tablet.”*

> **May be ambiguous, please check**
>
> The reviewer found problems below.

- TC-13 (grounding): TC-13 cites EV-01 (conditions-form.workspace.tsx), which is the parent workspace component that only renders ConditionsWidget and does not contain the search input field or keyboard navigation logic.

**What is missing:** Cite the component containing the condition search input field and keyboard navigation handlers (such as ConditionsWidget) rather than the parent workspace component, and ensure test cases explicitly validate keyboard behavior on both desktop and tablet screen sizes.

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-11** · happy path<br>Verify workspace title and tablet layout when recording a condition on a tablet screen size<br>*Code: EV-01* | • Browser viewport is set to tablet screen size (triggering useLayoutType tablet) | 1. Navigate to the patient chart and trigger recording a condition to open the conditions form workspace.<br>2. Inspect the workspace header title.<br>3. Observe the action button set containing Cancel and submit buttons at the bottom of the form. | The workspace header displays the title 'Record condition', and the button set is rendered with the tablet styling class. |   |   |
| **TC-12** · negative<br>Verify workspace title displays Edit condition when editing an existing condition on tablet screen size<br>*Code: EV-01* | • Browser viewport is set to tablet screen size<br>• A patient with at least one recorded condition is selected | 1. Open an existing condition to edit, opening the conditions form workspace with formContext set to editing.<br>2. Observe the title rendered at the top of the workspace. | The workspace title dynamically displays 'Edit condition' rather than 'Record condition' on tablet screen size. |   |   |
| **TC-13** · edge case<br>Verify condition search keyboard navigation on tablet screen size<br>*Code: EV-01* | • Browser viewport is set to tablet screen size with a keyboard connected or active<br>• A patient chart is open and the conditions form workspace is open | 1. Within the conditions form workspace, navigate to the condition search input field inside the ConditionsWidget.<br>2. Type a search query for an existing condition.<br>3. Use keyboard navigation keys (ArrowDown, ArrowUp) to move focus through the condition search results.<br>4. Press Enter to select the highlighted condition. | Focus moves sequentially through the condition search results using arrow keys and the selected condition populates the form upon pressing Enter on tablet screen size. |   |   |

Also tested in end-to-end flow TC-15.

## 4. End-to-end flows

| ID | Preconditions | Steps | Expected result | Actual result | Pass/Fail |
|---|---|---|---|---|---|
| **TC-14** · end-to-end flow<br>Keyboard navigation, escape cancelation, and selection in record condition workspace<br>*Covers AC1 → AC2 → AC3 → AC4*<br>*Code: EV-01* | • Logged in as \<user with clinician privileges\><br>• A patient chart is open for \<patient\><br>• The conditions form workspace is opened with formContext set to 'creating' | 1. In the conditions form workspace header, verify the workspace title.<br>2. Focus the condition search input field and type a condition search term (for example 'Hypertension').<br>3. Press the Down Arrow and Up Arrow keys to navigate through the condition search results list.<br>4. With focus on a condition search result item, press the Escape key.<br>5. Observe where focus lands and verify the search input content.<br>6. Press the Down Arrow key to navigate into the condition search results list again and press Enter to select a highlighted condition result.<br>7. Observe the focus location and the text displayed in the condition search input. | The workspace header displays 'Record condition'. Arrow keys move focus across search results with a visible focus indicator on the active item. Pressing Escape returns focus directly to the search input without selecting any condition. Pressing Enter selects the condition, returns focus to the search input, and keeps the selected condition's name displayed in the input. |   |   |
| **TC-15** · end-to-end flow<br>Edit condition workspace title and mouse selection across screen sizes<br>*Covers AC4 → AC5 → AC6*<br>*Code: EV-01* | • Logged in as \<user with clinician privileges\><br>• A patient chart is open for \<patient with an existing recorded condition\><br>• The browser layout is set to tablet screen size, then repeated on desktop screen size<br>• The conditions form workspace is opened for an existing condition with formContext set to 'editing' | 1. In the conditions form workspace header, inspect the title displayed when editing an existing condition.<br>2. Clear the condition search input field and type a search term for a new condition.<br>3. In the condition search results dropdown list, click on a search result using the mouse pointer (or tap on tablet).<br>4. Observe the selected condition name in the input field.<br>5. In the action button set at the bottom of the form, verify layout styling for tablet vs desktop before clicking 'Cancel' or submitting. | The workspace header displays 'Edit condition' instead of 'Record condition'. Mouse clicking (or tapping) a search result successfully selects the condition and updates the input field with the condition name. Workspace title and selection behave consistently across both tablet and desktop screen sizes. |   |   |

## 5. Open questions for the PM

1. Should pressing Escape in the search input also clear the user's typed search text, or only dismiss the search results dropdown while retaining the typed text?
2. The acceptance criterion specifies 'Record condition', but the English translation file en.json translates 'recordCondition' as 'Record a Condition'. Should the title strictly say 'Record condition'?
3. Has a translation key such as 'editCondition' been added to translation dictionaries for 'Edit condition'?
4. Should tablet testing be performed on a physical tablet device with a hardware keyboard, a virtual software keyboard, or responsive emulation in desktop browsers?

## 6. Notes from the code

<details><summary>Show the notes</summary>

What the writers noticed in the code:

- In E1 line 92, Workspace2 title is hardcoded to t('recordCondition', 'Record condition') regardless of formContext; the brief mentions updating workspace title dynamically for edit, which relates to a different criterion.
- In patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-form.workspace.tsx line 92, Workspace2 is currently hardcoded with title={t('recordCondition', 'Record condition')} and does not check isEditing or formContext to switch the title to 'Edit condition'. Testing the edit case against this implementation will fail until the title is made dynamic.
- In conditions-form.workspace.tsx line 92, Workspace2 title is hardcoded to t('recordCondition', 'Record condition') and does not yet switch to 'Edit condition' when isEditing is true.
- In E1 line 92, Workspace2 currently has hardcoded title={t('recordCondition', 'Record condition')}; it must be updated to conditionally display 'Record condition' or 'Edit condition' based on isEditing / formContext.
- The internal markup of the condition search input and dropdown list items is implemented inside ConditionsWidget (conditions-widget.component.tsx), which was referenced in E1 line 95 but not included in the provided evidence.

What the writers could not find:

- The implementation of ConditionsWidget (conditions-widget.component.tsx) was not provided in the evidence, so exact DOM element IDs and CSS class names for search input and dropdown items rely on conditions-form.workspace.tsx context.
- Code evidence showing the exact UI trigger (e.g. action menu or button label) on the conditions list/widget used to open conditions-form-workspace with formContext: 'editing'.
- The code for ConditionsWidget (conditions-widget.component.tsx) was not provided in the evidence, so exact DOM input names, dropdown role attributes, and specific key listeners for condition search results could not be directly verified from code.

</details>

## 7. Review report

**Criteria ok:** 1/6 · **Cases fully grounded:** 100% · **Review rounds:** 1

**Final:** AC1, AC2, AC3, AC5, AC6 still weak (after the retry round)

| Criterion | Verdict | Problems | Checked by |
|---|---|---|---|
| AC1 | **[NEEDS ATTENTION]** | 3 | AI and code checks |
| AC2 | **[NEEDS ATTENTION]** | 3 | AI and code checks |
| AC3 | **[NEEDS ATTENTION]** | 3 | AI and code checks |
| AC4 | **[OK]** | 0 | AI and code checks |
| AC5 | **[NEEDS ATTENTION]** | 3 | AI and code checks |
| AC6 | **[NEEDS ATTENTION]** | 1 | AI and code checks |

## 8. Code the test cases cite

| ID | File | Lines | Link |
|---|---|---|---|
| **EV-01** | `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-form.workspace.tsx` | 1-149 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-conditions-app/src/conditions/conditions-form.workspace.tsx#L1-L149) |
| **EV-02** | `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-overview.test.tsx` | 101-101 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-conditions-app/src/conditions/conditions-overview.test.tsx#L101-L101) |
| **EV-03** | `patient-chart/packages/esm-patient-conditions-app/src/conditions/conditions-overview.test.tsx` | 103-103 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-conditions-app/src/conditions/conditions-overview.test.tsx#L103-L103) |
| **EV-04** | `patient-chart/packages/esm-patient-conditions-app/translations/en.json` | 36-36 | [view at the frozen version](https://github.com/openmrs/openmrs-esm-patient-chart/blob/8ede2e3a641d470abcd31fe496f5714f2b4fc600/packages/esm-patient-conditions-app/translations/en.json#L36-L36) |

## 9. Run details

<details><summary>Show the run details</summary>

**Run:** `live-check-render-spec12` · mode dry-run

**Started:** 2026-11-11 15:35 UTC · about 7.1 min to this page

**Cost:** $0.181 (estimated from list prices) · 33,721 tokens

**Rounds:** 1 · **Worker runs:** 4

**Models:** gemini-3.5-flash-lite, gemini-3.8-flash

**Prompts:** e2e-v1 (2026-11-11), reviewer-v3 (2026-11-11), understand-v3 (2026-11-09), worker\_agent-v1 (2026-11-11), write\_cases-v1 (2026-11-11), render-v1

**Limits:** $0.25 per ticket, 2 rounds, 8 tool calls per worker

**Code version (frozen):** billing-app @ 6a0f8098, core @ cf088d52, dispensing-app @ 7f604ab7, patient-chart @ 8ede2e3a, patient-management @ 37d3c1bc

</details>
