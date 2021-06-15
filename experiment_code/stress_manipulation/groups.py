#  -*- coding: utf-8 -*-
import cPickle as pickle
import os
import random
import time
from random import uniform

import wx

import numpy as np
from psychopy import event, visual, core, gui

from save_data import SaveData
from stress_manipulation import StressManipulation
from itertools import groupby

from utils.event_tracker import EventTracker


class Groups():

    def __init__(self, group, data, config):

        self.sm = None
        self.config=config

        app = wx.App(False)
        self.display_width = wx.GetDisplaySize()[0]
        self.display_height = wx.GetDisplaySize()[1]

        self.sm_data_dictionary = {}
        self.hsb_data_dictionary = {}

        self.items = []
        count=1
        while "ITEM%s"%count in self.config:
            self.items.append(self.config["ITEM%s"%count].decode("UTF-8"))
            count = count+1

        self.trials = int(self.config["TRIALS"])

        self.rating_data = np.zeros((self.trials, len(self.items)))
        self.reaction_times = [0] * self.trials
        self.stress_durations = [0] * self.trials
        self.button_presses = [0] * self.trials
        self.shape_id_sequence = [0] * self.trials
        self.first_buttons_correct = ['None'] * self.trials

        self.sm_data_dictionary["subject_information"] = data
        self.group = group
        self.files = None
        self.save_dir = None


        group_folder_names = {1:"EC",2:"YC",3:"CC"}

        self.working_dir = self.config["WORKING_DIRECTORY"]
        if self.working_dir is None or self.working_dir == 'None':
            self.working_dir = os.path.dirname(__file__)
        print self.working_dir
        self.save_dir = self.working_dir + '\\subjects\\'+group_folder_names[group]
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        print self.save_dir
        if group == 2:
            self.files = gui.fileOpenDlg(self.working_dir + '\\subjects\\EC', prompt='Choose a sibling')

        print('Display res: ', self.display_width, self.display_height)
        self.win = visual.Window(fullscr=False, allowGUI=False, monitor="testMonitor", color=[50, 50, 50],
                                 colorSpace='rgb255', size=[self.display_width, self.display_height])#[800, 600] for testing
        self.s = SaveData(self.save_dir,self.config)
        self.current_trial = 0

    # Display instruction and wait for key input (spacebar) to continue with next section.
    # No "self" because method is not created inside a class but in a script
    def instruct(self, window, text):
        continu = False
        # pygame.event.clear() # All keys that were pressed before will be deleted
        start = visual.TextStim(window, text, color=[200, 200, 200], colorSpace='rgb255', height=0.06)
        start.draw()
        window.flip()
        while not continu:
            keys = event.getKeys(keyList=['space', 'q', 'ctrl'], modifiers=True)
            for key in keys:
                if key[0] == "space":
                    continu = True
                    blank = visual.TextStim(window, "", color=[200, 200, 200], colorSpace='rgb255', height=0.075)
                    blank.draw()
                    window.flip()
                elif key[0] == 'q' and key[1]['ctrl'] == True:
                    core.quit()


    def save_data(self):
        self.sm_data_dictionary['Rating Questions'] = self.items
        self.sm_data_dictionary['Rating Answers'] = self.rating_data
        self.sm_data_dictionary['Reaction Times'] = self.reaction_times
        self.sm_data_dictionary['Stress Durations'] = self.stress_durations
        self.sm_data_dictionary['shapes'] = self.shape_id_sequence
        self.sm_data_dictionary['First Button Correct'] = self.first_buttons_correct
        self.sm_data_dictionary['Button Presses'] = self.button_presses
        self.sm_data_dictionary['SM End Time'] = time.strftime("%H:%M:%S")
        self.sm_data_dictionary['event_names'] = self.sm.event_tracker.event_names
        self.sm_data_dictionary['event_values'] = self.sm.event_tracker.trials
        self.s.write_sm_data(self.sm_data_dictionary)
        self.s.sm_save_dict(self.sm_data_dictionary)

    def run_sm(self, sm, group_number):
        """
        Run complete test for a given group
        :param event_tracker:
        :param instructions: bool: Show instructions if true.
        :param sm: Instance of stress-manipulation class
        :param group_number: Group number
        :return:
        """
        if not sm.event_tracker.started:
            sm.event_tracker.start()
        self.sm = sm

        # Show instruction screens if not set NONE
        if not str(sm.config["START"]).decode('utf-8') == "NONE":
            self.instruct(self.win, sm.config["START"].decode('utf-8'))
        if not str(sm.config["SM_INSTRUCTION1"]).decode('utf-8').strip() == "NONE":
            self.instruct(self.win, sm.config["SM_INSTRUCTION1"].decode('utf-8'))
        if not str(sm.config["SM_INSTRUCTION2"]).decode('utf-8').strip() == "NONE":
            self.instruct(self.win, sm.config["SM_INSTRUCTION2"].decode('utf-8'))

        # Initialize list of shapes. Equal amounts of each shape (SQUARE, TRIANGLE, CIRCLE),
        # max sequence of 3
        shape_ids = sm.SHAPES.keys()
        if not self.trials % len(shape_ids) == 0:
            raise ValueError('Number of trials ('+str(self.trials) +
                             ') has to be divisible by number of possible shapes ('+str(len(shape_ids))+')')
        shape_sequence = generate_sequence(shape_ids, self.trials/len(shape_ids), 3)
        self.shape_id_sequence = shape_sequence # for log
        print shape_sequence
        while self.current_trial < self.trials:

            if self.current_trial == 0:
                self.sm_data_dictionary['Stress Onset Time'] = []
                sm.fixation_cross()
                #sm.wait_for_button(self.config["ANTICIPATION_TIME"])
            else:
                sm.pause_text()
                jitter = uniform(-float(sm.config["ITI_JITTER"]), float(sm.config["ITI_JITTER"]))
                sm.wait_for_button(float(sm.config["ITI"]) + jitter)
                sm.fixation_cross()
                #sm.wait_for_button(self.config["ANTICIPATION_TIME"])

            self.sm_data_dictionary['Stress Onset Time'].append(time.strftime("%H:%M:%S"))

            if group_number == 1:
                stress_dur, rt, keys, correct_key = sm.run_game(1, self.current_trial, shape_sequence[self.current_trial])
            elif group_number == 2:
                stress_dur, rt, keys, correct_key = sm.run_game(2, self.current_trial, shape_sequence[self.current_trial])
            elif group_number == 3:
                stress_dur, rt, keys, correct_key = sm.run_game(3, self.current_trial, shape_sequence[self.current_trial])

            # For log
            self.stress_durations[self.current_trial] = stress_dur
            self.reaction_times[self.current_trial] = rt
            self.first_buttons_correct[self.current_trial] = correct_key
            self.button_presses[self.current_trial] = [sm.KEYS[k] for k in keys]  # Discard first, keycodes to shape indices
            self.current_trial += 1
            current_question = 0

            if self.current_trial % int(sm.config["REPEAT_RATING"]) == 0:
                sm.pause_text()
                sm.wait_for_button(float(sm.config["ITI"]))
                for text in self.items:
                    self.rating_data[self.current_trial - 1, current_question] = sm.create_rating(text)
                    current_question += 1

            sm.event_tracker.trigger('event_ITI')
            sm.event_tracker.end_trial()

    def sm_group_1(self):
        """
        Runs stress manipulation for group 1
        :return:
        """

        sm = StressManipulation(self.win, stim_1_active=True, config=self.config)

        self.run_sm(sm,group_number=1)

        self.save_data()

        event.clearEvents()
        self.instruct(self.win, self.config["ENDE"].decode('utf-8'))

    def sm_group_2(self):
        subj_data = pickle.load(open(self.files[0], "rb"))
        stress_duration = subj_data["Stress Durations"]

        sm = StressManipulation(self.win, stress_dur=stress_duration, stim_1_active=False, config=self.config)

        self.run_sm(sm, group_number=2)

        self.save_data()
        event.clearEvents()
        self.instruct(self.win, self.config["ENDE"].decode('utf-8'))

    def sm_group_3(self):

        sm = StressManipulation(self.win, config=self.config)

        self.run_sm(sm,group_number=3)

        self.save_data()

        event.clearEvents()
        self.instruct(self.win, self.config["ENDE"].decode('utf-8'))


def generate_sequence(e, n, m):
    """
    :param e: Set of elements
    :param n: how often each element should occur
    :param m: maximum repetitions
    :return: list containing each element from e n times where no e is repeated more than m times in sequence.
    """
    # Final sequence
    s = []
    if n <= m:
        s = list(e) * n
        random.shuffle(s)
        return s
    # Extend s by n * len(elements) each iteration
    for i in range(n//m+m):

        remaining = (len(e)*n - len(s))//len(e)
        if remaining < m:
            r = list(e) * remaining
        else:
            r = list(e) * m
        random.shuffle(r)
        for _ in range(m):
            # List of all windows of size m+1 where at least one element is from s or r.
            windows = filter(lambda x: len(x) == m + 1,
                             [s[-i:] + r[:(m + 1 - i)] for i in range(1, m + 1)])
            # check if any window contains an invalid sequence
            if not all(len(set(window)) > 1 for window in windows):
                # rotate r one to right
                r = [r[-1]] + r[:-1]
            else:
                # Valid s+r
                s.extend(r)
                break
        if len(s) == len(e)*n:
            return s
