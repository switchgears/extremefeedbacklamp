#!/usr/bin/env python
# encoding: utf-8
""" Espeak Class for xfd
    Author Aske Olsson aske.olsson@switch-gears.dk
"""
import subprocess
import threading
import time

class Speech(object):
    """This class provides an easy way to output
    speech with the espeak module for the xfd"""

    def __init__(self):
        """Initialize"""
        self.lock = threading.Lock()
        self.text = "I'm sorry Dave, I'm afraid I can't do that"

    def run(self):
        """Start the thread"""
        self.speech_thread = threading.Thread(target = self.speechloop, name = 'Speech')
        self.speech_thread.setDaemon(1)
        self.speech_thread.start()

    def join(self):
        """join in its own method"""
        self.speech_thread.join()

    def speak(self, newtext):
        """Set new text to be read"""
        self.lock.acquire()
        try:
            if newtext:
                self.text = newtext
        finally:
            self.lock.release()

    def do_speak(self):
        """Do the speak/reading"""
        fhdevnull = open('/dev/null', 'w')
        try:
            subprocess.call(["espeak", "-p", "20", "-s", "130", "-a", "190", "\""+self.text+"\""], shell=False, stdout=fhdevnull, stderr=fhdevnull)
        finally:
            # Clear text
            self.text = ""
            fhdevnull.close()

    def speechloop(self):
        """Speech handle"""
        while(1):
            self.lock.acquire()
            try:
                if self.text:
                    self.do_speak()
            finally:
                self.lock.release()
            time.sleep(7)