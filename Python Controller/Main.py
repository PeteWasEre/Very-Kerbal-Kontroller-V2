from multiprocessing import Process, Queue, Array
from tkinter import Tk
import ctypes
from time import sleep, time
from Settings import *


from GUI import Application

# Define the shared data between the processes
msgQ = Queue(0)
data_array = Array(ctypes.c_ubyte, 50)

if __name__ == '__main__':
    # Create the root window
    root = Tk()
    root.title('KSP Controller')
    root.configure(background = "black")
    root.geometry('{0}x{1}'.format(c_screen_size_x,c_screen_size_y) + c_screen_pos)

    # Instatiate the GUI
    app = Application(root, data_array, msgQ)

    stage_prev = None
    frame_time = time()

    # Loop the window, calling an update then refreshing the window
    while 1:
        if time() > frame_time + 0.250:
            frame_time = time()

            if app.game_connected == False or app.vessel_connected == False:
                app.connect(msgQ)
            elif app.conn.krpc.current_game_scene == app.conn.krpc.current_game_scene.flight:
                if app.vessel.control.current_stage is not stage_prev:
                    app.update_streams()
                stage_prev = app.vessel.control.current_stage
                app.update(data_array, msgQ)

            root.update()
            root.update_idletasks()

            frame_delta = time() - frame_time
            if frame_delta > 0.25:
                print ('{0:0f}ms'.format(frame_delta*1000))
