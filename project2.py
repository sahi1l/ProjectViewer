#!/usr/bin/env python3

#------------------------------------------------------------
maindir = os.path.expanduser("~") + "/.projectdirs"
DESC = "@description.txt"
TODO = "TODO.todo"
STAT = "@status.txt"

#============================================================
#COMMANDS
#============================================================
def short_list(mode=None,show_shelved=False): 
    """Return a brief list of projects"""
    #mode can be None, "path", or "date"
    results = []
    for name in names(mode):
        if show_shelved or int(getstat(name))<2:
            results += [f"{prettyname(name)}: {getfile(name,DESC)}"]
    return '\n'.join(results)

#============================================================
def long_list(mode=None):
    """Return a detailed list of projects"""
    results = []
    for name in names(mode):
        results += [prettyname(name)]
        results += [getfile(name,DESC)]
        results += [gettodo(name).strip(),"\n"]
    return '\n'.join(results)
#============================================================
def cmd_add(name):
    """Add a new project"""
    try:
        path = ask("Where will this project live? (.) ",".")
        description = ask("Describe your project.\n", "")
        add_project(name, path, description)
    except EOFError:
        print("Aborted.")
        exit()
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
    """Return the path of the named project's folder"""
    print(icloud(os.path.realpath(link(name))))
#============================================================
def cmd_description(name, text=None):
    """Return or change a project's description"""
    name = getname(name)
    if text:
        setfile(name, DESC, text)
    else:
        print(getfile(name,DESC))
#============================================================
def cmd_status(name, level=None):
    """Return or change a project's status"""
    name = getname(name)
    print("Current status:",statuses[int(getstat(name))])
    if not level or level[0] not in "ANSans":
        while True:
            level = ask("Change the status? [ANS]","")
            if len(level) and level[0] in "ANSans": break
    if level:
        if level.isnumeric():
            level = statuses[int(level)]
        if level.lower() in "ans":
            level = {x[0]:x for x in statuses}
        if level in statuses:
            setfile(name, STAT, level)
            return f"Status changed to {level}"
#============================================================
def cmd_todo(name):
    """Open the TODO file for the project in an external editor"""
    touch(name)
    emacs = "/opt/homebrew/bin/emacs"
    subprocess.check_output([emacs, link(name,TODO)],
                                stderr = subprocess.DEVNULL)

#============================================================
def cmd_delete(name):
    ask(f"Should I delete the project {name}? ",None)
    path = os.path.join(maindir,name)
    print(f"OK, removing link to  {link(name,None,True)}.")
    os.remove(path)
#============================================================
def cmd_move(name,dir):
    if not dir:
        dir = ask("Where is the new location? ",None)
    make_link(name,dir,force=True)
#============================================================    
def cmd_help():
    print("""Usage:
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
def interactive():
    command = sys.argv[1] if len(sys.argv)>1 else ""
    prams = sys.argv[2:]
    if command == "ls"  or command == "":
        print(short_list(get_mode(prams),False))
        exit()
        #@LIST============================================================
    if command == "LS":
        print(short_list(get_mode(prams),True))
        exit()
    if command == "help":
        help(); exit()
    if command == "list":
        print(long_list(get_mode(prams)))
        exit()
        #I need to access the folder, description, status, and todo items
    if len(prams)<1:
        while True:
            name = ask("Enter project name: ", None)
            if name == "?": #get a list of all projects
                print(short_list(None,True))
            else:
                break
    else:
        name = getname(prams[0])
        
    print(f"Name: {name}")
    if command.startswith("ad"): cmd_add(name,*prams)
    elif command == "cd": cmd_changedir(name)
    elif command.startswith("pa"): cmd_path(name)
    elif command.startswith("des"): cmd_description(name,*prams)
    elif command.startswith("del"): cmd_delete(name)
    elif command == "mv": cmd_move(name,*prams)
    elif command.startswith("st"): cmd_status(name,*prams)
    elif command.startswith("to"): cmd_todo(name)

if __name__ == "__main__":
    interactive()
