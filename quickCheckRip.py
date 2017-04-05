#!/usr/bin/env python
"""
quickCheckRip.py
code: Connor Hornibrook (c) 2017

Script that iterates through the 6 URL's containing information on all QuickChek locations and scrapes them into
a PostgreSQL spatial database. Bing used for geocoding the addresses.
"""

import requests, psycopg2, os
from BeautifulSoup import BeautifulSoup
from geocoder import bing as geocoder

# the quick check website has 5 pages of store locations
URLS = ["http://quickchek.com/StoresList/List/3097/1", "http://quickchek.com/StoresList/List/3097/2",
        "http://quickchek.com/StoresList/List/3097/3", "http://quickchek.com/StoresList/List/3097/4",
        "http://quickchek.com/StoresList/List/3097/5"]

# needed for clean data, found during testing
ERROR_ADDS = {"116 RT. 46 EB": "116 RT. 46 E", "350 NJSH 57": "350 State Highway 57"}

# keys and passwords from .bash_profile
POSTGRESQL_PASSWORD = os.environ["HORNIBROOK_PASS"]
BING_KEY = os.environ["BING_MAPS_KEY"]

# names of the div classes we need from the raw html
STORE_ITEM = "store-item"  # parent div for address info
DIV_STORE_ADDRESS = "div-store-address"
DIV_STORE_CITY = "div-store-city-state-zip"
DIV_STORE_PHONE = "div-store-phone"

if __name__ == "__main__":

	qcLocations = []
	oid = 1
	fails = 0
	successes = 0
	for url in URLS:

		# extract html
		html = requests.get(url)
		html = html.text
		soup = BeautifulSoup(html)

		# grab the store info parents for this html page
		storeItems = soup.findAll("div", {"class": STORE_ITEM})

		# iterate through individual store info parents
		for si in storeItems:

			# within store info, grab the address and the city/zip ifno
			address = si.findAll("div", {"class": DIV_STORE_ADDRESS})[0].text
			cityTag = si.findAll("div", {"class": DIV_STORE_CITY})[0]

			# Phone numbers are in the div as "Phone XXX-XXX-XXXX"
			phone = si.findAll("div", {"class": DIV_STORE_PHONE})[0].text.split("Phone ")[1]

			address = address.upper()

			try:
				address = ERROR_ADDS[address]
			except KeyError:
				pass  # not a bad address

			cityInfo = cityTag.text.split(", ")
			city = cityInfo[0].upper()

			stateAndZip = cityInfo[1].split(" ")

			state, zipcode = stateAndZip[0].upper(), stateAndZip[1].upper()
			gcFeed = "{}, {}, {} {}".format(address, city, state, zipcode)

			geom = geocoder(gcFeed, key=BING_KEY)
			x, y = 0.0, 0.0

			# grab coordinates from json
			try:
				x, y = geom.json["lng"], geom.json["lat"]
				successes += 1
			except KeyError:
				fails += 1

			# create a row and add it to the overall list
			qcLocations.append([oid, address, city, state, zipcode, phone, x, y])
			oid += 1

	# connect to postgresql and create table if needed
	cnxn = psycopg2.connect(database='njgeodata', user='hornibrook', host='localhost', port='5433',
	                        password=POSTGRESQL_PASSWORD)
	cur = cnxn.cursor()
	sql = """DROP TABLE IF EXISTS quick_chek_locations;
			 CREATE TABLE quick_chek_locations(
			 ID           INT PRIMARY KEY NOT NULL,
			 STREET       TEXT NOT NULL,
			 CITY         TEXT NOT NULL,
			 STATE        TEXT NOT NULL,
			 ZIP          TEXT NOT NULL,
			 PHONE        TEXT NOT NULL,
			 X            DOUBLE PRECISION NOT NULL,
			 Y            DOUBLE PRECISION NOT NULL,
			 SHAPE        GEOMETRY);"""
	cur.execute(sql)

	# insert the locations into the table
	for row in qcLocations:
		oid, street, city, state, zipcode, phone, x, y = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]

		sql = """INSERT INTO quick_chek_locations (ID, STREET, CITY, STATE, ZIP, PHONE, X, Y, SHAPE)
				 VALUES ({0}, '{1}', '{2}', '{3}', '{4}', '{5}', {6}, {7},
				 ST_SetSRID(ST_MakePoint({6},{7}), 4326));""".format(oid, street, city, state, zipcode, phone, x, y)
		cur.execute(sql)

	if fails == 0:
		cnxn.commit()
	else:
		print "{} fails".format(successes)