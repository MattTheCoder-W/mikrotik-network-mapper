from classes.mikrotik import Mikrotik
from classes.arguments import get_args
from classes.iplist import IPList, Address, Port

import os
from argparse import ArgumentParser
import concurrent.futures
import routeros_api
import csv


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
            self.active.append({"host": host, "uname": None, "passwd": None, "conn": None})

    def find_active(self) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for host in self.hosts:
                executor.submit(self.check_host, host)

    def find_credentials(self, uname: str = "admin") -> None:
        for i, host in enumerate(self.active):
            host = host['host']
            correct_passwd = ""
            for passwd in self.passwords:
                try:
                    conn = routeros_api.RouterOsApiPool(str(host), username=uname, password=passwd, plaintext_login=True)
                    api = conn.get_api()
                except routeros_api.exceptions.RouterOsApiCommunicationError:
                    continue
                correct_passwd = passwd
                break
            if correct_passwd == "":
                print(f"Password for {str(host)} not found!")
            else:
                self.active[i]['uname'] = uname
                self.active[i]['passwd'] = passwd
                self.active[i]['conn'] = api
        header = ["Address", "User Name", "Password"]
        with open("passwords.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for host_row in self.active:
                if host_row['passwd'] is not None:
                    writer.writerow([host_row['host'], host_row['uname'], host_row['passwd']])
    
    def find_neighbors(self) -> None:
        for host in self.active:
            if host['api'] is None:
                continue
            api = host['api']
            neighbor_list = api.get_resource("/ip/neighbors").get()
            print("Neighbor list:", neighbor_list)


if __name__ == "__main__":
    args = get_args()
    print(args)
    mapper = Mapper(args)
    mapper.find_active()
    print(f"Found {len(mapper.active)} active mikrotik hosts!")
    mapper.find_credentials()
    print(mapper.active)

