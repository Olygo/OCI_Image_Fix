# coding: utf-8

import os
import oci
import csv
from os import name

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# def colors
# - - - - - - - - - - - - - - - - - - - - - - - - - -
class Color:
    ESCAPE_SEQ_START="\033[{}m"
    ESCAPE_SEQ_END="\033[0m"

    def __init__(self, code):
        self.code=code

    def __call__(self, text):
        try:
            return f"{self.ESCAPE_SEQ_START.format(self.code)}{text}{self.ESCAPE_SEQ_END}"
        except Exception:
            return text

# Color instances
default_c=Color(0)
white=Color(97)
cyan=Color(96)
magenta=Color(95)
blue=Color(94)
yellow=Color(93)
green=Color(92)
red=Color(91)
black=Color(90)
white_b=Color(47)
cyan_b=Color(46)
magenta_b=Color(45)
blue_b=Color(44)
yellow_b=Color(43)
green_b=Color(42)
red_b=Color(41)
black_b=Color(40)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# clear shell screen
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def clear():
    try:
        if name == "nt":  # Windows
            os.system("cls")
        else:  # macOS, Linux, and other UNIX-like systems
            os.system("clear")
    except Exception:
        pass

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# expand local path
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def path_expander(path):

    try:
        return os.path.abspath(os.path.expanduser(path))
    except OSError as e:
        print_error("Error expanding path:", e)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print script info
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def print_info(color, v1, v2, v3):

    align="<35" if isinstance(v3, int) else "35"
    print(color(f"{'*'*5:10} {v1:20} {v2:20} {v3:{align}} {'*'*5:5}"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# print script error
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def print_error(*args, color=red, level="ERROR"):

    color=yellow if level == "INFO" else color 
    max_length=min(max(len(str(error_message)) for error_message in args) + 6, 98)
    error_box_width=max_length + 4
    error_message_width=max_length + 2
    blank_line=color("║" + " " * error_box_width + "║")

    print(color("\n╔" + "=" * error_box_width + "╗"))
    print(blank_line)
    print(color("║"), color(f"{level}!".center(error_message_width)), color("║"))
    print(blank_line)

    for error_message in args:
        error_message=str(error_message)
        if len(error_message) > 98:
            split_messages=[error_message[i:i + 98] for i in range(0, len(error_message), 98)]
            for split_message in split_messages:
                print(color("║"), color(split_message.center(error_message_width)), color("║"))
        else:
            print(color("║"), color(error_message.center(error_message_width)), color("║"))

    print(blank_line)
    print(blank_line)
    print(color("╚" + "=" * error_box_width + "╝\n"))

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check if local folder already exists
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def check_folder(folder, **output):

    try:
        if not os.path.exists(folder):
            os.mkdir(folder)
            if output:
                print_info(yellow, 'Folder', 'creating', folder[:33])
        else:
            if output:
                print_info(green, 'Report', 'folder', folder[:33])

    except Exception as e:
        print_error("check_folder error:", e)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# init csv file
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def init_csv_report(csv_report):

    try:
        fieldnames = [
            'region_name',
            'compartment_name',
            'compartment_ocid',
            'display_name',
            'ocid',
            'state',
            'schema',
            'base_image_id',
            'billable_size_in_gbs',
            'launch_mode',
            'operating_system',
            'operating_system_version',
            'size_in_mbs',
            'created_on',
            'created_at',
            'time_created'

        ]

        with open(csv_report, mode='w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

    except Exception as e:
        print_error("init_csv_report error:", e)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# write output to csv file
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def write_to_csv(csv_report, data):

    try:
        
        with open(csv_report, mode='a', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    'region_name',
                    'compartment_name',
                    'compartment_ocid',
                    'display_name',
                    'ocid',
                    'state',
                    'schema',
                    'base_image_id',
                    'billable_size_in_gbs',
                    'launch_mode',
                    'operating_system',
                    'operating_system_version',
                    'size_in_mbs',
                    'created_on',
                    'created_at',
                    'time_created'
                    ])

            writer.writerow({
                'region_name': data.get('region_name'),
                'compartment_name': data.get('compartment_name'),
                'compartment_ocid': data.get('compartment_ocid'),
                'display_name': data.get('display_name'),
                'ocid': data.get('ocid'),
                'state': data.get('state'),
                'schema': data.get('schema'),
                'base_image_id': data.get('base_image_id'),
                'billable_size_in_gbs': data.get('billable_size_in_gbs'),
                'launch_mode': data.get('launch_mode'),
                'operating_system': data.get('operating_system'),
                'operating_system_version': data.get('operating_system_version'),
                'size_in_mbs': data.get('size_in_mbs'),
                'created_on': data.get('created_on'),
                'created_at': data.get('created_at'),
                'time_created': data.get('time_created')
            })

    except Exception as e:
        print_error("write_to_csv error:", e)
        raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# check if file size > xx bytes 
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def check_file_size(file_path, size):
    """
    Checks if a file exceeds a given size and returns:
      - the file size in a human-readable format (B, KB, MB, GB)
      - a boolean indicating whether it exceeds the threshold.
    If the file size is smaller than the threshold, the file is deleted.
    """

    file_size_bytes = os.path.getsize(file_path)
    exceeds_limit = file_size_bytes > size

    # Convert size to human-readable units
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    readable_size = file_size_bytes
    unit_index = 0
    while readable_size >= 1024 and unit_index < len(units) - 1:
        readable_size /= 1024
        unit_index += 1

    readable_size_str = f"{readable_size:.2f} {units[unit_index]}"

    # Delete the file if smaller than the threshold
    if not exceeds_limit:
        try:
            os.remove(file_path)
            print(green("  - No data collected, report file deleted"))
            return False
        except Exception as e:
            print_error("Error deleting file:", e)

    return readable_size_str, exceeds_limit

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# Calculate script execution duration
# - - - - - - - - - - - - - - - - - - - - - - - - - -
def format_duration(seconds):

    days, rem=divmod(seconds, 86400)
    hours, rem=divmod(rem, 3600)
    minutes, seconds=divmod(rem, 60)
    return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"