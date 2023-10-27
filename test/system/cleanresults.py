#!/usr/bin/env python3

import os
import sys

if __name__ == "__main__":
    # expect two input arguments
    # 1. raw results directory
    # 2. clean results file

    if not len(sys.argv) == 3:
        exit("Usage: python3 cleanresults.py [raw results] [clean results]")

    raw = sys.argv[1]
    clean = sys.argv[2]

    read_lines = 0
    written_lines = 0

    with open(clean, "w") as out_file:
        out_file.write(
            "a_shell,a_sat,t,b_shell,b_sat,expected_before,expected_after,actual\n"
        )

        # read all files in out directory
        for filename in os.listdir(raw):
            # split by underscore
            parts = filename.split("-")

            # check if gst or sat
            if len(parts) != 3:
                a_shell = "-1"
                a_sat = parts[1]
            else:
                # first part is a_shell
                a_shell = parts[1]
                # second part is a_sat
                a_sat = parts[2]

            with open(os.path.join(raw, filename), "r") as in_file:
                # read all lines
                # decide for each line if it is a data line
                while True:
                    line = in_file.readline()

                    if not line:
                        break

                    read_lines += 1

                    if not "," in line:
                        continue

                    # split line by comma
                    parts = line.split(",")

                    # second and third parts should be a number
                    try:
                        int(parts[1])
                        int(parts[2])
                    except:
                        continue

                    # write the line!
                    out_file.write(f"{a_shell},{a_sat},{line}")
                    written_lines += 1

    print(f"read {read_lines} lines, wrote {written_lines} lines")
