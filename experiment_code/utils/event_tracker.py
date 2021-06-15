from psychopy import core


class EventTracker:

    def __init__(self, event_names):
        """
        Tracks events over multiple trials
        :param event_names: ids of events to be tracked
        """
        self.clock = core.Clock()
        self.event_names = event_names
        self.trials = []
        self.current_trial = {}
        self.started = False

    def start(self):
        """
        Sets time to 0.
        :return: None
        """
        self.clock.reset()
        self.started = True

    def trigger(self, event_name):
        """
        Stores time of trigger called for event_name if it has not yet been triggered.
        An event can only be triggered once per trial.
        :param event_name:
        :return:
        """
        if event_name not in self.event_names:
            raise ValueError('Not tracking ' + str(event_name))
        if event_name not in self.current_trial:
            print 'triggered: ', event_name
            self.current_trial[event_name] = int(self.clock.getTime() * 1000)

    def end_trial(self):
        """
        Appends the current trial and resets it.
        Sets all not set events to None.
        :return: None
        """
        # Add missing names
        for name in self.event_names:
            if name not in self.current_trial:
                self.current_trial[name] = None
        print 'end_trial: ', self.current_trial
        self.trials.append(self.current_trial)
        self.current_trial = {}
