import functions as f
import os


class CST_Model():
    '''Read and edit parameters of a cst file
       only read simple results

       methods: getResultNames, getResult, getParam, getParams, editParam'''

    def __init__(self, filename):
        ''' initializes the path of the cst file
            and adds some internal variables

            returns None'''

        if not os.path.isfile(filename):
            raise FileNotFoundError(filename + "not found")

        self.filename = filename
        self.name = self.filename.split(
            "/")[-1]
        self.ResultPath = self.filename.split(
            ".")[:-1]  # removing fileextension
        # navigating to subfolder of file
        self.ResultPath = "".join(self.ResultPath) + "/Result/"
        self.ParamPath = "".join(self.filename.split(
            ".")[:-1]) + "/Model/3D/" + "Model.par"

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
        '''returns all available parameter triplets as a list'''
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
        # selction only param_name and its value
        self.params = params
        params = [param[0:2] + [evaluate(param[1])] for param in params]
        self.params = params
        # selction only param_name and its value
        while True:
            try:
                # abort when sum can be computed
                # abort when all p[2] are evalu
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

        if self.params:
            names = [a[0] for a in self.params]
            return self.params[names.index(paramname.lower())]
        else:
            self._loadParams()
        names = [a[0] for a in self.params]
        return self.params[names.index(paramname.lower())]

    def editParam(self, Paramname, value):
        '''edits the parameter value in the cst parameter file
           This Script was created for CST 2017

            parname: string, parametername which should be edited

            value: int or float, value which should be assigned to parameter

            returns None'''
        def count_rightnext(string, letter=" ", notLetter=False):
            ''' letter: string, which letter should be counted

                notLetter:  bool, inverts the logic,
                            i.e counts if the letter not occurs

                retunrs int, how many letters where counted'''
            assert len(letter) == 1
            for i, ltr in enumerate(string):
                if notLetter is False:
                    if ltr != letter:
                        return i  # space length
                if notLetter is True:
                    if ltr == letter:
                        return i  # wordlenth
        # the parameter file is a 771 chars long file ?
        # all chars where i < 256 belong to the parameter name ?
        # all chars where  255 < i < 513 belong to the equation ?
        # all chars where i < 512 belong to comment ?
        paramFile = open(self.ParamPath, "r")

        Paramname = " " + Paramname + " "  # asserting its the pure paramname
        assert self.ParamPath[-4:] == ".par"
        lines = paramFile.readlines()
        count = 0  # we only want to find one line
        name_end_idx = 255
        for i, line in zip(range(len(lines)), lines):
            assert len(line) == 771
            if Paramname.upper() in line[:name_end_idx + 2].upper() and line.replace(" ", "")[-3:-1] != "-1":
                index = i
                count += 1
        assert count == 1
        # tester1 = []
        # tester2 = ""
        # for i in range(len(lines[index])):
        #     if lines[index][i] != " ":
        #         tester1.append(str(i))
        #         tester2 += str(lines[index][i])
        # print("tester")
        # print(tester1)
        # countt = 0
        # for x in range(500):
        #     if (x) > 255 and (x) < 513:
        #         countt += 1
        # print("word length needed", countt)
        # print(tester2)
        # print([x for x in lines[index].split(" ") if x != ""])
        # a = lines[index].upper().index(Paramname[1:-1].upper())
        # assert a + len(Paramname[1:-1]) - 1 == name_end_idx
        # next_letter_space = count_rightnext(
        #     lines[index][name_end_idx + 1:])  # "val     32" returns 5
        # b = lines[index][name_end_idx + next_letter_space + 1:]
        # # count to next spaces ie "102.1  " returns 4
        # c = count_rightnext(b, notLetter=True)
        # val_end_index = name_end_idx + next_letter_space + c
        # print("a", a)
        # print("b", b)
        # print("c", c)
        # print(name_end_idx, next_letter_space, c)
        # print("val_end_index", val_end_index)
        # assert val_end_index == 512
        # # print("old", lines[index][val_end_index-10:val_end_index+10])
        # word = str(value)
        # newline = lines[index][:val_end_index -
        #                        len(word) + 1] + word + lines[index][val_end_index + 1:]
        # locked = True
        # i = 1
        # while locked:
        #     try:
        #         assert lines[index][:val_end_index - len(word) + 1][-i] == " "
        #         locked = False
        #     except:
        #         newline = lines[index][:val_end_index -
        #                                len(word) + 1 - i] + i * " " + word + lines[index][val_end_index + 1:]

        #         i += 1
        # print("new", newline[val_end_index-10:val_end_index+10],"\n")
        __v = str(value)
        if len(__v) > 255:
            print(__v)
            raise AttributeError("value length bigger than 255")
        # keeping name and comment
        newline = lines[index][:256] + " " * (512 - 255 -len(__v)) + __v + lines[index][513:]
        lines[index] = newline
        assert len(newline) == 771
        paramFile.close()
        paramFile = open(self.ParamPath, "w")
        for l in lines:
            paramFile.write(l)

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
