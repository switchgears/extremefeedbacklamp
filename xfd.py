#!/usr/bin/env python
# encoding: utf-8
"""Switch-Gears ApS Raspberry Pi eXtreme Feedback Device Controller"""
# please note: only h/w v6+ compatible

import ast
import FSM
import logging
import random
import socket
import sys
import threading
import time
import wiringpi2 as wiringpi
import os
import subprocess
from lcd import Lcd

#logging level
#DEBUG: Print EVERYTHING
#INFO
#WARNING
#ERROR
#CRITICAL: Print only critical issues
logging.basicConfig(stream=sys.stderr, level=logging.CRITICAL)
#logging.basicConfig(filename="/home/pi/extremefeedbacklamp/sg.log",level=logging.DEBUG)

# shared state variables
NEXT_STATE = 'setOff'
SIREN_NEXT_STATE = 'setOff'
SOUNDEFFECT_NEXT_STATE = 'setOff'
STATE_CHANGE_LOCK = threading.Lock()

# where to listen
UDPPORT = 39418
# I/O pin mapping, Red, Yellow, Green, Siren, Button
REDPIN = 0
YELPIN = 2
GRNPIN = 3
SRNPIN = 4
BTNPIN = 5

# LCD pin mapping, RS, E, D4, D5, D6, D7
LCD_ROWS = 2
LCD_CHARS = 16
LCD_BITS = 4
PIN_LCD_RS = 13
PIN_LCD_E = 14
PINS_LCD_DB = [11, 10, 6, 16, 0, 0, 0, 0]
PIN_LCD_BACKLIGHT = 12

# MP3/ Audio output
AUDIOPIN = 1

IO = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)
PWM_COUNT = 100

def fade_up(pin, step):
    """PWM ramp up to full duty"""
    logging.debug("Up")
    for i in range(0, PWM_COUNT, step):
        wiringpi.softPwmWrite(pin, i)
        IO.delay(12)
    IO.digitalWrite(pin, IO.HIGH)

def fade_down(pin, step):
    """PWM ramp down to zero duty"""
    logging.debug("Down")
    for i in reversed(range(0, PWM_COUNT, step)):
        wiringpi.softPwmWrite(pin, i)
        IO.delay(12)
    IO.digitalWrite(pin, IO.LOW)

def get_ip(iface):
    """Get Ip address of Pi for interface"""
    import fcntl
    import struct
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip_addr = socket.inet_ntoa(fcntl.ioctl(sock.fileno(), 0x8915, #SIOCGIFADDR
            struct.pack('256s', iface))[20:24])
    except IOError:
        ip_addr = "127.0.0.1"
    #cmd = "ip addr show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
    #p = Popen(cmd, shell=True, stdout=PIPE)
    #ip = p.communicate()[0]
    return ip_addr

def get_connection_string(iface):
    """Format ip address nicely"""
    ip_addr = get_ip(iface)
    if ip_addr == "127.0.0.1":
        ip_addr = "  network n/a  "
    if len(ip_addr) < 14:
        ip_addr = "IP %s" % ip_addr
    else:
        ip_addr = "%s" % ip_addr
    return ip_addr

# MAIN

# pin config
IO.pinMode(REDPIN, IO.OUTPUT)
IO.pinMode(YELPIN, IO.OUTPUT)
IO.pinMode(GRNPIN, IO.OUTPUT)
IO.pinMode(SRNPIN, IO.OUTPUT)
IO.pinMode(BTNPIN, IO.INPUT)

# audio, maps to existing pwm channel for line out audio jack
IO.pinMode(AUDIOPIN, IO.PWM_OUTPUT)

# Set PWM range to 100 (duty cycle can be 0-100)
wiringpi.softPwmCreate(REDPIN, 0, 100)
wiringpi.softPwmCreate(YELPIN, 0, 100)
wiringpi.softPwmCreate(GRNPIN, 0, 100)

LCD = Lcd(LCD_ROWS, LCD_CHARS, LCD_BITS, PIN_LCD_RS, PIN_LCD_E, PINS_LCD_DB)

# Siren state machine functions
def siren_on (fsm):
    """Turn on Siren"""
    IO.digitalWrite(SRNPIN, IO.HIGH)
    time.sleep(1.7)

def siren_off (fsm):
    """Turn off Siren"""
    IO.digitalWrite(SRNPIN, IO.LOW)
    time.sleep(0.5)

# Button state machine functions
def button_up (fsm):
    """Button is not pressed/ up"""
    time.sleep(0.1)

def button_down (fsm):
    """Button is pressed/ down"""
    global SIREN_NEXT_STATE
    global NEXT_STATE
    my_next_siren_state = 'setOff'
    my_next_lamp_state = 'setOff'
    currentstate = ['setOff', 'setSolidRed', 'setFlashingRed', 'setSolidYellow', 'setFlashingYellow', 'setSolidGreen', 'setFlashingGreen']
    nextstate = ['setSolidRed', 'setFlashingRed', 'setSolidYellow', 'setFlashingYellow', 'setSolidGreen', 'setFlashingGreen', 'setSolidRed']
    my_next_lamp_state = nextstate[currentstate.index(NEXT_STATE)]
    if (my_next_lamp_state == 'setSolidRed'):
        my_next_siren_state = 'setOn'
    # change to the next logical state
    STATE_CHANGE_LOCK.acquire()
    try:
        NEXT_STATE = my_next_lamp_state
        SIREN_NEXT_STATE = my_next_siren_state
    finally:
        STATE_CHANGE_LOCK.release()
    my_next_siren_state = 'setOff'
    time.sleep(1)

# Lamp state machine functions
# in case of missing transitions, turn on both red and yellow as a debug indicator
def error (fsm):
    """State machine error state"""
    logging.critical("FSM state error")
    fade_up(REDPIN, 1)
    fade_up(YELPIN, 1)

#solid
def red_on (fsm):
    """Turn on Red Lamp"""
    fade_up(REDPIN, 1)

def yellow_on (fsm):
    """Turn on Yellow Lamp"""
    fade_up(YELPIN, 1)

def green_on (fsm):
    """Turn on Green Lamp"""
    fade_up(GRNPIN, 1)

#one pulse
def red_flash (fsm):
    """Pulse Red Lamp once"""
    fade_up(REDPIN, 1)
    fade_down(REDPIN, 1)

def yellow_flash (fsm):
    """Pulse Yellow Lamp once"""
    fade_up(YELPIN, 1)
    fade_down(YELPIN, 1)

def green_flash (fsm):
    """Pulse Green Lamp once"""
    fade_up(GRNPIN, 1)
    fade_down(GRNPIN, 1)

#off
def red_off (fsm):
    """Turn off Red Lamp"""
    fade_down(REDPIN, 1)

def yellow_off (fsm):
    """Turn off Yellow Lamp"""
    fade_down(YELPIN, 1)

def green_off (fsm):
    """Turn off Green Lamp"""
    fade_down(GRNPIN, 1)

#change solid
def red_to_yellow (fsm):
    """Switch lamp from Solid Red to Solid Yellow"""
    fade_down(REDPIN, 1)
    fade_up(YELPIN, 1)

def red_to_green (fsm):
    """Switch lamp from Solid Red to Solid Green"""
    fade_down(REDPIN, 1)
    fade_up(GRNPIN, 1)

def yellow_to_red (fsm):
    """Switch lamp from Solid Yellow to Solid Red"""
    fade_down(YELPIN, 1)
    fade_up(REDPIN, 1)

def yellow_to_green (fsm):
    """Switch lamp from Solid Yellow to Solid Green"""
    fade_down(YELPIN, 1)
    fade_up(GRNPIN, 1)

def green_to_red (fsm):
    """Switch lamp from Solid Green to Solid Red"""
    fade_down(GRNPIN, 1)
    fade_up(REDPIN, 1)

def green_to_yellow (fsm):
    """Switch lamp from Solid Green to Solid Yellow"""
    fade_down(GRNPIN, 1)
    fade_up(YELPIN, 1)

# no_op
def no_op (fsm):
    """State machine no-op, sleeps for 1 sec. without changing lamp state"""
    time.sleep(1)

def siren_state_machine():
    """Siren control state machine"""
    global SIREN_NEXT_STATE

    # declare state machine for siren
    sfsm = FSM.FSM ('INIT', [])
    sfsm.set_default_transition (siren_off, 'INIT')
    sfsm.add_transition_any  ('INIT', None, 'INIT')

    # initialize
    sfsm.add_transition      ('setOff', 'INIT', siren_off, 'SIRENOFF')
    sfsm.add_transition      ('setOn', 'INIT', siren_on, 'SIRENON')

    # on
    sfsm.add_transition      ('setOn', 'SIRENOFF', siren_on, 'SIRENON')
    sfsm.add_transition      ('setOn', 'SIRENON', siren_on, 'SIRENON')

    # off
    sfsm.add_transition      ('setOff', 'SIRENON', siren_off, 'SIRENOFF')
    sfsm.add_transition      ('setOff', 'SIRENOFF', siren_off, 'SIRENOFF')

    # siren test & initial off state
    sfsm.process('setOn')
    sfsm.process('setOff')

    # eventloop
    while(1):
        my_next_state = 'setOff'
        STATE_CHANGE_LOCK.acquire()
        try:
            my_next_state = SIREN_NEXT_STATE
            # avoid the siren blairing continuously... unless polled continuously :)
            SIREN_NEXT_STATE = 'setOff'
        finally:
            STATE_CHANGE_LOCK.release()
        logging.info("siren processing: " + my_next_state)
        sfsm.process(my_next_state)

def button_state_machine():
    """Button toggle state manually for demos state machine"""

    # declare state machine for siren
    bfsm = FSM.FSM ('INIT', [])
    bfsm.set_default_transition (button_up, 'INIT')
    bfsm.add_transition_any  ('INIT', None, 'INIT')

    # initialize
    bfsm.add_transition      ('setOff', 'INIT', button_up, 'BUTTONUP')
    bfsm.add_transition      ('setOn', 'INIT', button_down, 'BUTTONDOWN')

    # on
    bfsm.add_transition      ('setOn', 'BUTTONUP', button_down, 'BUTTONDOWN')
    bfsm.add_transition      ('setOn', 'BUTTONDOWN', button_down, 'BUTTONDOWN')

    # off
    bfsm.add_transition      ('setOff', 'BUTTONUP', button_up, 'BUTTONUP')
    bfsm.add_transition      ('setOff', 'BUTTONDOWN', button_up, 'BUTTONUP')

    # eventloop
    while(1):
        # poll button state
        if (IO.digitalRead(BTNPIN) != 0):
            my_button_next_state = 'setOff'
        else:
            my_button_next_state = 'setOn'
        logging.info("button processing: " + my_button_next_state)
        bfsm.process(my_button_next_state)

def lamp_state_machine():
    """Lamp control state machine"""
    global NEXT_STATE

    # declare state machine for lights
    fsm = FSM.FSM ('INIT', [])
    fsm.set_default_transition (error, 'INIT')
    fsm.add_transition_any  ('INIT', None, 'INIT')

    # initialize
    fsm.add_transition      ('setOff', 'INIT', no_op, 'OFF')

    fsm.add_transition      ('setSolidRed', 'INIT', red_on, 'SOLIDRED')
    fsm.add_transition      ('setSolidYellow', 'INIT', yellow_on, 'SOLIDYELLOW')
    fsm.add_transition      ('setSolidGreen', 'INIT', green_on, 'SOLIDGREEN')

    fsm.add_transition      ('setFlashingRed', 'INIT', red_flash, 'FLASHINGRED')
    fsm.add_transition      ('setFlashingYellow', 'INIT', yellow_flash, 'FLASHINGYELLOW')
    fsm.add_transition      ('setFlashingGreen', 'INIT', green_flash, 'FLASHINGGREEN')

    # off
    fsm.add_transition      ('setOff', 'OFF', no_op, 'OFF')

    fsm.add_transition      ('setOff', 'SOLIDRED', red_off, 'OFF')
    fsm.add_transition      ('setOff', 'SOLIDYELLOW', yellow_off, 'OFF')
    fsm.add_transition      ('setOff', 'SOLIDGREEN', green_off, 'OFF')

    fsm.add_transition      ('setOff', 'FLASHINGRED', no_op, 'OFF')
    fsm.add_transition      ('setOff', 'FLASHINGYELLOW', no_op, 'OFF')
    fsm.add_transition      ('setOff', 'FLASHINGGREEN', no_op, 'OFF')

    fsm.add_transition      ('setFlashingRed', 'OFF', red_flash, 'FLASHINGRED')
    fsm.add_transition      ('setFlashingYellow', 'OFF', yellow_flash, 'FLASHINGYELLOW')
    fsm.add_transition      ('setFlashingGreen', 'OFF', green_flash, 'FLASHINGGREEN')

    fsm.add_transition      ('setSolidRed', 'OFF', red_on, 'SOLIDRED')
    fsm.add_transition      ('setSolidYellow', 'OFF', yellow_on, 'SOLIDYELLOW')
    fsm.add_transition      ('setSolidGreen', 'OFF', green_on, 'SOLIDGREEN')

    # set solid
    fsm.add_transition      ('setSolidRed', 'SOLIDRED', no_op, 'SOLIDRED')
    fsm.add_transition      ('setSolidRed', 'SOLIDYELLOW', yellow_to_red, 'SOLIDRED')
    fsm.add_transition      ('setSolidRed', 'SOLIDGREEN', green_to_red, 'SOLIDRED')

    fsm.add_transition      ('setSolidYellow', 'SOLIDRED', red_to_yellow, 'SOLIDYELLOW')
    fsm.add_transition      ('setSolidYellow', 'SOLIDYELLOW', no_op, 'SOLIDYELLOW')
    fsm.add_transition      ('setSolidYellow', 'SOLIDGREEN', green_to_yellow, 'SOLIDYELLOW')

    fsm.add_transition      ('setSolidGreen', 'SOLIDRED', red_to_green, 'SOLIDGREEN')
    fsm.add_transition      ('setSolidGreen', 'SOLIDYELLOW', yellow_to_green, 'SOLIDGREEN')
    fsm.add_transition      ('setSolidGreen', 'SOLIDGREEN', no_op, 'SOLIDGREEN')

    # from solid to flashing
    fsm.add_transition      ('setFlashingRed', 'SOLIDRED', red_off, 'FLASHINGRED')
    fsm.add_transition      ('setFlashingRed', 'SOLIDYELLOW', yellow_off, 'FLASHINGRED')
    fsm.add_transition      ('setFlashingRed', 'SOLIDGREEN', green_off, 'FLASHINGRED')

    fsm.add_transition      ('setFlashingYellow', 'SOLIDRED', red_off, 'FLASHINGYELLOW')
    fsm.add_transition      ('setFlashingYellow', 'SOLIDYELLOW', yellow_off, 'FLASHINGYELLOW')
    fsm.add_transition      ('setFlashingYellow', 'SOLIDGREEN', green_off, 'FLASHINGYELLOW')

    fsm.add_transition      ('setFlashingGreen', 'SOLIDRED', red_off, 'FLASHINGGREEN')
    fsm.add_transition      ('setFlashingGreen', 'SOLIDYELLOW', yellow_off, 'FLASHINGGREEN')
    fsm.add_transition      ('setFlashingGreen', 'SOLIDGREEN', green_off, 'FLASHINGGREEN')

    # flashing to solid (easy as all bulbs off when changing from flashing)
    fsm.add_transition      ('setSolidRed', 'FLASHINGRED', red_on, 'SOLIDRED')
    fsm.add_transition      ('setSolidRed', 'FLASHINGYELLOW', red_on, 'SOLIDRED')
    fsm.add_transition      ('setSolidRed', 'FLASHINGGREEN', red_on, 'SOLIDRED')

    fsm.add_transition      ('setSolidYellow', 'FLASHINGRED', yellow_on, 'SOLIDYELLOW')
    fsm.add_transition      ('setSolidYellow', 'FLASHINGYELLOW', yellow_on, 'SOLIDYELLOW')
    fsm.add_transition      ('setSolidYellow', 'FLASHINGGREEN', yellow_on, 'SOLIDYELLOW')

    fsm.add_transition      ('setSolidGreen', 'FLASHINGRED', green_on, 'SOLIDGREEN')
    fsm.add_transition      ('setSolidGreen', 'FLASHINGYELLOW', green_on, 'SOLIDGREEN')
    fsm.add_transition      ('setSolidGreen', 'FLASHINGGREEN', green_on, 'SOLIDGREEN')

    # set flash
    fsm.add_transition      ('setFlashingRed', 'FLASHINGRED', red_flash, 'FLASHINGRED')
    fsm.add_transition      ('setFlashingRed', 'FLASHINGYELLOW', red_flash, 'FLASHINGRED')
    fsm.add_transition      ('setFlashingRed', 'FLASHINGGREEN', red_flash, 'FLASHINGRED')

    fsm.add_transition      ('setFlashingYellow', 'FLASHINGRED', yellow_flash, 'FLASHINGYELLOW')
    fsm.add_transition      ('setFlashingYellow', 'FLASHINGYELLOW', yellow_flash, 'FLASHINGYELLOW')
    fsm.add_transition      ('setFlashingYellow', 'FLASHINGGREEN', yellow_flash, 'FLASHINGYELLOW')

    fsm.add_transition      ('setFlashingGreen', 'FLASHINGRED', green_flash, 'FLASHINGGREEN')
    fsm.add_transition      ('setFlashingGreen', 'FLASHINGYELLOW', green_flash, 'FLASHINGGREEN')
    fsm.add_transition      ('setFlashingGreen', 'FLASHINGGREEN', green_flash, 'FLASHINGGREEN')

    # bulb test & initial state
    fsm.process('setSolidRed')
    fsm.process('setSolidYellow')
    fsm.process('setSolidGreen')
    fsm.process('setOff')

    # eventloop
    while(1):
        my_next_state = 'setOff'
        STATE_CHANGE_LOCK.acquire()
        try:
            my_next_state = NEXT_STATE
        finally:
            STATE_CHANGE_LOCK.release()
        logging.info("processing: " + my_next_state)
        fsm.process(my_next_state)

def testloop():
    """Random next transition test, should uncover any transition bugs/ crashes within a few hours"""
    global NEXT_STATE
    logging.critical("***NOTE: YOU ARE RUNNING IN TEST FUZZING MODE, DO NOT USE THIS IN PRODUCTION***")
    while(1):
        time.sleep(random.randint(1, 11))
        list_of_fsm_set_calls = ['setSolidRed', 'setSolidYellow', 'setSolidGreen', 'setFlashingRed', 'setFlashingYellow', 'setFlashingGreen', 'setOff']
        # pick a random next transition from the list
        nexttransition = random.choice(list_of_fsm_set_calls)
        logging.critical(nexttransition)
        sys.stdout.flush()
        STATE_CHANGE_LOCK.acquire()
        try:
            NEXT_STATE = nexttransition
        finally:
            STATE_CHANGE_LOCK.release()

def netloop():
    """UDP network endpoint"""
    global NEXT_STATE
    global SIREN_NEXT_STATE
    global SOUNDEFFECT_NEXT_STATE
    global LCD
    my_next_state = 'setOff'
    my_next_siren_state = 'setOff'
    my_next_soundeffect_state = 'setOff'
    last_known_build_result_table = {}
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("", UDPPORT))
    data = {}
    while(1):
        logging.info("Listening")
        recv_data, addr = server_socket.recvfrom(4096)
        try:
            data = ast.literal_eval(recv_data)
            logging.info("udp datagram rcvd:")
            logging.info(data)

            if 'lcd_text' in data:
                LCD.update('text', data['lcd_text'])

            if ( 'siren' in data and
                 'action' in data and
                 data['action'] in ['ON', 'OFF']
               ):
                action = data['action'].title()
                my_next_siren_state = 'set' + action
                STATE_CHANGE_LOCK.acquire()
                try:
                    SIREN_NEXT_STATE = my_next_siren_state
                finally:
                    STATE_CHANGE_LOCK.release()
                my_next_siren_state = 'setOff'

            if ( 'soundeffect' in data and
                 'color' in data and
                 data['color'] in ['RED', 'GREEN', 'YELLOW']
               ):
                color = data['color'].title()
                my_next_soundeffect_state = 'set' + color
                STATE_CHANGE_LOCK.acquire()
                try:
                    SOUNDEFFECT_NEXT_STATE = my_next_soundeffect_state
                finally:
                    STATE_CHANGE_LOCK.release()
                my_next_soundeffect_state = 'setOff'

            if ( 'color' in data and
                 'action' in data and
                 data['color'] in ['RED', 'GREEN', 'YELLOW'] and
                 data['action'] in ['SOLID', 'FLASHING']
               ):
                color = data['color'].title()
                action = data['action'].title()
                my_next_state = 'set' + action + color

            elif 'name' in data:
                if not data['name'] in last_known_build_result_table:
                    logging.info("Setting default last_known_build_result_table to SUCCESS for:")
                    logging.info(data['name'])
                    last_known_build_result_table[data['name']] = 'SUCCESS'

                if data['build']['phase'] == 'STARTED':
                    if last_known_build_result_table[data['name']] == 'SUCCESS':
                        my_next_state = 'setFlashingGreen'
                    elif last_known_build_result_table[data['name']] == 'UNSTABLE':
                        my_next_state = 'setFlashingYellow'
                    elif last_known_build_result_table[data['name']] == 'FAILURE':
                        my_next_state = 'setFlashingRed'
                    else:
                        logging.warning("Warning: unknown last state:")
                        logging.warning(last_known_build_result_table[data['name']])
                        my_next_state = 'setFlashingRed'

                if data['build']['phase'] == 'FINISHED' or data['build']['phase'] == 'COMPLETED':
                    if data['build']['status']:
                        if data['build']['status'] == 'SUCCESS':
                            my_next_state = 'setSolidGreen'
                            last_known_build_result_table[data['name']] = 'SUCCESS'
                        elif data['build']['status'] == 'UNSTABLE':
                            my_next_state = 'setSolidYellow'
                            last_known_build_result_table[data['name']] = 'UNSTABLE'
                        elif data['build']['status'] == 'FAILURE':
                            my_next_state = 'setSolidRed'
                            last_known_build_result_table[data['name']] = 'FAILURE'
                        elif data['build']['status'] == 'ABORTED':
                            if last_known_build_result_table[data['name']] == 'SUCCESS':
                                my_next_state = 'setSolidGreen'
                            elif last_known_build_result_table[data['name']] == 'UNSTABLE':
                                my_next_state = 'setSolidYellow'
                            elif last_known_build_result_table[data['name']] == 'FAILURE':
                                my_next_state = 'setSolidRed'
                            else:
                                logging.warning("Warning: unknown last known state in ABORTED case")
                                logging.warning(data['name'])
                                logging.warning(last_known_build_result_table[data['name']])
                                my_next_state = 'setSolidRed'
                        else:
                            logging.warning("Warning: unknown end state:")
                            logging.warning(data['build']['status'])
                            my_next_state = 'setSolidRed'

        # incredibly important to ignore and carry on on networking issues
        except Exception, msg:
            logging.critical(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            logging.critical("UDP baguette handling exception:")
            logging.critical("Ignored, Continuing, hoping for the best :)...")
            logging.critical(msg)
            logging.critical("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            pass

        STATE_CHANGE_LOCK.acquire()
        try:
            NEXT_STATE = my_next_state
        finally:
            STATE_CHANGE_LOCK.release()

def soundeffectsloop():
    """Soundeffects playback handler"""
    global SOUNDEFFECT_NEXT_STATE
    my_soundeffect_next_state = 'setOff'
    while(1):
        STATE_CHANGE_LOCK.acquire()
        try:
            my_soundeffect_next_state = SOUNDEFFECT_NEXT_STATE
        finally:
            STATE_CHANGE_LOCK.release()
        playfolder = ""
        if my_soundeffect_next_state != 'setOff':
            if my_soundeffect_next_state == "setRed":
                playfolder = "/home/pi/extremefeedbacklamp/XFD-Audio/Red"
            elif my_soundeffect_next_state == "setYellow":
                playfolder = "/home/pi/extremefeedbacklamp/XFD-Audio/Yellow"
            elif my_soundeffect_next_state == "setGreen":
                playfolder = "/home/pi/extremefeedbacklamp/XFD-Audio/Green"
            else:
                logging.critical("Audio my_soundeffect_next_state unknown, defaulting to Red")
                logging.critical(my_soundeffect_next_state)
                playfolder = "/home/pi/extremefeedbacklamp/XFD-Audio/Red"
            try:
                fhdevnull = open('/dev/null', 'w')
                fullpathrandomtrack = os.path.join(playfolder, random.choice(os.listdir(playfolder)))
                retcode = subprocess.call(["mpg321", "--quiet", fullpathrandomtrack], shell=False, stdout=fhdevnull, stderr=fhdevnull)
                fhdevnull.close()
            except Exception, msg:
                logging.critical("Audio path join or MPG321 call exception, carry on...")
                logging.critical(msg)
                pass
            STATE_CHANGE_LOCK.acquire()
            try:
                SOUNDEFFECT_NEXT_STATE = 'setOff'
            finally:
                STATE_CHANGE_LOCK.release()
        time.sleep(0.5)

def iploop():
    """Watch ip address changes"""
    while(1):
        global LCD
        text = 'IP Address:\n' + get_connection_string("eth0")
        LCD.update('ip', text)
        time.sleep(5)

LAMP_THREAD = threading.Thread(target = lamp_state_machine, name = 'Bob')
LAMP_THREAD.setDaemon(1)
LAMP_THREAD.start()

SIREN_THREAD = threading.Thread(target = siren_state_machine, name = 'Annoyatron9000')
SIREN_THREAD.setDaemon(1)
SIREN_THREAD.start()

NET_THREAD = threading.Thread(target = netloop, name = 'Alice')
NET_THREAD.setDaemon(1)
NET_THREAD.start()

IP_THREAD = threading.Thread(target = iploop, name = 'IP')
IP_THREAD.setDaemon(1)
IP_THREAD.start()

SFX_THREAD = threading.Thread(target = soundeffectsloop, name = 'SFX')
SFX_THREAD.setDaemon(1)
SFX_THREAD.start()

BUTTON_THREAD = threading.Thread(target = button_state_machine, name = 'Demo')
BUTTON_THREAD.setDaemon(1)
BUTTON_THREAD.start()

LCD.run()

#uncomment the following three lines to run in state machine transition fuzzing mode
#TEST_THREAD = threading.Thread(target = testloop, name = 'Fuzz')
#TEST_THREAD.setDaemon(1)
#TEST_THREAD.start()
#TEST_THREAD.join()

LAMP_THREAD.join()
SIREN_THREAD.join()
NET_THREAD.join()
BUTTON_THREAD.join()
SFX_THREAD.join()

