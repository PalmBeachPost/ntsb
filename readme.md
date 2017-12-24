Scraper for National Transportation Safety Board docket files
============================

Clone or download this file.

Create a virtual environment with Python 3.

Run this:
    pip install -r requirements.txt

This attemps to get all the files from a NTSB docket that you're interested in. Visit the [docket search page](http://dms.ntsb.gov/pubdms/search/) to find your accident.

Click on the proper accident number. Your URL should change to something like:
> http://dms.ntsb.gov/pubdms/search/hitlist.cfm?docketID=58493&CFID=412431&CFTOKEN=417c98a88b613fe6-742125DD-D614-0B4B-8587CEEDDAB94E7C

That docket ID number there in the middle, 58493? That's what you want to feed to fetchdocket.py, like this:
    python fetchdocket.py 58493

After downloading the files, it will create a CSV in the main directory showing, among other things, URLs for files and the download status of each.

This tool has not been broadly tested. It attemps to handle issue where more than one version of a file is found, but there's no guarantee it handles them right.

That leads to: 

In general
----------

Pull requests are welcomed, as are suggestions. All credit goes to Palm Beach Newspapers, owner of The Palm Beach Post and Palm Beach Daily News, a Cox Media Group company.
