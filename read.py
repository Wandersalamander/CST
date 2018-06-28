import os


def get_files(path: str, filetypes: list):
    '''get all files in root and subdirs by filetypes


    Parameters
    ----------
    path: str
        directory to search files in
    filetypes: list
        list of strings
        all filetypes to search for

    Returns
    -------
    list,
        list of files as str(subdir + filename)
    '''
    assert isinstance(filetypes, list)
    res = []
    for path, subdirs, files in os.walk(path):
        for name in files:
            resname = os.path.join(path, name)
            resname = resname.replace("\\", "/")
            resname = resname.replace(path, "")
            for ft in filetypes:
                if ft in resname:
                    res.append(resname.replace(ft, ""))
    return res


def read_rd0(path):
    '''reads rd0 file and returns float'''
    file = open(path, mode='r')
    return float(file.readline())
