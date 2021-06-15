# Subject information from DialogBox.
- 'subject_ID'
- 'condition': EC/YC/CC
- 'experimenter'
- 'date'
- 'start_time'

# Trial
- 'SM_trial_nr': integer, ascending from 1 to TRIALS
- 'sm_stress_duration': duration (s) of trial. Time until right button press or STRESS_MAX (-decay) or same time as EC sibling in YC.
- 'sm_rt': duration (s) of stimulus presentation until first button press. -1 if no button press.
- 'sm_target': stimulus shown/expected button press(1/Rect/Up), (2/Triangle/Left), (3/Circle/ Right)
- 'sm_first_button_correct': True: first button pressed correct, False: first button pressed wrong, None: no button pressed (during stimulus display)
- 'sm_button_presses': [ID,..] list with all buttons pressed during stimulus display
- 'sm_stress_onset_time' start time of stress in first trial
- 'sm_rating_question_n': ratings. 0 if no rating in this trial, otherwise 1 (not at all) to 7 (very)
- 'sm_end_time', end of last trial(save_data is called)
- 'event_stress_onset': stress onset (from start of first trial in ms)
- 'event_shape_onset': onset of stimulus display
- 'event_response': onset of relevant button press
- 'event_ITI': onset of inter-trial interval