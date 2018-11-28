import ais.stream
import sys

sorting = "count"
if sys.argv[2:]:
    sorting = sys.argv[2]

msgs = {}
with open(sys.argv[1]) as f:
    for msg in ais.stream.decode(f, keep_nmea=True):
        if "tagblock_timestamp" not in msg:
            continue
        if msg["mmsi"] not in msgs:
            msgs[msg["mmsi"]] = []
        msgs[msg["mmsi"]].append(msg)

stats = {}
for mmsi, mmsimsgs in msgs.iteritems():
    interval = mmsimsgs[-1]["tagblock_timestamp"] - mmsimsgs[0]["tagblock_timestamp"]
    count = len(mmsimsgs)
    stats[mmsi] = {
        "mmsi": mmsi,
        "interval": interval,
        "count": count,
        "frequency": interval > 0 and count / float(interval) or 0}

mmsis = stats.keys()
mmsis.sort(lambda a, b: -cmp(stats[a][sorting], stats[b][sorting]))
for mmsi in mmsis:
    s = stats[mmsi]
    print "%(mmsi)s: %(count)smsgs / %(interval)ss = %(frequency)smsgs/s" % s
