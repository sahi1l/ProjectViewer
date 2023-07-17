#!/usr/bin/env python3.10
import project
import curses
import textwrap
LOG = open("/Users/sahill/Projects/ProjectViewer/LOG","w",buffering=1)

#import curses.wrapper #figure this out eventually
screen = curses.initscr()
#listing = screen
listing = curses.newwin(25, 40, 2, 0)
Wstatus = curses.newwin(1,40,1,0) #currently in second row
Wdesc = curses.newwin(25,41,2,0)
curses.start_color()
curses.init_pair(1,curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2,curses.COLOR_WHITE, curses.COLOR_BLACK)
curses.init_pair(3,curses.COLOR_YELLOW, curses.COLOR_BLACK)
curses.init_pair(5,curses.COLOR_BLACK, curses.COLOR_RED)
curses.init_pair(6,curses.COLOR_BLACK, curses.COLOR_WHITE)
curses.init_pair(7,curses.COLOR_BLACK, curses.COLOR_YELLOW)
curses.init_pair(8,curses.COLOR_WHITE, curses.COLOR_BLUE)
curses.noecho()
curses.cbreak()
screen.keypad(1)
screen.refresh()

rows = []
mode = "path"
H = 0
W = 0
MID  = 0
cur_row = 0
screen.addstr(0,0,"PROJECT VIEWER")
def adjust_size():
    global H
    global W
    global MID
    H, W = screen.getmaxyx()
    MID = 20
    curses.resizeterm(H,W)
    Wstatus.resize(1,W)
    listing.resize(H-2,MID)
    Wdesc.resize(H-2, W-MID-1)
    Wdesc.mvwin(2, MID+1)
    for y in range(2,H-2):
        screen.addch(y,MID,"|")
    screen.refresh()
    listing.refresh()
    Wstatus.refresh()
    Wdesc.refresh()
    display()

def display_desc():
    Wdesc.erase()
    name = cur_name()
    text = project.getfile(name, project.DESC)
    output = textwrap.wrap(text, W-MID-1)
    Wdesc.addstr(0,0,'\n'.join(output), curses.color_pair(8))
    Wdesc.addstr('\n')
    text = project.gettodo(name, False).strip().split("\n")
    output = []
    for line in text:
        output += textwrap.wrap(line, W-MID-1)
#    text = textwrap.wrap(project.getfile(name,project.DESC),W-MID-1)
    Wdesc.addstr('\n'.join(output))
    Wdesc.refresh()

def display_row(num, highlight=False):
    listing.move(num,0)
    listing.clrtoeol()
    name = project.names(mode)[num]
    st = project.getstat(name)
    st = int(st) + 1
    if highlight:
        st += 4
    listing.addstr(num, 0, name, curses.color_pair(st))
    
def display():
    global rows
    global cur_row
    global ymax
    Wstatus.move(0,0)
    Wstatus.clrtoeol()
    if mode == "date":
        Wstatus.addstr(0,0,"Sorted by last interaction")
    elif mode == "path":
        Wstatus.addstr(0,0,"Sorted by priority")
    elif mode == None:
        Wstatus.addstr(0,0,"Sorted alphabetically")
    Wstatus.refresh()
    listing.erase()
    
    curname = cur_name()
    y = 0 #current row
    rows = project.names(mode)
    for name in rows:
        display_row(y)
        y += 1
#        st = project.getstat(name)
#        listing.addstr(y, 0, name, curses.color_pair(int(st)+1))
    listing.move(0,0)
    cur_row = 1
    ymax = y-1
    if curname:
        goto_name(curname)
    else:
        goto(0)
    display_desc()
def cur_name():
    try:
        return rows[cur_row]
    except IndexError:
        return None

def goto_name(name):
    i = rows.index(name) #0 based
    if i>=0:
        goto(i)

def goto(row):
    global cur_row
    display_row(cur_row, False)
    cur_row = row
    listing.move(cur_row, 0)
    display_row(cur_row, True)
    display_desc()
    listing.move(cur_row, 0)
#    screen.refresh()
    listing.refresh()
    
def move_cursor(delta):
    new_row = min(ymax, max(0, cur_row + delta) )
    goto(new_row)

adjust_size()
display()
while True:
    if curses.is_term_resized(H,W):
        adjust_size()
    c = screen.getch()
    if c == ord('q'): break
    #MOTION
    if c == curses.KEY_UP:
        move_cursor(-1)
    if c == curses.KEY_DOWN:
        move_cursor(1)
    if c == ord('r'):
        display()
    #SORTING
    if c == ord('t'):
        mode = "date"
        display()
    if c == ord('p'):
        mode = "path"
        display()
    if c == ord('a'):
        mode = None
        display()
    
    if c == ord('T'):
        project.open_todo(cur_name())
    if c == ord('j') or c==13:
        project.change_dir(cur_name())
    if c == ord('S'):
        #cycle the status of the current item, then redraw screen
        pass

    

curses.nocbreak()
screen.keypad(0)
curses.echo()
curses.endwin()
LOG.close()
