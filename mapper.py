from classes.mikrotik import Mikrotik
from classes.arguments import get_args
from classes.iplist import IPList, Address, Port

import os
from argparse import ArgumentParser
import concurrent.futures


class Mapper:
    def __init__(self, args: dict) -> None:
        self.net_addr = Address(args['net_addr'])
        self.mask_addr = Address(args['net_mask'], is_mask=True)
        info = IPList().get_info(self.net_addr, self.mask_addr)
        self.hosts = info['hosts']
        self.net_addr = info['network']
        self.passwords = args['password_list']
        self.active = []
    
    def check_host(self, host) -> None:
        host_port = Port(host, 8291)
        # print(f"Checking {str(host)}:8291")
        if bool(host_port):
            self.active.append(host)

    def find_active(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for host in self.hosts:
                executor.submit(self.check_host, host)


if __name__ == "__main__":
    args = get_args()
    print(args)
    mapper = Mapper(args)
    mapper.find_active()
    print(f"Found {len(mapper.active)} active mikrotik hosts!")

