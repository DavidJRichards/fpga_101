#!/usr/bin/env python3
import os
os.system("openocd -f wukong.cfg -c 'init; pld load 0 ./build/gateware/top.bit; exit' ")
