# mikrotik-network-mapper
Script for generating network map from mikrotik devices.

# Goal

The goal of this script is to:

1. Create network map of mikrotik network

2. Export map in different formats:

    * PDF

    * Text

    * Json

    * Print out map in terminal

3. Save found credentials for devices in CSV format

# Requirements

Required Python packages:

* routeros-api

# Usage

To use this script run: `python mapper.py [options] net_addr net_mask password_list`

For more info about options run: `python mapper.py -h`

## Arguments

Argument name | Argument type | Description | Example
------------- | ------------- | ----------- | -------
`net_addr`    | Ip Address    | Ip address of mikrotik network | `192.168.1.0`
`net_mask`    | Mask Address  | Mask address of mikrotik network | `255.255.255.0`
`password_list` | List of strings or file path | Path to file with passwords or list of passwords separated by space | `passwords.txt` or `pass second haslo test`

# To Do

- [ ] Create base script

    - [ ] Arguments parsing

    - [ ] Arguments checking

    - [ ] Main program class

- [ ] Find alive devices

- [ ] Check if device uses mikrotik routerOs

- [ ] Find password for device using password list

- [ ] Save found passwords to CSV file

- [ ] Connect to mikrotik device

- [ ] Find mikrotik neighbors

- [ ] Create connections based on device neighbors

- [ ] Create network map based on found connections

- [ ] Generate network map

- [ ] Save network map in different formats

    - [ ] PDF

    - [ ] Text

    - [ ] Json

    - [ ] Terminal output

- [ ] Optimize code

# Author

Created by MattTheCoder-W
