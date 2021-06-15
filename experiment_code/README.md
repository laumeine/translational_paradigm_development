# GENERAL INFORMATION

Use this code to run the stress induction and the escape behaviour test as described in Meine et al., 2020, Int. J. Mol. Sci. https://doi.org/10.3390/ijms21176010. The code runs a slightly modified version of the paradigm described in study 2:
- trial number may differ (this can be set using the config files)
- length of trials may differ (can be set in config)
- number of rating time points may differ (in accordance with the number of trials)
- frustration rating has been added
- wording of ratings has been changed slightly to account for difficulties as described in the discussion
- available conditions: escapable stress ('EC'), yoked inescapable stress ('YC'), control condition ('CC')
- possibility to include noise AND electrical stimuli

The included code uses an older version of Python (2.7), it is therefore highly recommended to set up a virtual environment ('virtualenv') with the required packages (see screenshot 'required_python_packages.png'). There are many resources available online to guide you through the process of setting up the virtual environment.


# utils folder
- contains utility functions required for all tasks
- adapt line 19 of dialog_box.py to use the names of your experimenters.


# calibrate_shock.py
- run this script from the command line by calling 'calibrate_shock.bat'
- subjects can apply electrical stimulus themselves by pressing the spacebar
- to quit, press 'escape'
- this script can be used to calibrate the stimulus intensity for each individual


# the folder 'stress_manipulation' contains the code for the stress induction
- 'stress_manipulation/configs' contains all config files in which task parameters are specified. The current settings are recommended.
- 'stress_manipulation/subjects' is the output folder in which all subject logfiles are saved (see output_documentation.md for details)
- run the stress induction from the command line by calling 'run_StressInduction.bat'. Enter your subject ID, choose the condition (EC/YC/CC) and the experimenter name. To run a YC subject, you need to have an EC subject's logfile ('.dat') ready as input. You will be prompted to select this file for yoking of stress durations.
- to quit, press 'ctrl+q'


# the folder 'escape_behaviour_test' contains the code for the escape behaviour test
- 'escape_behaviour_test/configs' contains the config file
- 'escape_behaviour_test/output' is the output folder in which all subject logfiles are saved (see output_documentation.md)
- run the escape behaviour test from the command line by calling 'run_EscapeBehaviourTest.bat'. Enter your subject ID, choose the condition (EC/YC/CC) and the experimenter name.
- to quit, press 'ctrl+q'





