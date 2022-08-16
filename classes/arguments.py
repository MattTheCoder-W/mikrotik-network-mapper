from .const import *

from argparse import ArgumentParser
import os

def net_addr(value: str) -> str:
    if not value.count(".") == 3:
        raise ValueError(f"{value} is not valid address!")
    for octet in value.split("."):
        if not octet.isnumeric() or int(octet) not in range(0, 256):
            raise ValueError(f"Octet of value: {octet} is not valid address octet!")
    return value

def mask_addr(value: str) -> str:
    if not value.count(".") == 3:
        raise ValueError(f"{value} is not valid mask address!")
    for octet in value.split("."):
        if not octet.isnumeric() or int(octet) not in range(0, 256):
            raise ValueError(f"Octet of value: {value} is not valid mask address octet!")
        binary_octet = bin(int(octet))[2:]
        if "01" in binary_octet:
            raise ValueError(f"{value} is not valid mask address!")
    return value
    

def file_or_list(value: str) -> str:
    if not os.path.exists(value) or not os.path.isfile(value):
        return value.split(" ")
    return [line.strip() for line in open(value).readlines()]

def file_path(value: str) -> str:
    ext = value.split(".")[-1]
    if ext.lower() not in FILE_FORMATS:
        print(f"Format .{ext} of output file is not supported!")
        exit(0)
    if os.path.exists(value) and os.path.isfile(value):
        while True:
            confirm = str(input(f"File {value} already exists! Do you want to overwrite it? [y/N]: "))
            if not len(confirm) or confirm.lower() == "n":
                print("File will not be altered! Quitting")
                exit(0)
            if confirm.lower() not in ["y", "n"]:
                print("Incorrect answer!")
                continue
            break
    return value


def get_args():
    parser = ArgumentParser(description="Create network map of mikrotik network")
    
    parser.add_argument("net_addr", type=net_addr, help="Network address of mikrotik network")
    parser.add_argument("net_mask", type=mask_addr, help="Mask address of mikrotik network")
    parser.add_argument("password_list", type=file_or_list, help="List of password or path to file with passwords")
    
    parser.add_argument("--output-file", type=file_path, help="Output file path, supported formats: txt, pdf, json, png")

    args = vars(parser.parse_args())
    return args
