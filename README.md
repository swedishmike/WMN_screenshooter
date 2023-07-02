# WMN_screenshooter

This is a helper script that makes use of the great [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) project and adds a bit more functionality to one of the demo scripts that were provided there.

This script is based on the `web_accounts_list_checker.py` script that [WebBreacher](https://github.com/WebBreacher) provided, with some of my own additions.

What this script will do is that it will run through the sites provided in WhatsMyName against a given username. 

If there are any hits it will then try and create screenshots of those profile pages. The screenshots will be stored in a subdirectory whose name will be based on the current date/time and the username in question so it's easy to keep track of your investigation material.

*Disclaimer:* It might not be the prettiest code (my bit, not [WebBreacher](https://github.com/WebBreacher)'s ;-) ) but it does the job. I'm of course happy for anyone to come with suggestions and improvements.

## Pre-requsities

* Python 3, I've tested this on version 3.9,7+.
* A copy of, at least, the `wmn-data.json` file from the [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) project.

## Installation 

After cloning this project, run the following from within the directory that got created:

`pip install -r requirements.txt`

This should install all necessary dependencies. It could be recommended to try and use a virtual environment for this one.

## Usage

When you run the script you need to specify the full path to the Json file from WhatsMyName, including the filename, as well as the username you're investigating as per this:

`python3 ./WMN_screenshooter.py -c /opt/WhatsMyName/wmn-data.json -u covfefe`

There are two more settings that you can use when you launch the script. You can adjust the number of threads that are being used as well as how long the timeout should be for each request. This can be useful in case of issues with bandwidth, your DNS server being swamped and so on.

The number of threads is set by using the -n / --num-threads parameter and the timeout, in seconds, are set by the -t / --timeout parameter. The example below sets a maximum of 25 threads with a 5 second timeout.

`python3 ./WMN_screenshooter.py -c /opt/WhatsMyName/wmn-data.json -u covfefe -n 25 -t 5`

I have also taken into account that you might not want to query pr0n sites so by default any site that is marked with `XXXPORNXXX` in the site list will be skipped. If you DO want to check those, just add the -x / -xxx parameter and those will be checked as well.

`python3 ./WMN_screenshooter.py -c /opt/WhatsMyName/wmn-data.json -u covfefe -x`

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)