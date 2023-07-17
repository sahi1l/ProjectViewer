#!/usr/bin/env python3.10
"""Project"""
import sys
import os
import subprocess
import re
from glob import glob
from pathlib import Path
from termcolor import colored
maindir = os.path.expanduser("~") + "/.projectdirs"
DESC = "@description.txt"
TODO = "TODO.todo"
STAT = "@status.txt"
statuses=["active","normal","shelved"]
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
        result = input(colored(prompt,"yellow",attrs=["bold"]))
        if result=='':
            if ifnone is None:
                raise EOFError
            return ifnone
        return result
    except (EOFError, KeyboardInterrupt):
        output("Aborted.")
        sys.exit()
#============================================================
#DATES
def getdate(name):
    """Gets the last modification time of the description file"""
    return int(os.path.getmtime(link(name,DESC)))
#------------------------------------------------------------
def touch(name):
    """the date on the description file indicates which was last run"""
    Path(link(name,DESC)).touch()
#------------------------------------------------------------
def numlist():
    """list of projects sorted by status and access time"""
    return names("date")
#============================================================
#NUMBERS AS NAMES
def getname(name):
    """If a number is given as a project name, return the actual name instead"""
    if name.isnumeric():
        return numlist()[int(name)]
    return name
#============================================================
#PROJECT FILES like DESC and STAT
#------------------------------------------------------------
def getfile(name,typ):
    """Return the content of a file within project"""
    fname = link(name,typ)
    if os.path.exists(fname):
        with open(fname, "r") as F:
            return F.read().strip()
    else:
        return ""
#------------------------------------------------------------
def setfile(name,typ,val):
    """Write the content of a file within the project, like DESC or STAT"""
    with open(link(name,typ),"w") as F:
        F.write(val)
#============================================================
#STATUSES
#------------------------------------------------------------
def getstat(name) -> str:
    """returns 0 (the highest), 1, or 2, as a string"""
    result=getfile(name,STAT).strip()
    if result=="":
        return "1"
    return str(statuses.index(result))
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


def names(sort="alpha"):
    """Return a list of project names, sorted"""
    os.chdir(maindir)

    result = list(filter(lambda x:os.path.exists(x) and os.path.islink(x),glob("*")))

    def inv_status(K):
        return str(2-int(getstat(K)))

    if sort=="path": #sort by status, then path
        result.sort(key=lambda K:inv_status(K)+link(K,real=True), reverse=True)
    elif sort=="date":
        result.sort(key=lambda K:inv_status(K)+str(getdate(K)),reverse=True)
    else:
        result.sort(key=str.casefold)
    return result

def icloud(path):
    """Fix the path to point directly to ~/iCloud"""
    return path.replace("/Library/Mobile Documents/com~apple~CloudDocs/","/iCloud/")

def link(name,sub=None,real=False):
    """Return the link to a project directory or subdirectory"""
    path = os.path.join(maindir,name)
    if sub:
        path = os.path.join(path,sub)
    if real:
        return icloud(os.path.realpath(path))
    return path

#------------------------------------------------------------
def gettodo(name,color=True):
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
                    result += [colored(row,"cyan")]
                else:
                    result += [row]
            laststarred=[""]

    return '\n'.join(result)

def prettyname(name,bold=False):
    """Return the project name for use in listing"""
    NL = numlist()
    attrs=[]
    if bold: attrs=["bold","underline"]
    color = ["red", "white", "yellow"][int(getstat(name))]
    return colored(f'{NL.index(name)}. {name}', color,attrs=attrs)


class ProjectError(Exception):
    """Errors called due to usage, not code"""
    #FIX: Make this output something?


#============================================================
def make_link(name,path,force=False):
    """Make a link in maindir to path"""
    path = os.path.realpath(path)
    if os.path.exists(link(name)):
        if force:
            os.remove(link(name))
        else:
            raise ProjectError(f"{name} already exists.")
    if not os.path.isdir(path):
        raise ProjectError(f"{path} isn't a directory.")
    os.symlink(path, link(name))


def add_project(name=None, path=".", description=""):
    """Add a project with the given parameters, called by cmd_add"""
    make_link(name,path)
    path = os.path.realpath(path)
    os.chdir(path)
    if description or not os.path.exists(DESC):
        with open(DESC,"w") as F:
            F.write(description)
    if not os.path.exists(TODO):
        with open(TODO, "w") as F:
            F.write("")


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
def cmd_long_list(mode=None):
    """Return a list of projects with many details"""
    results = []
    for name in names(mode):
        results += [prettyname(name)]
        results += [getfile(name,DESC)]
        results += [gettodo(name).strip(),"\n"]
    return output('\n'.join(results))
#------------------------------------------------------------
def cmd_add(name):
    """Add a new project, prompts for details"""
    try:
        path = ask("Where will this project live? (.) ",".")
        description = ask("Describe your project.\n", "")
        add_project(name, path, description)
    except EOFError:
        output("Aborted.") #no return so ignored if not interactive
        sys.exit()
#============================================================
def cmd_changedir(name):
    """Open a new terminal window to the named project's folder"""
    os.chdir(maindir)
    touch(name)
    tgt = icloud(os.path.realpath(link(name)))
    cmd = f'tell app "Terminal" to do script "cd \\\"{tgt}\\\" && ~/bin/changetitle @{name} && clear && echo {name.upper()}"'
    subprocess.check_output(["osascript","-e",cmd],stderr=subprocess.DEVNULL)
#============================================================
def cmd_path(name):
    """Print the path of the named project's folder"""
    return output(icloud(os.path.realpath(link(name))))
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
    output(f"Current status: {statuses[int(getstat(name))]}")
    if not level or level[0] not in "ANSans":
        while True:
            level = ask("Change the status? [ANS] ","")
            if level and level[0] in "ANSans": break
    if level:
        if level.isnumeric():
            level = statuses[int(level)]
        if level.lower() in "ans":
            level = {x[0]:x for x in statuses}[level.lower()]
        if level in statuses:
            setfile(name, STAT, level)
            output(f"Status changed to {level}")
        else:
            output("Error: no status change")
#============================================================
def cmd_todo(name):
    """Open the TODO file for the project in an external editor"""
    touch(name)
#    emacs = "/usr/local/bin/aquamacs"
    emacs = "/opt/homebrew/bin/emacs"
    subprocess.check_output([emacs, link(name,TODO)],
                                stderr = subprocess.DEVNULL)
#============================================================
def cmd_delete(name):
    """Delete a project from maindir (folder is still there)"""
    ask(f"Should I delete the project {name}? ",None)
    path = os.path.join(maindir,name)
    output(f"OK, removing link to  {link(name,None,True)}.")
    os.remove(path)
#============================================================
def cmd_move(name,path=None):
    """Change the path on a project"""
    if not path:
        path = ask("Where is the new location? ",None)
    make_link(name,path,force=True)
#============================================================

def cmd_help():
    """Output a help message and exit"""
    output("""Usage:
    project add <name> <folder> [description], will prompt for all three
    project cd <project>
    project description <project> [description]
    project status <project> [status]
    project todo <project>
    project mv <project> <folder>
    project del <project>
    project ls
    project LS
    project list""")

#============================================================
#INTERACTIVE
#------------------------------------------------------------
def search_for_option(prams,starter):
    """Helper function, look through command-line arguments for a certain pattern"""
    result = list(filter(lambda x:x.startswith(starter),prams))
    if result == []: return None
    return result
#------------------------------------------------------------
def interactive():
    """Run from the command-line"""
    command = sys.argv[1] if len(sys.argv)>1 else ""
    prams = sys.argv[1:]
    if not command.startswith("-"):
        prams = sys.argv[2:]
    if command in ("ls","") or command.startswith("-"):
        sort_mode = "path"
        length = "short"
        shelved = False
        if search_for_option(prams,"-a"): sort_mode = "alpha"
        if search_for_option(prams,"-d"): sort_mode = "date"
        if search_for_option(prams,"-t"): sort_mode = "date"
        if search_for_option(prams,"-l"): length = "long"
        if search_for_option(prams,"-s"): shelved = True
        if length == "long":
            cmd_long_list(sort_mode)
        else:
            cmd_short_list(sort_mode, show_shelved = shelved)
        sys.exit()
    if command == "help":
        help()
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

    name = getname(name)
    try:
        details = prams[1]
    except IndexError:
        details = None
    output(f"Name: {name}")

    if command.startswith("ad"): cmd_add(name)
    elif command == "cd": cmd_changedir(name)
    elif command.startswith("pa"): cmd_path(name)
    elif command.startswith("des"): cmd_description(name,details)
    elif command.startswith("del"): cmd_delete(name)
    elif command == "mv": cmd_move(name,details)
    elif command.startswith("st"): cmd_status(name,details)
    elif command.startswith("to"): cmd_todo(name)

if __name__ == "__main__":
    interactive()
