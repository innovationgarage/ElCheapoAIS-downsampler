import click
import click_datetime
import aisdownsampler.message
import aisdownsampler.downsampler
import aisdownsampler.metric
import aisdownsampler.server
import random
import datetime
import ais.stream
import json

@click.group()
@click.pass_context
def main(ctx, **kw):
    ctx.obj = {}
    
@main.command()
@click.option('--station-id', default="unknown")
@click.option('--max-message-per-sec', type=float)
@click.option('--max-message-per-mmsi-per-sec', type=float)
@click.argument("input")
@click.argument("output")
@click.pass_context
def downsample(ctx, station_id, max_message_per_sec, max_message_per_mmsi_per_sec, input, output):
    sess = aisdownsampler.downsampler.Session(
        max_message_per_sec=max_message_per_sec,
        max_message_per_mmsi_per_sec=max_message_per_mmsi_per_sec)
    with open(input, "r") as inf:
        with open(output, "w") as outf:
            for msg in sess(aisdownsampler.message.NmeaMessage(line, station_id) for line in inf):
                if hasattr(msg, 'json'):
                    outf.write(msg.fullmessage)

@main.command()
@click.argument("config")
@click.pass_context
def server(ctx, config):
    """Example:

aisdownsampler server config.json
"""
    with open(config) as f:
        config = json.load(f)
    aisdownsampler.server.server(config)
                    
@main.group()
@click.pass_context
def test(ctx, **kw):
    ctx.obj = {}

@test.command()
@click.option('--station-id', default="unknown")
@click.option('--now', type=click_datetime.Datetime(format='%Y-%m-%d %H:%M:%S'), default=None)
@click.option('--delay-min', type=float, default=0)
@click.option('--delay-max', type=float, default=0)
@click.argument("input")
@click.argument("output")
@click.pass_context
def add_tagblock(ctx, station_id, now, delay_min, delay_max, input, output):
    if now is None:
        now = datetime.datetime.utcnow()
    now = int(now.strftime("%s"))

    if delay_max < delay_min:
        delay_max = delay_min

    with open(input, "r") as inf:
        with open(output, "w") as outf:
            for msg in (aisdownsampler.message.NmeaMessage(line, station_id) for line in inf):
                msg.tagblock['c'] = now
                msg.add_tagblock()
                outf.write(msg.fullmessage)
                now += int(delay_min + random.random() * (delay_max - delay_min))

@test.command()
@click.option('--station-id', default="unknown")
@click.option('--mmsis')
@click.argument("input")
@click.argument("output")
@click.pass_context
def filter(ctx, station_id, mmsis, input, output):
    mmsis = mmsis and [int(mmsi) for mmsi in mmsis.split(",")] or []
    with open(input, "r") as inf:
        with open(output, "w") as outf:
            for msg in (aisdownsampler.message.NmeaMessage(line, station_id) for line in inf):
                if hasattr(msg, "json") and msg.json["mmsi"] in mmsis:
                    outf.write(msg.fullmessage)

@test.command()
@click.option('--sorting', default="count")
@click.argument("input")
@click.pass_context
def metric(ctx, sorting, input):
    with open(input) as f:
        metric = aisdownsampler.metric.metric(ais.stream.decode(f, keep_nmea=True))
        print(aisdownsampler.metric.format_metric(metric, sorting))
