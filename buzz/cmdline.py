"""
buzz webapp: command-line processing
"""

import argparse


def _parse_cmdline_args():
    """
    Command line argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Run the buzzword app for a given corpus."
    )

    parser.add_argument(
        "-nl",
        "--load",
        default=True,
        action="store_true",
        required=False,
        help="Load corpus into memory. Longer startup, faster search.",
    )

    parser.add_argument(
        "-t",
        "--title",
        nargs="?",
        type=str,
        default="buzzword",
        required=False,
        help="Title for app",
    )

    parser.add_argument(
        "-d",
        "--drop-columns",
        nargs="?",
        type=str,
        required=False,
        help="Dataset columns to remove before loading (comma-separated)",
    )

    parser.add_argument(
        "-m",
        "--max-rows",
        nargs="?",
        type=int,
        required=False,
        help="Limit dataframe to this many rows",
    )

    parser.add_argument(
        "-s",
        "--table-size",
        nargs="?",
        type=str,
        required=False,
        default="2000,200",
        help="Max table dimensions as str ('nrows,ncolumns')",
    )

    parser.add_argument(
        "-r",
        "--rows",
        nargs="?",
        type=int,
        default=25,
        required=False,
        help="Rows to display per page",
    )

    parser.add_argument(
        "-debug",
        "--debug",
        default=False,
        action="store_true",
        required=False,
        help="Debug mode",
    )

    parser.add_argument("path", help="Path to the corpus")

    # postprocessing list-like arguments...
    kwargs = vars(parser.parse_args())
    if kwargs["drop_columns"] is not None:
        kwargs["drop_columns"] = kwargs["drop_columns"].split(",")
    if kwargs["table_size"] is not None:
        kwargs["table_size"] = [int(i) for i in kwargs["table_size"].split(",")][:2]
    return kwargs
