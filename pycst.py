import os
import time
import shutil
import copy
import subprocess
from config import Configuration
from pandas import DataFrame
# from pandas import read_csv
import pandas as pd
import numpy as np
import read
import write
import random


class CstModel:
    '''Multiple tools to access a cst file.


    Parameters
    ----------
    filename : str
        Path to .cst file.
    cst_path : str, optional
        Path of cst.exe. If None, path of
        config will be used.
    autoanswer : str, optional
        None, "Y" or "n"
        How to answer input-functions.
        Refer to Parfile-class.
        Refer to Parfile.__handle_existing_backup
        for further information.

    Attributes
    ----------
    csv_name: str
        how to name the csv when exporting
    parhandler : :obj:`Parfile`
        Refer to class Parfile.
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
        self.FILENAME = filename.replace("\\", "/")
        self.FILEPATH = "/".join(filename.split("/")[:-1]) + "/"
        self.RESULTPATH = self.FILENAME.split(
            ".")[:-1]  # removing fileextension
        # navigating to subfolder of file
        self.RESULTPATH = "".join(self.RESULTPATH) + "/Result/"
        self.csv_name = "Results%s.csv" % str(self)
        if cst_path:
            self.CST_PATH = cst_path
        else:
            try:
                self.CST_PATH = Configuration.cst_path
            except AttributeError:
                Configuration.__init__()
                self.CST_PATH = Configuration.cst_path

        self.parhandler = Parfile(
            path="".join(self.FILENAME.split(".")[:-1]) +
            "/Model/3D/Model.par",
            master_cav=self,
            autoanswer=autoanswer
        )

    def __str__(self):
        return self.FILENAME.split(
            "/")[-1].split(".")[0]

    def __repr__(self):
        return self.FILENAME

    def __exit__(self, *args):
        del self

    def __enter__(self):
        return self

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

    def get_resultnames(self, filetypes=[".rd0"]):
        '''Should return a list of all results in result path.


        Parameters
        ----------
        filetypes :  list or str
            Which file-extension should be searched for.

        Returns
        ------
        list
            All files in cst files ResultPath specified in __init__'''
        ROOT = self.RESULTPATH
        return read.get_files(path=ROOT, filetypes=filetypes)

    def get_result(self, resultname, filetype=".rd0", run_id="0"):
        '''Reads Result from Result folder

        Note
        ----
        Currently only rundID 0 supported


        Parameters
        ----------
        resultname : str
            Name of Result, must be located in self.RESULTPATH
        filetype : str, optional
            Currently only .rd0 files are implemented
        run_id : str, optional
            get Result by run_id
            only run_id 0 supported


        Returns
        -------
        float
            float of first line in corresponding filetype

        '''
        if run_id != "0":
            raise AttributeError("Only runID '0' allowed")
        if filetype != ".rd0":
            raise FileExistsError("Resulttype not implemented yet")
        path = self.RESULTPATH + resultname + filetype
        return read.read_one_liner(path)

    def get_results(self):
        '''Returns all rd0 results containesd in resultpath

        Returns
        -------
        res: dictionary
            keys: str, result names
            values: float, result values
        '''
        res = {}
        for resultname in self.get_resultnames():
            res[resultname] = self.get_result(resultname)
        return res

    def get_parameters(self):
        '''Loads and returns all parametes


        Returns
        -------
        dictionary
            {"parametername": {"equation": str, "value": float}}
        '''
        return read.eval_parfile(filepath=self.parhandler.path)

    def is_parameter(self, parametername):
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
            self.get_parameters()[parametername]
            return True
        except KeyError:
            return False

    def edit_parameters(self, parameters_values: dict):
        '''Imports a dictionary of Parameters to cst file

        Parameters
        ----------
        parameters_values: dict
            keys: Parameternames
            values: value
        '''
        filename = self.FILEPATH + "par_tmp.par"
        for key in parameters_values:
            assert self.is_parameter(key)
        assert os.path.isfile(self.FILENAME)
        with write.parfile_tmp(filename, parameters_values):
            self.cst_import_parfile(filename)

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
        cmd = self.CST_PATH + flags + self.FILENAME
        self.message(str(self), "running command:\n\t", cmd)

        # returncode = subprocess.call(cmd)
        p = subprocess.Popen(cmd)
        try:
            p.wait(timeout=timeout)
            returncode = p.returncode
        except subprocess.TimeoutExpired:
            returncode = 1
        # retcodes = {
        #     "0": "EXITCODE_SUCCESS",
        #     "1": "EXITCODE_FAILED",
        #     "2": "EXITCODE_ABORTEDBYUSER",
        #     "3": "EXITCODE_NOLICENSE",
        #     "4": "EXITCODE_FAILED_TO_OPEN",
        # }
        if returncode != 0:
            print(self.__str__(),)
            print("\tCommand", cmd)
            print("\treturncode %s")
        return returncode

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

    def cst_run_eigenmode(self, dc=None, timeout=None):
        '''Runs eigenmode solver for the model.

        Note
        ----
        flags = " -m -e "
        Exports CSV to self.path + self.csv_name

        Parameters
        ----------
        dc : str
            distributed comuting as "maincontroller:port" like
            "142.2.245.136:360000"
        timeout : int or float, optional
            time in seconds till the command is terminated

        Returns
        -------
        int
            returncode

        '''
        flags = " -m -e "
        self.message(str(self), "running Eigenmode Solver")
        self.toggle_mute(silent=True)
        returncode = self._run(flags, dc=dc, timeout=timeout)
        self.toggle_mute(silent=True)
        if returncode == 0:
            self.__export_csv()
        return returncode

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

    def cst_import_parfile(self, Parfilepath, timeout=600):
        '''Runs CST routine for importing .par file.

        Note
        ----
        flags = " -c -par " + Parfilepath + " "

        Parameters
        ----------
        Parfilepath: str
            Path to file which should be imported
            ending on ".par"
        timeout : int or float, optional
            time in seconds till the command is terminated

        Returns
        -------
        int
            returncode

        '''
        assert os.path.isfile(Parfilepath)
        flags = " -c -par " + Parfilepath + " "
        self.message(str(self), "importing parameter from\n\t", Parfilepath)
        self.toggle_mute(silent=True)
        returncode = self._run(flags)
        self.toggle_mute(silent=True)
        self.cst_rebuild()
        return returncode

    def __export_csv(self):
        def gen_dataframe():
            '''Creates a pandas-dataframe of all results and parameters'''
            dct = {}
            params = self.get_parameters()
            for key in params.keys():
                dct[key] = [params[key]["value"]]
            results = self.get_results()
            for key in results:
                dct[key] = [results[key]]
            return DataFrame.from_dict(dct)
        target = self.FILEPATH + self.csv_name
        df = gen_dataframe()
        write.write_csv(filepath=target, dataframe=df)
        print(str(self), "wrote to csv", target)

    def sweep(self, parametername, values, dc=None, flags=None):
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
        parametername : str
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
            assert isinstance(parametername, str)
            for v in values:
                assert isinstance(v, float) or isinstance(v, int)

        check_args()
        self.message(str(self), "sweeping", parametername)
        # value_init = self.get_parameter(parametername)[1]
        self.parhandler.backup()
        # self.message("\tInitial value", value_init)
        for run, value in enumerate(values):
            self.message("\nRun", run, "/", len(value))
            self.edit_paramert(parametername, value)
            self.cst_rebuild()
            if flags:
                self._run(flags, dc)
            else:
                self.cst_run_eigenmode(dc)
        # resetting to initial value
        self.message(str(self), "resetting to initial value")
        self.parhandler.recover()
        # self.edit_paramert(parametername, value_init)
        # self.cst_rebuild()


class Parfile:
    '''Class to handle Parfile

    Parameters
    ----------
    path : str
        Path to "Model.par".
    master_cav : :obj:`CstModel`
        Model corresponding to Parfile.
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
        assert isinstance(master_cav, CstModel)
        if not os.path.isfile(path):
            raise FileNotFoundError(str(path))
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

        Deals with a existing Parfile backup
        by asking to recover it

        Notes
        -----
        The backup-file will be DELETED
        either neglecting the parameters
        or applying them to the cst-file.

        '''
        if os.path.isfile(self._path_backup):
            self._master_cav.message("A Parfile backup has been detected")
            if self.autoanswer:
                answer = self.autoanswer
            else:
                answer = input("[Y/n] Recover parameters from Parfile?")
            if answer in ["Y", "y"]:
                self._master_cav.message("Recovering pramaters from Parfile")
                self.recover()
            else:
                self._master_cav.message("Removing", self._path_backup)
                os.remove(self._path_backup)


def TEST():
    path = "C:/Users/Simon/Desktop/Test2018/testfile2018.cst"
    ih = CstModel(path, autoanswer="A")
    assert ih.is_parameter("lackschmack") is False
    assert ih.is_parameter("Mesh_model") is True
    # print(ih.params)
    params = ih.get_parameters()
    print(params)
    # print(ih.get_parameter("tuner_stem_angle"))
    rand = random.randrange(900, 1200)
    ih.edit_parameters({"Shell_length": rand,
                        "Mesh_model": 1,
                        "Mesh_local_tubes": 0,
                        "Mesh_background": 1,
                        "Mesh_local_vac": 0,
                        })
    assert ih.get_parameters()["Shell_length"]["value"] == rand
    ih.cst_run_eigenmode()
    resnames = ih.get_resultnames()
    for r in resnames:
        ih.get_result(r)
    res = ih.get_results()
    print(res)


if __name__ == "__main__":
    TEST()
