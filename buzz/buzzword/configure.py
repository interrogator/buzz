# flake8: noqa

"""
buzz webapp: command-line and .env processing
"""

import argparse
import os

from dotenv import load_dotenv


def _from_cmdline():
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
        "-t", "--title", nargs="?", type=str, required=False, help="Title for app"
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
        "--max-dataset-rows",
        nargs="?",
        type=int,
        required=False,
        help="Truncate datasets at this many rows",
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
        "-p",
        "--page-size",
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

    parser.add_argument(
        "-g",
        "--add-governor",
        default=False,
        action="store_true",
        required=False,
        help="Load governor attributes into dataset. Slow to load and uses more memory, but allows more kinds of searching/showing",
    )

    parser.add_argument(
        "-e",
        "--env",
        nargs="?",
        type=str,
        required=False,
        help="Use .env file to load config, rather than command line",
    )

    parser.add_argument(
        "-c",
        "--corpora-file",
        default="corpora.json",
        type=str,
        nargs="?",
        help="Path to corpora.json",
    )

    kwargs = vars(parser.parse_args())
    if kwargs["drop_columns"] is not None:
        kwargs["drop_columns"] = kwargs["drop_columns"].split(",")
    if kwargs["table_size"] is not None:
        kwargs["table_size"] = [int(i) for i in kwargs["table_size"].split(",")][:2]
    return kwargs


def _configure_buzzword(name):
    """
    Configure application. First, look at command line args.
    If the user wants to use dotenv (--env flag), load from that.
    If not from main, use dotenv only.
    """
    env_path = os.path.join(os.getcwd(), ".env")
    config = _from_cmdline()
    if not config["env"]:
        return config
    else:
        env_path = config["env"]
    return _from_env(env_path)


def _from_env(env_path):
    """
    Read .env. Should return same as command line, except --env argument
    """
    trues = {"1", "true", "True", "Y", "y", "yes", True}
    load_dotenv(dotenv_path=env_path)
    drop_columns = os.getenv("BUZZWORD_DROP_COLUMNS")
    if drop_columns:
        drop_columns = drop_columns.split(",")
    table_size = os.getenv("BUZZWORD_TABLE_SIZE")
    if table_size:
        table_size = [int(i) for i in table_size.split(",")]
    max_dataset_rows = os.getenv("BUZZWORD_MAX_DATASET_ROWS")
    if max_dataset_rows:
        max_dataset_rows = int(max_dataset_rows)

    return dict(
        corpora_file=os.getenv("BUZZWORD_CORPORA_FILE", "corpora.json"),
        debug=os.getenv("BUZZWORD_DEBUG", True) in trues,
        load=os.getenv("BUZZWORD_LOAD", True) in trues,
        add_governor=os.getenv("BUZZWORD_ADD_GOVERNOR", False) in trues,
        title=os.getenv("BUZZWORD_TITLE"),
        page_size=int(os.getenv("BUZZWORD_PAGE_SIZE", 25)),
        max_dataset_rows=max_dataset_rows,
        drop_columns=drop_columns,
        table_size=table_size,
    )
