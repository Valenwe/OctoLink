# OctoLink

This is a personal student project.

This Python script is designed to scrap links from a website, store them in a SQLite database, and display the contents of the database. The goal is to extract all URLs (HTML `<a>`, `<link>`, `<script>`, `<img>`, `<source>`, `<video>` and `<audio>` tags) from the page and save them in a database, repeating this operation for each retrieved link up to a maximum depth of 3 levels.


# Installation

```bash
pip install -r requirements.txt
```

# Usage

Run the script by executing the following command:

```bash
python octo_link.py -h

usage: Octo Link [-h] [-u URL] [-d DEPTH] [-v] [-s] [-r]

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     Root target url (default: http://127.0.0.1)
  -d DEPTH, --depth DEPTH
                        Depth of web scraping (default: 3)
  -v, --verbose         Verbosity for debugging purposes (default: False)
  -s, --show            Only display the database (default: False)
  -r, --reset           Reset the database (default: False)
```

The script will collect all unique absolute URLs from the specified website and store them in an SQLite database table.

## Example Output

```
| ID | URL                                      | Depth | Secure |
| -- | ---------------------------------------- | ----- | ------ |
| 1  | http://localhost/test-intrusion.html     |   1   | 0      |
| 2  | http://localhost/recruit.html            |   2   | 0      |
| 3  | https://localhost/client                 |   2   | 1      |
```

## Database Table Structure

The table structure is predefined as follows:


```sql
CREATE TABLE page_url (
  id INTEGER PRIMARY KEY,
  secure INTEGER,
  depth INTEGER,
  url TEXT
);
```

```
id: Primary key
secure: Set to 1 if the URL starts with https, otherwise 0
url: The retrieved URL
depth: The depth level at which the URL was retrieved
```

