import argparse
from .budget_app import BudgetApp


def main():
    """Main entrypoint for the moomoolah budget application."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "state_file", help="Financial state to load and/or save to", type=str
    )
    args = parser.parse_args()

    app = BudgetApp(state_file=args.state_file)
    app.run()


if __name__ == "__main__":
    main()
