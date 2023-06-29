"""
This is a complete re-build of the client or at least that's the idea
"""

import argparse
import os
import signal
import sys
import json
from queue import Queue
from threading import Thread
from rich import print


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


def signal_handler(*_):
    print("[bold red] !!!  You pressed Ctrl+C. Exiting script.[/bold red]")
    sys.exit(130)


def read_in_the_useragents():
    user_agent_list = []
    try:
        with open("useragent_list.txt") as user_agents:
            for line in user_agents:
                user_agent_list.append(line.strip())
        return user_agent_list

    except:
        print(
            f"[bold red] Could not find the user agent file - useragent_list.txt [/bold red]"
        )
        print("[bold red] Exiting....[/bold red]")
        sys.exit(1)


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
        print(
            "[bold red] The Json configuration file did not parse correctly.[/bold red]"
        )
        print("[bold red] Exiting....[/bold red]")
        sys.exit(1)
    return data


def main():
    # Add this in case user presses CTRL-C
    signal.signal(signal.SIGINT, signal_handler)

    # Read in the user agent strings
    user_agent_list = read_in_the_useragents()

    # Read in the sitelist
    sitelist = read_in_the_json_file(args.config)

    # Suppress HTTPS warnings
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


if __name__ == "__main__":
    main()
