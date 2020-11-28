#!/usr/bin/python

"""
    Author : Micah Hoffman (@WebBreacher)
    Additions by: Mike Eriksson (@swedishmike)
    Description : Takes each username from the web_accounts_list.json file and performs the lookup to see if the entry is still valid and tries to take a screenshot of the valid ones. 

"""
import argparse
import codecs
import json
import os
import random
import signal
import string
import sys
import time
import re
import errno
from selenium import webdriver
from time import sleep
from datetime import datetime

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


###################
# Variables && Functions
###################
# Set HTTP Header info.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
}
# Regular expression to remove http/https from sites to use in filenames
remove_url = re.compile(r"https?://?")

# Create an empty list to hold the successful results
all_found_sites = []

# Parse command line input
parser = argparse.ArgumentParser(
    description="This standalone script will look up a single "
    "username using the JSON file and will attempt to take a screenshot of any profile pages that are identified."
)
parser.add_argument(
    "-s",
    "--site",
    nargs="*",
    help="[OPTIONAL] If this parameter is passed"
    "the script will check only the named site or list of sites.",
)
parser.add_argument(
    "-u",
    "--username",
    help="This is the username that will be used to check" "against.",
    required=True,
)
parser.add_argument(
    "-c",
    "--config",
    help="The full path to the web_accounts_list.json file",
    required=True,
)
args = parser.parse_args()

# Create the final results dictionary
overall_results = {}


def check_os():
    if os.name == "nt":
        operating_system = "windows"
    if os.name == "posix":
        operating_system = "posix"
    return operating_system


#
# Class for colors
#
if check_os() == "posix":

    class bcolors:
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        ENDC = "\033[0m"

        def disable(self):
            self.CYAN = ""
            self.GREEN = ""
            self.YELLOW = ""
            self.RED = ""
            self.ENDC = ""


# if we are windows or something like that then define colors as nothing
else:

    class bcolors:
        CYAN = ""
        GREEN = ""
        YELLOW = ""
        RED = ""
        ENDC = ""

        def disable(self):
            self.CYAN = ""
            self.GREEN = ""
            self.YELLOW = ""
            self.RED = ""
            self.ENDC = ""


def signal_handler(*_):
    print(bcolors.RED + " !!!  You pressed Ctrl+C. Exiting script." + bcolors.ENDC)
    finaloutput()
    sys.exit(0)


def web_call(location):
    try:
        # Make web request for that URL, timeout in X secs and don't verify SSL/TLS certs
        resp = requests.get(
            location, headers=headers, timeout=60, verify=False, allow_redirects=False
        )
    except requests.exceptions.Timeout:
        return (
            bcolors.RED
            + "      ! ERROR: CONNECTION TIME OUT. Try increasing the timeout delay."
            + bcolors.ENDC
        )
    except requests.exceptions.TooManyRedirects:
        return (
            bcolors.RED
            + "      ! ERROR: TOO MANY REDIRECTS. Try changing the URL."
            + bcolors.ENDC
        )
    except requests.exceptions.RequestException as e:
        return bcolors.RED + "      ! ERROR: CRITICAL ERROR. %s" % e + bcolors.ENDC
    else:
        return resp


def finaloutput():
    if len(overall_results) > 0:
        print("------------")
        print('The following previously "valid" sites had errors:')
        for site_with_error, results in sorted(overall_results.items()):
            print(
                bcolors.YELLOW
                + "     %s --> %s" % (site_with_error, results)
                + bcolors.ENDC
            )
    else:
        print(":) No problems with the JSON file were found.")


###################
# Main
###################

# Add this in case user presses CTRL-C
signal.signal(signal.SIGINT, signal_handler)

# Suppress HTTPS warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Attempt to read in the JSON file
try:
    with open(args.config) as data_file:
        data = json.load(data_file)
except:
    print(bcolors.RED + " Could not find the JSON file", args.config + bcolors.ENDC)
    print(bcolors.RED + " Exiting...." + bcolors.ENDC)
    sys.exit(1)


for site in data["sites"]:
    code_match, string_match = False, False
    # Examine the current validity of the entry
    if not site["valid"]:
        print(
            bcolors.CYAN
            + " *  Skipping %s - Marked as not valid." % site["name"]
            + bcolors.ENDC
        )
        continue
    if not site["known_accounts"][0]:
        print(
            bcolors.CYAN
            + " *  Skipping %s - No valid user names to test." % site["name"]
            + bcolors.ENDC
        )
        continue

    # Perform initial lookup
    # Pull the first user from known_accounts and replace the {account} with it
    url_list = []
    url = site["check_uri"].replace("{account}", args.username)
    url_list.append(url)
    uname = args.username

    for each in url_list:
        print(" -  Looking up %s" % each)
        r = web_call(each)
        if isinstance(r, str):
            # We got an error on the web call
            print(r)
            continue

        # Analyze the responses against what they should be
        code_match = r.status_code == int(site["account_existence_code"])
        string_match = r.text.find(site["account_existence_string"]) >= 0

        if args.username:
            if code_match and string_match:
                print(bcolors.GREEN + "[+] Found user at %s" % each + bcolors.ENDC)
                all_found_sites.append(each)
            continue


if all_found_sites:
    print("Trying to capture screenshot(s) from the identified site(s) now.")
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("window-size=1920x1080")
    driver = webdriver.Chrome(options=options)

    image_directory = os.path.join(
        os.getcwd(), datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + args.username
    )

    try:
        os.makedirs(image_directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # This was not a "directory exist" error..

    for site in all_found_sites:
        print(bcolors.GREEN + "Trying: ", site + bcolors.ENDC)
        filename = (
            remove_url.sub("", site)
            .replace("/", "")
            .replace("@", "")
            .replace("?", "")
            .replace("~", "")
            + ".png"
        )
        driver.get(site)
        sleep(2)
        driver.get_screenshot_as_file(image_directory + "/" + filename)

    driver.close()