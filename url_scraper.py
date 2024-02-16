"""Module responsible of all scraping around web pages."""

# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import logging
import warnings
from sqlite3 import Connection
from urllib.parse import urljoin, urlparse
import http.client
import requests
from requests.exceptions import Timeout, InvalidSchema, InvalidURL, TooManyRedirects
from bs4 import BeautifulSoup
from tqdm import tqdm

# our sql module
from sql_handler import add_url, select_by_url

# remove character replacement warning from bs4
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")
TIMEOUT = 3
processing_urls = set()

# ░█▄█░█▀▀░▀█▀░█░█░█▀█░█▀▄░█▀▀
# ░█░█░█▀▀░░█░░█▀█░█░█░█░█░▀▀█
# ░▀░▀░▀▀▀░░▀░░▀░▀░▀▀▀░▀▀░░▀▀▀


def spinner(previous_spinner: str = "   "):
    """ Small function to add a little spinner to the progress bar
    Args:
        previous_spinner (str): the last spinner displayed
    Returns:
        spinner (str): the next spinner to display
    """
    spinners = ['\\', '|', '/', '-']
    try:
        index = spinners.index(previous_spinner[1:2])
        next_index = (index + 1) % len(spinners)
    except ValueError:
        next_index = 0

    return "[" + spinners[next_index] + "]"


def get_depth(url: str, hostname: str):
    """ Will analyze given URL to find its depth
    Args:
        url (str): the url to analyze
        hostname (str): the hostname of the url
    Returns:
        depth (int): the depth of the url
    """
    depth = 0
    for url_part in url.split(hostname)[1].split("/"):
        if len(url_part) > 0:
            depth += 1
    return depth


def get_hostname(url: str):
    """ Will analyze given URL to find its hostname
    Args:
        url (str): the url to analyze
    Returns:
        hostname (str): the hostname of the url
    """

    return url.split('://')[1].split("/")[0]


def filter_url(url: str, max_depth: int, root_hostname: str):
    """Method responsible to filter a url depending on its hostname, depth, etc.
    Args:
        url(str): the url to filter
        max_depth (int): the maximum depth of the url
        root_hostname (str): the root hostname
    Returns:
        valid (bool): weither or not the url is valid
    """
    # check if we're still on the correct hostname
    try:
        hostname = get_hostname(url)
        if hostname != root_hostname:
            logging.info("[SKIPPING] %s: Wrong hostname", url)
            return False

        # check if we reached max depth
        depth = get_depth(url, hostname)
        if depth > max_depth:
            logging.info("[SKIPPING] %s: Max depth reached", url)
            return False
    except IndexError:
        logging.info("[SKIPPING] %s: Malformed URL", url)
        return False

    return True


def get_content(url: str, session: requests.Session) -> requests.Response:
    """Request the web content depending on the given URL and the WebSession
    Args:
        url(str): the URL to analyze
        session(Session): the 'requests' session
    """
    return session.get(url, timeout=TIMEOUT)


def get_header(url: str) -> dict:
    """Request the header of the given URL with 'http' and 'urlparse'
    Args:
        url(str): the URL to analyze
    """
    parsed_url = urlparse(url, allow_fragments=False)

    connection = http.client.HTTPConnection(parsed_url.netloc, timeout=TIMEOUT)
    connection.request("HEAD", parsed_url.path.replace(" ", "%20"))
    response = connection.getresponse()

    return {"url": response.getheader("Location", ""), "type": response.getheader("Content-Type")}
    # return requests.head(url, timeout=TIMEOUT, allow_redirects=True)


def process_page(con: Connection, url: str, max_depth: int, root_hostname: str, session: requests.Session, process_bar: tqdm, added_bar: tqdm):
    """ Will recursively process the given URL and add existing links to the DB
    Args:
        con (DB connection): sqlite connection
        url (str): the target url
        max_depth (int): the maximum depth to search for
        root_hostname (str): the root hostname to look for
        session(Session): the 'requests' session
        process_bar (tqdm): progress bar for processing urls
        added_bar (tqdm): progress bar for added urls
    """

    if not filter_url(url, max_depth, root_hostname):
        return

    # request the page content (exception in case of malformed or false url)
    try:
        # we use the request url in case of redirection
        web_header = get_header(url)

        # if the header url is valid
        if len(web_header["url"]) > 0 and root_hostname in web_header["url"]:
            url = web_header["url"]

        depth = get_depth(url, root_hostname)

        # if the content is not html, no need to request it
        if web_header["type"] is not None and "text/html" not in web_header["type"]:
            add_url(con, url, depth)
            return

        # check if the url has already been added
        if select_by_url(con, url) is not None:
            logging.info("[SKIPPING] %s: URL already added", url)
            return

        if session is None:
            session = requests.Session()
        web_response = get_content(url, session)
    except (UnicodeEncodeError, Timeout, InvalidSchema, InvalidURL, TooManyRedirects, requests.exceptions.ConnectionError) as e:
        logging.info("[SKIPPING] Could not retrieve content from %s", url)
        logging.info(e)
        return

    # finally, we can add this url as completed in the database
    add_url(con, url, depth, added_bar)

    # scap it and process the found urls
    web_soup = BeautifulSoup(web_response.content, "lxml")
    soup_links = web_soup.find_all(["a", "link"])
    soup_links += web_soup.find_all(["script",
                                    "img", "source", "video", "audio"])

    # use of global variable to access the same variable even in nested functions
    global processing_urls

    if soup_links is not None:
        # add to a set to remove the doublons
        all_links = set()
        for element in soup_links:
            _url = None
            if element.get("href") is not None:
                _url = element.get("href")
            elif element.get("src") is not None:
                _url = element.get("src")

            if _url is not None:
                # remove possible header navigation in URL
                _url = _url.split("#")[0]
                if _url not in processing_urls:
                    all_links.add(urljoin(url, _url))

        # prefilter all found urls

        # update the processing set
        processing_urls = processing_urls.union(all_links)

        # update total for the progress bar
        if process_bar is not None:
            process_bar.total += len(all_links)
            process_bar.refresh()

        for link in all_links:
            # update progress & description
            process_page(con, link, max_depth,
                         root_hostname, session, process_bar, added_bar)

            if process_bar is not None:
                process_bar.desc = f"{spinner(process_bar.desc.split()[0])} {process_bar.desc.split(' ', 1)[1]}"
                process_bar.update()
