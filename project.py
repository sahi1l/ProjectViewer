#!/Usr/bin/env python3.10
"""Project Viewer"""
import sys
import os
import subprocess
import re
from glob import glob
from pathlib import Path #might be inconsistent to mix this with os.path
#I only use Path once, to access the touch command
from termcolor import colored
linkdir = os.path.expanduser("~") + "/.projectdirs" #this directory stores all the softlinks
to_colorize = True
def colorize(text,*args,**kwargs):
    if to_colorize:
        return colored(text, *args,**kwargs)
    else:
        return text
    
DESC = "@description.txt"
TODO = "TODO.todo"
STAT = "@status.txt"
STATUSES=["active","normal","shelved"]
SAMHILL = True #set this as False if you're not the author
MAC = True #only if you have a mac
EDITOR = "/opt/homebrew/bin/emacs" #or the path to your favorite command-line editor
def ProjectError(message):
    print(colorize(message,"red"))
    sys.exit()
#------------------------------------------------------------
def output(value):
    """Print value if interactive, otherwise return it"""
    if __name__ == "__main__":
        print(value)
        return None
    return value

def ask(prompt,ifnone):
    """Prompts for a result, returns a default response OR exits if no response is given"""
    try:
        result = input(colorize(prompt,"yellow",attrs=["bold"]))
        if result=='':
            if ifnone is None:
                raise EOFError
            return ifnone
        return result
    except (EOFError, KeyboardInterrupt):
        ProjectError("Never mind.")
#============================================================
#DATES
def getdate(name):
    """Gets the last modification time of the description file"""
    return int(os.path.getmtime(project_dir(name,DESC)))
#------------------------------------------------------------
def touch(name):
    """the date on the description file indicates which was last run"""
    Path(project_dir(name,DESC)).touch()
#============================================================
#NUMBERS AS NAMES
def getproject(name):
    """If a number is given as a project name, return the actual name instead"""
    if name.isnumeric():
        name = names("date")[int(name)]
    return name
#============================================================
#PROJECT FILES like DESC and STAT
#------------------------------------------------------------
def getfile(name,typ):
    """Return the content of a file within project"""
    fname = project_dir(name,typ)
    if os.path.exists(fname):
        with open(fname, "r") as F:
            return F.read().strip()
    else:
        return ""
#------------------------------------------------------------
def setfile(name,typ,val):
    """Write the content of a file within the project, like DESC or STAT"""
    with open(project_dir(name,typ),"w") as F:
        F.write(val)
#============================================================
#STATUSES
#------------------------------------------------------------
def getstat(name) -> str:
    """returns 0 (the highest), 1, or 2, as a string"""
    result=getfile(name,STAT).strip()
    if result=="":
        return "1"
    return str(STATUSES.index(result))
#============================================================
#SORTING
#------------------------------------------------------------
def get_mode(prams):
    """Translate the mode given in the command-line
    An 'a' returns None
    A 't' or 'd' returns date
    Anything else returns path
"""

    if len(prams)>0:
        if prams[0] == "a":
            return None
        if prams[0] in "td":
            return "date"
    return "path"

#============================================================
#NAME LISTS
#============================================================
class NameList:
    def __init__(self):
        pass
    #----------------------------------------
    def unsorted(self):
        os.chdir(linkdir)
        return list(filter(check_link, glob("*")))
    def path(self):
        def pathsort(name):
            """Sort by status, then by path name of the project itself"""
            return getstat(name)+project_dir(name)

        return sorted(self.unsorted(),
                      key=pathsort)
    def date(self):
        def date_sort(name):
            """Sort by status, and then by date (latest first)"""
            inverse_status = str(2-int(getstat(name)))
            return inverse_status + str(getdate(name))
        
        return sorted(self.unsorted(), key=date_sort, reverse=True)
    
    def alpha(self):
        alpha_sort = str.casefold
        return sorted(self.unsorted(), key=alpha_sort)
    def Alpha(self):
        def alpha_sort(name):
            return getstat(name) + str.casefold(name)
        return sorted(self.unsorted(), key=alpha_sort)
        
    def numbers(self):
        return {x[1]:x[0] for x in enumerate(self.date())}

name_list = NameList() #key=sortmode, value=name
#------------------------------------------------------------
def names(sort="date"):
    """return a particular name_list; generate it if not generated already"""
    #pylint: disable=global-statement
    global name_list
    global num_list
    return {"path": name_list.path,
            "date": name_list.date,
            "alpha": name_list.alpha,
            "Alpha": name_list.Alpha
            }[sort]()
#    if sort not in name_list:
#        os.chdir(linkdir)
#        unsorted_list = list(filter(check_link,glob("*")))
        #----------------------------------------
#        name_list = {x:unsorted_list[:] for x in ["path","date","alpha"]}
#        name_list["path"].sort(key=path_sort)
#        name_list["date"].sort(key=date_sort,reverse=True)
#        name_list["alpha"].sort(key=alpha_sort)
#        num_list = {x[1]:x[0] for x in enumerate(name_list["date"])}
#    return name_list[sort]
#============================================================

def project_link(name):
    """Return the location of the link in linkdir"""
    return os.path.join(linkdir,name)

def fixpath(path):
    """Normalizes a path name"""
    if isinstance(path,list): path=path[0]
    path = os.path.expanduser(path)
    path = os.path.realpath(path)
    #This next bit is for my own personal benefit
    if SAMHILL:
        path = path.replace("/Library/Mobile Documents/com~apple~CloudDocs/","/iCloud/")
    return path
def project_dir(name,sub=None):
    """Return the location of the project's directory, which the link points to"""
    path = project_link(name)
    if sub:
        path = os.path.join(path,sub)
    return fixpath(path)
#------------------------------------------------------------
def gettodo(name,color=True):
    #pylint: disable=anomalous-backslash-in-string
    """Search the TODO file for current items marked TODO """
    text = getfile(name,TODO).strip().split("\n")
    result = []
    laststarred = [] #last row that was starred at a certain rank. Key is number of stars
    for line in text:
        if line.strip()=="": continue
        nstars = len(re.match("\**",line).group(0))
        while len(laststarred)<nstars:
            laststarred += [""]
        laststarred[nstars:] = [line.strip()] #replace all
        if re.search("^\*.*TODO", line):
            for row in laststarred[1:]:
                if row.strip()=="": continue
                if color:
                    result += [colorize(row,"cyan")]
                else:
                    result += [row]
            laststarred=[""]

    return '\n'.join(result)

def prettyname(name,bold=False):
    """Return the project name for use in listing"""

    attrs=[]
    if bold: attrs=["bold","underline"]
    color = ["red", "white", "yellow"][int(getstat(name))]
    names()
    num = name_list.numbers()[name]
    return colorize(f'{num}. {name}', color,attrs=attrs)




#============================================================
def make_link(name,path,force=False):
    """Make a link in linkdir to path"""
    path = fixpath(path)
    symlink = project_link(name)
    if os.path.islink(symlink):
        if force:
            os.remove(symlink)
        else:
            ProjectError(f"{name} already exists.")
    if not os.path.isdir(path):
        ProjectError(f"{path} isn't a directory.")
    os.symlink(path, symlink)
        
#------------------------------------------------------------
def check_link(name):
    """Check if the link in linkdir actually points to anything"""
    link = project_link(name)
    return os.path.exists(link) and os.path.islink(link)
#------------------------------------------------------------
def add_project(name=None, path=".", description=""):
    """Add a project with the given parameters, called by cmd_add"""
    path = os.path.realpath(path)
    make_link(name,path)
    os.chdir(path)
    if description or not os.path.exists(DESC):
        with open(DESC,"w") as F:
            F.write(description)
    if not os.path.exists(TODO):
        with open(TODO, "w") as F:
            F.write("")
    return path

#============================================================
#COMMANDS
#------------------------------------------------------------
def cmd_short_list(mode=None,show_shelved=False):
    """Return a brief list of projects"""
    results = []
    for name in names(mode):
        if show_shelved or int(getstat(name))<2:
            results += [f"{prettyname(name)}: {getfile(name,DESC)}"]
    return output('\n'.join(results))

#------------------------------------------------------------
def cmd_info(name,interact=True):
    """Return the long-form info for project"""
    results = [f"{prettyname(name)}"]
    #FIX, includes path and date in a nice form
    results += [getfile(name,DESC)]
    results += [gettodo(name).strip(),"\n"]
    results = '\n'.join(results)
    if interact:
        return output(results)
    return results
#------------------------------------------------------------
def cmd_long_list(mode=None):
    """Return a list of projects with many details"""
    results = []
    for name in names(mode):
        results += [cmd_info(name,False)]
        #        results += [f"{prettyname(name)} ({getdate(name)})"]
        #        results += [getfile(name,DESC)]
        #        results += [gettodo(name).strip(),"\n"]
    return output('\n'.join(results))
#------------------------------------------------------------
def cmd_raw_list():
    """Return a list of project name and project path, to be used in recreating linkdir"""
    results = []
    for name in names():
        results += ['\t'.join([name,project_dir(name)])]
    return output('\n'.join(results))
#------------------------------------------------------------
def cmd_find_errors():
    """Find all errant files in linkdir"""
    os.chdir(linkdir)
    cnt = 0
    for name in glob("*"):
        link = project_link(name)
        exists = os.path.exists(link)
        islink = os.path.islink(link)
        if not exists and islink:
            output(f"{name} is a broken link.")
        elif exists and not islink:
            output(f"{name} is not a link.")
        elif not exists and not islink:
            output(f"{name} is weird...")
        else:
            cnt += 1
    output(f"{cnt} files are OK")
#------------------------------------------------------------
def cmd_add(project,path=None):
    """Add a new project, prompts for details"""
    if path:
        add_project(project,path,"")
    else:
        try:
            path = ask("Where will this project live? (.) ",".")
            description = ask("Describe your project.\n", "")
            path = add_project(project, path, description)
        except EOFError:
            output("Aborted.") #no return so ignored if not interactive
            sys.exit()
        os.chdir(path)
        if ask("Should I set up a git repository in this directory? ","n") != "n":
            subprocess.run(["git", "init"],check=False)
#============================================================
def cmd_changedir(name):
    """Open a new terminal window to the named project's folder"""
    os.chdir(linkdir)
    touch(name)
    tgt = project_dir(name)
    cmd = f'tell app "Terminal" to do script "cd \\\"{tgt}\\\" '
    if SAMHILL:
        cmd += f'&& ~/bin/changetitle @{name} && clear && echo {name.upper()}"'
    if MAC:
        subprocess.check_output(["osascript","-e",cmd],stderr=subprocess.DEVNULL)
    else:
        output("cd "+cmd_path(name))
#============================================================
def cmd_path(name):
    """Print the path of the named project's folder"""
    return output(project_dir(name))
#============================================================
def cmd_description(name, text=None):
    """Return or change a project's description"""
    desc = output(getfile(name,DESC))
    if text is None and desc is None: #interactive
        text = ask("Enter a new description:\n",None)
    if text:
        setfile(name, DESC, text)
        output("Description changed")
        return None
    return desc
#============================================================
def cmd_status(name, level=None):
    """Return or change a project's status"""
    output(f"Current status: {STATUSES[int(getstat(name))]}")
    if level is not None: level = str(level)
    if level is None or level[0] not in "ANSans012":
        while True:
            level = ask("Change the status? [ANS] ","")
            if level and level[0] in "ANSans012": break
    if level:
        if level.isnumeric():
            level = STATUSES[int(level)]
        if level.lower() in "ans":
            level = {x[0]:x for x in STATUSES}[level.lower()]
        if level in STATUSES:
            setfile(name, STAT, level)
            output(f"Status changed to {level}")
        else:
            output("Error: no status change")
#============================================================
def cmd_todo(name):
    """Open the TODO file for the project in an external editor"""
    #pylint: disable=consider-using-with
    touch(name)
    subprocess.Popen([EDITOR, project_dir(name,TODO)])

#============================================================
def cmd_delete(name):
    """Delete a project from linkdir (folder is still there)"""
    yn=ask(f"Should I delete the project {name}? ",None)
    if yn.lower() != 'n':
        path = project_link(name)
        output(f"OK, removing link to  {project_dir(name)}.")
        os.remove(path)
    else:
        output("Aborted.")
#============================================================
def cmd_move(name,path=None):
    """Change the path on a project"""
    if not path:
        path = ask("Where is the new location? ",None)
    make_link(name,path,force=True)
#============================================================
def cmd_is(path="."):
    """Return the name of path's project, if it is a project"""
    if not path: path="."
    if isinstance(path,list):
        path = path[0]
    path = fixpath(path)
    for name in names():
        if path == project_dir(name):
            return output(name)
    return None
#============================================================
def cmd_help():
    """Output a help message and exit"""
    class Text:
        """A temporary class to build up help text"""
        def __init__(self):
            self.text = ""
            self.col = "red"
        def color(self,col):
            """Change the current color"""
            self.col = col
        def add(self,first,second="",col=""):
            """Add text; first will be highlight in color, second will not"""
            if col: self.color(col)
            colon = ""
            if first and second:
                colon = ": "
            if "|" in first:
                first = first.split("|")
                self.text += colorize(first[0],self.col,attrs=["underline"])
                self.text += colorize(first[1],self.col)
            else:
                self.text += colorize(first,self.col)
            self.text += colon+second+"\n"
        def output(self):
            """Output the final text"""
            output(self.text)
    def code(text):
        return colorize(text,"yellow")
    text = Text()
    text.add("USAGE","project <command> ...")
    text.add("","     Many commands can be abbreviated to the underlined letters")
    text.add("GENERAL COMMANDS")
    text.add("ls -aplsr","list all projects")
    text.add("","  default sort is by status and then by date modified")
    text.add("  -a","sorted in alphabetical order by name")
    text.add("  -p","sorted by status and then path name")
    text.add("  -l","include many more details")
    text.add("  -s","include shelved projects")
    text.add("  -r","a simple list of project name and project directory")
    text.add("","  (note that the 'ls' can be omitted.")
    text.add("",f"  e.g. {code('project ls -psl')} or {code('project -psl')})")
    text.add("raw", "same as ls -r")
    text.add("help", "display this help")
    text.add("er|ror", "find broken links in the project list")
    text.add("is <directory>", "return the name of the project <directory> belongs to")
    text.add("PROJECT COMMANDS","","cyan")
    text.add("a|dd <name> <directory>","Add a new project named <name> for <directory>")
    text.add("cd <project>","Open a new terminal window in the project directory")
    text.add("pa|th <project>","Returns the path of <project>.")
    text.add("",f"     (Try {code('cd $(project path <project>)')} )")
    text.add("to|do <project>","Open the TODO.todo file for <project> in a text editor.")
    text.add("d|escription <path> <new>","View or change the <project>'s description")
    text.add("st|atus <project>","View or change the <project>'s status")
    text.add("","     (active, normal, or shelved)")
    text.add("mv <project_name> <dest>","Reassign <project_name> to <dest>")
    text.add("","     (the directory is not moved)")
    text.add("rm <project>","Removes <project> from the project list")
    text.add("","     (the directory is not deleted)")
    text.add("in|fo <project>","Show information about <project>")

    text.output()
#    project add <name> <folder> [description], will prompt for all three
#    project cd <project>
#    project description <project> [description]
#    project status <project> [status]
#    project todo <project>
#    project mv <project> <folder>
#    project del <project>
#    project ls
#    project LS
#    project list""")

#============================================================
#INTERACTIVE
#------------------------------------------------------------
def search_for_option(prams,starter):
    """Helper function, look through command-line arguments for a certain pattern"""
    result = list(filter(lambda x:x.startswith(starter),prams))
    if not result: return None
    return result
#------------------------------------------------------------
def pram_match(command,tomatch):
    """Return true if command startswith one of the strings in tomatch"""
    if isinstance(tomatch,str):
        tomatch = [tomatch]
    for match in tomatch:
        if command.startswith(match):
            return True
    return False

def general_commands(command,prams):
    """Commands that are not specific to one project name"""

    if command in ("ls","") or command.startswith("-"):
        sort_mode = "date"
        length = "short"
        shelved = False
        raw = False
        flags = ""
        for item in prams:
            if item.startswith("-"):
                flags += item[1:]
        if "a" in flags: sort_mode = "alpha"
        if "p" in flags: sort_mode = "path"
        if "l" in flags: length = "long"
        if "s" in flags: shelved = True
        if "r" in flags: raw = True
        if raw:
            cmd_raw_list()
        elif length == "long":
            cmd_long_list(sort_mode)
        else:
            cmd_short_list(sort_mode, show_shelved = shelved)
        return "DONE"

    if command == "raw":
        cmd_raw_list()
        return "DONE"

    if command == "help":
        cmd_help()
        return "DONE"

    if command.startswith("er"):
        cmd_find_errors()
        return "DONE"

    if command == "is":
        cmd_is(prams[:1])
        return "DONE"

    return ""

def specific_commands(command,project,details):
    """Commands for a specific project"""
    if pram_match(command,"a"): cmd_add(project,details)
    elif command == "cd": cmd_changedir(project)
    elif pram_match(command,"pa"): cmd_path(project)
    elif pram_match(command,["d"]): cmd_description(project,details)
    elif pram_match(command,["rm"]): cmd_delete(project)
    elif pram_match(command,["i"]): cmd_info(project)
    elif command == "mv": cmd_move(project,details)
    elif pram_match(command,"st"): cmd_status(project,details)
    elif pram_match(command,"to"): cmd_todo(project)

#------------------------------------------------------------
def interactive():
    """Run from the command-line"""
    command = sys.argv[1] if len(sys.argv)>1 else ""
    prams = sys.argv[1:]
    if not command.startswith("-"):
        prams = sys.argv[2:]
    if general_commands(command,prams) == "DONE":
        sys.exit()


    if len(prams)<1:
        while True:
            name = ask("Enter project name: ", None)
            if name == "?": #get a list of all projects
                cmd_short_list(None,True)
            else:
                break
    else:
        name = prams[0]

    project = getproject(name) #result is of type Project
    try:
        details = prams[1]
    except IndexError:
        details = None
    if pram_match(command,"pa"):
        #Don't output the name for these commands
        pass
    else:
        output(f"Project: {project}")

    specific_commands(command,project,details)

if __name__ == "__main__":
    interactive()
