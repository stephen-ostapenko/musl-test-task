#!/usr/bin/python3

import argparse
import os
import glob
import shutil
import subprocess
import time

def get_args():
	parser = argparse.ArgumentParser(description = "Script to compile clang from sources")

	parser.add_argument("-n", "--steps", type = int, default = 1, help = "Bootstrap steps count (default: 1).")
	parser.add_argument("-j", "--threads", type = int, default = 1, help = "Number of threads to work with (default: 1).")

	return parser.parse_args()

def get_cmake_prompt_with_compilers(version, c_compiler_path, cxx_compiler_path):
	result = f"cmake -S llvm -B build-v{version} -G \"Unix Makefiles\" -DLLVM_ENABLE_PROJECTS=\"clang\" -DCMAKE_BUILD_TYPE=Release"

	if (c_compiler_path):
		result += f" -DCMAKE_C_COMPILER=\"{c_compiler_path}\""

	if (cxx_compiler_path):
		result += f" -DCMAKE_CXX_COMPILER=\"{cxx_compiler_path}\""

	return result

def get_cmake_prompt(version):
	return get_cmake_prompt_with_compilers(version, "", "")

LATEST_VERSION_FILE_NAME = ".clang-from-sources-latest-available-version"

def write_latest_version_to_file(version):
	out = open(LATEST_VERSION_FILE_NAME, "w")
	out.write(str(version))
	out.close()

LLVM_PROJECT_PATH = "llvm-project"

args = get_args()
bootstrap_count = args.steps
thread_count = args.threads

# Downloading sources from github
if (not os.path.exists(LLVM_PROJECT_PATH)):
	subprocess.check_call("git clone https://github.com/llvm/llvm-project.git", shell = True)

# Doing cleanup before start
os.chdir(LLVM_PROJECT_PATH)
if (os.path.exists(LATEST_VERSION_FILE_NAME)):
	os.remove(LATEST_VERSION_FILE_NAME)

list_of_build_dirs = glob.glob("build-v*")
for d in list_of_build_dirs:
	shutil.rmtree(d)

# First compilation
exit(0)
start = time.time()

subprocess.check_call(get_cmake_prompt(1), shell = True)

os.chdir("build-v1")
subprocess.check_call(f"make clang -j {thread_count}", shell = True)
os.chdir("..")

end = time.time()
print(f"Version 1 created in {end - start} s")

# Further compilations
for version in range(2, bootstrap_count + 1):
	start = time.time()

	compiler_path = f"build-v{version - 1}/bin"
	subprocess.check_call(get_cmake_prompt_with_compilers(version, compiler_path + "clang", compiler_path + "clang++"), shell = True)

	os.chdir(f"build-v{version}")
	subprocess.check_call(f"make clang -j {thread_count}", shell = True)
	os.chdir("..")

	end = time.time()
	print(f"Version {version} created in {end - start} s")
