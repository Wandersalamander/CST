import functions as f
import os
import shutil
import subprocess
from cst_model_reader_config import config


class CST_Model:
    '''Multiple tools to access a cst file.


    Parameters
    ----------
    filename : str
        Path to .cst file.
    cst_path : str, optional
        Path of cst.exe. If None, path of
        cst_model_reader_config will be used.
    autoanswer : str, optional
        None, "Y" or "n"
        How to answer input-functions.
        Refer to parfile-class.
        Refer to parfile.__handle_existing_backup
        for further information.

    Attributes
    ----------
    parfile0 : :obj:`parfile`
        Refer to class parfile.
    verbose : bool
        Wether messages should be printed or not.

    '''

    def __init__(self, filename, cst_path=None, autoanswer=None):
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
        self.ResultPath = self.filename.split(
            ".")[:-1]  # removing fileextension
        # navigating to subfolder of file
        self.ResultPath = "".join(self.ResultPath) + "/Result/"
        # self.ParamPath = "".join(self.filename.split(
        #     ".")[:-1]) + "/Model/3D/" + "Model.par"
        self.parfile0 = parfile(
            path="".join(self.filename.split(".")[:-1]) +
            "/Model/3D/Model.par",
            master_cav=self,
            autoanswer=autoanswer
        )
        if cst_path:
            self.cst_path = cst_path
        else:
            try:
                self.cst_path = config.cst_path
            except AttributeError:
                config.__init__()
                self.cst_path = config.cst_path

    def __str__(self):
        return self.filename.split(
            "/")[-1].split(".")[0]

    def __repr__(self):
        return self.filename

    def message(self, *args):
        '''Prints a message if self.verbose set to True.

        Parameters
        ----------
        args : str(arg)-compatible
            will be handed to print() method
        '''
        if self.verbose:
            msg = ""
            for arg in args:
                msg += str(arg) + " "
            msg.strip()
            print(msg)

    def toggle_mute(self, silent=False):
        '''Toggels verbose value between True and False

        Parameters
        ----------
        silent : bool, optional
            Wether mute, unmute state should be printed
            when running this method.

        '''
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
        '''Should return a list of all results in result path.

        Note
        ----
        Results in sub-directories are not included yet.

        Parameters
        ----------
        filetypes :  list or str
            Which file-extension should be searched for.

        Returns
        ------
        list
            All files in cst files ResultPath specified in __init__'''
        filepaths = f.get_files(self.ResultPath, filetypes)
        # removing long path to display only the names of the files
        return [filename.split("/")[-1] for filename in filepaths]

    def getResult(self, Resultname, filetype=".rd0"):
        '''
        Parameters
        ----------
        Resultname : str
            Name of Result, must be located in self.ResultPath
        filetype : str, optional
            Currently only .rd0 files are implemented

        Returns
        -------
        float
            float of first line in corresponding rd0-file'''
        if filetype != ".rd0":
            raise FileExistsError("Resulttype not implemented yet")
        if Resultname[-4] != filetype:
            splt = Resultname.split(".")
            assert len(splt) <= 2
            Resultname = splt[0] + filetype
        file = open(self.ResultPath + Resultname, mode='r')
        return float(file.readline())

    def getParams(self):
        '''Loads and returns all parametes

        Returns all available parameter triplets as a list
        in form [[parName, parEquation, parValue],]

        Returns
        -------
        list
            list of the above mentioned triplets
        '''
        try:
            self.params
        except AttributeError:
            self._loadParams()
        return self.params

    def _loadParams(self):
        '''Loads and evaluates all parameters in parfile

        Should read all cst file parameters and insert
        it in internal list self.params'''

        def clean(param_raw):
            '''returns a list of all params neglegting parameters whichs
               value is -1
            '''

            # parameter in cst cant be named using a whitespace
            # therefore all spaces will be deleted
            params = param_raw.split("  ")
            params = [param.replace(" ", "") for param in params if param !=
                      "" and param != "\n"]
            params = [param.lower() for param in params]
            return params

        def evaluate(equation_raw):
            '''should replace parameter-names by its value or function
            '''
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
            '''should replace parameter-names only by its value
            '''
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
        file = open(self.parfile0.path, mode='r')
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
        '''Returns name, formula and computed value of Parameter

        Parameters
        ----------
        parname : string
            The parameter whichs triplet should be returned.

        Returns
        -------
        list
            list[0]: name, list[1]: formula, list[2] value
        '''
        self.getParams()
        names = [a[0] for a in self.params]
        return self.params[names.index(Paramname.lower())]

    def isParam(self, Paramname):
        '''Check if parameter is existing

        Parameters
        ----------
        Paramnmane : str
            the parameter to be checked

        Returns
        -------
        bool
            True if parameter exists
            else Flase

        '''
        try:
            self.getParam(Paramname)
            return True
        except ValueError:
            return False
    def editParam(self, Paramname, value, method="scary"):
        '''Edits the parameter value.

        Edits the parameter value in the cst parameter file
        This Script was created for CST 2017

        Note
        ----
        Call cst_rebuild after editing all parameters
        to update the geometry.

        Parameters
        ----------
        parname : string
            Parametername which should be edited.
        value : int or float
            Value which should be assigned to parameter
        method : str
            Use "scary" or "slow".

            "scary" will edit entries in the .par-file
            which is not recommended by cst staff

            "slow" will call a cst routine,
            but for more parameters its really slow.
            You may use cst_import_parfile-method
            and write your own .par file

        '''

        def scary(self, Paramname, value):
            # the parameter file is a 771 chars long file ?
            # all chars where i < 256 belong to the parameter name ?
            # all chars where  255 < i < 513 belong to the equation ?
            # all chars where i < 512 belong to comment ?
            paramFile = open(self.parfile0.path, "r")
            #  asserting its the pure paramname
            Paramname = " " + Paramname + " "
            assert self.parfile0.path[-4:] == ".par"
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
            paramFile = open(self.parfile0.path, "w")
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
        assert self.isParam(Paramname)
        self.message(str(self), "setting", Paramname, "to", value)
        if method == "slow":
            slow(self, Paramname, value)
        elif method == "scary":
            scary(self, Paramname, value)

    def _run(self, flags, dc=None):
        '''Run cst command for this file.

        Note
        ----
        Use flags as specified in
        CST manual chapter "command line options"

        Parameters
        ----------
        flags : str
            Refer to CST manual

        dc : str
            distributed comuting as "maincontroller:port"
            like "112.2.245.136:360000"
        '''
        if dc:
            flags += "-withdc=" + str(dc) + " "
        cmd = self.cst_path + flags + self.filename
        self.message(str(self), "running command:\n\t", cmd)

        returncode = subprocess.call(cmd)
        if returncode != 0:
            print(self.__str__(), "returncode", returncode)

    def cst_rebuild(self):
        '''CST History will be updated completely

        Note
        ----
        flags = " -m -rebuild"


        '''
        flags = " -m -rebuild "
        self.message(str(self), "rebuilding")
        self.toggle_mute(silent=True)
        self._run(flags)
        self.toggle_mute(silent=True)
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_run_eigenmode(self, dc=None):
        '''Runs eigenmode solver for the model.

        Note
        ----
        flags = " -m -e "

        Parameters
        ----------
        dc : str
            distributed comuting as "maincontroller:port" like
            "142.2.245.136:360000"

        '''
        flags = " -m -e "
        self.message(str(self), "running Eigenmode Solver")
        self.toggle_mute(silent=True)
        self._run(flags, dc=dc)
        self.toggle_mute(silent=True)
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_run_optimizer(self, dc=None):
        '''Runs microwave studio optimizer for the model.

        Note
        ----
        flags = " -m -o "

        Parameters
        ----------
        dc : str
            distributed comuting as "maincontroller:port" like
            "142.2.245.136:360000"

        '''
        flags = " -m -o "
        self.message(str(self), "running Eigenmode optimizer")
        self.toggle_mute(silent=True)
        self._run(flags, dc=dc)
        self.toggle_mute(silent=True)
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_import_parfile(self, parfilepath):
        '''Runs CST routine for importing .par file.

        Note
        ----
        flags = " -c -par " + parfilepath + " "

        Parameters
        ----------
        parfilepath: str
            Path to file which should be imported
            ending on ".par"


        '''
        assert os.path.isfile(parfilepath)
        flags = " -c -par " + parfilepath + " "
        self.message(str(self), "importing parameter from\n\t", parfilepath)
        self.toggle_mute(silent=True)
        self._run(flags)
        self.toggle_mute(silent=True)

    def export_csv(self):
        print("export not implemented yet")
        pass

    def sweep(self, Paramname, values, dc=None, flags=None):
        '''Performs a Eigenmode Sweep on the given values.

        Will perform a Eigenmode Sweep on the given values.
        Seperate Instances of CST will be called
        in order to perfom.

        Note
        ----
        Parameters before and after sweep will
        be the same.

        If flags are given, its not a eigenmode sweep,
        but a sweep with the selcted flag.

        Parameters
        ----------
        Paramname : str
            The selected parameter to sweep.

        values : iterable(float or int)
            The values to sweep over.

        dc : str
            Distributed comuting as "maincontroller:port" like
            "142.2.245.136:360000".

        flags : str
            Refer to module _run().
        '''

        def check_args():
            assert isinstance(Paramname, str)
            for v in values:
                assert isinstance(v, float) or isinstance(v, int)

        check_args()
        self.message(str(self), "sweeping", Paramname)
        # value_init = self.getParam(Paramname)[1]
        self.parfile0.backup()
        # self.message("\tInitial value", value_init)
        for run, value in enumerate(values):
            self.message("\nRun", run, "/", len(value))
            self.editParam(Paramname, value)
            self.cst_rebuild()
            if flags:
                self._run(flags, dc)
            else:
                self.cst_run_eigenmode(dc)
        # resetting to initial value
        self.message(str(self), "resetting to initial value")
        self.parfile0.recover()
        # self.editParam(Paramname, value_init)
        # self.cst_rebuild()


class parfile:
    '''Class to handle parfile

    Parameters
    ----------
    path : str
        Path to "Model.par".
    master_cav : :obj:`CST_Model`
        Model corresponding to parfile.
    autoanswer : str, optional
        None, "Y" or "n"
        How to answer question asked by input-funtion

    Attributes
    ----------
    path : str
        Path to Model.par

    '''

    def __init__(self, path, master_cav, autoanswer=None):
        self.autoanswer = autoanswer
        self._filetype = ".par"
        self._filetype_backup = ".parbackup"
        assert path[-len(self._filetype):] == self._filetype
        assert isinstance(master_cav, CST_Model)
        assert os.path.isfile(path)
        self._master_cav = master_cav
        self.path = path
        self._path_backup = \
            self.path[:-len(self._filetype)] + \
            self._filetype_backup
        self.__handle_existing_backup()

    def backup(self):
        '''Copies /3D/Model/Model.par to Model.parbackup.
        '''
        shutil.copyfile(self.path, self._path_backup)

    def recover(self):
        '''Recovers parameters from backup.

        Replaces content of /3D/Model/Model.par
        by content of Model.parbackup
        and rebuilds correspinding cst file.

        '''
        assert os.path.isfile(self._path_backup)
        os.remove(self.path)
        os.rename(self._path_backup, self.path)
        self._master_cav.cst_rebuild()

    def __handle_existing_backup(self):
        '''Handles previously created parameter-backups.

        Deals with a existing parfile backup
        by asking to recover it

        Notes
        -----
        The backup-file will be DELETED
        either neglecting the parameters
        or applying them to the cst-file.

        '''
        if os.path.isfile(self._path_backup):
            self._master_cav.message("A parfile backup has been detected")
            if self.autoanswer:
                answer = self.autoanswer
            else:
                answer = input("[Y/n] Recover parameters from parfile?")
            if answer == "Y" or "y":
                self._master_cav.message("Recovering")
                self.recover()
            else:
                self._master_cav.message("Removing", self._path_backup)
                os.remove(self._path_backup)


def TEST():
    path = "C:/Users/Simon/Desktop/Test2018/testfile2018.cst"
    ih = CST_Model(path)
    names = ih.getResultNames()
    ih._loadParams()
    assert ih.isParam("lackschmack") is False
    assert ih.isParam("Mesh_model") is True
    # for a in ih.params:
    #     print(a)
    # print(ih.getParam("tuner_stem_angle"))
    ih.editParam("shell_length", 6689)


if __name__ == "__main__":
    TEST()
