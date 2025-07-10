#!/usr/bin/env python3
"""
Script to automatically update screenshots for the README.

This script creates two screenshots:
1. demo_main_screen.svg - The main screen loaded with demo_state.json
2. demo_add_expense.svg - The add expense modal with "Public Transport" filled in

Usage:
    python scripts/update_screenshots.py                # Creates new_*.svg files
    python scripts/update_screenshots.py --approve      # Replaces the original files
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the moomoolah package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from moomoolah.budget_app import BudgetApp


async def create_main_screen_screenshot():
    """Create a screenshot of the main screen with demo data."""
    print("Creating main screen screenshot...")

    # Make sure demo_state.json exists
    demo_state_path = Path(__file__).parent.parent / "demo_state.json"
    if not demo_state_path.exists():
        print(f"Error: {demo_state_path} not found")
        return False

    try:
        app = BudgetApp(state_file=str(demo_state_path))
        async with app.run_test(size=(120, 50)) as pilot:
            # Wait for the app to fully initialize
            await pilot.pause()

            # Take screenshot of the main screen
            app.save_screenshot("demo_main_screen.new.svg")

        # Check if screenshot was created
        screenshot_path = Path("demo_main_screen.new.svg")
        if screenshot_path.exists():
            print(f"✓ Created {screenshot_path}")
            return True
        else:
            print("✗ Failed to create main screen screenshot")
            return False

    except Exception as e:
        print(f"✗ Error creating main screen screenshot: {e}")
        return False


async def create_add_expense_screenshot():
    """Create a screenshot of the add expense modal with Public Transport filled in."""
    print("Creating add expense screenshot...")

    # Make sure demo_state.json exists
    demo_state_path = Path(__file__).parent.parent / "demo_state.json"
    if not demo_state_path.exists():
        print(f"Error: {demo_state_path} not found")
        return False

    try:
        app = BudgetApp(state_file=str(demo_state_path))
        async with app.run_test(size=(120, 50)) as pilot:
            # Wait for the app to fully initialize
            await pilot.pause()

            # Press Insert to add entry from main screen
            await pilot.press("insert")
            await pilot.pause()

            # Click "Expense" button in the entry type modal
            await pilot.click("#add_expense")
            await pilot.pause()

            # Fill in the expense form with "Public Transport" data
            description_input = app.screen.query_one("#entry_description")
            description_input.value = "Public Transport"

            amount_input = app.screen.query_one("#entry_amount")
            amount_input.value = "50"

            category_input = app.screen.query_one("#entry_category")
            category_input.value = "Essentials"

            # Set required fields
            start_date_input = app.screen.query_one("#entry_start_date")
            start_date_input.value = "2025-01-01"

            every_input = app.screen.query_one("#entry_every")
            every_input.value = "1"

            # Wait a bit for the form to be fully populated
            await pilot.pause()

            # Take screenshot of the add expense modal
            app.save_screenshot("demo_add_expense.new.svg")

        # Check if screenshot was created
        screenshot_path = Path("demo_add_expense.new.svg")
        if screenshot_path.exists():
            print(f"✓ Created {screenshot_path}")
            return True
        else:
            print("✗ Failed to create add expense screenshot")
            return False

    except Exception as e:
        print(f"✗ Error creating add expense screenshot: {e}")
        return False


def approve_screenshots():
    """Replace the original screenshots with the new ones."""
    print("Approving screenshots...")

    screenshots = [
        ("demo_main_screen.new.svg", "demo_main_screen.svg"),
        ("demo_add_expense.new.svg", "demo_add_expense.svg"),
    ]

    success = True
    for new_file, old_file in screenshots:
        new_path = Path(new_file)
        old_path = Path(old_file)

        if new_path.exists():
            if old_path.exists():
                old_path.unlink()  # Remove old file
            new_path.rename(old_path)  # Rename new file to old name
            print(f"✓ Replaced {old_file}")
        else:
            print(f"✗ {new_file} not found, cannot replace {old_file}")
            success = False

    return success


async def main():
    parser = argparse.ArgumentParser(description="Update README screenshots")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Replace the original screenshot files with the new ones",
    )

    args = parser.parse_args()

    if args.approve:
        success = approve_screenshots()
        if not success:
            sys.exit(1)
    else:
        print("Updating screenshots...")

        # Create both screenshots
        main_success = await create_main_screen_screenshot()
        add_expense_success = await create_add_expense_screenshot()

        if main_success and add_expense_success:
            print("\n✓ All screenshots created successfully!")
            print("Run with --approve to replace the original files.")
        else:
            print("\n✗ Some screenshots failed to create.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
