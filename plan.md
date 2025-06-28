# Development Plan

## Completed Features

- [X] split "Manage entries" into separate Expenses and Income screens
- [X] implement delete entry
- [X] display next 12 months forecast on main screen
- [X] display previous 3 months at the bottom
- [X] refresh forecast when getting back from manage expenses/income to main screen
- [X] when user press Insert in main screen, display modal if wants to add
      expense or income

## Planned Features
- [ ] display income list in light green background, and expenses in light
      orange background
- [ ] view details for a given month forecast, detailing expenses per category
- [ ] fix forecast calculation to take into account start_date and end_date
- [ ] add special function for "Savings" category: accumulate it on forecast
    => the idea is to be able to forecast:
        - "will i have enough to pay for the upcoming expenses?"
        - "can i afford to spend on something, like a long distance trip?"
- [ ] display an indication (e.g. * in the title) if there are unsaved changes
- [ ] ask confirmation when exiting with unsaved changes

## Bugs to fix

- [X] hit Enter on empty income/expense list causes crash
