from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from statistics import fmean
from bisect import bisect
import pickle, os, sys, time
import epaper

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

def draw_graph( entries, draw, x, y, width, height, lmax, lmin, min_max=None ):

    if len(entries) > width:
        entries = entries[-width:]

    if min_max is None:
        min_entry = min(entries)
        max_entry = max(entries)
    else:
        min_entry = min_max[0]
        max_entry = min_max[1]

    min_entry = min(0, min_entry)
    max_entry = max(0, max_entry)

    y_mid = int(y + height * (max_entry / (max_entry - min_entry)))
    scale = height / (max_entry - min_entry)

    draw.line((x, y_mid, x + width, y_mid), fill = 0)
    draw.line((x, y, x, y + height), fill = 0)

    spacing = width / 24
    for i in range(25):
        lx = x + (i*spacing)
        ys = y_mid - 2
        ye = y_mid + 2
        if (i % 6) == 0:
            ys -= 2
            ye += 2
        if (i % 12) == 0:
            ys -= 2
            ye += 2
        draw.line((lx, ys, lx, ye), fill = 0)


    for x_off, value in enumerate(entries):
        x_off += 1
        draw.line((x + x_off, y_mid, x + x_off, y_mid - (scale*value)), fill = 0)

    if max_entry != 0:
        text_max = lmax(max_entry)
        bbox = draw.textbbox((x + 5, y + 1), text_max, font=font)
        draw.rectangle(bbox, fill = 255)
        draw.text((x + 5, y + 1), text_max, font=font)
    if min_entry != 0:
        text_min = lmin(min_entry)
        bbox = draw.textbbox((x + 5, y + height - 1 - 18), text_min, font=font)
        draw.rectangle(bbox, fill = 255)
        draw.text((x + 5, y + height - 1 - 18), text_min, font=font)


entries = []
status_db_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.status.db')

if os.path.exists(status_db_filename):
    try_again = True
    while(try_again):
        try:
            with open(status_db_filename, 'rb') as f:
                entries = pickle.load(f)
            try_again = False
        except:
            print('Unable to load old status database. Trying again in 3 seconds.')
            time.sleep(3)
else:
    print('There is no status database.')
    sys.exit(0)

graph_width = int((SCREEN_WIDTH / 2) - 8)
graph_height = int((SCREEN_HEIGHT / 2) - 10)

ltz = ZoneInfo('Europe/Stockholm')
now = datetime.now(tz=ltz)
time_span = timedelta(hours=24)
pixel_width = time_span / graph_width
old = now - time_span

data = sorted(entries, key=lambda entry: entry['Timestamp'])
keys = [x['Timestamp'] for x in data]

prod_w = [0] * graph_width
feed_w = [0] * graph_width
cons_w = [0] * graph_width
batt_c = [0] * graph_width

for i in range(graph_width):
    start_time = old + (pixel_width*i)
    end_time = old + (pixel_width*(i+1))
    start_i = bisect(keys, start_time)
    end_i = bisect(keys, end_time)
    ranged = data[start_i:end_i]
    if ranged:
        prod_w[i] = fmean([x['Production_W'] for x in ranged])
        feed_w[i] = fmean([x['GridFeedIn_W'] for x in ranged])
        cons_w[i] = fmean([x['Consumption_W'] for x in ranged])
        batt_c[i] = fmean([x['USOC'] for x in ranged])

font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Font.ttc'), 18)

image = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 255)  # 255: clear the frame

draw = ImageDraw.Draw(image)

def wat_lbl(e):
    return f'{e/1000.0:.1f}kW'

def percent_lbl(e):
    return f'{e} %'

draw_graph(prod_w, draw, 4, 5, graph_width, graph_height, lmax=wat_lbl, lmin=wat_lbl)
draw_graph(feed_w, draw, 4, 5 + graph_height + 10, graph_width, graph_height, lmax=wat_lbl, lmin=wat_lbl)
draw_graph(cons_w, draw, (4*3) + graph_width, 5, graph_width, graph_height, lmax=wat_lbl, lmin=wat_lbl)
draw_graph(batt_c, draw, (4*3) + graph_width, 5 + graph_height + 10, graph_width, graph_height, lmax=percent_lbl, lmin=percent_lbl, min_max=(0,100))

epd = epaper.epaper('epd7in5_V2').EPD()
epd.init()
epd.display(epd.getbuffer(image))
epd.sleep()
