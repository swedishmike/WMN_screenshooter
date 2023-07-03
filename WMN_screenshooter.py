"""
    Initial author : Micah Hoffman (@WebBreacher)
    Additions by: Mike Eriksson (@swedishmike)
    Description : Takes each username from the wmn-data.json file and performs the lookup to see if the entry is still valid and tries to take a screenshot of the valid ones that matches the username. 
"""

import argparse
import urllib3
import signal
import sys
import json
import re
from queue import Queue
from threading import Thread
from rich import print
from selenium import webdriver
from datetime import datetime
from pathlib import Path
from time import sleep
import httpx


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
    help="The full path to the wmn-data.json file. If it's in the same path as this program - just wmn-data.json works.",
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
parser.add_argument(
    "-x",
    "--xxx",
    help="Whether or not to query XXX sites. Default is set to No.",
    action="store_true",
)

args = parser.parse_args()

# Set HTTP Header info.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
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


def read_in_the_json_file(filelocation):
    # Attempt to read in the JSON file
    try:
        with open(filelocation) as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        print(
            f"[bold red] [!] Could not find the JSON file - {filelocation} [/bold red]"
        )
        print("[bold red] [!] Exiting....[/bold red]")
        sys.exit(1)
    except json.decoder.JSONDecodeError:
        print(
            "[bold red] [!] The Json configuration file did not parse correctly.[/bold red]"
        )
        print("[bold red] [!] Exiting....[/bold red]")
        sys.exit(1)
    return data


def validate_site(i, site_queue):
    code_match, string_match = False, False

    while True:
        site = site_queue.get()
        url = site["uri_check"].replace("{account}", args.username)
        r = web_call(url)
        if isinstance(r, str):
            # We got an error on the web call
            print(r)

        else:
            # Analyze the responses against what they should be
            code_match = r.status_code == int(site["e_code"])
            string_match = r.text.find(site["e_string"]) >= 0

            if args.username:
                if code_match and string_match:
                    # print(f"[bold green][+] Found user at {url}[/bold green]")
                    all_found_sites.append(url)
                    # continue
        site_queue.task_done()


def web_call(location):
    try:
        # Make web request for that URL, timeout in X secs and don't verify SSL/TLS certs
        resp = httpx.get(
            location,
            headers=headers,
            timeout=args.timeout,
            verify=False,
        )

    except Exception as e:
        return "[bold red] [!] ERROR " + location + " -> " + str(e) + "[/bold red]"

    else:
        return resp


def queues_and_threads(sitelist):
    # Setting up the threads, ready to query URL's.
    for i in range(num_of_threads):
        worker = Thread(
            target=validate_site,
            args=(
                i,
                site_queue,
            ),
        )
        worker.daemon = True
        worker.start()
    # Validating the data in the json file so we only try sites that are valid
    for site in sitelist["sites"]:
        if not site["valid"]:
            print(
                f"[bold cyan] [*]  Skipping {site['name']} - Marked as not valid.[/bold cyan]"
            )
            continue
        if not site["known"][0]:
            print(
                f"[bold cyan] [*]  Skipping {site['name']} - No valid user names to test.[/bold cyan]"
            )
            continue
        if not args.xxx and site["cat"] == "XXXPORNXXX":
            print(
                f"[bold cyan] [*]  Skipping {site['name']} - category is XXXPORNXXX and you're running the script without the -x/-xxx parameter.[/bold cyan]"
            )
            continue
        site_queue.put(site)
    site_queue.join()


def grab_screenshots(all_found_sites):
    print(
        "[bold green]\n [-] Trying to capture screenshot(s) from the identified site(s) now.[/bold green]"
    )
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("window-size=1920x1080")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(args.timeout)

    # eml_out = Path(Path.cwd() / "emls")

    # eml_out = Path(Path.cwd() / "emls")

    image_directory = Path(
        Path.cwd() / (datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + args.username)
    )

    try:
        print(
            f"[bold green] [-] The screenshots will be stored in [/bold green][bold cyan]{image_directory}[/bold cyan]"
        )
        if not image_directory.exists():
            image_directory.mkdir()

        # os.makedirs(image_directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise  # This was not a "directory exist" error..

    for site in all_found_sites:
        print(f"[bold green] [-] Capturing: {site}[/bold green]")
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
            driver.get_screenshot_as_file(str(image_directory) + "/" + filename)
        except TimeoutException as e:
            print(f"[bold red] [!] Timed out when trying to reach: {site}[/bold red]")
            continue
    driver.close()


def main():
    # Add this in case user presses CTRL-C
    signal.signal(signal.SIGINT, signal_handler)

    # Read in the sitelist
    sitelist = read_in_the_json_file(args.config)

    # Suppress HTTPS warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Set up the threads and queues
    queues_and_threads(sitelist)

    # Check if there's any sites to take a screenshot of - if there are, take it.
    if all_found_sites:
        grab_screenshots(all_found_sites)
    else:
        print("[bold yellow] [:(] No sites found[/bold yellow]")


if __name__ == "__main__":
    main()
