#!/usr/bin/env python
"""
dinerRip.py
code: Connor Hornibrook (c) 2017

Script that rips NJ diner information from an old website and puts it into a spatial PostgreSQL database.
"""

import requests, psycopg2, os
from BeautifulSoup import BeautifulSoup
from geocoder import bing as geocoder

# the diner list url
DINER_URL = "http://njdiners.com/cgi-bin/listing.cgi?ALL"

# keys and passwords from .bash_profile
POSTGRESQL_PASSWORD = os.environ["HORNIBROOK_PASS"]
BING_KEY = os.environ["BING_MAPS_KEY"]

# last address, found from page source
LAST_ADDRESS = "44 Route 46, Washington Township - (908) 813-0404"

if __name__ == "__main__":

	soup = BeautifulSoup(requests.get(DINER_URL).text)  # grab the soup

	# connect to postgresql and create table if needed
	cnxn = psycopg2.connect(database="njgeodata", user="hornibrook", host="localhost", port="5433",
	                        password=POSTGRESQL_PASSWORD)
	cur = cnxn.cursor()
	sql = """DROP TABLE IF EXISTS nj_diner_locations;
		CREATE TABLE nj_diner_locations(
		ID           INT PRIMARY KEY NOT NULL,
		ADDRESS      TEXT NOT NULL,
		PHONE        TEXT NOT NULL,
		X            DOUBLE PRECISION NOT NULL,
		Y            DOUBLE PRECISION NOT NULL,
		SHAPE        GEOMETRY);"""
	cur.execute(sql)

	# Begin the scraping process
	# This very old html follows a pattern:
	# <b>DINER NAME</b>
	# <font>Address</font>

	successes, fails = 0, 0
	oid = 0
	currentDiner = soup.b  # grab the first diner and start from there
	keepGoing = True
	while keepGoing:
		dinerName = currentDiner.text
		dinerInfo = currentDiner.findNext("font").text

		# format diner info
		parts = dinerInfo.split(" - ")  # formatted on site as "address - phone"
		address, phone = parts[0], parts[1]
		x, y = 0.0, 0.0

		# geocode and put into database
		geom = geocoder("{}, NJ".format(address), key=BING_KEY)
		try:
			x, y = geom.json["lng"], geom.json["lat"]
			successes += 1
		except KeyError:
			fails += 1

		# replace single quotes with doubles so this will work with SQL syntax
		if "'" in address:
			address = address.replace("'", "''")

		sql = """INSERT INTO nj_diner_locations (ID, ADDRESS, PHONE, X, Y, SHAPE)
			VALUES ({0}, '{1}', '{2}', {3}, {4},
			ST_SetSRID(ST_MakePoint({3},{4}), 4326));""".format(oid, address, phone, x, y)
		cur.execute(sql)
		oid += 1

		if dinerInfo == LAST_ADDRESS:
			keepGoing = False
		else:
			currentDiner = currentDiner.findNext("b")

	# not all will geocode nicely, set the bad ones' shapes to null for now
	cur.execute("UPDATE nj_diner_locations SET SHAPE=NULL WHERE X=0 AND Y=0;")
	cnxn.commit()