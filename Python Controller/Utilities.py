from math import sqrt
from tkinter import *
from tkinter import ttk

# UTILITY Functions
# determines if bit n is set in val x


def is_set(val, pos):
    return val & 2 ** pos != 0


# takes a flight control input 0-255 and returns a value -1 to 1.
# it also applies a linear dead band, adds a trim value and allows scaling


def map_flt_ctl(ctl_raw, db, trim, fine):
    ctl = ctl_raw / 255 * 2 - 1
    if abs(ctl) < db:
        return 0, trim * fine
    else:
        return ctl, ((ctl - abs(ctl) / ctl * db) / (1 - db) + trim) * fine


# returns the length of a position vector


def norm(v):
    return sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

# converts two bytes to a signed int


def bytes2int(btes):
    return int.from_bytes([btes[0], btes[1]], byteorder='big', signed=True)

# This is a frame with fixed text on the left and variable text on the right


class SubframeLabel:
    def __init__(self, root, title, labels):
        self.frame_name = ttk.LabelFrame(root, text=title)

        for i in range(len(labels)):
            ttk.Label(self.frame_name, text=labels[i], style='Display.TLabel').grid(column=0, row=i, sticky=E)

        self.data_labels = []
        for i in range(len(labels)):
            self.data_labels.append(StringVar())
            ttk.Label(self.frame_name, textvariable=self.data_labels[i], style='Display.TLabel')\
                .grid(column=1, row=i, sticky=W)

    def pack(self):
        self.frame_name.pack(anchor=N, expand=1, fill=X)

    def update(self, value_strings):
        for i in range(len(value_strings)):
            self.data_labels[i].set(value_strings[i])
