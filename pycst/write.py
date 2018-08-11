import os
import time
import pandas as pd


class parfile_tmp:
    '''creates a temporary parameter file at filepath

    Parameters
    ----------
    filepath: str
        target to write
    parameters_values: dict
        keys: Parameternames
        values: value
    '''

    def __init__(self, filepath: str, parameters_values: dict):
        self.filepath = filepath
        if os.path.isfile(self.filepath):
            os.remove(self.filepath)
        self.parameters_values = parameters_values

    def __enter__(self):
        file = open(self.filepath, "w")
        for key in self.parameters_values:
            value = self.parameters_values[key]
            line = key + "=" + str(value) + "\n"
            file.write(line)
        file.close()

    def __exit__(self, exc_type, exc_value, traceback):
        del self

    def __del__(self):
        os.remove(self.filepath)


def write_csv(filepath, dataframe, delimiter=";"):
    '''writes dataframe to filepath

    Notes
    -----
    Appends to csv if one is existing in filepath

    Parameters
    ----------
    filepath: str
        path where file should be written
    dataframe: pandas.dataframe
        data to be written into csv
    delimiter: str, optional
        how delimiter aka seperator shoud be choosen
    '''
    if os.path.isfile(filepath):
        df0 = pd.read_csv(filepath, delimiter=delimiter, index_col=0)
        dataframe = pd.concat([dataframe, df0], ignore_index=True)
    dataframe.to_csv(filepath, sep=delimiter)


if __name__ == "__main__":
    def test_parfile_tmp():
        path = "C:/Users/Simon/Desktop/Optimizer-test/patfile_tmp_test.par"
        dct = {"some": 1}
        with parfile_tmp(path, dct) as pfl:
            print("hey")
            time.sleep(5)
            print("goodnight")
    test_parfile_tmp()
