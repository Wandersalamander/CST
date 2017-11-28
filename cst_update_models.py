import functions as f
import shutil
import os
import datetime
import cst_model_reader as cmr
import subprocess


class model_updater:
    '''updates all cst files by the master files in a
       selected directory
       (corresponding folders will be copied too)

       PARAMETERS should be PERSISTENT while moving
       results etc. to a subfolder

       keys: iterable, linking the file read and written to.

             for example if keys = ["8Gaps", "9Gaps"]:
                master_8Gaps is then linked with IH1a_8Gaps, IH_1b_8Gaps
                master_9Gaps is then linked with IH2a_9Gaps, IH_2b_9Gaps

       mute: bool, print infos or mute them

       cst_path: str, speciefies the path of "CST DESIGN ENVIRONMENT.exe"'''

    def __init__(self, target_directory, master_directory,
                 keys=[str(i) + "Gaps" for i in range(20)],
                 mute=True,
                 cst_path=None):
        if cst_path:
            self.cst_path = cst_path
        else:
            self.cst_path = "C:/Program Files (x86)/CST STUDIO SUITE 2017/CST DESIGN ENVIRONMENT.exe"
        self.keys = keys
        self.target_directory = target_directory
        assert target_directory[-1] != "/"
        assert "\\" not in target_directory
        self.files = f.get_files(target_directory, ".cst")
        self.mute = mute
        self.master_directory = master_directory
        assert master_directory[-1] != "/"
        assert "\\" not in master_directory
        self.files_master = f.get_files(master_directory, ".cst")

        now = datetime.datetime.now()

        self.subfolder = target_directory +\
            "/OLD/" +\
            str(now.year) +\
            str(now.month) +\
            str(now.day) +\
            str(now.hour) +\
            str(now.minute) +\
            "/"
        # print(self.files)
        # print(self.files_master)
        self.__check_for_keys()
        # self.rebase()

    # def rebase(self, skipParams=[]):
    def rebase(self, method="slow"):
        '''updates all cavitys using the new master file

            skipParams: list, ignores the given parameter names
                        when creating the rebased files

            method: str,"slow" or "scary",
                       "slow" uses cst import parameter method, safe to use
                       "scary" replaces parameter values in Model.par,
                                        its very fast but may lead to errors
        '''
        # self.skipParams = [x.lower() for x in skipParams]
        # assert isinstance(skipParams, list)
        self.__move_to_subfolder()
        self.__copy_from_master()
        self.__update_parameters(method=method)

    def __check_for_keys(self):
        '''checks if all required files are given by the master files
        '''
        if self.mute is False:
            print("\n\Will write CST Model from MASTER to TARGET\n\n")
        for to_file in self.files:
            src = None
            for key in self.keys:  # max 20 gaps
                if key in to_file:
                    src = f.elemByKey(self.files_master, key)
                    if self.mute is False:
                        print("MASTER\t", src)
                        print("TARGET\t", to_file, "\n")
            if src is None:
                raise FileNotFoundError(
                    "No files using keyword '" + key + "' found")

    def __move_to_subfolder(self):
        '''moves all old files to a sub directory'''
        if self.mute is False:
            print("\n\n Moving outdated models to\n", self.subfolder, "\n\n")
        for from_file in self.files:
            from_folder = from_file.split(".")[0]
            shutil.copytree(from_folder,
                            self.subfolder + from_folder.split("/")[-1])
            shutil.rmtree(from_folder)
            shutil.move(from_file,
                        self.subfolder + from_file.split("/")[-1])

    def __copy_from_master(self):
        '''adds master files to target directory
           by using the names as stated in old files'''
        if self.mute is False:
            print("\n\nCopying renamed master files to target_directory\n",
                  self.target_directory,
                  "\n\n")
        for to_file in self.files:
            to_folder = to_file.split(".")[0]
            src = None
            for key in self.keys:  # max 20 gaps
                if key in to_file:
                    src = f.elemByKey(self.files_master, key)
            shutil.copyfile(src, to_file)
            shutil.copytree(src.split(".")[0], to_folder)

    def __update_parameters(self, method="slow"):
        '''updates the parameters in the newly copied
           (copied from master to target directory)
           files

           method: str,"slow" or "scary",
                       "slow" uses cst import parameter method, safe to use
                       "scary" replaces parameter values in Model.par,
                                        its very fast but may lead to errors
              '''

        def scary(self, from_file, to_file):
            to_cst = cmr.CST_Model(to_file)
            from_cst = cmr.CST_Model(from_file)
            for param in from_cst.getParams():
                if param[0].lower() not in self.skipParams:
                    to_cst.editParam(param[0], param[1])

        def slow(self, from_file, to_file):
            par_path = "Model/3D/Model.par"
            from_par = from_file.split(".")[0] + par_path
            flag = " -c -par " + from_par
            cmd = self.cst_path + flag + " " + to_file
            assert os.path.isfile(from_file)
            assert os.path.isfile(to_file)
            assert os.path.isfile(from_par)
            subprocess.call(cmd)
        methods = ["slow", "scary"]
        assert method in methods
        if self.mute is False:
            print('''\n\nReading parameters from outdated file 
                and writing it to renamed master
                files to target_directory\n\n''')
        for to_file in self.files:
            from_file = self.subfolder + to_file.split("/")[-1]
            print(to_file)
            if method == "scary":
                scary(self, from_file, to_file)
            elif method == "slow":
                slow(self, from_file, to_file)


if __name__ == "__main__":
    def test0():
        u = model_updater("C:/Users/Simon/Desktop/IHs_newDD_notBase",
                          "C:/Users/Simon/Desktop/IHs_newDD/Tuner and Frequ")

    def test01():
        subfolder = "C:/Dropbox/Uni_privat/Master/Python/CST/TEST/OLD/201710181453/"
        for to_file in f.get_files("C:/Dropbox/Uni_privat/Master/Python/CST/TEST", ".cst"):
            to_cst = cmr.CST_Model(to_file)
            from_cst = cmr.CST_Model(subfolder + to_file.split("/")[-1])
            for param in from_cst.getParams():
                print(param)
                print(param[0], param[1])
                to_cst.editParam(param[0], param[1])
    test0()
