import os
import copy


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
        neglecting file extension
    '''
    assert isinstance(filetypes, list)
    res = []
    for _path, subdirs, files in os.walk(path):
        for name in files:
            resname = os.path.join(_path, name)
            resname = resname.replace("\\", "/")
            resname = resname.replace(path, "")
            for ft in filetypes:
                if ft in resname:
                    res.append(resname.replace(ft, ""))
    return res


def read_one_liner(path: str):
    '''Reads single lined file and returns float

    Note
    ----
    rd0 file cosists of only on line
    containing the result digits

    Retruns
    -------
    float
        '''
    file = open(path, mode='r')
    lines = file.readlines()
    assert len(lines) == 1
    return float(lines[0])


def eval_parfile(filepath: str):
    '''Reads and evaluates all parameters in Parfile

    Parameters
    ----------
    filepath: str
        absolute path to parfile

    Returns
    -------
    dictionary
        {"parametername": {"equation": str, "value": float}}
    '''
    def compute_values(params):
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

    file = open(filepath, mode='r')
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
    params = compute_values(params)
    # return dictionary as result
    res = {}
    for p in params:
        res[p[0]] = {"equation": p[1], "value": float(p[2])}
    return res
