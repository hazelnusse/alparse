"""Parse C output file from Autolev code dynamics().

    Prints the following to stdout:

    Parameters with default values
    States variables listed with default initial conditions

    Section to evaluate constants
    Section to evaluate right hand side of state derivatives
    Section to evaluate output quantities

"""

def seekto(fp, string):
    for l in fp:
        if l.strip() == string:
            break


def alparse(filenamebase, code="DynSysIn", classname=None):
    """
        filenamebase : string of the base output filename.  alparse() expects
        that filenamebase.c and filenamebase.in exist in the current working
        directly.

        code : valid choices are "DynSysIn", "Python", "C" or "C++"

        classname : for "Python" and "C++" code, creates a class with this name
    """

    parameters, states = alparsein(filenamebase, code)

    variables, constants, odefunc, outputs = alparsec(filenamebase, code, classname)

    print("[Parameters]")
    print(parameters)
    
    print("[States]")
    print(states)

    print("[Constants]")
    print(constants)

    print("[Equations of Motion]")
    print(odefunc)

    print("[Outputs]")
    print(outputs)


def alparsein(filenamebase, code):
    """Parse the .in file from Autolev to grab all the lines that begin with
    the word 'Constant' or 'Initial Value'
    """

    fp = open(filenamebase + ".in", "r")

    parameters = ""
    states = ""

    for l in fp:
        l = l.split()
        if l:
            if l[0] == "Constant":
                parameters += l[1] + " = " + l[4]
                if l[2] != "UNITS" and code == "DynSysIn":
                    parameters += ", " + l[2]
                if code == "C" or code == "C++":
                    parameters += ";"
                parameters += "\n"
            if l[0] == "Initial" and l[1] == "Value":
                states += l[2] + " = " + l[5]
                if l[3] != "UNITS" and code == "DynSysIn":
                    states += ", " + l[3]
                if code == "C" or code == "C++":
                    states += ";"
                states += "\n"
    fp.close()
    return parameters, states

def alparsec(filenamebase, code, classname):
    """Parse the .c file from Autolev to grab:
        1) list of variables that appear in all numerical calculations
        2) Evaluate constants section
        3) ode function
        4) output function

        These 4 things are arranged in different ways, depending on the value
        of code and whether or not a class is to be automatically generated for
        C++ or Python code
    """

    fp = open(filenamebase + ".c", "r")

    # For the Autolev C files I've examined, there are 20 lines of comments,
    # #include statements, and function forward declarations at the top.  The
    # following tosses these out the proverbial window.
    i = 0
    while i < 20:
        fp.next()
        i += 1

    # Loop to grab the statement that declares all the global variables,
    # assumes that they are declared as type 'double'
    variables = []
    for l in fp:
        l = l.strip().split()
        if l:
            if l[0] == "double":
                l = l[1].strip().split(',')

                if l[0] == "Pi":
                    l = l[1:]
                if l[0] == "DEGtoRAD":
                    l = l[1:]
                if l[0] == "RADtoDEG":
                    l = l[1:]

                # multi line statement
                while l[-1] == '':
                    l.pop(-1)
                    l += fp.next().strip().split(',')
                
                if l[-1][-1] == ';':
                    l[-1] = l[-1][:-1]

                # Get rid of the Encode[??]
                if l[-1][:6] == "Encode":
                    l.pop(-1)

            if l[0] == "/*" and l[2] == "MAIN" and l[4] == "*/":
                break
            variables += l

    # Seek to the line has the comment above the constants
    seekto(fp, "/* Evaluate constants */")

    # Get all the equations for the Evaluate constants
    constants = ""
    for l in fp:
        l = l.strip()
        if l:
            # Handle multi-line statements
            while l[-1] != ';':
                l += fp.next().strip()

            if code == "DynSysIn" or code == "Python":
                l = l[:-1]  # remove the semi-colon at end
            l += "\n"
            constants += l
        else:
            break

    # Seek to the line in the ode func that has the comment above the equations
    seekto(fp, "/* Update variables after integration step */" )
    while fp.next().strip() != '':
        pass

    # Get the equations in the right hand side of the odes
    odefunc = ""
    for l in fp:
        l = l.strip()
        if l:
            if l == "/* Update derivative array prior to integration step */":
                break

            # Handle multi-line statements
            while l[-1] != ';':
                l += fp.next().strip()
            if code == "DynSysIn" or code == "Python":
                l = l[:-1]
            l += "\n"
            odefunc += l

    # Seek to the first line of the output equations
    seekto(fp, "/* Evaluate output quantities */")

    outputs = ""
    for l in fp:
        l = l.strip()

    return variables, constants, odefunc, ""


alparse("slotted_discs_al", code="C")

