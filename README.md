# WMN_screenshooter

This is a helper script that makes use of the great [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) project and adds a bit more functionality to one of the demo scripts that are provided there.

This script is based on the `web_accounts_list_checker.py` script that [WebBreacher](https://github.com/WebBreacher) provides there, with some of my own additions.

What this script will do is that it will run through the sites provided in WhatsMyName against a given username. 

If there are any hits it will then try and create screenshots of those profile pages. The screenshots will be stored in a subdirectory whose name will be based on the current date/time and the username in question so it's easy to keep track of your investigation material.

*Disclaimer:* It might not be the prettiest code (my bit, not [WebBreacher](https://github.com/WebBreacher)'s ;-) ) but it does the job. I'm of course happy for anyone to come with suggestions and improvements.

## Pre-requsities

* A working installation of [Selenium Web Driver](https://www.selenium.dev/documentation/en/) complete with the Chrome driver. The Chrome driver needs to be a in a directory where the Python 3 interpreter you are using can find it. 

* A copy of, at least, the `web_accounts_list.json` file from the [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) project.

## Installation 

After cloning this project, run the following from within the directory that got created:

`pip install -r requirements.txt`

This should install all necessary dependencies. It could be recommended to try and use a virtual environment for this one.

## Usage

When you run the script you need to specify the full path to the Json file from WhatsMyName, including the filename, as well as the username you're investigating as per this:

`python3 ./WMN_screenshooter.py -c /opt/WhatsMyName/web_accounts_list.json -u covfefe`
