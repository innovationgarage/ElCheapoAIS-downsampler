import aisserver
import sys

with open(sys.argv[1], "r") as inf:
    with open(sys.argv[2], "w") as outf:
        for msg in (aisserver.nmeaMessage(line, "XYZZY") for line in inf):
            outf.write(msg.fullmessage)
