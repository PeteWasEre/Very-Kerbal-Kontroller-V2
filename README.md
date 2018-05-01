# Very-Kerbal-Kontroller-V2
The return of the controller!

This repository is a place for me to keep and share my code, designs and data for my custom KSP Control Panel.

The VKK had a few issues that meant it wasnt often used:
1. It was physically too big, which made it a pain to setup on the desk
2. The use of seperate power and USB made it even more of a hassle
3. The python end was pretty and getting prettier but:
	a. All the stream data from KSP slowed KSP down (which on my new gaming rig was a NO!)
	b. Most it just repeated onscreen data I can get in MJ, KER or other mods
4. The slow frame rate (caused by the python end mostly) made some controls like camera unusable
5. Some controls were not well thought out. For example, have the camera selector as a rotory switch was a pain as 
   not every mode is always available.
5. I got behind KRPC and KSP versions so the connection was flaky and needed a rebuild anyway

So this project is to apply some lessons learned and rebuild the panel to be much more usable.

The design brief is:
1. A much smaller panel, less than A3 size
2. Works off a single USB, or at worst a data and power USB connecter. That is, 5V supply only!
3. Reorganise some controls for better usability
4. Make the python end a connector only, no output.

The physical changes are mostly done (waiting on a few switches and LED surrounds), now its time to code!

The contents are:

1. Arduino Code - The modules that run on the Arduino Mega 2560
2. Documentation - Design document (still to be done), schematics (TinyCad and PDF) and general design stuff - TO BE UPDATED
3. Panel Graphics - The printed graphics used on the panels. Open Office Draw and MS Word formats - DONE
4. Python Code - The python module that runs at the PC end of the link

Although this stuff is all specific to my build it should be pretty easy to adapt to any other applications. 
If it helps you then please use it. If it doesnt make sense, ask as i probably screwed up. 

Note: The python code is very WIP and I am NOT a python expert, or even moderately knowledgable. 
It works, but i dont always know how. Clean ups will follow.
