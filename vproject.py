#!/usr/bin/env python3
import curses
import textwrap
import project
project.to_colorize=False
#from strip_ansi import strip_ansi
LOG = open("/Users/sahill/Projects/ProjectViewer/LOG","w",buffering=1) #pylint: disable=consider-using-with
def log(text):
    LOG.write(str(text)+"\n")
    LOG.flush()
screen = curses.initscr()

class Listing:
    """The listing of projects on the left"""
    def __init__(self):
        self.window = curses.newwin(25, 40, 2, 0)
        self.mode = "path"
        self.cur_row = 0
        self.rows = []
        self.ymax = 0

    def cur_name(self):
        try:
            return self.rows[self.cur_row]
        except IndexError:
            return None
    
    def goto_name(self,name):
        i = self.rows.index(name)
        if i>=0:
            self.goto(i)
    def goto(self,row):
        self.update_row(self.cur_row, False)
        self.cur_row = row
        self.window.move(self.cur_row, 0)
        self.update_row(self.cur_row, True)
        details.show_description()
        self.window.move(self.cur_row, 0)
        self.window.refresh()

    def move_cursor(self,delta):
        new_row = min(self.ymax, max(0, self.cur_row + delta))
        self.goto(new_row)

    def update_row(self, num, highlight=False):
        self.window.move(num,0)
        self.window.clrtoeol()
        name = project.names(self.mode)[num]
        st = project.getstat(name)
        st = int(st) + 1
        if highlight: st += 4
        self.window.addstr(num, 0, name, curses.color_pair(st))

    def update(self):
        status_text = "Sorted "
        status_text += {"date": "by priority and last interaction",
                        "path": "by priority and path",
                        "alpha": "alphabetically",
                        "Alpha": "by priority and alphabetically",
                        }[self.mode]
        status.write(status_text)
        curname = self.cur_name()
        y = 0
        self.rows = project.names(self.mode)
        for name in self.rows: #FIX: replace with for y in range(len(self.rows))
            listing.update_row(y)
            y += 1
        listing.window.move(0,0)
        self.cur_row = 1
        self.ymax = y-1
        if curname:
            self.goto_name(curname)
        else:
            self.goto(0)
        details.show_description()
    def set_mode(self,mode):
        self.mode = mode
        self.update()
    def cycle_status(self):
        name = self.cur_name()
        stat = int(project.getstat(name))
        stat = (stat+1)%3
        project.cmd_status(name,stat)
        self.update()
        
class Status:
    """The status row"""
    def __init__(self):
        self.window = curses.newwin(1,40,1,0) #currently in second row
    def clear(self):
        self.window.move(0,0)
        self.window.clrtoeol()
        self.window.refresh()
    def write(self,text):
        self.clear()
        self.window.addstr(0,0,text)
        self.window.refresh()


class Details:
    """The details area on the right"""
    def __init__(self):
        self.window = curses.newwin(25,41,2,0)
    def write(self,text,color=None):
        output = textwrap.wrap(text, W-MID-1)
        #log("@@@")
        #log(f"{output}")
        #log("\n")
        output = '\n'.join(output)+'\n'
        if color is None:
            self.window.addstr(output)
        else:
            self.window.addstr(output, curses.color_pair(color))
        self.window.refresh()
    def clear(self):
        self.window.erase()
        self.window.move(0,0)
        self.window.refresh()
    def show_help(self):
        self.clear()
        self.write("COMMANDS")
        self.write("========")
        self.write("r: refresh listing")
        self.write("")
        self.write("t: sort by priority and time")
        self.write("p: sort by priority and path")
        self.write("a: sort alphabetically")
        self.write("A: sort by priority and by name")
        self.write("")
        self.write("T: open todo file")
        self.write("j: open terminal window")
        self.write("S: toggle status")
        
    def show_description(self):
        self.clear()
        name = listing.cur_name()
        #self.write(project.cmd_info(name))
        status = project.getstat(name)
        self.write(project.getfile(name, project.DESC), 8)
        self.write(project.project_dir(name),3)
        self.write("\n")
        text = project.gettodo(name, False).strip().split("\n")
        output = []
        for line in text: self.write(line)



listing = Listing()
status = Status()
details = Details()

def init_curses():
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
    screen.addstr(0,0,"PROJECT VIEWER")

init_curses()

#================================================================================

H = 0
W = 0
MID  = 0

def adjust_size():
    global H
    global W
    global MID
    H, W = screen.getmaxyx()
    MID = 20
    curses.resizeterm(H,W)
    status.window.resize(1,W)
    listing.window.resize(H-2,MID)
    details.window.resize(H-2, W-MID-1)
    details.window.mvwin(2, MID+1)
    for y in range(2,H-2):
        screen.addch(y,MID,"|")
    screen.refresh()
    listing.window.refresh()
    status.window.refresh()
    details.window.refresh()
    listing.update()


adjust_size()
listing.update()

while True:
    if curses.is_term_resized(H,W):
        adjust_size()
    k = screen.getch()
    c = chr(k)
    log(k)
    KEYUP = curses.KEY_UP
    KEYDOWN = curses.KEY_DOWN
    RETURN = 13
    ESCAPE = 27
    if c == 'q': break
    #MOTION
    if k == KEYUP: listing.move_cursor(-1)
    if k == KEYDOWN: listing.move_cursor(1)
    if c == 'r' or k == ESCAPE: listing.update()
    #SORTING
    if c == 't': listing.set_mode("date")
    if c == 'p': listing.set_mode("path")
    if c == 'a': listing.set_mode("alpha")
    if c == 'A': listing.set_mode("Alpha")

    if c == 'T': project.cmd_todo(listing.cur_name())
    if c == 'j' or k == RETURN:
        project.cmd_changedir(listing.cur_name())
    if c == 'S':
        listing.cycle_status()
        #cycle the status of the current item, then redraw screen
        pass
    if c == '?': details.show_help()

    #CHECK FOR ERRORS
    #MOVE
    #DELETE

curses.nocbreak()
screen.keypad(0)
curses.echo()
curses.endwin()
LOG.close()
