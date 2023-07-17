#!/usr/bin/env python3
import sys
import os
import tkinter as tk
try:
    link = sys.argv[1]
except IndexError:
    print("Give me a link name"); exit()
if not os.path.islink(link):
    print(f"Give me a real link; I don't know {link}"); exit()
destination = os.path.realpath(link)
if os.path.exists(link):
    print("That link is fine."); exit()
def change():
    newdest = entry.get()
    print(newdest)
    if os.path.exists(newdest):
        temp = ".temp"
        os.symlink(newdest,temp)
        os.rename(temp,link)

root = tk.Tk()
label = tk.Label(root,text=link)
entry = tk.Entry(root,width=80)
entry.insert(0,destination)
button = tk.Button(root,text="Change",command=change)
label.pack(anchor="w")
entry.pack(anchor="w")
button.pack(anchor="w")
entry.focus()
root.mainloop()
