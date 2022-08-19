from classes.arguments import get_args
from classes.iplist import IPList, Address, Port

import concurrent.futures
import routeros_api
import csv
import math
from PIL import Image, ImageDraw, ImageFont
import random
import json


class Mapper:
    def __init__(self, args: dict) -> None:
        self.net_addr = Address(args['net_addr'])
        self.mask_addr = Address(args['net_mask'], is_mask=True)
        info = IPList().get_info(self.net_addr, self.mask_addr)
        self.hosts = info['hosts']
        self.net_addr = info['network']
        self.passwords = args['password_list']
        self.passwords.append("")
        self.active = []
        self.macs = []
        self.nodes = []
    
    def check_host(self, host) -> None:
        if bool(Port(host, 8291)):
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
                    api = routeros_api.RouterOsApiPool(str(host), username=uname, password=passwd, plaintext_login=True).get_api()
                except routeros_api.exceptions.RouterOsApiCommunicationError:
                    continue
                correct_passwd = passwd
                break
            if correct_passwd == None:
                print(f"Password for {str(host)} not found!")
            else:
                self.active[i]['uname'] = uname
                self.active[i]['passwd'] = passwd
                self.active[i]['conn'] = api
        with open("passwords.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "User Name", "Password"])
            for host_row in self.active:
                if host_row['passwd'] is not None:
                    writer.writerow([host_row['host'], host_row['uname'], host_row['passwd']])
    
    def find_neighbors(self) -> None:
        for i, host in enumerate(self.active):
            if host['conn'] is None:
                continue
            api = host['conn']
            node_info = {
                'name': api.get_resource("/system/identity").get()[0]['name'],
                'interfaces': {}
            }
            for addr_info in api.get_resource("/ip/addr").get():
                interface_info = {"neighbors": []}
                name = addr_info['interface']
                interface_info['address'] = addr_info['address']
                for inter in api.get_resource("/interface").get():
                    if inter['name'] == name:
                        interface_info['mac'] = inter['mac-address']
                        if interface_info['mac'] not in self.macs:
                            self.macs.append(interface_info['mac'])
                        break
                node_info['interfaces'][name] = interface_info
            neighbor_list = api.get_resource("/ip/neighbor").get()
            for neighbor in neighbor_list:
                neighbor_info = {}
                if "address" in neighbor:
                    neighbor_info["address"] = neighbor['address']
                try:
                    interface = neighbor['interface']
                    neighbor_info["mac"] = neighbor['mac-address']
                    neighbor_info["hostname"] = neighbor['identity']
                except KeyError:
                    continue
                if "," in interface:
                    continue
                node_info['interfaces'][interface]['neighbors'].append(neighbor_info)
                if neighbor['mac-address'] not in self.macs:
                    self.macs.append(neighbor['mac-address'])
            self.nodes.append(node_info)
    
    def make_map(self, out_file: str = "png"):
        out_format = out_file.split(".")[-1] if "." in out_file else "stdout"
        if out_format == "json":
            json_obj = json.dumps(self.nodes, indent=4)
            with open(out_file, "w") as out:
                out.write(json_obj)
            return
        if out_format == "txt" or out_format == "stdout":
            out = []
            for node in self.nodes:
                out.append(f"{node['name']}:")
                for interface in node['interfaces']:
                    interface_info = node['interfaces'][interface]
                    out.append(f"\tInterface: {interface} -> {interface_info['address']} ({interface_info['mac']})")
                    for neighbor in interface_info['neighbors']:
                        if "address" in neighbor:
                            out.append(f"\t\tAddress: {neighbor['address']}")
                        out.append(f"\t\tMAC: {neighbor['mac']}")
                        out.append(f"\t\tHostname: {neighbor['hostname']}")
                        out.append("\t\t" + "="*20)
            if out_format == "txt":
                with open(out_file, "w") as f:
                    f.writelines([line+"\n" for line in out])
            else:
                for line in out:
                    print(line)
            return

        # GRAPHICAL
        W, H = [1080, 1080]
        OFFSET = 300
        CENTER = [int(W//3), int(H//1.5)]
        RADIUS = int(W//2)
        amount = len(self.macs)
        deg_step = int(360 // amount)

        points = []
        cur_deg = deg_step
        for i, mac in enumerate(self.macs):
            point_info = {}
            y = int(round(math.cos(math.radians(cur_deg)) * RADIUS, 0))+CENTER[1]
            x = int(round(math.sin(math.radians(cur_deg)) * RADIUS, 0))+CENTER[0]
            point_info['mac'] = mac
            point_info['pos'] = [x, y]
            points.append(point_info)
            cur_deg += deg_step
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
        node_macs = []
        for node in self.nodes:
            for interface in node['interfaces']:
                interface = node['interfaces'][interface]
                node_macs.append(interface['mac'])
        for node in self.nodes:
            for interface in node['interfaces']:
                interface = node['interfaces'][interface]
                mac = interface['mac']
                pos = [p['pos'] for p in points if p['mac'] == mac][0]
                # draw.text((pos[0]-60+(OFFSET), pos[1]+60), node['name'], (0, 0, 0), font=font)
                # draw.text((pos[0]-60+(OFFSET), pos[1]+90), interface['address'], (0, 0, 0), font=font)
                for neighbor in interface['neighbors']:
                    if neighbor['mac'] in node_macs:
                        continue
                    next_pos = [p['pos'] for p in points if p['mac'] == neighbor['mac']][0]
                    draw.line([pos[0]+(OFFSET), pos[1], next_pos[0]+(OFFSET), next_pos[1]], (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)), width=5)
                    draw.text((next_pos[0]-60+(OFFSET), next_pos[1]+60), neighbor['hostname'], (0, 0, 0), font=font)
                    if "address" in neighbor:
                        draw.text((next_pos[0]-60+(OFFSET), next_pos[1]+90), neighbor['address'], (0, 0, 0), font=font)
        img.save(out_file)


if __name__ == "__main__":
    args = get_args()
    out_file = "stdout" if args['output_file'] is None else args['output_file']
    mapper = Mapper(args)
    mapper.find_active()
    print(f"Found {len(mapper.active)} active mikrotik hosts!")
    mapper.find_credentials()
    mapper.find_neighbors()
    mapper.make_map(out_file=out_file)
