import os
import shutil

source_folder = os.environ["REZ_BUILD_SOURCE_PATH"].replace("\\","/")
dest_folder = os.environ["REZ_BUILD_INSTALL_PATH"].replace("\\","/")
version = os.environ["CGMTOOLS_VERSION"]

if os.path.exists(dest_folder):
    shutil.rmtree(dest_folder)

folders = [
    "mayaScratch",
    "mayaTools",
    "pi-files",
    "scripts",
]

files = [
    "cgm.wpr",
]

print("Replicating cgmTools module...")

for folder in folders:
    source_folder_path = os.path.join(source_folder, folder).replace("\\","/")
    dest_folder_path   = os.path.join(dest_folder, folder).replace("\\","/")

    try:
        shutil.copytree(source_folder_path, dest_folder_path)
        print(f"Copied folder: {dest_folder_path}")
    except Exception as e:
        print(f" - {e}")
        pass

for file in files:
    source_file_path = os.path.join(source_folder, file).replace("\\","/")
    dest_file_path   = os.path.join(dest_folder, file).replace("\\","/")

    try:
        shutil.copy(source_file_path, dest_file_path)
        print(f"Copied file: {dest_file_path}")
    except Exception as e:
        print(f" - {e}")

print("cgmTools copy complete.")

module_file_path = os.path.join(dest_folder, "cgmToolbox.mod").replace("\\","/")
cgm_scripts_path = os.path.join(dest_folder, "mayaTools").replace("\\","/")

module_contents = f"""
+ cgmTools {version} {dest_folder}
REPOSPATH = {dest_folder}
"""

with open(module_file_path, "w") as fp:
    fp.write(module_contents)

print(f"Created Maya module file: {module_file_path}")

