# WebScraping
Various web scraping scripts

## [Diner Scraper](https://github.com/cfh294/WebScraping/tree/master/Diner%20Scraper)
Goes through a [VERY old website](http://njdiners.com/cgi-bin/listing.cgi?ALL) and scrapes New Jersey diner information.
Diners are then put into a spatial PostgreSQL database. Not all of the 500+ diners geocode properly. Last time this was
run there were 483 successes and 42 fails. Working on cleaning up the data a little.

## [QuickChek Scraper](https://github.com/cfh294/WebScraping/tree/master/QuickChek%20Scraper)
Goes through the [six pages of QuickChek locations](http://quickchek.com/StoresList/List/3097/1) and scrapes them into
a spatial PostgreSQL database. Bing used for geocoding. All addresses successfully geocoded.
