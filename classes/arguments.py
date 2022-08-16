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

def get_args():
    parser = ArgumentParser(description="Create network map of mikrotik network")
    parser.add_argument("net_addr", type=net_addr, help="Network address of mikrotik network")
    parser.add_argument("net_mask", type=mask_addr, help="Mask address of mikrotik network")
    parser.add_argument("password_list", type=file_or_list, help="List of password or path to file with passwords")
    args = vars(parser.parse_args())
    return args
