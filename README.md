This is a tool for keeping track of multiple projects on your computer
via the command-line.  Each project lives in a directory somewhere on
the system, and the program keeps a set of symbolic links to those
folders in the directory `~/.projectdirs`.

When you create a project out of a directory, the program creates
three files in that directory:
* `@description.txt` which stores the project's description
* `@status.txt` which stores the project's status: active (highest), normal, or status.
* `TODO.todo` which can be used for todo notes

Here are the various commands:

USAGE: `project.py <command> ...`
---
**GENERAL COMMANDS**
* `project ls -aplsr`: list all projects
    *  **SORTING COMMANDS**
    *  default sort is by status and then by date modified
    + `-a`: sorted in alphabetical order by name
    + `-A`: sort by status, and then alphabetical order
    + `-p`: sorted by status and then path name
  ---  
  *  `-l`: include many more details
  *  `-s`: include shelved projects
  *  `-r`: a simple list of project name and project directory
*  `project raw`: same as `ls -r`
* `project help`: display this help
* `project error`: find broken links in the project list
* `project is <directory>`: return the name of the project `<directory>` belongs to
---
**PROJECT COMMANDS**
* `project add <name> <directory>`: Add a new project named <name> for <directory>
* `project cd <project>`: Open a new terminal window in the project directory
* `project path <project>`: Returns the path of `<project>`. *(Try `cd $(project path <project>`)*
* `project todo <project>`: Open the `TODO.todo` file for `<project>` in a text editor.
* `project description <path> <new>`: View or change the `<project>`'s description
* `project status <project>`: View or change the `<project>`'s status *(active, normal, or shelved)*
* `project mv <project_name> <dest>`: Reassign `<project_name>` to `<dest>` *(the directory is not moved)*
* `project rm <project>`: Removes `<project>` from the project list *(the directory is not deleted)*
* `project info <project>`: Show information about `<project>`

There is also a program called `vproject` which presents a menu-like version of the same information.  Press `?` in that program for help.
