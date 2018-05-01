from multiprocessing import Queue, Array
import ctypes
from tkinter import Tk
from Settings import *

from GUI import Application

# Define the shared data between the processes
msgq = Queue(0)
data_array = Array(ctypes.c_ubyte, c_input_buffer_size+2)

if __name__ == '__main__':
    # Create the root window
    root = Tk()
    root.title('VKK-V2')
    root.configure(background="black")
    root.geometry('{0}x{1}'.format(c_screen_size_x, c_screen_size_y)+c_screen_pos)

    # Instantiate the GUI
    app = Application(root, data_array, msgq)

    # Run the main GUI loop
    Tk.mainloop(root)
