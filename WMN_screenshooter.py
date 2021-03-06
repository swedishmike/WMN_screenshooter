#!/usr/bin/python

"""
    Author : Micah Hoffman (@WebBreacher)
    Additions by: Mike Eriksson (@swedishmike)
    Description : Takes each username from the web_accounts_list.json file and performs the lookup to see if the entry is still valid and tries to take a screenshot of the valid ones. 
"""
import argparse
import json
import os
import signal
import sys
import re
import errno
from rich import print
from queue import Queue
from threading import Thread
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from time import sleep
from datetime import datetime

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning


# Parse command line input
parser = argparse.ArgumentParser(
    description="This standalone script will look up a single "
    "username using the JSON file and will attempt to take a screenshot of any profile pages that are identified."
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
parser.add_argument(
    "-t",
    "--timeout",
    help="The amount of seconds the script will wait for a site to respond.",
    type=int,
    default=10,
)
parser.add_argument(
    "-n",
    "--num-threads",
    help="The amount concurrent threads the program will use to poll sites etc.",
    type=int,
    default=50,
)
args = parser.parse_args()

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

# Set up the number of threads available
num_of_threads = args.num_threads

# Create an empty list to hold the successful results
all_found_sites = []


# Set up the queue of sites to query
site_queue = Queue()


def signal_handler(*_):
    print("[bold red] !!!  You pressed Ctrl+C. Exiting script.[/bold red]")
    sys.exit(130)


def web_call(location):
    try:
        # Make web request for that URL, timeout in X secs and don't verify SSL/TLS certs
        resp = requests.get(
            location,
            headers=headers,
            timeout=args.timeout,
            verify=False,
            allow_redirects=False,
        )
    except requests.exceptions.Timeout:
        return "[bold red]      ! ERROR: CONNECTION TIME OUT. Try increasing the timeout delay.[/bold red]"
    except requests.exceptions.TooManyRedirects:
        return "[bold red]      ! ERROR: TOO MANY REDIRECTS. Try changing the URL.[/bold red]"
    except requests.exceptions.RequestException as e:
        return "[bold red]      ! ERROR: CRITICAL ERROR." + e + "[/bold red]"
    else:
        return resp


def read_in_the_json_file(filelocation):
    # Attempt to read in the JSON file
    try:
        with open(filelocation) as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        print(f"[bold red] Could not find the JSON file - {filelocation} [/bold red]")
        print("[bold red] Exiting....[/bold red]")
        sys.exit(1)
    except json.decoder.JSONDecodeError:
        print("[bold red] The Json configuration file did not parse correctly.[/bold red]")
        print("[bold red] Exiting....[/bold red]")
        sys.exit(1)

    return data


def validate_site(i, site_queue):
    code_match, string_match = False, False

    while True:
        site = site_queue.get()
        url = site["check_uri"].replace("{account}", args.username)
        r = web_call(url)
        if isinstance(r, str):
            # We got an error on the web call
            print(r)

        else:
            # Analyze the responses against what they should be
            code_match = r.status_code == int(site["account_existence_code"])
            string_match = r.text.find(site["account_existence_string"]) >= 0

            if args.username:
                if code_match and string_match:
                    print(f"[bold green][+] Found user at {url}[/bold green]")
                    all_found_sites.append(url)
                    # continue
        site_queue.task_done()


def queues_and_threads(data):
    # Setting up the threads, ready to query URL's.
    for i in range(num_of_threads):
        worker = Thread(
            target=validate_site,
            args=(
                i,
                site_queue,
            ),
        )
        worker.setDaemon(True)
        worker.start()
    # Validating the data in the json file so we only try sites that are valid
    for site in data["sites"]:
        if not site["valid"]:
            print(f"[bold cyan] *  Skipping {site['name']} - Marked as not valid.[/bold cyan]")
            continue
        if not site["known_accounts"][0]:
            print(
                f"[bold cyan] *  Skipping {site['name']} - No valid user names to test.[/bold cyan]"
            )
            continue
        site_queue.put(site)
    site_queue.join()


def grab_screenshots(all_found_sites):
    print(
        "[bold green]\nTrying to capture screenshot(s) from the identified site(s) now.[/bold green]"
    )
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(args.timeout)

    image_directory = os.path.join(
        os.getcwd(), datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + args.username
    )

    try:
        print(
            f"[bold green]The screenshots will be stored in [/bold green][bold cyan]{image_directory}[/bold cyan]"
        )
        os.makedirs(image_directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # This was not a "directory exist" error..

    for site in all_found_sites:
        print(f"[bold green]Capturing: {site}[/bold green]")
        filename = (
            remove_url.sub("", site)
            .replace("/", "")
            .replace("@", "")
            .replace("?", "")
            .replace("~", "")
            + ".png"
        )
        try:
            driver.get(site)
            sleep(2)
            driver.get_screenshot_as_file(image_directory + "/" + filename)
        except TimeoutException as e:
            print(f"[bold red]Timed out when trying to reach: {site}[/bold red]")
            continue
    driver.close()


def main():
    # Add this in case user presses CTRL-C
    signal.signal(signal.SIGINT, signal_handler)

    # Suppress HTTPS warnings
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Read in the Json file with site definitions
    data = read_in_the_json_file(args.config)

    # Create the threads and queues to check all the sites
    queues_and_threads(data)

    # Check if there's any sites to take a screenshot of - if there are, take it.
    if all_found_sites:
        grab_screenshots(all_found_sites)
    else:
        print("[bold yellow]No sites found[/bold yellow]")


if __name__ == "__main__":
    main()
