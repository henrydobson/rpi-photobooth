#!/usr/bin/python
import time, os, subprocess, sys, urllib2, logging, datetime
import gphoto2 as gp
from squid import Squid, RED, GREEN, BLUE, WHITE, YELLOW, OFF
from button import Button
from os.path import join, basename, expanduser

### DECLARATIONS ###

devnull = open(os.devnull, 'wb')

rgb = Squid(18, 23, 24)
rgb2 = Squid(4, 17, 27)

b = Button(25)

gphoto_config = {
    'autofocusdrive': 0 # true
}

out = expanduser('~/photobooth_images')

### LED FUNCTIONS ###

def led_indicate_error():
    rgb2.set_color(RED, 100)
    time.sleep(3)

def led_indicate_ok():
    rgb2.set_color(GREEN, 100)
    time.sleep(3)

def led_indicate_camera():
    rgb.set_color(YELLOW, 100)
    rgb2.set_color(OFF)

def led_indicate_wifi():
    rgb.set_color(BLUE, 100)
    rgb2.set_color(OFF)

def led_indicate_off():
    rgb.set_color(OFF)
    rgb2.set_color(OFF)

def led_indicate_dropbox_upload_processing():
    count = 0
    while (count < 2):
        rgb.set_color(BLUE, 100)
        rgb2.set_color(BLUE, 100)
        time.sleep(0.05)
        rgb.set_color(OFF)
        rgb2.set_color(OFF)
        time.sleep(0.05)
        count = count + 1

def led_indicate_dropbox_upload_ok():
    rgb.set_color(GREEN, 100)
    rgb2.set_color(GREEN, 100)
    time.sleep(1)
    rgb.set_color(OFF)
    rgb2.set_color(OFF)
    time.sleep(0.5)

def led_indicate_dropbox_upload_fail():
    rgb.set_color(RED, 100)
    rgb2.set_color(RED, 100)
    time.sleep(3)
    rgb.set_color(OFF)
    rgb2.set_color(OFF)
    time.sleep(0.5)

def led_indicate_camera_photo_requested():
    count = 0
    while (count < 2):
        rgb.set_color(WHITE, 100)
        rgb2.set_color(WHITE, 100)
        time.sleep(0.05)
        rgb.set_color(OFF)
        rgb2.set_color(OFF)
        time.sleep(0.05)
        count = count + 1

def check_leds():
    count = 0
    count2 = 100
    colors = [RED, GREEN, BLUE]
    for current_color in colors:
        while (count < 100):
          rgb.set_color(current_color, count)
          rgb2.set_color(current_color, count)
          count = count + 1
          time.sleep(0.005)

        while (count2 > 0):
          rgb.set_color(current_color, count2)
          rgb2.set_color(current_color, count2)
          count2 = count2 - 1
          time.sleep(0.005)

def GetDateTimeString():
    #format the datetime for the time-stamped filename
    dt = str(datetime.datetime.now()).split(".")[0]
    clean = dt.replace(" ","_").replace(":","_")
    return clean

def check_leds():
    colors = [ RED, GREEN, BLUE ]
    for current_color in colors:
        count = 0
        while (count < 100):
          rgb.set_color(current_color, count)
          rgb2.set_color(current_color, count)
          count = count + 1
          time.sleep(0.005)

        count2 = 100
        while (count2 > 0):
          rgb.set_color(current_color, count2)
          rgb2.set_color(current_color, count2)
          count2 = count2 - 1
          time.sleep(0.005)

def check_network_on():
    led_indicate_wifi()
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=1)
        led_indicate_ok()
        return True
    except urllib2.URLError, err:
        led_indicate_error()
        return False

def detect_camera():
    led_indicate_camera()
    logging.basicConfig(
        format='%(levelname)s: %(name)s: %(message)s', level=logging.WARNING)
    gp.check_result(gp.use_python_logging())
    context = gp.gp_context_new()
    if hasattr(gp, 'gp_camera_autodetect'):
        # gphoto2 version 2.5+
        cameras = gp.check_result(gp.gp_camera_autodetect(context))
    else:
        port_info_list = gp.check_result(gp.gp_port_info_list_new())
        gp.check_result(gp.gp_port_info_list_load(port_info_list))
        abilities_list = gp.check_result(gp.gp_abilities_list_new())
        gp.check_result(gp.gp_abilities_list_load(abilities_list, context))
        cameras = gp.check_result(gp.gp_abilities_list_detect(abilities_list, port_info_list, context))
    n = 0
    for name, value in cameras:
        print('camera number', n)
        print('===============')
        print(name)
        print(value)
        print
    if name == 'Canon EOS 600D':
        led_indicate_ok()
    elif name == '':
        led_indicate_error()
    else:
        led_indicate_error()
        n += 1
    return 0

def camera_init():
    """ Detect the camera and set the various settings """
    cfg = ['--set-config=%s=%s' % (k, v) for k, v in gphoto_config.items()]
    subprocess.call(['gphoto2', '--auto-detect'] + cfg)

def capture_photo():
    """ Capture a photo and download it from the camera """
    filepath = join(out, '%s.jpg' % str(GetDateTimeString()))
    subprocess.call(['gphoto2', '--capture-image-and-download', "--filename=%s" % filepath ])
    filename = basename(filepath) 
    return filename

def upload_to_dropbox(filename):
    led_indicate_dropbox_upload_processing()
    command = [ "/usr/local/bin/dropbox_uploader", "upload", "/home/pi/photobooth_images/%s" % filename, " %s" % filename ] 
    proc = subprocess.call(command, stdout=devnull, stderr=subprocess.STDOUT)
    time.sleep(2)
    print proc
    if proc == 0:
        led_indicate_dropbox_upload_ok()
        os.remove("/home/pi/photobooth_images/%s" % filename)
    else:
	led_indicate_dropbox_upload_fail()

### END ###

if __name__ == "__main__":
    check_leds()
    check_network_on()
    detect_camera()
    try:
        camera_init()
        print "\nLet's get photoboothing!"
	while True:
            led_indicate_camera()
            if b.is_pressed():
                led_indicate_camera_photo_requested()
                filename = capture_photo()
		upload_to_dropbox(filename)

    except KeyboardInterrupt:
        print "\nExiting..."

