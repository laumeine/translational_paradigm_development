from psychopy import parallel, core, visual, event
import wx

port = parallel.ParallelPort(0x0378)
port.setData(0) # set all pins low

# One shock lasts 2 ms (can be changed manually on the digitimer)


# Create a window that fits the screen size
app = wx.App(False)
display_width = wx.GetDisplaySize()[0]
display_height = wx.GetDisplaySize()[1]
win = visual.Window(fullscr=False, allowGUI=False, monitor="testMonitor", color=[50, 50, 50], colorSpace='rgb255',
                    size=(display_width, display_height))

# Onset of stimulation
stimulation = True

# Draw waiting screen for participants
instruction = visual.TextStim(win, 'Please wait for further instructions from the experimenter. \n \n'
                              'To start the electrical stimulus, press the space bar.',
                              color=[200, 200, 200], colorSpace='rgb255', height=0.06)

instruction.draw()
win.flip()

while stimulation:
    # Wait for keys
    keys = event.waitKeys(keyList=['space', 'return', 'escape'])
    for key in keys:
        if key == 'space':
            for i in range(2):    # Number of mini-shocks that make up a total shock
                port.setPin(2, 1) # Send 1 to pin 2
                port.setPin(3, 1) # Set event marker
                core.wait(0.03)
                port.setPin(2, 0) # Send 0 to pin 2
                port.setPin(3, 0)
        elif key == 'return':
            stimulation = False
        elif key == 'escape':
            stimulation = False
            core.quit()

danke = visual.TextStim(win, 'Thank you. Please wait for further instruction from the experimenter.', color=[200, 200, 200],
                        colorSpace='rgb255')
danke.draw()
win.flip()

# Wait for experimenter to quit calibration
keys = event.waitKeys(keyList=['return'])
for key in keys:
    if key == 'return':
        core.quit()
