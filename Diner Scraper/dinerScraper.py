import urllib2, BeautifulSoup, geopy, csv, sys, os

__author__ = 'CFH'

# Method that changes '$amp;' characters to '&' characters when writing to csv
def fixAmper(diner):
    if '&amp;' in diner:
        parts = diner.split('&amp;')
        diner = parts[0] + '&' + parts[1]
        return diner
    else:
        return diner


if __name__ == '__main__':

    # manage user input from terminal
    dir = sys.argv[1]
    while not os.path.isdir(dir):
        print 'Invalid directory. Please enter a new one.'
        dir = input('> ')

    if(dir[-1] != '/'):
        dir += '/'

    # Start scraping procedure
    soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen('http://njdiners.com/cgi-bin/listing.cgi?ALL'))
    pTags = soup.findChildren('p') # grabs all paragraph tags where addresses are stored

    # diner locations and names found in p tags range 1 - 524, 0 is style stuff and 526 is empty
    # 'b' tags contain diner name, 'font' tags contain address
    dinerDict = {}
    print 'Scraping diners...'
    j = 0
    for i in range(1, 525):

        # grab diner name and information from individual "child" tags, fix ampersand characters in html if needed
        dinerName = pTags[i].findChildren('b')[0].string
        part2 = pTags[i].findChildren('font')[0].string

        # split address and phone number
        part2 = part2.split(' - ')
        address = part2[0] + ', NJ'
        phoneNumber = part2[1]

        dinerDict[dinerName] = address, phoneNumber
        j += 1
        sys.stdout.write('\r%d diner(s) scraped'%j)
    print

    # A large amount of these addresses are missing numbers i.e. "Route 1 North" opposed to "44 Route 1 North"
    # Gotta find a solution to this problem. For now, the clean address dict is created using all of the complete ones
    numberLess = {}
    clean = {}
    for name, info in dinerDict.iteritems():
        addr = info[0]
        number = info[1]

        try:
            tmp = int(addr.split(' ')[0])
            clean[str(name)] = str(addr), str(number)
        except(ValueError):
            numberLess[str(name)] = str(addr), str(number)
    print str(len(clean)) + ' clean diners found.'

    geocodedAddresses = []
    geocoder = geopy.geocoders.GoogleV3()

    j = 0
    print 'Geocoding diner addresses...'
    for name, info in clean.iteritems():

        addr = info[0]
        number = info[1]
        lat = 0.0
        longit = 0.0
        location = None

        try:
            location = geocoder.geocode(addr)
            lat = location.latitude
            longit = location.longitude

        # Thrown if too many requests are made for the GoogleV3 geocoder, this allows a partial csv to still be made
        except(geopy.exc.GeocoderQuotaExceeded):
            print
            print 'Too many requests for Google right now! Partially finished CSV will be created.'
            break

        # GEOCODE TESTING
        # if type(lat) == None or type(longit) == None:
        #     print "NONE!!"
        # else:
        #     print 'latitude: ' + str(lat)
        #     print 'longitude: ' + str(longit)
        #     print

        # append the geocoded addresses to the list a size 4 tuple
        tup = name, addr, number, lat, longit
        geocodedAddresses.append(tup)
        j += 1
        sys.stdout.write('\r%d diner(s) geocoded.'%j)
    print


    fields = ['NAME', 'ADDRESS', 'PHONE', 'LAT', 'LONG']
    print 'Writing CSV file...'
    with open(dir + 'diners.csv', 'w') as csvFile:
        writer = csv.DictWriter(csvFile, fieldnames=fields)
        writer.writeheader()
        for tup in geocodedAddresses:
            name = tup[0]
            addr = tup[1]
            number = tup[2]
            lat = tup[3]
            longit = tup[4]
            writer.writerow({'NAME' : fixAmper(name), 'ADDRESS' : addr, 'PHONE' : number,
                             'LAT' : lat, 'LONG' : longit})

    print 'Finished.'













