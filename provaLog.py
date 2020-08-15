import os

with open('fred.txt', 'w') as outfile:
    s = "I'm Not Dead Yet!"
    print(s)  # writes to stdout
    print(s, file=outfile)  # writes to outfile

    # Note: it is possible to specify the file parameter AND write to the screen
    # by making sure file ends up with a None value either directly or via a variable
    myfile = None
    print(s, file=myfile)  # writes to stdout
    print(s, file=None)   # writes to stdout
