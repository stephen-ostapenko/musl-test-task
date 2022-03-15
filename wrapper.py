#!/usr/bin/python3

import sys
import os
import subprocess
import datetime
import hashlib

# Folder with LLVM project
LLVM_PROJECT_PATH = "llvm-project"

# Finding output file ("-o" option) in list of arguments
def find_output_file():
	args = sys.argv
	occ = args.count("-o")
	if (occ > 1):
		print("Multiple output files (-o).")
		exit(1)
	elif (occ == 0):
		print("Missing output file (-o).")
		exit(1)

	ind = args.index("-o")
	if (ind == len(args) - 1):
		print("-o option requires exactly one argument.")
		exit(1)

	return ind + 1

# Latest available version number is stored in the following file
LATEST_VERSION_FILE_NAME = ".clang-from-sources-latest-available-version"

def get_latest_version_from_file():
	if (not os.path.exists(LATEST_VERSION_FILE_NAME)):
		return 0

	fin = open(LATEST_VERSION_FILE_NAME, "r")
	version = int(fin.read().split()[0])
	fin.close()
	return version

# Writing executable script to file
def write_script(script, output_file_name):
	fout = open(output_file_name, "w")
	fout.write(script)
	fout.close()

	subprocess.check_call(f"chmod +x {output_file_name}", shell = True)

if __name__ == "__main__":
	args = sys.argv
	cur_path = os.getcwd()
	script_path = os.path.dirname(args[0])

	# Trying to find the latest available version of clang
	latest_version = 0
	os.chdir(script_path)
	if (os.path.exists(LLVM_PROJECT_PATH)):
		os.chdir(LLVM_PROJECT_PATH)
		latest_version = get_latest_version_from_file()
		os.chdir("..")

	# If there is no clang available, it has to be compiled
	if (latest_version == 0):
		subprocess.check_call("./compile-clang.py", shell = True)

		os.chdir(LLVM_PROJECT_PATH)
		assert(get_latest_version_from_file() == 1)
		latest_version = 1
		os.chdir("..")

	# Modifying arguments to create executable
	of = find_output_file()
	output_file_name = args[of]
	hsh = hashlib.md5(output_file_name.encode("utf-8")).hexdigest()
	args[of] += "-binary-file-" + hsh
	compiler_path = f"{os.getcwd()}/{LLVM_PROJECT_PATH}/build-v{latest_version}/bin/"
	args[0] = compiler_path + "clang++"

	os.chdir(cur_path)

	# Compiling
	print(f"Compiling executable \"{output_file_name}\" using clang version from build-v{latest_version}.")
	time = datetime.datetime.now()
	subprocess.check_call(args)

	wrapper_script = (f"#!/usr/bin/python3" "\n"
					  "\n"
					  f"# This is an automatically generated wrapper script for executable \"{output_file_name}\"." "\n"
					  f"# It executes file \"{output_file_name}-binary-file-{hsh}\"." "\n"
					  "\n"
					  "import sys" "\n"
					  "import subprocess" "\n"
					  "\n"
					  f"print(\"This executable was compiled at {time}.\", file = sys.stderr)" "\n"
					  "\n"
					  f"args = sys.argv" "\n"
					  f"args[0] += \"-binary-file-{hsh}\"" "\n"
					  f"subprocess.Popen(args = args, stdin = sys.stdin, stdout = sys.stdout, stderr = sys.stderr)" "\n")

	write_script(wrapper_script, os.path.abspath(output_file_name))
