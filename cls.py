import epaper, urllib.request, json
from PIL import Image,ImageDraw,ImageFont

# Just clear the screen

epd = epaper.epaper('epd7in5_V2').EPD()

epd.init()

epd.Clear()

epd.sleep()