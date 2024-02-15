"""Module responsible of all SQL queries and displaying."""

# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import os
import logging
import sqlite3
from tqdm import tqdm

# ░█▄█░█▀▀░▀█▀░█░█░█▀█░█▀▄░█▀▀
# ░█░█░█▀▀░░█░░█▀█░█░█░█░█░▀▀█
# ░▀░▀░▀▀▀░░▀░░▀░▀░▀▀▀░▀▀░░▀▀▀


def sql_connection(db_name="octo_find.db", reset=False):
    """ Create a connection with SQLite database specified
        by the octo_find.db file, and create the table if not exists
    Args:
        db_name (str): the filename of our database
        reset (bool): defines if we start over a new db
    Returns:
        Connection object or Error"""
    new_file = not os.path.exists(db_name)

    # delete db if asked
    if reset and not new_file:
        logging.info("Deleting old database file")
        os.remove(db_name)
        new_file = True

    connection = sqlite3.connect(db_name)

    # create the tables if new sql file
    if new_file:
        with open("tab.sql", encoding="utf8", mode="r") as f:
            content = f.read()

        cur = connection.cursor()
        cur.execute(content)
        connection.commit()

    return connection


def add_url(con: sqlite3.Connection, url: str, depth: int, progress_bar: tqdm = None):
    """  Inserts the given url to the database
    Args:
        con (DB connection): sqlite connection
        url (str): the target url
        depth (int): depth of the url
    """
    logging.info("[DEPTH %s] Adding URL %s", depth, url)
    query = """INSERT INTO page_url (url, secure, depth) VALUES(?,?,?)"""

    cur = con.cursor()
    cur.execute(query, (url, url.startswith("https://"), depth))
    con.commit()

    if progress_bar is not None:
        progress_bar.update()


def select_all(con: sqlite3.Connection, table="page_url"):
    """Select all elements from the given table
    Args:
        con (DB connection): sqlite connection
        table (str): table name
    Returns: all elements, or None
    """
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    cur.execute(f'SELECT * FROM {table}')
    rows = cur.fetchall()

    return None if len(rows) == 0 else rows


def select_by_url(con, url):
    """Select single element from the page_url table
    Args:
        con (DB connection): sqlite connection
        url (str): the url to look for
    Returns: The element or None
    """

    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    cur.execute('SELECT * FROM page_url WHERE url = ? LIMIT 1', (url, ))
    rows = cur.fetchall()

    return None if len(rows) == 0 else rows[0]


def pprint_urls(urls: list, max_url_len=60):
    """ Will pretty print the given URLs from the database.
    Args:
        urls (list): the list of urls with their sql data
        max_url_len (int): the maximum URL length for each line
    """

    # Banner printing
    print(f"|  ID  | {'URL'.ljust(max_url_len)} | Depth | Secure |")
    print(f"| ---- | {''.ljust(max_url_len, '-')} | ----- | ------ |")

    if urls is None or len(urls) == 0:
        print(
            f"| ---- | {'No URLs yet registered.'.ljust(max_url_len, '-')} | ----- | ------ |")
        return
    for url in urls:
        lines = []
        # if the url is too long, cut it into multiple lines
        if len(url["url"]) > max_url_len:
            lines.append(
                f'| {url["id"]:<4} | {url["url"][:max_url_len]} | {url["depth"]:<5} | {url["secure"]:<6} |')
            sub_url = url["url"]
            for _ in range(len(sub_url) // max_url_len):
                sub_url = sub_url[min(max_url_len, len(sub_url)):]
                lines.append(
                    f"|      | {sub_url[:max_url_len].ljust(max_url_len)} |       |        |")
        else:
            lines.append(
                f'| {url["id"]:<4} | {url["url"]:<{max_url_len}} | {url["depth"]:<5} | {url["secure"]:<6} |')

        print("\n".join(lines))
    print(f"| ---- | {''.ljust(max_url_len, '-')} | ----- | ------ |")
