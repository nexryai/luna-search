import sys
import os
import time
import inspect


def info(message: str):
    target_file = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
    sys.stdout.write(f"[{target_file}]\033[32;1m [INFO]\033[0m " + str(message) + "\n")


def warn(message: str):
    target_file = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
    sys.stdout.write(f"[{target_file}]\033[33;1m [WARNING]\033[0m " + str(message) + "\n")


def dbg(message: str):
    if os.environ['DEBUG_MODE'] == "true":
        target_file = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
        sys.stdout.write(f"[{target_file}]\033[90;1m [DEBUG] @{time.time()}\033[0m " + str(message) + "\n")


def error(message: str):
    target_file = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
    sys.stderr.write(f"[{target_file}]\033[31;1m [ERROR] " + str(message) + "\033[0m\n")


def fatal_error(message: str):
    target_file = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]
    sys.stderr.write("\n\033[31;1m=!=========FATAL ERROR=========!=\n")
    sys.stderr.write(f"\033[31m[{target_file}] {message}\n")
    sys.stderr.write("\033[31;1m=================================\033[0m\n")
