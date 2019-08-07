"""
buzz webapp: command-line processing
"""

import argparse
import os


def _parse_cmdline_args():
    """
    Command line argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Run the buzzword app for a given corpus."
    )

    parser.add_argument(
        "-l",
        "--load",
        default=True,
        action="store_true",
        required=False,
        help="Load corpus into memory. Longer startup, faster search.",
    )

    parser.add_argument(
        "-t", "--title", nargs="?", type=str, default="buzzword", required=False, help="Title for app"
    )

    parser.add_argument(
        "-r", "--rows", nargs="?", type=int, required=False, help="Rows per page"
    )

    parser.add_argument("path", help="Path to the corpus")

    return vars(parser.parse_args())
