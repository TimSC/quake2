
Porting the Quake 2 engine to python. This is just an experiment and may
never be completed.

The code is all licensed under the terms of the GPL (gnu public license).
You should read the entire license, but the gist of it is that you can do 
anything you want with the code, including sell your new version.  The catch 
is that if you distribute new binary versions, you are required to make the 
entire source code available for free to everyone.

All of the Q2 data files remain copyrighted and licensed under the 
original terms, so you cannot redistribute data from the original game, but if 
you do a true total conversion, you can create a standalone game based on 
this code.

   pip3 install -r requirements.txt

   python3 setup.py build_ext --inplace

   python3 main.py +set basedir /path/to/quake2data/Data

