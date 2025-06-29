# Development Plan

## Completed Features

- [X] split "Manage entries" into separate Expenses and Income screens
- [X] implement delete entry
- [X] display next 12 months forecast on main screen
- [X] display previous 3 months at the bottom
- [X] refresh forecast when getting back from manage expenses/income to main screen
- [X] when user press Insert in main screen, display modal if wants to add
      expense or income
- [X] display an indication (e.g. * in the title) if there are unsaved changes
      and ask for confirmation when exiting with unsaved changes
- [x] in the add/update dialogs, hit the primary button when user press ENTER
- [x] in the modal dialog, let user use left/right arrow keys to switch focus
  to left/right
- [x] do not require state file be given as argument -- if not given, create a
  file in the proper default user dir (follow freedesktop specs), using
  appropriate private permissions

## Planned Features

- [X] view details for a given month forecast, detailing expenses per category
  **Product Specification:**
  - [X] User interaction: Click/select month row in forecast or history table and press Enter
  - [X] Display format: Modal dialog with two views
    - [X] Summary view: Categories with totals (e.g., "Groceries: €250", "Salary: €3000")
    - [X] Individual entries view: All entries for that month with descriptions
  - [X] Visual design: 
    - [X] Expenses displayed in red text
    - [X] Income displayed in green text
    - [X] Both expenses and income in same table/view
  - [X] Scope: Works for both future forecast months and historical months
  - [X] Interaction mode: Read-only (view only, no editing from this modal)
- [ ] fix forecast calculation to take into account start_date and end_date
- [ ] add special function for "Savings" category: accumulate it on forecast
    => the idea is to be able to forecast:
        - "will i have enough to pay for the upcoming expenses?"
        - "can i afford to spend on something, like a long distance trip?"

## Bugs to fix

- [X] hit Enter on empty income/expense list causes crash
- [X] the screenshots in the README aren't displaying in pypi.org/project/moomoolah
      we should replace the local URLs by Github absolute URLs when building the package
- [X] when modifying an entry, when user hits ENTER, it shouldn't save and close dialog,
      and not trigger it again
