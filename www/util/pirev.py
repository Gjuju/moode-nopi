#!/usr/bin/python3
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2014 The moOde audio player project / Tim Curtis
# Copyright 2020 @bitlab (@bitkeeper Git)
#

#
# Show Pi revision code information
#
# Revision code information taken from:
# https://www.raspberrypi.org/documentation/hardware/raspberrypi/revision-codes/README.md
#

import argparse
import subprocess
import sys

OLD_REVISION_CODES = {
    # code  mod   rev    mem      manufacturer
    0x002: ["B", "1.0", "256MB", "Egoman"],
    0x003: ["B", "1.0", "256MB", "Egoman"],
    0x004: ["B", "2.0", "256MB", "Sony UK"],
    0x005: ["B", "2.0", "256MB", "Qisda"],
    0x006: ["B", "2.0", "256MB", "Egoman"],
    0x007: ["A", "2.0", "256MB", "Egoman"],
    0x008: ["A", "2.0", "256MB", "Sony UK"],
    0x009: ["A", "2.0", "256MB", "Qisda"],
    0x00d: ["B", "2.0", "512MB", "Egoman"],
    0x00e: ["B", "2.0", "512MB", "Sony UK"],
    0x00f: ["B", "2.0", "512MB", "Egoman"],
    0x010: ["B+", "1.2", "512MB", "Sony UK"],
    0x011: ["CM1", "1.0", "512MB", "Sony UK"],
    0x012: ["A+", "1.1", "256MB", "Sony UK"],
    0x013: ["B+", "1.2", "512MB", "Embest"],
    0x014: ["CM1", "1.0", "512MB", "Embest"],
    0x015: ["A+", "1.1", "256MB/512MB", "Embest"]
}

PI_TYPES = {
    # code [type, model num, dsi ports]
    0: ["A","1"],
    1: ["B","1","1"],
    2: ["A+","1","1"],
    3: ["B+","1","1"],
    4: ["2B","2","1"],
    5: ["Alpha (early prototype)","1","1"],
    6: ["CM1","1","1"],
    8: ["3B","3","1"],
    9: ["Zero","0","0"],
    0xa: ["CM3","3","2"],
    0xc: ["Zero W","0","0"],
    0xd: ["3B+","3","1"],
    0xe: ["3A+","3","1"],
    0xf: ["Internal","Internal","Internal"],
    0x10: ["CM3+","3","2"],
    0x11: ["4B","4","1"],
    0x12: ["Zero 2 W","0","0"],
    0x13: ["400","4","1"],
    0x14: ["CM4","4","2"],
    0x15: ["CM4S","4","2"],
    0x16: ["Internal use only","Internal","Internal"],
    0x17: ["5B","5","2"],
    0x18: ["CM5","5","2"],
    0x19: ["500","5","1"],
    0x1a: ["CM5 Lite","5","2"]
}

PI_MEM = {
    0: "256MB",
    1: "512MB",
    2: "1GB",
    3: "2GB",
    4: "4GB",
    5: "8GB",
    6: "16GB"
}

PI_PROC = {
    0: "BCM2835",
    1: "BCM2836",
    2: "BCM2837",
    3: "BCM2711",
    4: "BCM2712"
}

PI_MAN = {
    0: "Sony UK",
    1: "Egoman",
    2: "Embest",
    3: "Sony Japan",
    4: "Embest",
    5: "Stadium"
}

def decode_new_style_code(code):
    # Mask: NOQuuuWuFMMMCCCCPPPPTTTTTTTTRRRR
    new_style = (code>>23)&0x1 == 1 # new/old style F

    if new_style == True:
        try:
            type = PI_TYPES[(code>>4)&0xff][0] # model TTTTTTTT
        except KeyError:
            type = "Unknown Pi model"
        try:
            num = PI_TYPES[(code>>4)&0xff][1] # model num N
        except KeyError:
            num = "Unknown Pi model"
        try:
            dsi = PI_TYPES[(code>>4)&0xff][2] # dsi ports N
        except KeyError:
            dsi = "Unknown Pi model"
        try:
            mem = PI_MEM[(code>>20)&0x7] # mem MMM
        except KeyError:
            mem = "?GB"
        try:
            man = PI_MAN[(code>>16)&0xf] # manufacture CCCC
        except KeyError:
            man = "Unknown manufacturer"
        try:
            proc = PI_PROC[(code>>12)&0xf] # proc PPPP
        except KeyError:
            proc = "Unknown processor"

        if type == "Unknown Pi model":
            rev = "?.?"
        else:
            rev = "1.%d" %(code&0xf) # rev RRRR

        rev_info = {
            "type": type,
            "rev": rev,
            "mem": mem,
            "man": man,
            "proc": proc,
            "num": num,
            "dsi": dsi
        }
    else:
        # Original was code&0x17 but this returned the entry for 0x004 when code = 0x00e
        old_rev = OLD_REVISION_CODES[code]
        rev_info = {
            "type": old_rev[0],
            "rev": old_rev[1],
            "mem": old_rev[2],
            "man": old_rev[3],
            "proc": "?",
            "num": "?",
            "dsi": "?"
        }
    return rev_info


def is_raspberry_pi():
    # True only on real Raspberry Pi hardware, matching the PHP isPi() (device-tree
    # model test). NOT the "/proc/cpuinfo has a Revision line" heuristic: armhf SBCs
    # (e.g. Allwinner H3) always carry Revision/Hardware/Serial lines whose code is
    # not a valid Pi revision, so decoding it crashes - they must take the generic
    # path. On x86 the model file is absent -> False.
    try:
        with open("/proc/device-tree/model") as f:
            return "Raspberry Pi" in f.read()
    except OSError:
        return False


def generic_rev_info():
    # Build a revision-info profile for a non-Pi platform (generic x86/other SBC)
    # using standard /proc files so System info has meaningful values.
    try:
        with open("/proc/cpuinfo") as f:
            cpuinfo = f.read()
        proc = next((l.split(":", 1)[1].strip() for l in cpuinfo.splitlines()
                     if l.startswith("model name") or l.startswith("Model")), "Unknown")
    except OSError:
        proc = "Unknown"
    try:
        with open("/proc/meminfo") as f:
            kb = int(next(l for l in f if l.startswith("MemTotal")).split()[1])
        mem = "%dMB" % round(kb / 1024)
    except (OSError, StopIteration, ValueError):
        mem = "?GB"

    return {
        "type": "PC",
        "rev": "1.0",
        "mem": mem,
        "man": "Generic",
        "proc": proc,
        "num": "0",
        "dsi": "0"
    }


def main():
    parser = argparse.ArgumentParser(description='Print Pi revision code information. If [code] is not present then the code for this Pi is used.')
    parser.add_argument('-t', '--type', action='store_true', help='Print model type')
    parser.add_argument('-n', '--num', action='store_true', help='Print model number')
    parser.add_argument('-d', '--dsi', action='store_true', help='Print number dsi ports')
    parser.add_argument('-r', '--rev', action='store_true', help='Print model revision')
    parser.add_argument('-m', '--mem', action='store_true', help='Print memory')
    parser.add_argument('-b', '--man', action='store_true', help='Print manufacturer')
    parser.add_argument('-p', '--proc', action='store_true', help='Print processor')
    parser.add_argument('-c', '--rcode', action='store_true', help='Print revision code')
    parser.add_argument('-a', '--all', action='store_true', help='Print all')
    parser.add_argument('code', nargs='?', help='Revision code (like a02082 or 0xa02082)')
    args = parser.parse_args()

    if not len(sys.argv) > 1:
        args.all = True

    if args.code:
        code = int(args.code if "0x" == args.code[:2] else "0x" + args.code, 16)
        rev_info = decode_new_style_code(code)
    elif not is_raspberry_pi():
        # Not a Raspberry Pi (generic x86 or a non-Pi ARM SBC). x86 simply has no
        # Revision line, but armhf SBCs (e.g. Allwinner H3) DO carry one that is not
        # a valid Pi revision code - decoding it crashes (KeyError). Gate on the
        # device-tree model like the PHP isPi() so EVERY non-Pi board gets the
        # synthetic profile. Model number 0 keeps the platform out of Pi-specific
        # code paths, which are additionally guarded by isPi() on the PHP side.
        code = 0
        rev_info = generic_rev_info()
    else:
        # NOTE: In otp_dump the Pi5 revcode is on line 32 while < Pi5 is on line 30.
        #cmd = "vcgencmd otp_dump | awk -F: '/^30:/{print substr($2,3)}'"
        # Alternate command for obtaining the revision code.
        cmd = "cat /proc/cpuinfo | awk -F': ' '/Revision/ {print $2}'"
        revcode = subprocess.run(cmd, shell=True, text=True, capture_output=True).stdout.rstrip()
        if revcode == "":
            code = 0
            rev_info = generic_rev_info()
        else:
            code = int("0x" + revcode, 16)
            rev_info = decode_new_style_code(code)

    info_text = ''
    if args.rcode or args.all or args.code:
        info_text += hex(code) + "\t"
    if args.type or args.all or args.code:
        info_text += rev_info['type'] + "\t"
    if args.rev or args.all or args.code:
        info_text += rev_info['rev'] + "\t"
    if args.mem or args.all or args.code:
        info_text += rev_info['mem'] + "\t"
    if args.man or args.all or args.code:
        info_text += rev_info['man'] + "\t"
    if args.proc or args.all or args.code:
        info_text += rev_info['proc'] + "\t"
    if args.num or args.all or args.code:
        info_text += rev_info['num'] + "\t"
    if args.dsi or args.all or args.code:
        info_text += rev_info['dsi'] + "\t"
    info_text = info_text.strip()

    print(info_text)

if __name__ == "__main__":
    main()
