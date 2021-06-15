#  -*- coding: utf-8 -*-
import numpy
from psychopy import data
# import parameters as params
import cPickle as pickle
# This class is responsible for data storage in the text file
class SaveData:
    def __init__(self, directory, config):
        self.sm = data.ExperimentHandler(name='Stress Manipulation')
        self.hsb = data.ExperimentHandler(name='Escape Behaviour Test')
        self.hsb_coordinates = data.ExperimentHandler(name='EBT - Coordinates')
        self.directory = directory
        self.config=config

    def write_subject_information(self, dat):
        self.sm.addData('subject_ID', dat[0])
        self.sm.addData('condition', dat[1])
        self.sm.addData('experimenter', dat[2])
        self.sm.addData('date', dat[3])
        self.sm.addData('start_time', dat[4])

    def write_sm_data(self, data_dictionary):
        dat = data_dictionary['subject_information']
        print ('dat', dat)
        stress_dur = data_dictionary['Stress Durations']
        sm_rt = data_dictionary['Reaction Times']
        sm_shapes = data_dictionary['shapes']
        sm_first_button_correct = data_dictionary['First Button Correct'] # First press correct, incorrect or none
        sm_but_presses = data_dictionary['Button Presses']  # Remaining button presses
        questions = data_dictionary['Rating Questions']
        ratings = data_dictionary['Rating Answers']
        event_names = data_dictionary['event_names']
        event_values = data_dictionary['event_values']
        print dat
        for i in range(int(self.config["TRIALS"])):
            if 'conditions' in data_dictionary:
                dat[1] = data_dictionary['conditions'][i]
            self.write_subject_information(dat)
            self.sm.addData('SM_trial_nr', i+1)
            self.sm.addData('sm_stress_duration', stress_dur[i])
            self.sm.addData('sm_rt', sm_rt[i])
            self.sm.addData('sm_target', sm_shapes[i])
            self.sm.addData('sm_first_button_correct', sm_first_button_correct[i])
            self.sm.addData('sm_button_presses', sm_but_presses[i])
            self.sm.addData("sm_stress_onset_time", data_dictionary['Stress Onset Time'][i])
            for question in range(ratings.shape[1]):
                self.sm.addData('\"' + questions[question] + '\"', ratings[i, question])
            self.sm.addData("sm_end_time", data_dictionary['SM End Time'])
            for name in event_names:
                self.sm.addData(name, event_values[i][name])
            self.sm.nextEntry()
        date = dat[3].replace('.', '') + '_' + dat[4].replace(':', '')
        self.sm.saveAsWideText(self.directory + '\\sm_'+str(dat[0])+'_'+date)

    def sm_save_dict(self, sm_dict):
        dat = sm_dict['subject_information']
        date = dat[3].replace(':', '')
        pickle.dump(sm_dict, open(self.directory + "\\sm_dict_data_"+str(dat[0])+'_'+date+".dat", "wb"))

    def hsb_save_dict(self, sm_dict, hsb_dict):
        dat = sm_dict['subject_information']
        pickle.dump(hsb_dict, open(self.directory + "\\hsb_dict_data_"+str(dat[0])+".dat", "wb"))
