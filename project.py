#!/usr/bin/env python3.10
import sys,os,subprocess
from glob import glob
from pathlib import Path
from functools import partial
from termcolor import colored
import re
maindir = os.path.expanduser("~") + "/.projectdirs"
DESC = "@description.txt"
TODO = "TODO.todo"
STAT = "@status.txt"
def getdate(name):
    return int(os.path.getmtime(link(name,DESC)))

def touch(name):
    """the date on the description file indicates which was last run"""
    Path(link(name,DESC)).touch()

def numlist(): #list of projects sorted by status and access time
    return names("date")

def getname(name):
    if name.isnumeric():
        return numlist()[int(name)]
    return name

def getfile(name,typ):
    fname = link(name,typ)
    if os.path.exists(fname):
        with open(fname, "r") as F:
            return F.read().strip()
    else:
        return ""
    
def setfile(name,typ,val):
    with open(link(name,typ),"w") as F:
        F.write(val)

statuses=["active","normal","shelved"]
def getstat(name):
    """returns 0, 1, or 2, 0 is the best"""
    result=getfile(name,STAT).strip()
    if result=="":
        return "1"
    return str(statuses.index(result))


#EXTERNAL
def names(sort=None):
    os.chdir(maindir)
    result = glob("*")
    status = lambda K: str(2-int(getstat(K)))

    if sort=="path": #sort by status, then path
        result.sort(key=lambda K:status(K)+link(K,real=True), reverse=True)
    elif sort=="date":
        result.sort(key=lambda K:status(K)+str(getdate(K)),reverse=True)
    else:
        result.sort(key=str.casefold)
    return result
        
def icloud(path):
    return path.replace("/Library/Mobile Documents/com~apple~CloudDocs/","/iCloud/")

def link(name,sub=None,real=False):
    path = os.path.join(maindir,name)
    if sub:
        path = os.path.join(path,sub)
    if real:
        return icloud(os.path.realpath(path))
    else:
        return path

def gettodo(name,color=True):
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
#            laststarred[nstars] = line.strip().replace("TODO","",1)
#            print("STARTROW")
            for row in laststarred[1:]:
                if row.strip()=="": continue
#                print(f"{row=}")
                if color:
                    result += [colored(row,"cyan")]
                else:
                    result += [row]
            laststarred=[""]
    
    return '\n'.join(result)

def prettyname(name,bold=False):
    NL = numlist()
    attrs=[]
    if bold: attrs=["bold","underline"]
    color = ["red", "white", "yellow"][int(getstat(name))]
    return colored(f'{NL.index(name)}. {name}', color,attrs=attrs)

def help():
    print("""Usage:
    project add <name> <folder> [description]
    project cd <project>
    project description <project> [description]
    project status <project> [status]
    project todo <project>
    project ls
    project list""")

class Usage(Exception):
    pass
class ProjectError(Exception):
    pass
#============================================================
def add_project(name=None, dir=".", description=""):
    if name == None:
        raise Usage("Usage: project add <name> [directory] [description]")
        return #or throw error
    name = getname(name)
    dir = os.path.realpath(dir)
    if os.path.exists(link(name)):
        raise ProjectError(f"{name} already exists.")
    if not os.path.isdir(dir):
        raise ProjectError(f"{dir} isn't a directory.")
    os.symlink(dir, link(name))
    os.chdir(dir)
    if description or not os.path.exists(DESC):
        with open(DESC,"w") as F:
            F.write(description)
    if not os.path.exists(TODO):
        with open(TODO, "w") as F:
            F.write("")

def change_dir(name):
    os.chdir(maindir)
    touch(name)
    tgt = icloud(os.path.realpath(link(name)))
    cmd = f'tell app "Terminal" to do script "cd \\\"{tgt}\\\" && ~/bin/changetitle @{name} && clear && echo {name.upper()}"'
    subprocess.check_output(["osascript","-e",cmd],stderr=subprocess.DEVNULL)

def description(name, text=None):
    name = getname(name)
    if text:
        setfile(name, DESC, text)
        return ""
    else:
        return getfile(name,DESC)
def status(name, level=None):
    name = getname(name)
    if level:
        if level.isnumeric():
            level = statuses[int(level)]
        elif level in statuses:
            setfile(name, STAT, level)
            return f"Status changed to {level}"
        else:
            return f"Possible statuses: {','.join(statuses)}"
    else:
        return statuses[int(getstat(name))]
def open_todo(name):
    touch(name)
    subprocess.check_output(["/usr/local/bin/aquamacs", link(name,TODO)],
                                stderr = subprocess.DEVNULL)
def get_mode(prams):
    if len(prams)>0:
        if prams[0] == "a":
            return None
        elif prams[0] in "td":
            return "date"
    return "path"
    
def short_list(mode=None): #mode can be None, "path", or "date"
    results = []
    for name in names(mode):
        results += [f"{prettyname(name)}: {getfile(name,DESC)}"]
    return '\n'.join(results)

def long_list(mode=None):
    results = []
    for name in names(mode):
        results += [prettyname(name)]
        results += [getfile(name,DESC)]
        results += [gettodo(name).strip(),"\n"]
    return '\n'.join(results)

#@LS============================================================
def interactive():
    command = sys.argv[1] if len(sys.argv)>1 else ""
    prams = sys.argv[2:]
    if command == "ls"  or command == "":
        print(short_list(get_mode(prams)))
        #@LIST============================================================
    elif command == "help":
        help(); exit()
    elif command == "list":
        print(long_list(get_mode(prams)))
        #I need to access the folder, description, status, and todo items
    elif len(prams)<1:
        print("project name missing")
        exit()
    else:
        name = getname(prams[0])
        print(f"Name: {name}")
        #@ADD========================================
        if command.startswith("ad"): add_project(*prams)
        elif command == "cd": change_dir(name)
        elif command.startswith("de"): print(description(*prams)) #FIX?: or I might return this instead of printing?
        elif command.startswith("st"): print(status(*prams))
        elif command.startswith("to"): open_todo(name)

if __name__ == "__main__":
    interactive()
