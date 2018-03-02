import functions as f
import os
import subprocess
from cst_model_reader_config import config


class CST_Model():
    '''Read and edit parameters of a cst file
       only read simple results

       methods: getResultNames, getResult, getParam, getParams, editParam'''

    def __init__(self, filename, cst_path=None):
        ''' initializes the path of the cst file
            and adds some internal variables

            returns None'''
        self.verbose = True

        if not os.path.isfile(filename):
            raise FileNotFoundError(
                filename + "not found"
            )
        if " " in filename:
            raise Warning(
                '''Please remove spaces from filename'''
            )
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
            self.cst_path = config.cst_path

    def __str__(self):
        return self.name.split(".")[0]

    def __repr__(self):
        return self.filename

    def message(self, *args):
        '''prints a message if self.verbose set to True
        '''
        if self.verbose:
            msg = ""
            for arg in args:
                msg += str(arg) + " "
            msg.strip()
            print(msg)

    def toggle_mute(self, silent=False):
        self.verbose = not self.verbose
        if self.verbose:
            if not silent:
                print("Unmuted")
        elif not self.verbose:
            if not silent:
                print("Muted")
        else:
            raise Exception("self.verbose is not bool", self.verbose)

    def getResultNames(self, filetypes=[".rd0"]):
        ''' should return a list of all results in result path

            filetypes:  list or str, which file-extension
                        should be searched for

            returns all files in cst files ResultPath specified in __init__'''
        filepaths = f.get_files(self.ResultPath, filetypes)
        # removing long path to display only the names of the files
        return [filename.split("/")[-1] for filename in filepaths]

    def getResult(self, Resultname, filetype=".rd0"):
        '''returns float of Result value from rd0-file'''
        if filetype != ".rd0":
            raise FileExistsError("Resulttype not implemented yet")
        if Resultname[-4] != filetype:
            splt = Resultname.split(".")
            assert len(splt) <= 2
            Resultname = splt[0] + filetype
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

        self.message(str(self), "loading Parameters")
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

    def getParam(self, Paramname):
        ''' parname: string, the parameter which should be returned

            returns list, [0]: name, [1]: formula, [2] value'''
        self.getParams()
        names = [a[0] for a in self.params]
        return self.params[names.index(Paramname.lower())]

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
            # flag = " -c -par " + filename + " "
            # cmd = self.cst_path + flag + self.filename
            # print(cmd)
            assert os.path.isfile(self.filename)
            # subprocess.call(cmd)
            self.cst_import_parfile(filename)
            os.remove(filename)
        methods = ["slow", "scary"]
        assert method in methods
        self.message(str(self), "setting", Paramname, "to", value)
        if method == "slow":
            slow(self, Paramname, value)
        elif method == "scary":
            scary(self, Paramname, value)

    def _run(self, flags, dc=None):
        ''' Use flags as specified in
            cst manual chapter "command line options"

            flags: str

            dc: str, distributed comuting as "maincontroller:port"
                     like "142.2.245.136:360000"
        '''
        if dc:
            flags += "-withdc=" + str(dc) + " "
        cmd = self.cst_path + flags + self.filename
        self.message(str(self), "running command:\n\t", cmd)

        returncode = subprocess.call(cmd)
        if returncode != 0:
            print(self.__str__(), "returncode", returncode)

    def cst_rebuild(self):
        ''' CST History will be updated completely

            flags = " -m -rebuild

            returns None"
        '''
        flags = " -m -rebuild "
        self.message(str(self), "rebuilding")
        self.toggle_mute(silent=True)
        self._run(flags)
        self.toggle_mute(silent=True)
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_run_eigenmode(self, dc=None):
        ''' runs eigenmode solver for the model

            flags = " -m -e "
            dc: str, distributed comuting as "maincontroller:port" like
                     "142.2.245.136:360000"

            returns None
        '''
        flags = " -m -e "
        self.message(str(self), "running Eigenmode Solver")
        self.toggle_mute(silent=True)
        self._run(flags)
        self.toggle_mute(silent=True)
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_run_optimizer(self, dc=None):
        ''' runs microwave studio optimizer for the model

            flags = " -m -o "
            dc: str, distributed comuting as "maincontroller:port" like
                     "142.2.245.136:360000"

            returns None
        '''
        flags = " -m -o "
        self.message(str(self), "running Eigenmode optimizer")
        self.toggle_mute(silent=True)
        self._run(flags)
        self.toggle_mute(silent=True)
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_import_parfile(self, parfile):
        ''' runs microwave studio optimizer for the model

            flags = " -c -par " + parfile + " "

            returns None
        '''
        assert os.path.isfile(parfile)
        flags = " -c -par " + parfile + " "
        self.message(str(self), "importing parameter from\n\t", parfile)
        self.toggle_mute(silent=True)
        self._run(flags)
        self.toggle_mute(silent=True)

    def export_csv(self):
        print("export not implemented yet")
        pass

    def sweep(self, Paramname, values, dc=None, flags=None):
        ''' Will perform a Eigenmode Sweep on the given values.
            Seperate Instances of CST will be called
            in order to perfom.

            The Sweep will be performed, after completion
            the value will be set to the initial
            value before sweeping.

            Paramname: str, the selected parameter to sweep

            values: iterable(float or int), the values to sweep over

            dc: str, distributed comuting as "maincontroller:port" like
                     "142.2.245.136:360000"

            flags: refer to module _run()
        '''

        def check_args():
            assert isinstance(str, Paramname)
            for v in values:
                assert isinstance(float, v) or isinstance(int, v)

        check_args()
        self.message(str(self), "sweeping", Paramname)
        value_init = self.getParam(Paramname)[1]
        self.message("\tInitial value", value_init)
        for value in values:
            self.editParam(Paramname, value)
            self.cst_rebuild()
            if flags:
                self._run(flags, dc)
            else:
                self.cst_run_eigenmode(dc)
        # resetting to initial value
        self.message(str(self), "resetting to initial value")
        self.editParam(Paramname, value_init)
        self.cst_rebuild()


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
