#!/usr/bin/env python3

import argparse
import os
import os.path
import re
import sys
import time

from cefpython3 import cefpython as cef

player_info_re = re.compile(r"Player name changed to (\w+) Clan: (\w+) AccountId: (\w+)")
mission_name_re = re.compile(r"Mission name: (.+)")
mission_difficulty_re = re.compile(r"    difficulty=(.+)")

browser_settings = {"file_access_from_file_urls_allowed": True,
                    "javascript_access_clipboard_disallowed": True}

endscreen_file_name = None

player_status = {}
mission_status = {}

def show_screen(file_name):
    browser = cef.CreateBrowserSync(url=endscreen_file_name,
                                    window_title="This should be borderless",
                                    settings=browser_settings)
    bindings = cef.JavascriptBindings(bindToFrames=True, bindToPopups=True)
    bindings.SetProperty("player_status", player_status)
    bindings.SetProperty("mission_status", mission_status)
    browser.SetJavascriptBindings(bindings)
    cef.MessageLoop()

def process_line(line):
    global player_status
    global mission_status

    if "Player name changed" in line:
        matches = player_info_re.search(line)
        player_status["name"] = matches.group(1)
        player_status["clan"] = matches.group(2)
        print("Your name: " + matches.group(1))
        print("Your clan: " + matches.group(2))
        print("Your ID: " + matches.group(3))
    elif "Mission name:" in line:
        matches = mission_name_re.search(line)
        mission_status = {}
        mission_status["name"] = matches.group(1)
        print("Mission name: " + matches.group(1))
    elif line.startswith("    difficulty="):
        matches = mission_difficulty_re.search(line)
        mission_status["difficulty"] = matches.group(1)
        print("Mission difficulty: " + matches.group(1))
    elif "EndOfMatch.lua: Mission Succeeded" in line:
        print("End of mission!")
        print("-----------------------------------")
        show_screen(endscreen_file_name)

def process_log(log_file_name, log_interval):
    with open(log_file_name) as log_file:
        #log_file.seek(0,2)
        while True:
            curr_position = log_file.tell()
            line = log_file.readline()
            if not line:
                log_file.seek(curr_position)
                time.sleep(log_interval)
            else:
                process_line(line)

if __name__ == "__main__":
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    local_appdata_folder = os.getenv("localappdata")

    parser = argparse.ArgumentParser(description="Custom endscreen for Warframe")
    parser.add_argument("--log", default=os.path.join(local_appdata_folder, "Warframe", "EE.log"), help="Log file to read", metavar="EE.log")
    parser.add_argument("--log-interval", default=1, help="Interval between log updates")
    parser.add_argument("--screen", default="file:///default.html", help="Enscreen to use", metavar="SCREEN.HTML")
    args = parser.parse_args()

    cef.Initialize()

    endscreen_file_name = args.screen
    try:
        process_log(args.log, args.log_interval)
    except KeyboardInterrupt:
        pass

    cef.Shutdown()
