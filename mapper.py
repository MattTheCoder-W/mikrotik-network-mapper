from classes.mikrotik import Mikrotik
from classes.arguments import get_args
from classes.iplist import IPList, Address, Port

import os
from argparse import ArgumentParser
import concurrent.futures
import routeros_api
import csv
import math
from PIL import Image, ImageDraw, ImageFont
import random


class Mapper:
    def __init__(self, args: dict) -> None:
        self.net_addr = Address(args['net_addr'])
        self.mask_addr = Address(args['net_mask'], is_mask=True)
        info = IPList().get_info(self.net_addr, self.mask_addr)
        self.hosts = info['hosts']
        self.net_addr = info['network']
        self.passwords = args['password_list']
        self.passwords.append("")
        print(self.passwords)
        self.active = []
        self.macs = []
        self.nodes = []
    
    def check_host(self, host) -> None:
        host_port = Port(host, 8291)
        if bool(host_port):
            self.active.append({"host": host, "uname": None, "passwd": None, "conn": None})

    def find_active(self) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for host in self.hosts:
                executor.submit(self.check_host, host)

    def find_credentials(self, uname: str = "admin") -> None:
        for i, host in enumerate(self.active):
            host = host['host']
            correct_passwd = None
            for passwd in self.passwords:
                try:
                    conn = routeros_api.RouterOsApiPool(str(host), username=uname, password=passwd, plaintext_login=True)
                    api = conn.get_api()
                except routeros_api.exceptions.RouterOsApiCommunicationError as e:
                    continue
                correct_passwd = passwd
                break
            if correct_passwd == None:
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
        for i, host in enumerate(self.active):
            if host['conn'] is None:
                continue
            api = host['conn']
            node_info = {}

            node_info['name'] = api.get_resource("/system/identity").get()[0]['name']

            node_info["interfaces"] = {}
            addr_list = api.get_resource("/ip/addr").get()
            mac_list = api.get_resource("/interface").get()

            for addr_info in addr_list:
                interface_info = {"neighbors": []}
                name = addr_info['interface']
                interface_info['address'] = addr_info['address']
                for inter in mac_list:
                    if inter['name'] == name:
                        interface_info['mac'] = inter['mac-address']
                        if interface_info['mac'] not in self.macs:
                            self.macs.append(interface_info['mac'])
                        break
                node_info['interfaces'][name] = interface_info

            neighbor_list = api.get_resource("/ip/neighbor").get()
            for neighbor in neighbor_list:
                print(neighbor)
                neighbor_info = {}
                if "address" in neighbor:
                    neighbor_info["address"] = neighbor['address']

                try:
                    interface = neighbor['interface']
                    neighbor_info["mac"] = neighbor['mac-address']
                    neighbor_info["hostname"] = neighbor['identity']
                except KeyError:
                    continue
                node_info['interfaces'][interface]['neighbors'].append(neighbor_info)
                if neighbor['mac-address'] not in self.macs:
                    self.macs.append(neighbor['mac-address'])
            self.nodes.append(node_info)
    
    def make_map(self):
        W, H = [1080, 1080]
        OFFSET = 300
        max_in_row = 3
        row_step = int(W//max_in_row)
        amount = len(self.macs)
        rows = int(math.ceil(amount / max_in_row))
        vertical_step = int(H // rows)
        points = []
        for i, mac in enumerate(self.macs):
            point_info = {}
            row = int(math.ceil((i+1) / max_in_row))
            y = row * vertical_step
            column = int((i+1) % 3)
            x = column * row_step
            point_info['mac'] = mac
            point_info['pos'] = [x, y]
            points.append(point_info)
        print(points)
        print(rows, len(points))

        img = Image.new("RGB", (W+OFFSET, H+OFFSET), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("SansSerif.ttf", size=20)
        for point in points:
            pos = point['pos']
            pos = [pos[0]+(OFFSET), pos[1]]
            tl = [pos[0]-25, pos[1]-25]
            br = [pos[0]+25, pos[1]+25]
            draw.ellipse([tl[0], tl[1], br[0], br[1]], "red")
            draw.text((pos[0]-80, pos[1]+30), point['mac'], (0, 0, 0), font=font)
        
        for node in self.nodes:
            for interface in node['interfaces']:
                interface = node['interfaces'][interface]
                mac = interface['mac']
                pos = [p['pos'] for p in points if p['mac'] == mac][0]
                draw.text((pos[0]-60+(OFFSET), pos[1]+60), node['name'], (0, 0, 0), font=font)
                draw.text((pos[0]-60+(OFFSET), pos[1]+90), interface['address'], (0, 0, 0), font=font)
                print(pos, mac)
                for neighbor in interface['neighbors']:
                    next_pos = [p['pos'] for p in points if p['mac'] == neighbor['mac']][0]
                    draw.text((next_pos[0]-60+(OFFSET), next_pos[1]+60), neighbor['hostname'], (0, 0, 0), font=font)
                    if "address" in neighbor:
                        draw.text((next_pos[0]-60+(OFFSET), next_pos[1]+90), neighbor['address'], (0, 0, 0), font=font)
                    draw.line([pos[0]+(OFFSET), pos[1], next_pos[0]+(OFFSET), next_pos[1]], (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)), width=5)
        
        img.save("output.png")


if __name__ == "__main__":
    args = get_args()
    print(args)
    mapper = Mapper(args)
    mapper.find_active()
    print(f"Found {len(mapper.active)} active mikrotik hosts!")
    mapper.find_credentials()
    # print(mapper.active)
    mapper.find_neighbors()

    print(mapper.nodes)

    mapper.make_map()
