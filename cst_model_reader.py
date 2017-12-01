import functions as f
import os
import subprocess


class CST_Model():
    '''Read and edit parameters of a cst file
       only read simple results

       methods: getResultNames, getResult, getParam, getParams, editParam'''

    def __init__(self, filename, cst_path=None):
        ''' initializes the path of the cst file
            and adds some internal variables

            returns None'''

        if not os.path.isfile(filename):
            raise FileNotFoundError(filename + "not found")

        self.filename = filename.replace("\\", "/")
        self.FilePath = "/".join(filename.split("/")[:-1]) + "/"
        self.name = self.filename.split(
            "/")[-1]
        self.ResultPath = self.filename.split(
            ".")[:-1]  # removing fileextension
        # navigating to subfolder of file
        self.ResultPath = "".join(self.ResultPath) + "/Result/"
        self.ParamPath = "".join(self.filename.split(
            ".")[:-1]) + "/Model/3D/" + "Model.par"
        if cst_path:
            self.cst_path = cst_path
        else:
            self.cst_path = "C:/Program Files (x86)/CST STUDIO SUITE 2017/CST DESIGN ENVIRONMENT.exe"

    def getResultNames(self, filetypes=[".rd0"]):
        ''' should return a list of all results in result path

            filetypes:  list or str, which file-extension
                        should be searched for

            returns all files in cst files ResultPath specified in __init__'''
        filepaths = f.get_files(self.ResultPath, filetypes)
        # removing long path to display only the names of the files
        return [filename.split("/")[-1] for filename in filepaths]

    def getResult(self, Resultname):
        '''returns float of Result value from rd0-file'''
        file = open(self.ResultPath + Resultname, mode='r')
        return float(file.readline())

    def getParams(self):
        '''returns all available parameter triplets as a list

            as [parName, parEquation, parValue]
        '''
        try:
            self.params
        except AttributeError:
            self._loadParams()
        return self.params

    def _loadParams(self):
        '''should read all cst file parameters and insert
           it in internal list self.params'''

        def clean(param_raw):
            ''' returns a list of all params neglegting parameters whichs
                value is -1'''

            # parameter in cst cant be named using a whitespace
            # therefore all spaces will be deleted
            params = param_raw.split("  ")
            params = [param.replace(" ", "") for param in params if param !=
                      "" and param != "\n"]
            params = [param.lower() for param in params]
            return params

        def evaluate(equation_raw):
            ''' should replace parameter-names by its value or function '''
            equation = "".join(equation_raw)
            while True:
                for par in self.params:
                    par_name = par[0]
                #     print(equation)
                    if par_name in equation:
                        # print(par_name, equation,self.getParam(par_name)[1])
                        try:
                            if equation[
                                equation.index(par_name) + len(par_name)
                            ] in ["+", "-", "*", "/", "^", ")"]:
                                equation = equation.replace(
                                    par_name,
                                    "(" + self.getParam(par_name)[1] + ")"
                                )
                        except IndexError:
                            pass
                try:
                    return eval(equation)
                except NameError:
                    return equation
                except SyntaxError:
                    equation = equation[:-1]

        def evaluate2(equation):
            ''' should replace parameter-names only by its value'''
            for param in self.params:
                if param[0] in str(equation):
                    try:
                        if equation[equation.index(param[0]) + len(param[0])] in ["+", "-", "*", "/", "^", ")"]:
                            equation = equation.replace(
                                param[0], "(" + str(param[2]) + ")")
                    except IndexError:
                        equation = equation.replace(
                            param[0], "(" + str(param[2]) + ")")
            try:
                return eval(str(equation).replace("^", "**"))
            except NameError:
                return equation
        file = open(self.ParamPath, mode='r')
        params = [clean(param_raw) for param_raw in file.readlines()]
        params = [param for param in params if param[1] != "-1\n"]
        params = sorted(params, key=lambda x: -len(x[0]))
        # selction only param_name and its value
        self.params = params
        params = [param[0:2] + [evaluate(param[1])] for param in params]
        self.params = params
        # selction only param_name and its value
        while True:
            try:
                # abort when sum can be computed
                # abort when all p[2] are evaluated
                # print([p[2] for p in self.params])
                # print()
                sum([p[2] for p in self.params])
                break
            except:
                params = [param[0:2] + [evaluate2(param[2])]
                          for param in params]
                self.params = params

        file.close()
        # params = [param[0:2] + [evaluate2(param[2])] for param in params]
        # self.params = params

    def getParam(self, paramname):
        ''' parname: string, the parameter which should be returned

            returns list, [0]: name, [1]: formula, [2] value'''
        self.getParams()
        names = [a[0] for a in self.params]
        return self.params[names.index(paramname.lower())]

    def editParam(self, Paramname, value, method="scary"):
        '''edits the parameter value in the cst parameter file
           This Script was created for CST 2017

            parname: string, parametername which should be edited

            value: int or float, value which should be assigned to parameter

            returns None'''

        def scary(self, Paramname, value):
            # the parameter file is a 771 chars long file ?
            # all chars where i < 256 belong to the parameter name ?
            # all chars where  255 < i < 513 belong to the equation ?
            # all chars where i < 512 belong to comment ?
            paramFile = open(self.ParamPath, "r")
            #  asserting its the pure paramname
            Paramname = " " + Paramname + " "
            assert self.ParamPath[-4:] == ".par"
            lines = paramFile.readlines()
            count = 0  # we only want to find one line
            name_end_idx = 255
            for i, line in zip(range(len(lines)), lines):
                assert len(line) == 771
                if\
                        Paramname.upper() in line[:name_end_idx + 2].upper()\
                        and\
                        line.replace(" ", "")[-3:-1] != "-1":
                    index = i
                    count += 1
            assert count == 1
            __v = str(value)
            if len(__v) > 255:
                print(__v)
                raise AttributeError("value length bigger than 255")
            # keeping name and comment
            newline = lines[index][:256] + " " * \
                (512 - 255 - len(__v)) + __v + lines[index][513:]
            lines[index] = newline
            assert len(newline) == 771
            paramFile.close()
            paramFile = open(self.ParamPath, "w")
            for l in lines:
                paramFile.write(l)

        def slow(self, Paramname, value):
            filename = self.FilePath + "par_tmp.par"
            file = open(filename, "w")
            file.write(Paramname + "\t\t\t" + str(value))
            file.close()
            flag = " -c -par " + filename + " "
            cmd = self.cst_path + flag + self.filename
            print(cmd)
            assert os.path.isfile(filename)
            assert os.path.isfile(self.filename)
            subprocess.call(cmd)
            os.remove(filename)
        methods = ["slow", "scary"]
        assert method in methods
        if method == "slow":
            slow(self, Paramname, value)
        elif method == "scary":
            scary(self, Paramname, value)

    def rebuild(self):
        '''CST History will be updated completely'''
        falgs = " -m -rebuild "
        cmd = self.cst_path + falgs + self.filename
        subprocess.call(cmd)


def TEST():
    path = "C:/Dropbox/Uni_privat/Master/Python/CST/Test/IH_10a_25mm_5Gaps.cst"
    ih_12a = CST_Model(path)
    names = ih_12a.getResultNames()
    ih_12a._loadParams()
    # for a in ih_12a.params:
    #     print(a)
    # print(ih_12a.getParam("tuner_stem_angle"))
    ih_12a.editParam("shell_length", 6689)


if __name__ == "__main__":
    TEST()
