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
        return trim * fine
    else:
        return ((ctl - abs(ctl) / ctl * db) / (1 - db) + trim) * fine


# returns the length of a position vector


def norm(v):
    return sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


# returns a string representation of a value with SI prefixs to it is between 0 and 1000


def si_val(num, prec=3):
    prefixes = [''] + list('kMGTPE')
    if num >= 0:
        temp = num
        neg = 1
    else:
        temp = abs(num)
        neg = -1

    index = 0
    while temp > 1000:
        temp /= 1000
        index += 1

    if index == 0:
        prec = 0

    return '{0:.{1}f}'.format(temp * neg, prec) + prefixes[index]


# returns a string of readable time converted from seconds


def sec2time(sec):
    # Convert seconds to 'D days, HH:MM:SS'
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    pattern = r'%02d:%02d:%02d'
    if d == 0:
        return pattern % (h, m, s)

    return ('%d days, ' + pattern) % (d, h, m, s)


# converts two bytes to a signed int

def bytes2int(bytes):
    # if bytes[0] == 0:
    #     return int.from_bytes([bytes[1]], byteorder='big', signed = True)
    # else:
    return int.from_bytes([bytes[0], bytes[1]], byteorder='big', signed=True)


# This is a frame with fixed text on the left and variable text on the right


class SubframeLabel:
    def __init__(self, root, title, labels):
        self.frame_name = ttk.LabelFrame(root, text=title)

        for i in range(len(labels)):
            ttk.Label(self.frame_name, text=labels[i], style='Display.TLabel').grid(column=0, row=i, sticky=E)

        self.data_labels = []
        for i in range(len(labels)):
            self.data_labels.append(StringVar())
            ttk.Label(self.frame_name, textvariable=self.data_labels[i], style='Display.TLabel').grid(column=1, row=i, sticky=W)

    def pack(self):
        self.frame_name.pack(anchor=N, expand=1, fill=X)

    def update(self, value_strings):
        for i in range(len(value_strings)):
            self.data_labels[i].set(value_strings[i])


# This is a frame with variable text on both sides, with a known number of maximum lines


class SubframeVar:
    def __init__(self, root, title, num_lines):
        self.frame_name = ttk.LabelFrame(root, text=title)
        self.lines = num_lines

        self.data_labels_l = []
        for i in range(num_lines):
            self.data_labels_l.append(StringVar())
            ttk.Label(self.frame_name, textvariable=self.data_labels_l[i], style='Display.TLabel').grid(column=0, row=i, sticky=E)

        self.data_labels_r = []
        for i in range(num_lines):
            self.data_labels_r.append(StringVar())
            ttk.Label(self.frame_name, textvariable=self.data_labels_r[i], style='Display.TLabel').grid(column=1, row=i, sticky=W)

    def pack(self):
        self.frame_name.pack(anchor=N, expand=1, fill=X)

    def update(self, l_value_strings, r_value_strings):
        for i in range(self.lines):
            if i < len(l_value_strings):
                self.data_labels_l[i].set(l_value_strings[i])
            else:
                self.data_labels_l[i].set("")
        for i in range(self.lines):
            if i < len(r_value_strings):
                self.data_labels_r[i].set(r_value_strings[i])
            else:
                self.data_labels_r[i].set("")
