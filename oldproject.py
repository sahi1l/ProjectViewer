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


def names(sort=None):
    os.chdir(maindir)
    result = glob("*")
    status = lambda K: str(2-int(getstat(K)))

    if sort=="path": #sort by status, then path
        result.sort(key=lambda K:status(K)+link(K,real=True), reverse=True)
    elif sort=="date":
        result.sort(key=lambda K:status(K)+str(getdate(K)),reverse=True)
    else:
        result.sort()
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

def gettodo(name):
    text = getfile(name,TODO).strip().split("\n")
    result = []
    for line in text:
        if re.search("^\*.*TODO", line):
            result += [colored(line.strip().replace("TODO","",1),"cyan")]
    return '\n'.join(result)
    #get all lines with "* TODO"
    #returns a list
def prettyname(name,bold=False):
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
def add(name=None, dir=".", description=""):
    if name == None:
        raise Usage("Usage: project add <name> [directory] [description]")
        return #or throw error
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


#@LS============================================================
command = sys.argv[1] if len(sys.argv)>1 else ""
prams = sys.argv[2:]
if command == "ls"  or command == "":
    """A quick listing of all projects, one per line, maybe with description?"""
    mode="path"
    if len(prams)>0:
        if prams[0].startswith("a"): mode=None
        elif prams[0][0] in ["t","d"]: mode="date"
    NL = numlist()
    for name in names(mode):
        print(f"{prettyname(name)}: {getfile(name,DESC)}")
#        print(name)
#@LIST============================================================
elif command == "help":
    help()
    exit()
elif command == "list":
    #I need to access the folder, description, status, and todo items
    NL = numlist()
    results = {}
    mode="path" #sort by status first, then path
    if len(prams)>0 and prams[0][0] in ["t","d"]:
        mode="date" #sort by status first, then time
    for name in names(mode):
        print(prettyname(name))
        print(getfile(name,DESC))
        print(gettodo(name).strip(),"\n")
elif len(prams)<1:
    print("project name missing")
    exit()
else:
    name = getname(prams[0])
    print(f"Name: {name}")
    #@ADD========================================
    if command == "add":
        add(*prams)
        if len(prams)<2:
            print("project add <name> <directory> [description]")
            exit()
        name,dir = prams[:2]
        dir = os.path.realpath(dir)
        description=""
        if len(prams)>=3:
            description = prams[2]
        #does this name already exist in maindir?
        #if not, make a softlink in maindir to dir
        if os.path.exists(link(name)): #name already exists
            print(f"{name} already exists.")
            exit()
        if not os.path.isdir(dir): #directory needs to exist
            print(f"{dir} isn't a directory")
            exit()
    #        os.mkdir(dir) #make the directory
        os.symlink(dir,link(name))
        #create a description file
        os.chdir(dir)
        if description or not os.path.exists(DESC):
            with open(DESC,"w") as F:
                F.write(description)
        if not os.path.exists(TODO):
            with open(TODO,"w") as F:
                F.write("")
    #@CD========================================
    elif command == "cd":
        os.chdir(maindir)
        touch(name)
        tgt = icloud(os.path.realpath(link(name)))
        cmd = f'tell app "Terminal" to do script "cd \\\"{tgt}\\\" && ~/bin/changetitle @{name} && clear && echo {name.upper()}"'
        print(cmd)
        subprocess.check_output(["osascript","-e",cmd],stderr=subprocess.DEVNULL)
        pass
    #@DESCRIPTION========================================
    elif command.startswith("desc"):
        if len(prams)==1: #display description
            print(getfile(name,DESC))
        else:
            setfile(name,DESC,prams[1])
    #@STATUS========================================
    elif command == "status":
        if len(prams)==1: #display description
            print(statuses[int(getstat(name))])
        else:
            s = prams[1]
            if s.isnumeric():
                s = statuses[int(s)]
            setfile(name,STAT,s)
            print("Status changed to",s)
        pass
    #@TODO========================================
    elif command == "todo":
        touch(name)
        subprocess.check_output(["/usr/local/bin/aquamacs",link(name,TODO)],stderr=subprocess.DEVNULL)
        #open via aquamacs

