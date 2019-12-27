__author__ = 'mlambir'

import datetime, time
def date(fmt=None,timestamp=None):
    "Manejo de fechas (simil PHP)"
    if fmt=='U': # return timestamp
        t = datetime.datetime.now()
        return int(time.mktime(t.timetuple()))
    if fmt=='c': # return isoformat
        d = datetime.datetime.fromtimestamp(timestamp)
        return d.isoformat()
    if fmt=='Ymd':
        d = datetime.datetime.now()
        return d.strftime("%Y%m%d")
