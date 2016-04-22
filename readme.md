Scraper for National Transportation Safety Board docket files
============================

This may grab all the files from a NTSB docket that you're interested in. Visit the [docket search page](http://dms.ntsb.gov/pubdms/search/) to find your accident.

Click on the proper accident number. Your URL should change to something like:
> http://dms.ntsb.gov/pubdms/search/hitlist.cfm?docketID=58493&CFID=412431&CFTOKEN=417c98a88b613fe6-742125DD-D614-0B4B-8587CEEDDAB94E7C

That docket ID number there in the middle, 58493? That's what you want to feed to fetchdocket.py, like this:
`fetchdocket.py 58493`

This tool has not been broadly tested. There's at least one bug, where multiple versions of files are offered, that it will crash on (docket number 52664). Which leads to:


In general
----------

Pull requests are welcomed, as are suggestions. All credit goes to Palm Beach Newspapers, owner of The Palm Beach Post and Palm Beach Daily News, a Cox Media Group company.
