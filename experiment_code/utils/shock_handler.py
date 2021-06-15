from psychopy import parallel, core
import logging
import math



class Shocker():

    def __init__(self,num_shocks=2,time_between=0.03):
        self.do_shock=True
        self.num_shocks=num_shocks
        self.time_between=time_between
        self.duration=0.01
        try:
            self.port = parallel.ParallelPort(address=0x0378)
            self.port.setData(0)  # sets all pins 0
            pass
        except OSError:
            logging.error("COULD NOT FIND SHOCKER PORT")
            logging.warning("FALLBACK TO NO SHOCK")
        # self.do_shock=False (if this is not commented out, there will be no shock)

    def shock(self,duration=None):
        logging.debug("Shock start")
        for _ in range(self.num_shocks):
            if self.do_shock:
                self.port.setPin(2, 1)
                self.port.setPin(3, 1)
                if duration==None:
                    core.wait(self.duration)
                else:
                    core.wait(duration)
                self.port.setPin(2, 0)
                self.port.setPin(3, 0)
            else:
                logging.error("NO SHOCK ADMINISTERED")
                core.wait(self.duration)
            core.wait(max(self.time_between-self.duration,0))

    def send_event_marker(self):
        if self.do_shock:
            self.port.setPin(3, 1)
            core.wait(1)
            self.port.setPin(3, 0)
        else:
            logging.error("NO EVENT MARKER SENT")

class Empty_Shocker():

    def __init__(self,num_shocks=2,time_between=0.03):
        self.num_shocks = num_shocks
        self.time_between = time_between
        self.duration = 0.01


    def shock(self,duration=None):
        pass

    def send_event_marker(self):
        pass
