import aisdownsampler.message
import sys
import datetime
import random

args = []
kwargs = {}
for arg in sys.argv[1:]:
    if arg.startswith("--"):
        arg = arg[2:]
        value = True
        if "=" in arg:
            arg, value = arg.split("=", 1)
        kwargs[arg] = value
    else:
        args.append(arg)

if "help" in kwargs:
    print """Usage:
addtagblock.py OPTIONS INPUT.nmea OUTPUT.nmea

Available options:

    --now TIMESTAMP (YYYY-MM-DD HH:MM:SS)
    --delay-min DELAY (in seconds)
    --delay-max DELAY (in seconds)
"""
    sys.exit(1)

if "now" in kwargs:
    now = int(datetime.datetime.strptime(kwargs["now"], "%Y-%m-%d %H:%M:%S").strftime("%s"))
else:
    now = int(datetime.datetime.utcnow().strftime("%s"))

delay_min = "delay-min" in kwargs and float(kwargs["delay-min"]) or 0
delay_max = "delay-max" in kwargs and float(kwargs["delay-max"]) or delay_min

with open(args[0], "r") as inf:
    with open(args[1], "w") as outf:
        for msg in (aisdownsampler.message.NmeaMessage(line, "XYZZY") for line in inf):
            msg.tagblock['c'] = now
            msg.add_tagblock()
            outf.write(msg.fullmessage)
            now += int(delay_min + random.random() * (delay_max - delay_min))
