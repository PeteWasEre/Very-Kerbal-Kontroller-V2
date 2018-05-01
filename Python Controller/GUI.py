from tkinter import *
from tkinter import ttk
from multiprocessing import Process
from time import time

from Settings import *
from PanelControl import panel_control
from Utilities import SubframeLabel


class Application:
    def __init__(self, root, data_array, msgq):

        # Define Styles
        self.styles = ttk.Style()
        self.styles.configure('Display.TLabel', font=('helvetica', '18'), padding=(10, 0), background='black',
                              foreground='blue')
        self.styles.configure('Msg.TLabel', font=('helvetica', '12'), padding=(10, 0), background='black',
                              foreground='blue')
        self.styles.configure('Ind.TLabel', font=('helvetica', '16', 'bold'), padding=(10, 0), relief='raised',
                              anchor='center')
        self.styles.configure('TLabelframe.Label', font=('helvetica', '24', 'bold'), background='black')
        self.styles.configure('TLabelframe', background='black')
        self.styles.configure('TFrame', background='black')
        self.styles.configure('TButton', font=('helvetica', '16', 'bold'))

        # Build the Upper area for the messages and buttons
        upperframe = ttk.Frame(root)

        # Build the Message box with four data lines
        self.msgframe = ttk.LabelFrame(upperframe, text='Status Messages')

        self.msgL1 = StringVar()
        self.msgL2 = StringVar()
        self.msgL3 = StringVar()
        self.msgL4 = StringVar()

        self.msg1 = ttk.Label(self.msgframe, style='Msg.TLabel', textvariable=self.msgL1).pack(anchor=W)
        self.msg2 = ttk.Label(self.msgframe, style='Msg.TLabel', textvariable=self.msgL2).pack(anchor=W)
        self.msg3 = ttk.Label(self.msgframe, style='Msg.TLabel', textvariable=self.msgL3).pack(anchor=W)
        self.msg4 = ttk.Label(self.msgframe, style='Msg.TLabel', textvariable=self.msgL4).pack(anchor=W)

        self.msgframe.pack(side=LEFT, expand=1, fill=BOTH, padx=5, pady=5)

        # Once the Upper area is complete, pack it in
        upperframe.pack(expand=1, fill=BOTH, padx=5, pady=5)

        # Define the low maintenance frame and its sub frames.

        self.T9L = ttk.Frame(root)
        self.T9R = ttk.Frame(root)

        self.T9_DI = SubframeLabel(self.T9R, 'Digital Inputs', (
            'Arduino Pins:', 'MUX 0 Bank A:', 'MUX 0 Bank B:', 'MUX 1 Bank A:', 'MUX 1 Bank B:',
            'MUX 2 Bank A:', 'MUX 2 Bank B:', 'MUX 3 Bank B:', 'MUX 4 Bank B:'))
        self.T9_DI.pack()

        # Buttons
        self.panel_status = StringVar()
        self.panel_button = StringVar()
        self.panel_status.set("Disconnected")
        self.panel_button.set("Connect Panel")

        self.buttonframe = ttk.LabelFrame(self.T9R, text='Controls')

        ttk.Button(self.buttonframe, textvariable=self.panel_button,
                   command=lambda: self.connect_panel(data_array, msgq), width=25).grid(
            column=1, row=0, padx=5, pady=3)
        self.panel_status_button = ttk.Label(self.buttonframe, textvariable=self.panel_status, width=22,
                                             style='Ind.TLabel', relief='raised').grid(
            column=1, row=1, padx=4, pady=6, ipady = 3)
        ttk.Button(self.buttonframe, text='Exit',
                   command=lambda: self.exit(root, data_array, msgq), width=10).grid(
            column=2, row=0, rowspan = 2, padx=15, pady=3, ipady = 20)

        self.buttonframe.pack(anchor=N, expand=1, fill=X)

        self.T9_ST = SubframeLabel(self.T9L, 'Status', (
            'Status Byte:', 'Temperature:', 'GUI Frame Rate:', 'Panel SW Frame Rate:', 'Arduino Frame Rate:'))
        self.T9_ST.pack()

        self.T9_AI = SubframeLabel(self.T9L, 'Analogue Inputs',
                                   ('Rotation X:', 'Rotation Y:', 'Rotation Z:', 'Translation X:', 'Translation Y:',
                                    'Translation Z:', 'Throttle:'))
        self.T9_AI.pack()

        self.T9L.pack(anchor=N, side=LEFT, expand=1, fill=X, padx=5)
        self.T9R.pack(anchor=N, side=RIGHT, expand=1, fill=X, padx=5)

        # Initialise connection attributes
        self.panel_proc = None

        # initialise attributes that require a state
        self.panel_connected = False
        self.game_connected = False
        self.vessel_connected = False
        self.maintapp_visible = False
        self.last_frame_time = 0
        self.frame_time = 0
        self.status_prev = 0
        self.discon_counter = 0

        # Create a welcome message
        self.msgL4.set("Welcome to the Very Kerbal Kontroller - V2 Edition!")

        # trigger the first update
        self.update(data_array, msgq)

    def update(self, data_array, msgq):
        # Update message area
        if not msgq.empty():
            m = msgq.get()
            self.msgL1.set(self.msgL2.get())
            self.msgL2.set(self.msgL3.get())
            self.msgL3.set(self.msgL4.get())
            self.msgL4.set(msg_prefix[m[0]] + ': ' + m[1])

        self.last_frame_time = self.frame_time
        self.frame_time = time()

        temp = ['{0:08b}'.format(data_array[0]),
                '{0:.0f}deg'.format(data_array[10] * 0.69310345 - 68.0241379),
                '{:d}ms'.format(int((self.frame_time - self.last_frame_time)*1000)),
                '{:d}ms'.format(data_array[19]),
                '{:d}ms'.format(data_array[18])]
        self.T9_ST.update(temp)

        # Digital Data SubframeLabel
        temp = ['{0:08b}'.format(data_array[1]),
                '{0:08b}'.format(data_array[2]),
                '{0:08b}'.format(data_array[3]),
                '{0:08b}'.format(data_array[4]),
                '{0:08b}'.format(data_array[5]),
                '{0:08b}'.format(data_array[6]),
                '{0:08b}'.format(data_array[7]),
                '{0:08b}'.format(data_array[8]),
                '{0:08b}'.format(data_array[9])
                ]
        self.T9_DI.update(temp)

        # Analogue Data SubframeLabel
        temp = [data_array[11],
                data_array[12],
                data_array[13],
                data_array[14],
                data_array[15],
                data_array[16],
                data_array[17]]
        self.T9_AI.update(temp)

        # Test and update the panel connection
        if self.panel_connected:
            if data_array[0] == 0:  # Status byte is 0 when disconnected, so will remain 0 till connection complete
                self.panel_status.set("Connecting")
                self.styles.configure('Ind.TLabel', background='blue')
                self.panel_button.set("Disconnect Panel")
            else:  # if there is a valid status bit, we must be connected
                self.panel_status.set("Connected")
                self.styles.configure('Ind.TLabel', background='green')
                if data_array[0] == self.status_prev:  # if the heartbeat is not increase, start a counter
                    self.discon_counter = self.discon_counter + 1
                else:  # if it is increasing, reset the counter
                    self.discon_counter = 0

                if self.discon_counter >= 20:  # if the counter exceed the limit, trigger the disconnect.
                    self.connect_panel(data_array, msgq)

            self.status_prev = data_array[0]  # keep the previous status byte for comparison.
        else:
            self.discon_counter = 0

        self.msgframe.after(50, self.update, data_array, msgq)

    def connect_panel(self, data_array, msgq):
        if self.panel_connected == FALSE:
            # Start the panel controller module
            self.panel_proc = Process(target=panel_control, args=(data_array, msgq))
            self.panel_proc.start()
            self.panel_connected = True
        else:
            self.panel_proc.terminate()
            self.panel_connected = False
            data_array[0] = 0
            self.panel_status.set("Disconnected")
            self.styles.configure('Ind.TLabel', background='light grey')
            self.panel_button.set("Connect Panel")

    def exit(self, root, data_array, msgq):
        if self.panel_connected:
            self.connect_panel(data_array, msgq)
        root.destroy()
        quit()
