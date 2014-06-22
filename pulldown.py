#!/usr/bin/env python

from bs4 import BeautifulSoup
from urllib import urlopen
from csv import DictReader, DictWriter
from datetime import datetime
import re
import os

def cook_soup():
    sfcl = 'https://sfbay.craigslist.org/sfc/apa/'
    f =  urlopen(sfcl)
    hypertext = f.read()
    f.close()
    soup = BeautifulSoup(hypertext)
    return soup

def get_listings(soup, dateadded, min_price_per_room):
    loc_pat = re.compile("\(.*\)")
    room_pat = re.compile("[1-9]br")
    listings = []
    for e in soup.find_all('p'):
        uniform_resource_locator = 'https://sfbay.craigslist.org' + e.a.get('href')
        try:
            price = e.find_all("span", class_="price")[0].get_text()
            price = int(re.sub("\$", "", re.sub(",", "", price)))
        except IndexError:
            price = -1
        location = e.find_all("span", class_="pnr")[0].get_text().strip()
        loc_mat = re.search(loc_pat, location)
        if loc_mat:
            location = location[loc_mat.start():loc_mat.end()]
        try: 
            rooms_raw = e.find_all("span", class_="l2")[0].get_text()
            rooms = e.find_all("span", class_="l2")[0].get_text().strip().split('-')[0].split('/')[1].strip()
            if not re.match(room_pat, rooms):
                rooms = "1br"
        except IndexError:
            rooms = "1br"
        finally:
            if price > min_price_per_room:
                listings.append({'price':price, 'bedrooms':rooms, 'location':location, 
                                 'url':uniform_resource_locator, 'dateadded':dateadded})
    return listings

def read_prev_findings(f_name):
    listings = []
    if os.path.isfile(f_name):    
        with open(f_name, 'r') as f:
            dr = DictReader(f)
            for row in dr:
                listings.append(row)
    return listings

def filter_listings(prev_findings, curr_findings, dateadded):
    urls = set([])
    listings = []
    dateadded = [int(d) for d in dateadded.split("-")]
    if len(prev_findings) > 0:
        for finding in prev_findings:
            urls.add(finding['url'])
            date = [int(d) for d in finding['dateadded'].split("-")]
            if date[1] < dateadded[1] + 7 or (date[0] != dateadded[0] and date[1] + 30 < dateadded[1] + 7):
                listings.append(finding)
    for finding in curr_findings:
        if finding['url'] not in urls:
            listings.append(finding)
    return listings

def write_findings(listings, f_name, max_price_per_room, min_price_per_room):
    header = ["price", "bedrooms", "location", "url", "dateadded"]
    with open(f_name, 'w') as f:
        dw = DictWriter(f, fieldnames=header)
        dw.writeheader()
        for listing in listings:
            price = int(listing['price'])
            rooms = int(re.sub("[^0-9]", "", listing['bedrooms']))
            if price/rooms < max_price_per_room and price/rooms > min_price_per_room:
                dw.writerow(listing)

def main(f_name, max_price_per_room, min_price_per_room):
    dateadded = str(datetime.today().month) + "-" + str(datetime.today().day) 
    write_findings(filter_listings(read_prev_findings(f_name), 
                                   get_listings(cook_soup(), dateadded, min_price_per_room), 
                                   dateadded),
                   f_name,
                   max_price_per_room,
                   min_price_per_room)
        
if __name__ == '__main__':
    f_name = '/home/kjs/listings.csv'
    max_price_per_room = 2000
    min_price_per_room = 800
    main(f_name, max_price_per_room, min_price_per_room)

