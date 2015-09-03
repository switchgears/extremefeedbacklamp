#!/usr/bin/env python
# encoding: utf-8
"""LCD Class for xfd"""

import wiringpi2 as wiringpi
import time
import threading

class Lcd(object):
    """This class provides an easy way to update the display on the 
       extremefeedbacklamp"""

    def __init__(self, lcd_rows=2, lcd_chars=16, lcd_bits=4, pin_lcd_rs=13,
                 pin_lcd_e=14, pins_lcd_db=[11,10,6,16,0,0,0,0]):
        """Initialize lcd and get ip address"""
        self.rows = lcd_rows
        self.chars = lcd_chars

        self.lcd = wiringpi.lcdInit(lcd_rows, lcd_chars, lcd_bits,
                                    pin_lcd_rs, pin_lcd_e, *pins_lcd_db)
        wiringpi.lcdHome(self.lcd)

        self.screens = { 'splash':['GitGear.com/xfd','eXtremeFeedback!'],
                         'ip':['IP Address:','Searching...'],
                         'text':['Comming soon:',
                                 'Customise this',
                                 'text in Jenkins',
                                 'from the extreme',
                                 'feedback plugin'],
                       }
        self.lock = threading.Lock()
        self.io = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)

    def run(self):
        """Start the thread"""
        self.lcd_thread = threading.Thread(target = self.lcdloop, name = 'LCD')
        self.lcd_thread.setDaemon(1)
        self.lcd_thread.start()

    def join(self):
        """Join in its own method"""
        self.lcd_thread.join()
        

    def format_text(self, text):
        """ Format string for LCD, break on newlines and
            spaces close to maximum lcd  chars"""
        # Split on newlines:
        lines = text.splitlines()
        lcd_lines = []
        for line in lines:
            if len(line) > self.chars:
                lcd_lines.extend(self.split_long_line(line, self.chars))
            else:
                lcd_lines.append(line)
        return lcd_lines

    @staticmethod
    def split_long_line(line, length):
        """Split long lines on space or <length> charaters"""
        result = []
        while line:
            if len(line) < length:
                result.append(line)
                line = None
            else:
                # Split on spaces
                idx = line.rfind(' ', 0, length)
                if idx == -1:
                    # No spaces split on length chars
                    result.append(line[:length])
                    line = line[length:]
                else:
                    result.append(line[:idx])
                    line = line[idx+1:]
        return result

    def update(self, name, text):
        """Update or add screen"""
        screen = {name: self.format_text(text)}
        try:
            self.lock.acquire()
            self.screens.update(screen)
        finally:
            self.lock.release()

    def write(self, lcd_one, lcd_two):
        """Write to the display Only printable chars, no tabs nor newlines"""
        lcd_one = filter( lambda x: 32 <= ord(x) <= 126, lcd_one)
        lcd_two = filter( lambda x: 32 <= ord(x) <= 126, lcd_two)

        line_one = lcd_one[0:self.chars]
        line_two = lcd_two[0:self.chars]

        wiringpi.lcdPosition (self.lcd, 0, 0)
        self.io.delay(2)
        wiringpi.lcdPuts(self.lcd, line_one.ljust(self.chars))
        self.io.delay(2)
        wiringpi.lcdPosition (self.lcd, 0, 1)
        self.io.delay(2)
        wiringpi.lcdPuts(self.lcd, line_two.ljust(self.chars))

    def lcdloop(self):
        """LCD display handler"""
        depeche = 0
        line = 0
        old_screen_len = 0
        while(1):
            wiringpi.lcdHome(self.lcd)
            self.io.delay(2)
            self.lock.acquire()

            try:
                key = self.screens.keys()[depeche]
                screen_len = len(self.screens[key])
                if screen_len != old_screen_len:
                    line = 0;
                if len(self.screens[key]):
                    lcd_one = self.screens[key][line]
                line += 1
                if len(self.screens[key]) == 1:  # Only one line, second blank
                    lcd_two = ""
                else:
                    lcd_two = self.screens[key][line]
                if line >= len(self.screens[key])-1:
                    line = 0
                    depeche = (depeche + 1) % len(self.screens)
                    update_freq = 3
                else:
                    update_freq = 1
                old_screen_len = screen_len
            except TypeError:
                pass
            finally:
                self.lock.release()
            self.write(lcd_one, lcd_two)
            time.sleep(update_freq)

