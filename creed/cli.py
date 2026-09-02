"""Command-line entry point for creed."""

import argparse
import sys
from pathlib import Path

from creed.apply import apply_creeds
from creed.profiles import PROFILES, render_block
from creed.validate import validate_repository


class CreedArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports command errors with exit code 1."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _build_parser() -> CreedArgumentParser:
    parser = CreedArgumentParser(prog="creed", description="Manage AI-dependency creeds for repositories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="print all available creeds")

    apply_parser = subparsers.add_parser("apply", help="install the declared creed and synchronize mirrors")
    apply_parser.add_argument(
        "--creed",
        choices=PROFILES,
        help="override the creed declared in CREED.json",
    )

    subparsers.add_parser("validate", help="validate the declared creed and instruction mirrors")

    show_parser = subparsers.add_parser("show", help="print the managed block for a creed")
    show_parser.add_argument("name", choices=PROFILES, help="creed name")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the creed command-line interface."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    root = Path.cwd()

    try:
        if arguments.command == "list":
            for profile in PROFILES.values():
                print(f"{profile.name} — {profile.summary}")
            return 0

        if arguments.command == "show":
            print(render_block(arguments.name), end="")
            return 0

        if arguments.command == "apply":
            selected_creeds = apply_creeds(root, arguments.creed)
            print(f"Applied the {selected_creeds} creed to AGENTS.md and synchronized instruction mirrors.")
            return 0

        issues = validate_repository(root)
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
            return 1

        print("Validation passed: declared creed, managed block, and instruction mirrors are synchronized.")
        return 0
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
