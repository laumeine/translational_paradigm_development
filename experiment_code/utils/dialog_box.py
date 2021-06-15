# coding:utf-8
# Creates output data file and dialog box with subject information
from psychopy import gui#, data
import time

class DialogBox:
    def __init__(self, data_dict=None):
        #self.data_file = data.TrialHandler
        self.data = data_dict

    def show_dlg(self):
        myDlg = gui.Dlg(title="experiment name")
        myDlg.addText('subject_information')
        myDlg.addField('subject ID:')
        # 1: EC: Escape Condition (Stress Control)
        # 2: YC: Yoked Condition (Stress no Control)
        # 3: CC: Control Condition (No Stress)
        myDlg.addField('condition:', choices=["EC", "YC", "CC"])
        myDlg.addField('experimenter:', choices=["name", "name1", "name2"])
        ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
        ok_data.append(time.strftime("%d.%m.%Y"))
        ok_data.append(time.strftime("%H:%M:%S"))
        if myDlg.OK:  # or if ok_data is not None
            # save subject info in dictionary
            self.data = ok_data
        else:
            print('user cancelled')

        return self.data


if __name__=="__main__":
    dial = DialogBox({})
    print dial.show_dlg()
