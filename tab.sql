CREATE TABLE page_url (
  id INTEGER PRIMARY KEY,
  secure INTEGER,
  depth INTEGER,
  url TEXT
);

/*
Query to check for doublons:

SELECT   COUNT(url) AS nbr_doublon, url
FROM     page_url
GROUP BY url
HAVING   COUNT(url) > 1
*/