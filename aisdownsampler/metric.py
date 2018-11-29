import ais.stream
import sys

def metric(messages):
    first = None
    last = None
    count = 0
    msgs = {}
    for msg in messages:
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
        
    return {
        "overall": overall,
        "overall_per_mmsi": permmsioverall,
        "overall_mmsis": mmsioverall,
        "per_mmsi": stats
    }

def format_metric(metric, sorting="count"):
    mmsis = metric["per_mmsi"].keys()
    mmsis.sort(lambda a, b: -cmp(metric["per_mmsi"][a][sorting], metric["per_mmsi"][b][sorting]))
    sorted_stats = [(mmsi, metric["per_mmsi"][mmsi]) for mmsi in mmsis]

    res  = "Overall: %(count)smsgs / %(interval)ss = %(frequency)smsgs/s\n" % metric["overall"]
    res += "         %(count)smsgs / %(interval)ss / mmsi = %(frequency)smsgs/s/mmsi\n" % metric["overall_per_mmsi"]
    res += "         %(count)smmsis / %(interval)ss = %(frequency)smmsis/s\n" % metric["overall_mmsis"]
    for mmsi, s in sorted_stats:
        res += "%(mmsi)s: %(count)smsgs / %(interval)ss = %(frequency)smsgs/s\n" % s
    return res
