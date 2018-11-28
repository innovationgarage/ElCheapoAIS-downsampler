import ais.stream
import sys

sorting = "count"
if sys.argv[2:]:
    sorting = sys.argv[2]

first = None
last = None
count = 0
msgs = {}
with open(sys.argv[1]) as f:
    for msg in ais.stream.decode(f, keep_nmea=True):
        if "tagblock_timestamp" not in msg:
            continue
        count += 1
        if first is None: first = msg
        last = msg
        if msg["mmsi"] not in msgs:
            msgs[msg["mmsi"]] = []
        msgs[msg["mmsi"]].append(msg)

interval = last["tagblock_timestamp"] - first["tagblock_timestamp"]
overall = {"count": count,
           "interval": interval,
           "frequency": interval > 0 and count / float(interval) or 0}
mmsioverall = {"count": len(msgs.keys()),
               "interval": interval,
               "frequency": interval > 0 and len(msgs.keys()) / float(interval) or 0}
permmsioverall = {"count": float(overall["count"]) / mmsioverall["count"],
                  "interval": interval,
                  "frequency": interval > 0 and (float(overall["count"]) / mmsioverall["count"]) / float(interval) or 0}

stats = {}
for mmsi, mmsimsgs in msgs.iteritems():
    interval = mmsimsgs[-1]["tagblock_timestamp"] - mmsimsgs[0]["tagblock_timestamp"]
    count = len(mmsimsgs)
    stats[mmsi] = {
        "mmsi": mmsi,
        "interval": interval,
        "count": count,
        "frequency": interval > 0 and count / float(interval) or 0}

print "Overall: %(count)smsgs / %(interval)ss = %(frequency)smsgs/s" % overall
print "         %(count)smsgs / %(interval)ss / mmsi = %(frequency)smsgs/s/mmsi" % permmsioverall
print "         %(count)smmsis / %(interval)ss = %(frequency)smmsis/s" % mmsioverall
mmsis = stats.keys()
mmsis.sort(lambda a, b: -cmp(stats[a][sorting], stats[b][sorting]))
for mmsi in mmsis:
    s = stats[mmsi]
    print "%(mmsi)s: %(count)smsgs / %(interval)ss = %(frequency)smsgs/s" % s
