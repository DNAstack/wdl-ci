import os.path


def find_wdl_files():
    cwd = os.getcwd()
    wdl_files = []
    for root_path, _, filenames in os.walk(cwd):
        for filename in filenames:
            if filename.endswith(".wdl"):
                wdl_files.append(
                    os.path.relpath(os.path.join(root_path, filename), cwd)
                )
    return wdl_files
