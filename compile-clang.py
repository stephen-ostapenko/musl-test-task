#!/usr/bin/python3

import argparse
import os
import glob
import shutil
import subprocess
import time

# Folder with LLVM project and git branch with actual version
LLVM_PROJECT_PATH = "llvm-project"
ACTUAL_GIT_BRANCH = "release/13.x"

def get_args():
	parser = argparse.ArgumentParser(description = "Script to compile clang from sources")
	parser.add_argument("-j", "--threads", type = int, default = 1, help = "Number of threads to work with (default: 1).")

	group = parser.add_mutually_exclusive_group()
	group.add_argument("-n", "--steps", type = int, default = 1, help = "Initial bootstrap steps count (default: 1).")
	group.add_argument("-a", "--add", type = int, help = "Additional bootstrap steps count.")

	return parser.parse_args()

# Getting cmake configuration prompt
def get_cmake_prompt_with_compilers(version, c_compiler_path, cxx_compiler_path):
	result = f"cmake -S llvm -B build-v{version} -G \"Unix Makefiles\" -DLLVM_ENABLE_PROJECTS=\"clang\" -DCMAKE_BUILD_TYPE=Release"

	if (c_compiler_path):
		result += f" -DCMAKE_C_COMPILER=\"{c_compiler_path}\""

	if (cxx_compiler_path):
		result += f" -DCMAKE_CXX_COMPILER=\"{cxx_compiler_path}\""

	return result

def get_cmake_prompt(version):
	return get_cmake_prompt_with_compilers(version, "", "")

# Latest available version number is stored in the following file
LATEST_VERSION_FILE_NAME = ".clang-from-sources-latest-available-version"

def write_latest_version_to_file(version):
	fout = open(LATEST_VERSION_FILE_NAME, "w")
	fout.write(f"{version}\n")
	fout.close()

def get_latest_version_from_file():
	if (not os.path.exists(LATEST_VERSION_FILE_NAME)):
		return 0

	fin = open(LATEST_VERSION_FILE_NAME, "r")
	version = int(fin.read().split()[0])
	fin.close()
	return version

# Building completely new versions of clang from sources
def build_from_scratch(thread_count, bootstrap_count):
	# Doing cleanup before start
	if (os.path.exists(LATEST_VERSION_FILE_NAME)):
		os.remove(LATEST_VERSION_FILE_NAME)

	list_of_build_dirs = glob.glob("build-v*")
	for d in list_of_build_dirs:
		shutil.rmtree(d)

	build_versions(1, bootstrap_count, thread_count)

# Building some new versions using the latest available version of clang
def build_with_addition(thread_count, add_bootstrap_count):
	cur_version = get_latest_version_from_file()
	build_versions(cur_version + 1, cur_version + add_bootstrap_count, thread_count)

def build_versions(from_version, to_version, thread_count):
	for version in range(from_version, to_version + 1):
		start = time.time()

		# Getting right prompt for cmake
		prompt = ""
		if (version == 1):
			prompt = get_cmake_prompt(1)
		else:
			compiler_path = f"{os.getcwd()}/build-v{version - 1}/bin/"
			prompt = get_cmake_prompt_with_compilers(version, compiler_path + "clang", compiler_path + "clang++")
		
		# Configuring cmake
		subprocess.check_call(prompt, shell = True)

		# Building clang
		os.chdir(f"build-v{version}")
		subprocess.check_call(f"make clang -j {thread_count}", shell = True)
		os.chdir("..")

		end = time.time()

		write_latest_version_to_file(version)
		print(f"\n\n\tVersion {version} was built in {end - start} s\n\n")

if __name__ == "__main__":
	# Parsing arguments
	args = get_args()
	thread_count = args.threads
	bootstrap_count = args.steps
	add_bootstrap_count = args.add

	# Downloading sources from github
	if (not os.path.exists(LLVM_PROJECT_PATH)):
		subprocess.check_call("git clone https://github.com/llvm/llvm-project.git", shell = True)

	# Setting working directory
	os.chdir(LLVM_PROJECT_PATH)
	subprocess.check_call(f"git checkout {ACTUAL_GIT_BRANCH}", shell = True)

	if (add_bootstrap_count == None):
		print(f"\nBuilding {bootstrap_count} generation(s) of clang from scratch\n")
		build_from_scratch(thread_count, bootstrap_count)
	else:
		print(f"\nBuilding {add_bootstrap_count} additional generation(s) of clang\n")
		build_with_addition(thread_count, add_bootstrap_count)

	print("\n\ndone!")