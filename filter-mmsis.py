import aisserver
import sys

mmsis = [int(mmsi) for mmsi in sys.argv[1].split(",")]
with open(sys.argv[2], "r") as inf:
    with open(sys.argv[3], "w") as outf:
        for msg in (aisserver.nmeaMessage(line, "XYZZY") for line in inf):
            if hasattr(msg, "json") and msg.json["mmsi"] in mmsis:
                outf.write(msg.fullmessage)
