"""Parse C output file from Autolev code dynamics().

    Prints the following to stdout:

    Parameters with default values
    States variables listed with default initial conditions

    Section to evaluate constants
    Section to evaluate right hand side of state derivatives
    Section to evaluate output quantities

"""
import os

def seekto(fp, string):
    for l in fp:
        if l.strip() == string:
            break

def writeDynSysIn(filenamebase, classname, infilestrings, cfilestrings,
        directory=None):
    if not directory == None:
        classFile = os.path.join(directory, classname)
    else:
        classFile = classname
    intopts, parameters, states = infilestrings
    variables, constants, odefunc, outputs = cfilestrings
    fp = open(classFile + ".txt", "w")
    fp.write("[Name]\n" + classname + "\n\n")

    fp.write("[Integration Options]\n")
    fp.write(intopts + "\n")

    fp.write("[Parameters]\n")
    fp.write(parameters + "\n")

    fp.write("[States]\n")
    fp.write(states + "\n")

    fp.write("[Constants]\n")
    fp.write(constants + "\n")

    fp.write("[Equations of Motion]\n")
    fp.write(odefunc + "\n")

    fp.write("[Outputs]\n")
    fp.write(outputs + "\n")

    print(filenamebase + ".dir and " + filenamebase + ".c sucessfully" +
            " parsed.  Output code is in:\n" + fp.name)
    fp.close()

def writeC(infilestrings, cfilestrings, classname):
    raise Exception
    intopts, parameters, states = infilestrings
    variables, constants, odefunc, outputs = cfilestrings

    filenamebase += "_al"
    fp_header = open(filenamebase + ".h", "w")
    fp_implementation = open(filenamebase + ".c", "w")
    fp_driver = open(filenamebase + "_main.c", "w")

    # Write the variables on one long line
    varstring = ""
    for v in variables:
        varstring += v + ", "
    varstring = varstring[:-2] + ";\n"

    # Write the header file
    fp_header.write(
        "#ifndef " + filenamebase.upper() + "_H\n" +
        "#define " + filenamebase.upper() + "_H\n\n" +
        "// All variables defined as globals with file scope\n" +
        "double " + varstring + "\n" +
        "// Function prototypes\n" +
        "int initConstants(void);\n" +
        "int eoms(double t, const double x[], double f[], void * p);\n" +
        "void outputs(void);\n" +
        "#endif")
    fp_header.close()

    # Write the implementation file
    indented_constants = ""
    indented_odefun = ""
    indented_outputs = ""
    for l in constants.splitlines(True):
        indented_constants += "  " + l
    for l in odefun.splitlines(True):
        indented_odefun += "  " + l
    for l in outputs.splitlines(True):
        indented_outputs += "  " + l

    fp_implementation.write(
        "#include <math.h>\n"
        "#include <gsl/gsl_odeiv.h>\n" +
        "#include \"" + fp_header.name() + "\"\n" +
        "int initConstants(void)\n{\n" + constants + "\n}" +
        "// initConstants()\n\n" +
        "int eoms(double t, const double x[], double f[], void * p)\n{\n")
        #for i in range(len(
        #
        #        "void outputs(void);\n" +
        #        "#endif")
    fp_implementation.close()

def writePython(infilestrings, cfilestrings, classname):
    raise Exception

def writeCxx(infilestrings, cfilestrings, classname):
    raise Exception

def alparsein(filenamebase, code):
    """Parse the .in file from Autolev to grab all the lines that begin with
    the word 'Constant' or 'Initial Value'
    """

    print "cwd: ", os.getcwd()
    fp = open(filenamebase + ".in", "r")
    for i in range(6):
        fp.next()

    intopts = ""
    parameters = ""
    states = ""

    for l in fp:
        l = l.strip().split()
        if l:
            if l[0] == "Constant":
                parameters += l[1] + " = " + l[4]
                if l[2] != "UNITS" and code == "DynSysIn":
                    parameters += ", " + l[2]
                if code == "C" or code == "C++":
                    parameters += ";"
                parameters += "\n"
            elif l[0] == "Initial" and l[1] == "Value":
                states += l[2] + " = " + l[5]
                if l[3] != "UNITS" and code == "DynSysIn":
                    states += ", " + l[3]
                if code == "C" or code == "C++":
                    states += ";"
                states += "\n"
            elif l[2] == 'TINITIAL':
                intopts += "ti = " + l[5]
                if code == "C" or code == "C++":
                    intopts += ";"
                elif code == "DynSysIn" and l[3] != "UNITS":
                    intopts += ", " + l[3]
                intopts += "\n"
            elif l[2] == 'TFINAL':
                intopts += "tf = " + l[5]
                if code == "C" or code == "C++":
                    intopts += ";"
                elif code == "DynSysIn" and l[3] != "UNITS":
                    intopts += ", " + l[3]
                intopts += "\n"
            elif l[2] == 'INTEGSTP':
                intopts += "ts = " + l[5]
                if code == "C" or code == "C++":
                    intopts += ";"
                elif code == "DynSysIn" and l[3] != "UNITS":
                    intopts += ", " + l[3]
                intopts += "\n"
            elif l[2] == 'ABSERR':
                intopts += "abserr = " + l[4]
                if code == "C" or code == "C++":
                    intopts += ";"
                intopts += "\n"
            elif l[2] == 'RELERR':
                intopts += "relerr = " + l[4]
                if code == "C" or code == "C++":
                    intopts += ";"
                intopts += "\n"
                break

    fp.close()
    return intopts, parameters, states

def alparsec(filenamebase, code):
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
        continue

    # Get the equations in the right hand side of the odes
    odefunc = ""
    for l in fp:
        l = l.strip()
        if l:
            if l == "/* Update derivative array prior to integration step */":
                break

            if l == "/* Quantities to be specified */":
                pass
            else:
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
        if l:
            # Handle multi-line statements
            while l[-1] != ';':
                l += fp.next().strip()
            if code == "DynSysIn" or code == "Python":
                l = l[:-1]
            l += "\n"
            outputs += l
            continue
        break

    seekto(fp, "/* Write output to screen and to output file(s) */")
    for l in fp:
        l = l.strip()
        if l:
            if l[:6] == "writef":
                continue
            # Handle multi-line statements
            while l[-1] != ';':
                l += fp.next().strip()
            if code == "DynSysIn" or code == "Python":
                l = l[:-1]
            l += "\n"
            outputs += l
            continue
        break

    return variables, constants, odefunc, outputs

def alparse(filenamebase, classname, code="DynSysIn", directory=None):
    """
        filenamebase : string of the base input filename.  alparse() expects
        that filenamebase.c and filenamebase.in exist in the current working
        directory.

        classname : Name of system.  Used to name classes in
        Psuedo-Code/C++/Python code, used to name struct in C code.  Output
        code is written to a file of title classname.*

        code : valid choices are "DynSysIn", "Python", "C" or "C++"

        directory : Optional path to the directory in which filenamebase.c and
        filenamebase.in exist. If 'None', alparse assumes files are in current
        working directory.
    """
    if not directory == None:
        filenamebase = os.path.join(directory, filenamebase)

    infilestrings = alparsein(filenamebase, code)
    cfilestrings = alparsec(filenamebase, code)

    if code == "DynSysIn":
        writeDynSysIn(filenamebase, classname, infilestrings, cfilestrings,
                directory=directory)
    elif code == "C":
        writeC(infilestrings, cfilestrings, classname)
    elif code == "Python":
        writePython(infilestrings, cfilestrings, classname)
    elif code == "C++":
        writeC++(infilestrings, cfilestrings, classname)

