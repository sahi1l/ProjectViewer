function div { echo ------------------------------------------------------------; }
function Wait { echo "Press RETURN to continue"; read; }
project="_testproject"

echo "***Testing listing"
./project.py ls
Wait
div

echo "***Creating a project"
mkdir A 2>/dev/null

./project.py add $project A
div

echo "***Getting the path"
echo The path is $(./project.py path $project)
div

echo "***Setting the description"
./project.py desc $project "Just a generic description"
div

echo "***Setting the status"
./project.py status $project A
div

echo "***Here is the info for this project"
./project.py info $project
div

echo "***Changing directory: you should end up in directory A"
./project.py cd $project
Wait
div

echo "***Opening the TODO file"
./project.py todo $project
Wait
div

echo "***Moving to B"
mv A B
./project.py mv $project B

echo "***Checking the info now"
./project.py info $project


echo "***Deleting the project"
./project.py rm $project
rm -rf B
div
