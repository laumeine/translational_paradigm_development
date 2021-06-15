#  -*- coding: utf-8 -*-

import logging
import threading
from random import uniform

from psychopy import visual, event, core
from scipy.optimize._lsq.common import check_termination

from utils.audio_handler import Audio

# import parameters as params
from utils.event_tracker import EventTracker
from utils.shock_handler import Empty_Shocker, Shocker


def ConfigSectionMap(Config, section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option.upper()] = Config.get(section, option)
            if dict1[option.upper()] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option.upper()] = None
    return dict1


class StressManipulation:
    def __init__(self, win, stress_dur=None, stim_1_active=None, config=None, event_tracker=None):

        self.config = config
        self.SHOW_SHAPE = float(self.config["SHOW_SHAPE"])
        self.SHOW_SHAPE_JITTER = float(self.config["SHOW_SHAPE_JITTER"])
        self.SHOW_SHAPE_DECAY = float(self.config["SHOW_SHAPE_DECAY"])
        self.SHOW_SHAPE_DECAY_INTERVAL = int(self.config["SHOW_SHAPE_DECAY_INTERVAL"])
        self.HIDE_SHAPE = float(self.config["HIDE_SHAPE"])
        self.GROUP = int(self.config["GROUP"])
        self.NOISE = str(self.config["NOISE"]).strip().lower() == "true"
        self.NOISE_PATH = self.config["NOISE_PATH"]
        self.DISCOUNT = float(self.config["DISCOUNT"])
        self.STRESS_PAUSE = self.config["STRESS_PAUSE"]
        self.ISI_MIN = float(self.config["ISI_MIN"])
        self.ISI_MAX = float(self.config["ISI_MAX"])
        self.SM_SOUND_LENGTH = float(self.config["SOUND_LENGTH"])
        self.SHOCK = str(self.config["SHOCK"]).strip().lower() == "true"
        self.SHOCK_INTERVAL = float(self.config["SHOCK_INTERVAL"])
        self.SHOCK_JITTER = float(self.config["SHOCK_JITTER"])
        # One shock event
        self.NUMBER_SHOCK_REPETITIONS = int(self.config["NUMBER_SHOCK_REPETITIONS"])
        self.TIME_BETWEEN_SHOCKS = float(self.config["TIME_BETWEEN_SHOCKS"])
        self.SM_STRESS_MAX = float(self.config["STRESS_MAX"])

        self.fixation = None
        self.instruction = None
        self.go_to_next_trial = False
        # Reaction time
        self.rt = 0
        self.win = win
        self.stress_dur = stress_dur
        self.shocker = Shocker()
        self.stim_1_active = False
        if self.stress_dur != None:
            self.discount = [0] * len(self.stress_dur)
            self.create_discount_values()

        self.audio = Audio(self.NOISE_PATH)

        # Shapes to be drawn
        self.RECT_ID = 1
        self.TRIANGLE_ID = 2
        self.CIRCLE_ID = 3
        self.SHAPES = {
            self.RECT_ID: visual.Rect(self.win, width=0.2, height=0.2, fillColor=[0, 200, 0], fillColorSpace='rgb255',
                                lineColor=[0, 200, 0], lineColorSpace='rgb255', units="height"),
            self.TRIANGLE_ID: visual.Polygon(self.win, edges=3, radius=0.1, fillColor=[0, 200, 0], fillColorSpace='rgb255',
                                       lineColor=[0, 200, 0], lineColorSpace='rgb255', units="height"),
            self.CIRCLE_ID: visual.Circle(self.win, radius=0.1, fillColor=[0, 200, 0], fillColorSpace='rgb255',
                                    lineColor=[0, 200, 0],
                                    lineColorSpace='rgb255', units="height")
        }
        self.KEYS = {"up": self.RECT_ID, "left": self.TRIANGLE_ID, "right": self.CIRCLE_ID}

        # Event tracker
        self.event_tracker = event_tracker
        if self.event_tracker is None:
            self.event_tracker = EventTracker(['event_stress_onset',
                                               'event_shape_onset',
                                               'event_response',
                                               'event_shape_offset',
                                               'event_ITI'])


    def create_discount_values(self):
        for i in range(len(self.stress_dur)):
            # interval in which shape appears in YC: always input (sibling's) stress duration - discount as lower limit and input stress duration - hide_shape as upper limit
            self.discount[i] = uniform(self.stress_dur[i] - self.DISCOUNT, self.stress_dur[i]-self.HIDE_SHAPE) # adapted 9.April 2018, sync with HIDE_SHAPE


    def create_shock_intervals(self):
        interval_start = 0
        # TODO interval step with jittered show_shape
        interval_step = float(self.SHOW_SHAPE) / float(self.NUMBER_OF_SHOCKS)
        interval_end = interval_start + interval_step
        for i in range(int(self.NUMBER_OF_SHOCKS)):
            self.shock_intervals[i] = (interval_start, interval_end)
            self.shock_start[i] = uniform(interval_start, interval_end)
            interval_start = interval_end
            interval_end += interval_step
        #print self.shock_intervals


    def fixation_cross(self):
        self.fixation = visual.TextStim(self.win, '+', color=[200, 200, 200], colorSpace='rgb255')
        self.fixation.draw()
        self.win.flip()

    def pause_text(self):
        self.instruction = visual.TextStim(self.win, self.STRESS_PAUSE, color=[200, 200, 200],
                                           colorSpace='rgb255', height=0.075)
        self.instruction.draw()
        self.win.flip()



    def check_terminate(self):
        """Checks if user wants to terminate program and terminates on ctrl+q."""
        keys = event.getKeys(keyList=['q', 'ctrl'], modifiers=True)
        for key in keys:
            # print key
            if key[0] == "q" and key[1]["ctrl"]:
                logging.critical("PROGRAM WAS TERMINATED WITH CTRL-Q")
                core.quit()

    def space_pressed(self):
        """Checks if user wants to terminate program. If not checks if space was pressed
        and returns true if yes."""
        self.check_terminate()
        keys = event.getKeys(keyList=['space'], modifiers=False)
        simple_keys = [k[0] for k in keys]
        if 'space' in simple_keys:
            return True
        return False

    def keys_pressed(self):
        """Checks if user wants to terminate program. If not checks if space was pressed
        and returns true if yes."""
        keys = event.getKeys(keyList=self.KEYS.keys(), modifiers=False)
        return keys

    def run_cross_game(self, max_time, show_shape, group, shape_id):
        """
        Runs a single round of the cross game
        :param max_time: Max Time the game should run
        :param show_shape: Time the shape should be shown
        :param group: Group number
        :param shape_id: id of shape to be shown
        :return: tuple (time, rt, keys, correct)
            WHERE
            time : how long the game ran
            rt: reaction time, -1 if no key pressed
            list keys: all pressed keys
            boolean correct: True if the first key was the correct key
        """
        rt = -1
        correct_key = None
        #show_circle = 0

        self.fixation_cross()
        next_audio = uniform(self.ISI_MIN, self.ISI_MAX)
        next_shock = 0
        next_jitter = 0

        self.wait_for_time(float(self.config["ANTICIPATION_TIME"]))
        clk = core.Clock()
        keys = [] # sequence of pressed keys
        while clk.getTime()<max_time:
            #check if circle should be shown
            shape_shown = self.check_shape(clk, show_shape, self.HIDE_SHAPE, shape_id)
            #check if shock should be provided
            next_shock, next_jitter = self.check_shock(clk, next_shock, next_jitter)
            #check if audio should be played
            next_audio = self.check_audio(clk,next_audio)

            self.check_terminate()
            # Keys pressed this this frame
            pressed = self.keys_pressed()
            if clk.getTime() > show_shape:
                keys.extend(pressed)
                if len(keys) == 1:  # First key pressed
                    rt = clk.getTime() - show_shape
                    self.event_tracker.trigger('event_response')
            if shape_shown:
                if len(keys) == 1:  # First key pressed
                    if self.KEYS[keys[0]] == shape_id:  # Correct key pressed
                        correct_key = True
                        # Group condition
                        if (group == 1 or group == 3):
                            self.go_to_next_trial = True  # why?
                            return clk.getTime(), rt, keys, correct_key
                    else:
                        correct_key = False

        return clk.getTime(), rt, keys, correct_key

    def check_audio(self, clk, next_audio):
        """
        Checks if sound should be played
        And if yes plays sound and calculates time until next sound
        :param clk: Current game clock
        :param next_audio: At what point a sound should be played
        :return: At what point next sound should be played
        """
        if self.NOISE and clk.getTime() > next_audio:
            self.audio.play(self.SM_SOUND_LENGTH)
            self.event_tracker.trigger('event_stress_onset')
            next_audio = clk.getTime() + self.SM_SOUND_LENGTH + uniform(self.ISI_MIN, self.ISI_MAX)
        return next_audio

    def check_shock(self, clk, next_shock, next_jitter):
        """
        Checks if a shock should be provided and, if yes, provides a shock
        :param next_jitter: jitter for next shock
        :param next_shock: time of next shock without jitter
        :param clk: current game clock
        :return: time of next shock and jitter
        """
        if self.SHOCK and clk.getTime() > next_shock + next_jitter:
            #thread = threading.Thread(target=self.shocker.shock, args=(self.TIME_BETWEEN_SHOCKS,))
            #thread.daemon = True  # Daemonize thread
            #thread.start()
            self.shocker.shock(self.TIME_BETWEEN_SHOCKS)
            print("Shock at:", clk.getTime(), "-jitter", clk.getTime()-next_jitter)
            self.event_tracker.trigger('event_stress_onset')
            next_shock += self.SHOCK_INTERVAL
            next_jitter = uniform(-self.SHOCK_JITTER, self.SHOCK_JITTER)
        return next_shock, next_jitter


    def check_shape(self, clk_shape, show_shape, hide_shape, shape_id):
        """
        Checks if shape should be displayed and, if yes, displays it
        :param clk_shape: Current game clock
        :param show_shape: Time when shape should be shown
        :param hide_shape: Duration after which shape should not be shown
        :param shape_id: id of shape to be drawn
        :return: True if shape was shown, else False
        """
        if show_shape < clk_shape.getTime() <= show_shape+hide_shape:
            # Draw shape
            self.SHAPES[shape_id].draw()
            self.win.flip()
            self.event_tracker.trigger('event_shape_onset')
            return True
        elif clk_shape.getTime() > show_shape+hide_shape:
            self.fixation_cross()
            self.event_tracker.trigger('event_shape_offset')
        return False


    def wait_for_button(self,max_time):
        """
        Waits for a given maximum time or until space
         is pressed, whichever happens sooner
        :param max_time: Max time that should be waited
        :return:
        """
        clk = core.Clock()
        while clk.getTime() < max_time:
            if self.space_pressed():
                break


    def wait_for_time(self,time):
        """Waits until time has passed"""
        clk = core.Clock()

        while clk.getTime() < time:
            pass

    def run_game(self, group, trial, shape_id):
        """
        Convenience function for cross_game that calculates
        show_circle and maxtime for a given group
        :param group: Group number
        :param trial: Trial number
        :param shape_id: Shape to draw
        :return: tuple (time, rt, keys, correct)
            WHERE
            time
        """

        maxtime = 0
        if group == 1 or group == 3:
            show_shape = self.SHOW_SHAPE
            maxtime = self.SM_STRESS_MAX
            # Decay show_shape
            decay = (trial//self.SHOW_SHAPE_DECAY_INTERVAL) * self.SHOW_SHAPE_DECAY
            show_shape -= decay
            maxtime -= decay

            # Jitter show_shape
            show_shape = show_shape + uniform(-self.SHOW_SHAPE_JITTER, self.SHOW_SHAPE_JITTER)
            show_shape = float(max(0, show_shape))
            maxtime = max(show_shape, maxtime)  # Ensure maxtime is >= show_shape
            print (trial, 'maxtime:', maxtime, 'show_shape', show_shape, 'decay', decay)
        elif group == 2 and trial is not None:
            show_shape = self.discount[trial]
            maxtime = self.stress_dur[trial]
        return self.run_cross_game(maxtime, show_shape, group, shape_id)


    def create_rating(self, text):
        ratingScale = visual.RatingScale(self.win, scale=text, choices=[1, 2, 3, 4, 5, 6, 7],
                                         leftKeys='left', rightKeys='right', acceptKeys='space', markerStart=3,
                                         marker="slider", markerColor="LightGrey", showAccept=False, pos=(0, 0))
        lowAnchorText = visual.TextStim(self.win, 'not at all', pos=(-0.45, -0.2), color=[200, 200, 200], colorSpace='rgb255', height=0.075)
        highAnchorText = visual.TextStim(self.win, 'very', pos=(0.45, -0.2), color=[200, 200, 200], colorSpace='rgb255', height=0.075)
        while ratingScale.noResponse:
            keys = event.getKeys(['q', 'ctrl'], modifiers=True)
            for key in keys:
                if key[0] == 'q' and key[1]['ctrl'] == True:
                    core.quit()
            ratingScale.draw()
            lowAnchorText.draw()
            highAnchorText.draw()
            self.win.flip()
        rating = ratingScale.getRating()
        #decisionTime = ratingScale.getRT()
        #choiceHistory = ratingScale.getHistory()

        return rating

