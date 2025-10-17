import argparse
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cereb", description="Cerebrosphere CLI skeleton"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (repeat for more verbose)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Example subcommand
    cmd_example = subparsers.add_parser("example", help="Run example action")
    cmd_example.add_argument("--name", default="world", help="Name to greet")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = build_parser()
    return parser.parse_args(argv)


def run_example(ns: argparse.Namespace) -> None:
    if ns.verbose:
        print(f"[debug] Running example with name={ns.name}")
    print(f"Hello, {ns.name}!")


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv)
    if ns.command == "example":
        run_example(ns)
        return 0
    # No command: show help
    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
