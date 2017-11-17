def get_files(path, filetypes=[".jpg"]):
    ''' path: string

        filetypes:  list or str, which file-extension
                    should be searched for

        returns path of all files as list'''
    from os import listdir
    from os.path import isfile, join
    if type(filetypes) is str:
        filetypes = [filetypes]
    for i in range(len(filetypes)):
        if filetypes[i][0] != ".":
            print()
            print("WARNING: " + filetypes[i] + " overwritten with ." + filetypes[i])
            print()
            filetypes[i] = "." + filetypes[i]
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    # print(">>> path:", path, "type:", filetype)
    # print(">>> num all files in dir:", len(onlyfiles))
    files = []
    if path[-1] != "/":
        path += "/"
    for filetype in filetypes:
        files += [path + onlyfiles[i]
                  for i in range(len(onlyfiles))
                  if onlyfiles[i][-len(filetype):] == filetype]
    # print(">>> num selected files in", path, "\n\t", len(files))
    return files


def elemByKey(lst, key):
    '''returns first list element containing key'''
    rslt = []
    for f in lst:
        if key in f:
            rslt.append(f)
    assert len(rslt) == 1
    return rslt[0]


def elemByKey_test():
    ihs = ["8aaa", "8b", "9a", "9b1", "9b2",
           "10a", "10b", "11a", "11b", "12a", "12b"]
    assert elemByKey(ihs, "8a") is "8aaa"
    assert elemByKey(ihs, "8b") is "8b"
    try:
        elemByKey(ihs, "9b")
        raise AssertionError("Modul does not react to two occuring keys")
    except AssertionError:
        pass


def notInB(iterable, B):
    ''' returns False if one
    of the iterable elements is contained in B'''
    for l in iterable:
        if l in B:
            return False
    return True


def notInB_test():
    a = ["6", "7"]
    b_false = 'GapM7'
    b_true = 'GapM5'
    assert notInB(a, b_false) is False
    assert notInB(a, b_true) is True


def testcases():
    notInB_test()
    elemByKey_test()


def timeStamp():
    import datetime
    now = datetime.datetime.now()
    m = str(now.month)
    y = str(now.year)
    if len(m) == 1:
        m = "0" + m
    return "_" + m + "_" + y

if __name__ == "__main__":
    testcases()
