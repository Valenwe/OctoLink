"""Module for web scrapping all urls from a given hostname."""

# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import sys
import logging
import argparse
from tqdm import tqdm

# import all necessary methods from our modules
from sql_handler import sql_connection, select_all, pprint_urls
from url_scraper import process_page, spinner, get_hostname

# ░█▄█░█▀█░▀█▀░█▀█
# ░█░█░█▀█░░█░░█░█
# ░▀░▀░▀░▀░▀▀▀░▀░▀


# Argument parsing
parser = argparse.ArgumentParser(prog="Octo Link", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-u", "--url", dest="url",
                    default="http://127.0.0.1", help="Root target url")
parser.add_argument("-d", "--depth", dest="depth", type=int,
                    default=3, help="Depth of web scraping")
parser.add_argument("-v", "--verbose", dest="verbose",
                    action="store_true", default=False, help="Verbosity for debugging purposes")
parser.add_argument("-s", "--show", dest="show",
                    action="store_true", default=False, help="Only display the database")
parser.add_argument("-r", "--reset", dest="reset",
                    action="store_true", default=False, help="Reset the database")


args, unknownargs = parser.parse_known_args()
args = vars(args)

if __name__ == "__main__":
    if args["verbose"]:
        logging.basicConfig(level=logging.INFO)
        logging.info("Verbose mode enabled")

    if args["show"]:
        with sql_connection(reset=args["reset"]) as db:
            all_urls = select_all(db)
            pprint_urls(all_urls)
            sys.exit()

    # security checks input
    if args["depth"] < 0 or args["depth"] > 3:
        logging.exception(
            "Bad depth argument. Authorized values are between [0;3].")
        sys.exit()

    if not (args["url"].startswith("http://") or args["url"].startswith("https://")):
        args["url"] = "https://" + args["url"]

    # sql create & connect (the with will close the connection)
    with sql_connection(reset=args["reset"]) as db:

        # count the previous findings
        previous_urls = select_all(db)
        if previous_urls is None:
            NB_PREVIOUS_URLS = 0
        else:
            NB_PREVIOUS_URLS = len(previous_urls)

        pbar = tqdm(desc=spinner() + " Processing URLs",
                    total=1, position=0, colour="#800080", unit="url")
        abar = tqdm(desc="Added URLs", position=1, unit="url")
        process_page(db, args["url"], args["depth"],
                     get_hostname(args["url"]), None, pbar, abar)

        # close all bars
        pbar.update()
        abar.close()
        pbar.close()

        # get all added urls
        all_urls = select_all(db)

        # count the new findings
        previous_urls = select_all(db)
        if previous_urls is None:
            NB_ALL_URLS = 0
        else:
            NB_ALL_URLS = len(previous_urls)

    logging.info("%s new URLs found / %s total URLs found.",
                 NB_ALL_URLS - NB_PREVIOUS_URLS, NB_ALL_URLS)

    # display all urls
    pprint_urls(all_urls)
