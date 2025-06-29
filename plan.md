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

## Planned Features

- [ ] do not require state file be given as argument -- if not given, create a
  file in the proper default user dir (follow freedesktop specs), using
  appropriate private permissions
- [ ] view details for a given month forecast, detailing expenses per category
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
