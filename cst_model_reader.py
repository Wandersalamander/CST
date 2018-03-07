import functions as f
import os
import shutil, copy
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
                filename + " not found"
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
        if cst_path:
            self.cst_path = cst_path
        else:
            try:
                self.cst_path = config.cst_path
            except AttributeError:
                config.__init__()
                self.cst_path = config.cst_path

        self.parfile0 = parfile(
            path="".join(self.filename.split(".")[:-1]) +
            "/Model/3D/Model.par",
            master_cav=self,
            autoanswer=autoanswer
        )

    def __str__(self):
        return self.filename.split(
            "/")[-1].split(".")[0]

    def __repr__(self):
        return self.filename

    def message(self, *args, **kwargs):
        '''Prints a message if self.verbose set to True.

        Parameters
        ----------
        args : str(arg)-compatible
            will be passed to print(*args) method
        '''
        if self.verbose:
            print(*args, **kwargs)

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
        it in internal list self.params

        '''
        def compute(params):
            '''compute the value of all equations
            '''

            def evaluate():
                '''try to evaluate all equations

                Note
                ----
                _params and params will be edited
                '''
                for idx, p in enumerate(_params):
                    equation = p[1]
                    equation.replace("^", "**")
                    try:
                        if len(p) != 3:
                            # for working
                            p.append(eval(equation))
                        if len(params[idx]) != 3:
                            # for output
                            params[idx].append(eval(equation))
                    except NameError:
                        pass

            # working copy
            # to apply .lower() without changing it in params
            _params = copy.deepcopy(params)
            evaluate()
            while True:
                evaluated = [p for p in _params if len(p) == 3]
                for e in evaluated:
                    name, val = e[0].lower(), e[2]
                    for i, p in enumerate(_params):
                        equation = p[1].lower()
                        if name in equation:
                            idx = equation.index(name) + len(name)
                            if idx == len(equation):
                                _params[i][1] = \
                                    equation.replace(name, str(val))
                            else:
                                # mathematical symbols after name so that
                                # following example cant happen
                                # "ih" : 1,"ih_1" :9
                                # "ih_1".replace(..)
                                # "9_1"
                                if equation[idx] in\
                                   ["+", "-", "*", "/", "^", ")"]:
                                    _params[i][1] = \
                                        equation.replace(name, str(val))
                evaluate()
                if len(evaluated) == len(_params):
                    return params

        self.message(str(self), "loading Parameters")
        file = open(self.parfile0.path, mode='r')
        # formatting
        params = [x for x in file.readlines()]
        params = [x.split("  ") for x in params]
        params = [[a for a in x if a not in [""]] for x in params]
        params = [[a.replace(" ", "") for a in x] for x in params]
        params = [x for x in params if x[-1] != "-1\n"]
        # assumption:
        # [0]: name, [1]: equation, [2]: comment
        # asserting assumtion
        for p in params:
            if len(p) > 3:
                raise Exception("Bug occured, pleas fix here")
        # neglection comment
        params = [x[:2] for x in params]
        params = sorted(params, key=lambda x: -len(x[0]))
        params = compute(params)
        self.params = params

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
        names = [a[0].lower() for a in self.params]
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

        def slow(self, Paramname, value,):
            filename = self.FilePath + "par_tmp.par"
            file = open(filename, "w")
            file.write(Paramname + "\t\t\t" + str(value))
            file.close()
            assert os.path.isfile(self.filename)
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

    def _run(self, flags, dc=None, timeout=None):
        '''Run cst command for this file.

        Note
        ----
        Use flags as specified in
        CST manual chapter "command line options"

        Parameters
        ----------
        flags : str
            Refer to CST manual
        dc : str, optional
            distributed comuting as "maincontroller:port"
            like "112.2.245.136:360000"
        timeout : int or float, optional
            time in seconds till the command is terminated

        Returns
        -------
        int
            returncode

        '''
        if dc:
            flags += "-withdc=" + str(dc) + " "
        cmd = self.cst_path + flags + self.filename
        self.message(str(self), "running command:\n\t", cmd)

        # returncode = subprocess.call(cmd)
        p = subprocess.Popen(cmd)
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise TimeoutError(
                cmd + "\nCommand reached timeout of %d seconds" % timeout)
        # except KeyboardInterrupt:
        #     # try:
        #     p.terminate()
        #     # except OSError:
        #     #    pass
        # p.wait()
        if p.returncode != 0:
            print(self.__str__(),)
            print("\tCommand", cmd)
            print("\treturncode", p.returncode)
        return p.returncode

    def cst_rebuild(self, timeout=5 * 60):
        '''CST History will be updated completely

        Note
        ----
        flags = " -m -rebuild"

        Parameters
        ----------
        timeout : int or float, optional
            time in seconds till the command is terminated

        Returns
        -------
        int
            returncode

        '''
        flags = " -m -rebuild "

        self.message(str(self), "rebuilding")
        self.toggle_mute(silent=True)
        returncode = self._run(flags=flags, timeout=timeout)
        self.toggle_mute(silent=True)
        return returncode

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

        Returns
        -------
        int
            returncode

        '''
        flags = " -m -e "
        self.message(str(self), "running Eigenmode Solver")
        self.toggle_mute(silent=True)
        returncode = self._run(flags, dc=dc)
        self.toggle_mute(silent=True)
        return returncode
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

        Returns
        -------
        int
            returncode

        '''
        flags = " -m -o "
        self.message(str(self), "running Eigenmode optimizer")
        self.toggle_mute(silent=True)
        returncode = self._run(flags, dc=dc)
        self.toggle_mute(silent=True)
        return returncode
        # cmd = self.cst_path + flags + self.filename
        # subprocess.call(cmd)

    def cst_import_parfile(self, parfilepath, timeout=600):
        '''Runs CST routine for importing .par file.

        Note
        ----
        flags = " -c -par " + parfilepath + " "

        Parameters
        ----------
        parfilepath: str
            Path to file which should be imported
            ending on ".par"
        timeout : int or float, optional
            time in seconds till the command is terminated

        Returns
        -------
        int
            returncode

        '''
        assert os.path.isfile(parfilepath)
        flags = " -c -par " + parfilepath + " "
        self.message(str(self), "importing parameter from\n\t", parfilepath)
        self.toggle_mute(silent=True)
        returncode = self._run(flags)
        self.toggle_mute(silent=True)
        return returncode

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
            if answer in ["Y", "y"]:
                self._master_cav.message("Recovering pramaters from parfile")
                self.recover()
            else:
                self._master_cav.message("Removing", self._path_backup)
                os.remove(self._path_backup)


def TEST():
    path = "C:/Users/Simon/Desktop/Test2018/testfile2018.cst"
    ih = CST_Model(path,autoanswer="A")
    names = ih.getResultNames()
    ih._loadParams()
    assert ih.isParam("lackschmack") is False
    assert ih.isParam("Mesh_model") is True
    for a in ih.params:
        print(a)
    # print(ih.getParam("tuner_stem_angle"))
    ih.editParam("shell_length", 6689)

if __name__ == "__main__":
    TEST()
