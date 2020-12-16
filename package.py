name = "cgmTools"
version = "2020.4-ta.0.0.1"
build_command = "python {root}/rez_build.py"


# Release this as an internal package
with scope("config") as c:
    import sys
    if 'win' in str(sys.platform):
        c.release_packages_path = "R:/int"
        # c.local_packages_path = "E:/dev/path"
    else:
        c.release_packages_path = "/r/int"
        # c.local_packages_path = "/t/dev/path"


authors=["kiki"]


@early()
def set_version_in_env():
    import os
    os.putenv("CGMTOOLS_VERSION", this.version)


def commands():
    env["MAYA_SCRIPT_PATH"].append("{root}/mayaTools")
    env["PYTHONPATH"].append("{root}/mayaTools")
    env["MAYA_MODULE_PATH"].append("{root}")

