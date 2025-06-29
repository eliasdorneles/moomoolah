import argparse
from .budget_app import BudgetApp
from .config import get_default_state_file_path


def main():
    """Main entrypoint for the moomoolah budget application."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "state_file",
        nargs="?",
        help="Financial state to load and/or save to (default: XDG data directory)",
        type=str,
    )
    args = parser.parse_args()

    # Use default path if no state file provided
    state_file = (
        args.state_file if args.state_file else str(get_default_state_file_path())
    )

    app = BudgetApp(state_file=state_file)
    app.run()


if __name__ == "__main__":
    main()
