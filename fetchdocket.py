from pyquery import PyQuery as pq
import requests
import os
import time
import argparse
import sys
from slugify import slugify, SLUG_OK        # from unicode-slugify
import urllib2
from collections import OrderedDict


# Many thanks to @rdmurphy for recommendation on unicode-slugify
# To install dependencies:
# pip install pyquery requests unicode-slugify



#URL to look like this: http://dms.ntsb.gov/pubdms/search/hitlist.cfm?docketID=58493&StartRow=1&EndRow=3000&CurrentPage=1&order=1&sort=0&TXTSEARCHT=


## Get file
## Parse to get accident number
## Make directory with accident number, not docket number, if it doesn't already exist
## Parse to get list of document numbers, URLs, titles
## Possibly clean up titles some -- bad characters not translating? Maybe use Django slugify code
    ## http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
## For each master URL, go into the page and parse the correct file URL (highest quality download, etc.), add to list of to-dos
## Save each document with name, appropriate extension (recycle extension)
## Save our list as a CSV or similar for later reference    
    

#if os.path.isfile(target):
#	print("Deleting old file " + target)
#	os.remove(target)

docketurlprefix = "http://dms.ntsb.gov/pubdms/search/hitlist.cfm?docketID="
docketurlsuffix = "&StartRow=1&EndRow=3000&CurrentPage=1&order=1&sort=0&TXTSEARCHT="

masterurlprefix = "http://dms.ntsb.gov/pubdms/search/"
detailurlprefix = "http://dms.ntsb.gov/"

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

accidentnumber = str(pq(html)('title').text()).split()[2]           # Grab the third word from the title tag
allrows = pq(html)('tr').filter('.odd') + pq(html)('tr').filter('.leave')
print("Found " + str(len(allrows('tr'))) + " things to download")
totalpages = 0
totalphotos = 0
masterdict = {}


for row in allrows('tr'):
    docno = int(pq(pq(row)('td')[0]).text().strip())
    masterdict[docno] = {}
    masterdict[docno]['docdate'] = pq(pq(row)('td')[1]).text()
    masterdict[docno]['doctitle'] = unicode(pq(pq(row)('td')[2]).text())    # This needs to get cleaned up
    masterdict[docno]['docmasterurl'] = masterurlprefix + pq(pq(pq(pq(row)('td')[2])('a'))).attr('href')
    try:
        docpages = int(unicode(pq(pq(row)('td')[3]).html()).replace("--", "").strip())
    except:
        docpages = 0
    try:
        docphotos = int(unicode(pq(pq(row)('td')[4]).html()).replace("--", "").strip())
    except:
        docphotos = 0
    totalpages += docpages
    totalphotos += docphotos
    masterdict[docno]['docpages'] = docpages
    masterdict[docno]['docphotos'] = docphotos

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
    time.sleep(0.5)
    #print(detailurl)
    masterdict[record]["detailurl"] = detailurl
    localfilename = masterdict[record]['doctitle']
    localfilename = slugify(localfilename, only_ascii=True)      # Clean up text, eliminate spaces
    localfilename = localfilename + "_No" + str(record)      # append document number
    localfilename = localfilename + "." + detailurl.split(".")[-1]  # append correct file extension
    localfilename = docketid + "/" + localfilename  #use docketid name for subdirectory
    masterdict[record]["localfilename"] = localfilename
    

# Let's get a master dictionary sorted by document number, so we can download in order, maybe.
masterdict = OrderedDict(sorted(masterdict.items(), key=lambda t: t[0]))
   
    
# Download files if we don't already have them
for record in masterdict:
    localfilename = masterdict[record]["localfilename"]
    detailurl = masterdict[record]["detailurl"]
    if os.path.exists(localfilename):
        print(localfilename + " already downloaded. Skipping.")
    else:
        print("Fetching " + detailurl + " to " + localfilename + ".")
        remotefilehandle = urllib2.urlopen(detailurl)
        with open(localfilename, 'wb') as localfilehandle:
            localfilehandle.write(remotefilehandle.read())
        time.sleep(0.5)
        
   
