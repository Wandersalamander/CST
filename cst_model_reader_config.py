import os


class config:

    # here new paths can be added
    __cst_paths = {
        "2017": "C:/Program Files (x86)/CST STUDIO SUITE 2017/CST DESIGN ENVIRONMENT.exe",
        "2018": "C:/Program Files (x86)/CST STUDIO SUITE 2018/CST DESIGN ENVIRONMENT.exe",
    }

    def __init__(version="2018"):
        '''Variables to run cst.

        Parameters
        ----------
        version : str or int, optional
            The Year of the cst version
            like "2018"

        '''
        for version in config.__cst_paths.keys():
            path = config.__cst_paths[version]
            assert os.path.isfile(path)
        print("Using CST", str(version))
        config.cst_path = config.__cst_paths[str(version)]

    def set_version(year):
        '''sets the environment path to the specified cst-version by year

        Parameters
        ----------
        year : str or int
            Something like "2017"

        '''
        if str(year) in config.__cst_paths.keys():
            config.cst_path = config.__cst_paths[str(year)]
        else:
            raise Exception(
                "No Path for selected year specified, go specify it yourself"
            )
