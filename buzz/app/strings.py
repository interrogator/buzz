"""
buzz webapp: making human-readable strings from data
"""

from buzz.constants import SHORT_TO_LONG_NAME


def _make_table_name(history):
    """
    Generate a table name from its history
    """
    if history == "initial":
        return "Show wordclasses by file"
    specs, show, subcorpora, relative, keyness, sort, n = history
    show = [SHORT_TO_LONG_NAME.get(i, i).lower().replace("_", " ") for i in show]
    show = "+".join(show)
    relkey = ", rel. freq." if relative else ", keyness"
    if keyness:
        relkey = f"{relkey} ({keyness})"
    if relative is False and keyness is False:
        relkey = " showing absolute frequencies"
    basic = f"{show} by {subcorpora}{relkey}, sorting by {sort}"
    parent = specs[-1] if isinstance(specs, tuple) else 0
    if not parent:
        return basic
    return f"{basic} -- from search #{parent}"


def _make_search_name(history):
    """
    Generate a search name from its history
    """
    if isinstance(history, str):
        return f"Search entire corpus: {history}"
    previous, col, skip, search_string, n = history
    no = "not " if skip else ""
    basic = f"{SHORT_TO_LONG_NAME.get(col, col)} {no}matching '{search_string}'"
    hyphen = ""
    while isinstance(previous, tuple):
        hyphen += "──"
        previous = previous[0]
    if hyphen:
        basic = f"└{hyphen} " + basic
    return f"({n}) {basic}"


def _search_error(col, search_string):
    """
    Check for problems with search
    """
    if not search_string:
        return "No search string provided."
    if not col:
        return "No feature selected to search."
    return ""


def _table_error(show, subcorpora):
    """
    Check for problems with table
    """
    errors = []
    if not show:
        errors.append("No choice made for feature to use as columns.")
    if not subcorpora:
        errors.append("No choice made for feature to use as index")
    if not errors:
        return ""
    return "* " + "\n* ".join(errors)
