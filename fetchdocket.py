from pyquery import PyQuery as pq
import requests
from slugify import slugify        # from awesome-slugify
import os
import time
import argparse
import sys
from collections import OrderedDict
import csv
import datetime
import re


docketurlprefix = "https://dms.ntsb.gov/pubdms/search/hitlist.cfm?docketID="
docketurlsuffix = "&StartRow=1&EndRow=3000&CurrentPage=1&order=1&sort=0&TXTSEARCHT="

masterurlprefix = "https://dms.ntsb.gov/pubdms/search/"
detailurlprefix = "https://dms.ntsb.gov/"

sleeptime = 0.5         # Delay between scrapes and downloads. 0.3 timed out sometimes. 0.5 seemed OK

parser = argparse.ArgumentParser(description="This file attempts to fetch National Transportation Safety Board docket files.")
parser.add_argument('docketid', metavar='docketid', help='docketID number from NTSB URL for the file you want')

try:
    args = parser.parse_args()
except:
    parser.print_help()
    print("Get the docket ID number from the URL the NTSB gives you with a successful search.")
    print("Example: 58493 is the number in http://dms.ntsb.gov/pubdms/search/hitlist.cfm?docketID=58493")
    sys.exit(1)
get_input = input

docketid = args.docketid

if not os.path.exists(docketid):
    os.mkdir(docketid)

docketurl = docketurlprefix + docketid + docketurlsuffix
print(docketurl)
raw = requests.get(docketurl)
html = pq(raw.content)

accidentnumber = pq(html)('title').text().split()[2]           # Grab the third word from the title tag
allrows = pq(html)('tr').filter('.odd') + pq(html)('tr').filter('.leave')
print("Found " + str(len(allrows('tr'))) + " things to download")
totalpages = 0
totalphotos = 0
masterdict = {}


for row in allrows('tr'):
    docno = int(pq(pq(row)('td')[0]).text().strip())
    masterdict[docno] = {}
    docdate = pq(pq(row)('td')[1]).text().strip()
    masterdict[docno]['doctitle'] = pq(pq(row)('td')[2]).text()    # This needs to get cleaned up
    masterdict[docno]['docmasterurl'] = masterurlprefix + pq(pq(pq(pq(row)('td')[2])('a'))).attr('href')
    docdate = datetime.datetime.strptime(docdate, "%b %d, %Y")
    docdate = datetime.datetime.strftime(docdate, "%Y-%m-%d")
    masterdict[docno]['docdate'] = docdate
    try:
        docpages = int(str(pq(pq(row)('td')[3]).html()).replace("--", "").strip())
    except:
        docpages = 0
    try:
        docphotos = int(str(pq(pq(row)('td')[4]).html()).replace("--", "").strip())
    except:
        docphotos = 0
    totalpages += docpages
    totalphotos += docphotos
    masterdict[docno]['docpages'] = docpages
    masterdict[docno]['docphotos'] = docphotos
    # print(masterdict[docno])

print("Trying to download the " + str(len(allrows('tr'))) + " files with " + str(totalpages) + " pages and " + str(totalphotos) + " photos")


# Scrape to find URLs, generate local filename
for record in masterdict:
    docmasterurl = masterdict[record]["docmasterurl"]
    print("Scraping " + docmasterurl)
    docmasterraw = requests.get(docmasterurl)
    docmasterhtml = pq(docmasterraw.content)
    try:
        detailurl = detailurlprefix + pq(pq(docmasterhtml)('input')[1]).attr('value')
    except:
        print("Multiple download options found. Trying to get high-quality one for this record.")
        detailurl = detailurlprefix + pq(pq(docmasterhtml)('option')[-2]).attr('value')
    if detailurl == "https://dms.ntsb.gov/View":
        detailurl = detailurlprefix + re.sub("(.*\')(.*)(\'.*)", r"\2", pq(pq(docmasterhtml)('input')[1]).attr("onclick"))
    if len(detailurl) <= 2 or detailurl == "http://dms.ntsb.gov/Download":             # If we got a blank or nearly blank download link ...
        try:
            detailurl = detailurlprefix + pq(pq(docmasterhtml)('option')[-2]).attr('value')     # Try to pull from "option" choices on download, taking the second-to-last one
            print("Trying alternate download link, maybe, from " + docmasterurl)
        except:
            print("Still having problems finding download url from " + docmasterurl)

    time.sleep(sleeptime)       # Wait to avoid pounding server
    masterdict[record]["detailurl"] = detailurl
    localfilename = masterdict[record]['doctitle']
    docdate = masterdict[record]['docdate']
    localfilename = slugify(localfilename)      # Clean up text, eliminate spaces
    localfilename = docdate + "-" + localfilename   # prepend date
    localfilename = localfilename + "." + detailurl.split(".")[-1]  # append correct file extension
    localfilename = docketid + "/" + localfilename  # use docketid name for subdirectory
    masterdict[record]["localfilename"] = localfilename

# Let's get a master dictionary sorted by document number, so we can download in order, maybe.
masterdict = OrderedDict(sorted(masterdict.items(), key=lambda t: t[0]))

# Download files if we don't already have them
for record in masterdict:
    localfilename = masterdict[record]["localfilename"]
    detailurl = masterdict[record]["detailurl"]
    print(masterdict[record])
    if os.path.exists(localfilename):
        print(localfilename + " already downloaded. Skipping.")
        masterdict[record]['download'] = "File already existed"
    else:
        print("Fetching " + detailurl + " to " + localfilename + ".")
        attempts = 0
        success = False
        r = requests.get(detailurl, stream=True)
        with open(localfilename, 'wb') as localfilehandle:
            for chunk in r.iter_content(chunk_size=100*1024):
                if chunk:
                    localfilehandle.write(chunk)
        masterdict[record]['download'] = "Good"
        time.sleep(sleeptime)
        success = True
        
        while attempts < 3 and not success:
            try:
                r = requests.get(detailurl, stream=True)
                with open(localfilename, 'wb') as localfilehandle:
                    for chunk in r.iter_content(chunk_size=100*1024):
                        if chunk:
                            localfilehandle.write(chunk)
                masterdict[record]['download'] = "Good"
                time.sleep(sleeptime)
                success = True
            except:
                print("*** HEY! This " + detailurl + " thing wasn't working for me. ***")
                print("*** Try downloading the right version yourself from " + masterdict[docno]['docmasterurl'] + " ***")
                masterdict[record]['download'] = "Bad"
                attempts += 1
                time.sleep(3*sleeptime)             # Extra margins in case of time out or network problems.

print("Attempting to build a CSV")
with open(docketid + ".csv", "w", newline='') as csvfile:
    put = csv.writer(csvfile)
    headerrowdict = OrderedDict(sorted(masterdict[record].items(), key=lambda t: t[0]))     # using last record. It'll be fine.
    headerrow = ["accidentnumber", "docketid", "recordnumber"]
    for key in headerrowdict.keys():
        headerrow.append(key)
    put.writerow(headerrow)
    for record in masterdict:
        row = [accidentnumber, docketid, record]
        recorddict = OrderedDict(sorted(masterdict[record].items(), key=lambda t: t[0]))
        for key in recorddict.keys():
            row.append(recorddict[key])
        put.writerow(row)
print("CSV should be saved at " + docketid + ".csv")
