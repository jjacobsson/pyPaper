from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from statistics import fmean
from bisect import bisect
import requests, json, os, sys, time
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


graph_width = int((SCREEN_WIDTH / 2) - 8)
graph_height = int((SCREEN_HEIGHT / 2) - 10)

sensors = [
  'sensor.solar_power',
  'sensor.net_power',
  'sensor.house_consumption',
  'sensor.battery_usoc'
]

def conv_float(v):
  try:
      return float(v)
  except ValueError:
    return 0.0

def conv_ts(s):
  return datetime.fromisoformat(s)

HS_TOKEN = os.getenv('HS_API_TOKEN')

def get_sensor_data(sensor, hs_token):
  headers = {
    'Authorization': f'Bearer {hs_token}',
    'Content-Type': 'application/json'
  }
  url = f'https://assistant.moonbig.org/api/history/period?filter_entity_id={sensor}'
  response = requests.get(url, headers=headers)
  response = json.loads(response.text)
  response = response[0]
  response = [{'state': conv_float(e['state']), 'time': conv_ts(e['last_changed'])} for e in response]
  return response

results = []
for sensor in sensors:
  results.append(get_sensor_data(sensor, HS_TOKEN))

graph_width = int((SCREEN_WIDTH / 2) - 8)
graph_height = int((SCREEN_HEIGHT / 2) - 10)

ltz = ZoneInfo('Europe/Stockholm')
now = datetime.now(tz=ltz)
time_span = timedelta(hours=24)
pixel_width = time_span / graph_width
old = now - time_span

def produce_y_values(json_data):
  data = sorted(json_data, key=lambda entry: entry['time'])
  keys = [x['time'] for x in data]
  result = [0] * graph_width
  for i in range(graph_width):
    start_time = old + (pixel_width*i)
    end_time = old + (pixel_width*(i+1))
    start_i = bisect(keys, start_time)
    end_i = bisect(keys, end_time)
    ranged = data[start_i:end_i]
    if ranged:
      result[i] = fmean([x['state'] for x in ranged])
    elif i > 0:
      result[i] = result[i-1]
  return result

prod_w = produce_y_values(results[0])
feed_w = produce_y_values(results[1])
cons_w = produce_y_values(results[2])
batt_c = produce_y_values(results[3])

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
