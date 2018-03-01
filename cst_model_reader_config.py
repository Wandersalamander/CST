import os


class config:

        # paths to cst versions
        # you may edit this dictionary
    __cst_paths = {
        "2017": "C:/Program Files (x86)/CST STUDIO SUITE 2017/CST DESIGN ENVIRONMENT.exe",
        "2018": "C:/Program Files (x86)/CST STUDIO SUITE 2018/CST DESIGN ENVIRONMENT.exe",
    }

    def __init__():
        for version in config.__cst_paths.keys():
            path = config.__cst_paths["version"]
            assert os.path.isfile(path)
        config.cst_path = config.__cst_paths["2017"]

    def set_version(year):
        '''sets the environment path to the specified cst-version by year

                year: str or int'''
        if str(year) in config.__cst_paths.keys():
            config.cst_path = config.__cst_paths[str(year)]
        else:
            raise Exception(
                "No Path for this year specified, go specify it yourself"
            )
