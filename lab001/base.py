#!/usr/bin/env python3

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("user_led",  0, Pins("V17"), IOStandard("LVCMOS33")),

    ("user_sw",  0, Pins("J21"), IOStandard("LVCMOS33")),

    ("user_btn", 0, Pins("M6"), IOStandard("LVCMOS33")),

    ("clk50", 0, Pins("M21"), IOStandard("LVCMOS33")),

    ("cpu_reset", 0, Pins("H26"), IOStandard("LVCMOS33"), Misc("PULLUP True")),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk50"
    default_clk_period = 1e9/50e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xc7a100t-2fgg676", _io, toolchain="vivado")

# Design -------------------------------------------------------------------------------------------

# Create our platform (fpga interface)
platform = Platform()
led = platform.request("user_led")

# Create our module (fpga description)
module = Module()

# Create a counter and blink a led
counter = Signal(26)
module.comb += led.eq(counter[25])
module.sync += counter.eq(counter + 1)

# Build --------------------------------------------------------------------------------------------

platform.build(module)
