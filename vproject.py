#!/usr/bin/env python3
"""This is the curses version of the project program"""
#pylint: disable=invalid-name
import os
import curses
import textwrap
import project
project.to_colorize=False
#from strip_ansi import strip_ansi
LOG = open("/Users/sahill/Projects/ProjectViewer/LOG","w",buffering=1) #pylint: disable=consider-using-with

def getcolor(st,highlight):
    """Given the status and highlighting of a row, return the right color"""
    cp = int(st)+1
    if highlight: cp += 4
    return curses.color_pair(cp)

def DONE():
    """Reset curses before we end"""
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()
    LOG.close()


def log(text):
    """Output text to the log file"""
    LOG.write(str(text)+"\n")
    LOG.flush()


class Items:
    """Keeps tracks of the items in the listing, separately of the graphics"""
    #FIX: when mode changed, probably need to re-sort, eh?
    def __init__(self):
        self.mode = "path"
        self.rows = [] #list of items
        self.current = None
    def get(self,idx):
        """Return the name in row idx, if it exists"""
        if self.inbounds(idx):
            try:
                return self.rows[idx]
            except IndexError:
                pass
        return None
    def inbounds(self,idx):
        """Is this index in the range of allowed values?"""
        return 0<=idx<len(self.rows)

    def normalize(self,idx):
        """If it isn't in the right range, fix it"""
        if idx is None: idx = 0
        if idx<0: idx=0
        elif idx>=len(self.rows): idx=len(self.rows)-1
        return idx

    def shift(self,delta):
        """Shift the current value by delta"""
        self.current = self.normalize(self.current+delta)

    def setcurrent(self,idx):
        """Set the current item to idx"""
        if type(idx) == int:
            self.current = self.normalize(idx)
        elif type(idx) == str:
            try:
                self.current = self.rows.index(idx)
            except ValueError:
                pass
                
    def curname(self):
        """Get the currently selected name"""
        if self.current is not None:
            return self.rows[self.current]
        return ""
    def update(self):
        """Populate the list of names, given the current mode"""
        oldcur = self.curname()
        self.rows = project.names(self.mode)
        try:
            self.current = self.rows.index(oldcur)
        except ValueError:
            self.current = 0


class Listing:
    """The listing of projects on the left"""
    def __init__(self):
        self.window = curses.newwin(self.Nrows()+2, 40, 2, 0)
        self.cur_row = 0
        self.items = Items()
        self.ymax = 0
        self.start = 0 #where on the list to start
    def Nrows(self):
        """Return the number of available rows"""
        return os.get_terminal_size().lines - 2

    def visible(self,item):
        """Is this item visible on screen?"""
        return self.inbounds(item-self.start)

    def inbounds(self,row):
        """Is this row visible on screen?"""
        if row < 0 : return False
        if row >= self.Nrows(): return False
        return True
    def item2row(self,item):
        """Convert item number to row number"""
        return item - self.start
    def row2item(self,row):
        """Convert row number to item number"""
        return row + self.start
    def make_visible(self,item):
        """Adjust self.start so that item is in range; returns True if it needed to adjust"""
        middle = self.Nrows()//2
        if item < self.start: #too far up?
            if item < middle:
                self.start = 0
            else:
                self.start = item - middle  #move it to the top of the list
            return True
        if item >= self.Nrows() + self.start: #too far down
            self.start = item - middle #move item to middle of page
            return True
        return False

    def move(self,item): #move cursor to a particular row, but why?
        """Move cursor to a particular item, scrolling if necessary"""
        #two uses move to the current row
        #update_row takes the name of a row
        refresh = self.make_visible(item)
        self.window.move(self.item2row(item),0)
        return refresh

    def set_current(self):
        """This can be run multiple times without messing anything up"""
        item = self.items.normalize(self.items.current) #the target item
        refreshQ = self.make_visible(item)
        self.cur_row = self.item2row(item)
        details.show_description()
        self.window.move(self.cur_row,0) #goto the row after writing description
        self.update_row(self.cur_row,True)
        if refreshQ: self.update()
        self.window.refresh()

    def move_cursor(self,delta):
        """Move the cursor with step delta through items, and adjust the screen accordingly"""
        self.update_row(self.cur_row, False) #Remove highlight the current row
        self.items.shift(delta)
        self.make_visible(self.items.current) #make sure it is on the screen
        self.set_current()
        self.update()


    def update_row(self, row, highlight=False):
        """Write the given row with the correct color and highlighting"""
        if not self.inbounds(row): return #don't update it if we can't see it!
        self.window.move(row,0) #move to the specified row
        self.window.clrtoeol() #clear it
        name = self.items.get(self.row2item(row))
        st = project.getstat(name) #status of name, converted to a color pair
        if self.inbounds(row) and name is not None:
            self.window.addstr(row, 0, name, getcolor(st,highlight))

    def update(self):
        """Update the listing"""
        status_text = "Sorted "
        status_text += {"date": "by priority and last interaction",
                        "path": "by priority and path",
                        "alpha": "alphabetically",
                        "Alpha": "by priority and alphabetically",
                        }[self.items.mode]
        status.write(status_text)
        #        curname = self.items.curname()
        self.items.update()
        for row in range(0,self.Nrows()):
            self.update_row(row)
        self.window.move(0,0)
        self.set_current()

    def set_mode(self,mode):
        """Set the mode of the display, and update"""
        self.items.mode = mode
        self.update()

    def cycle_status(self):
        """Adjust the current item to the next status, and refresh the screen"""
        #FIX? What happens if it ends up offscreen?
        name = self.items.curname()
        stat = int(project.getstat(name))
        stat = (stat+1)%3
        project.cmd_status(name,stat)
        self.items.update()
        self.items.setcurrent(name)
        self.update()

class Status:
    """The status row"""
    def __init__(self):
        self.window = curses.newwin(1,40,1,0) #currently in second row
    def clear(self):
        """Clear the status"""
        self.window.move(0,0)
        self.window.clrtoeol()
        self.window.refresh()
    def write(self,text):
        """Write out the status"""
        self.clear()
        self.window.addstr(0,0,text)
        self.window.refresh()


class Details:
    """The details area on the right"""
    def __init__(self):
        self.window = curses.newwin(25,41,2,0)
    def write(self,text,color=None):
        """Write a line to Details"""
        output = textwrap.wrap(text, mywindow.W - mywindow.MID - 1)
        output = '\n'.join(output)+'\n'
        if color is None:
            self.window.addstr(output)
        else:
            self.window.addstr(output, curses.color_pair(color))
        self.window.refresh()
    def clear(self):
        """Clear the Details window"""
        self.window.erase()
        self.window.move(0,0)
        self.window.refresh()
    def show_help(self):
        """Show a help message in Details"""
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
        """Display the description of the current item"""
        self.clear()
        name = listing.items.curname()
        if not name: return
        #self.write(project.cmd_info(name))
        #stat = project.getstat(name) #FIX: Not used
        self.write(project.getfile(name, project.DESC), 8)
        self.write(project.project_dir(name),3)
        self.write("\n")
        text = project.gettodo(name, False).strip().split("\n")
        #output = []
        for line in text: self.write(line)




def init_curses():
    """Initialize curses"""
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


#================================================================================

#FIX: Make adjust-size a class?

class Screen:
    """Keeps track of the screen size"""
    def __init__(self):
        self.H,self.W = screen.getmaxyx()
        self.MID = 20
    def adjust(self):
        """Adjust the size of all the subwindows"""
        self.H,self.W = screen.getmaxyx()
        curses.resizeterm(self.H,self.W)
        status.window.resize(1,self.W)
        listing.window.resize(self.H-2,self.MID)
        details.window.resize(self.H-2, self.W-self.MID-1)
        details.window.mvwin(2, self.MID+1)
        for y in range(2,self.H-2):
            screen.addch(y,self.MID,"|")
        screen.refresh()
        listing.window.refresh()
        status.window.refresh()
        details.window.refresh()
        listing.update()
    def check(self):
        """Check if the window has been resized, if so, adjust"""
        if curses.is_term_resized(self.H,self.W):
            self.adjust()

#============================================================
screen = curses.initscr()
init_curses()
status = Status()
listing = Listing()
mywindow = {"W":0,"H":0,"MID":0}
details = Details()
mywindow = Screen()
listing.update()
mywindow.adjust()

while True:
    mywindow.check()
    k = screen.getch()
    if k>=0: c = chr(k)
    else: c=''
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

    if c == 'T': project.cmd_todo(listing.items.curname())
    if c == 'j' or k == RETURN:
        project.cmd_changedir(listing.items.curname())
    if c == 'S':
        listing.cycle_status()
        #cycle the status of the current item, then redraw screen

    if c == '?': details.show_help()

    #CHECK FOR ERRORS
    #MOVE
    #DELETE

DONE()
