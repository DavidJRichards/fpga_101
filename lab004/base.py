#!/usr/bin/env python3

from migen import *

from migen.genlib.io import CRG

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores import dna, xadc
from litex.soc.cores.spi import SPIMaster

from ios import Led, RGBLed, Button, Switch
from display import SevenSegmentDisplay

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # LEDs
    ("user_led",   0, Pins("V17"),   IOStandard("LVCMOS33")),
    ("user_led",   1, Pins("V16"),   IOStandard("LVCMOS33")),

    ("user_led",   2, Pins("D26"),   IOStandard("LVCMOS33")), # expansion LEDs on cmera connector
    ("user_led",   3, Pins("E26"),   IOStandard("LVCMOS33")),
    ("user_led",   4, Pins("E23"),   IOStandard("LVCMOS33")),
    ("user_led",   5, Pins("F23"),   IOStandard("LVCMOS33")),
    ("user_led",   6, Pins("G21"),   IOStandard("LVCMOS33")),
    ("user_led",   7, Pins("G20"),   IOStandard("LVCMOS33")),
    ("user_led",   8, Pins("F25"),   IOStandard("LVCMOS33")),
    ("user_led",   9, Pins("G25"),   IOStandard("LVCMOS33")),

    # Switches
    ("user_sw", 0, Pins("J21"), IOStandard("LVCMOS33")),
    ("user_sw", 1, Pins("K21"), IOStandard("LVCMOS33")),
    ("user_sw", 2, Pins("H22"), IOStandard("LVCMOS33")),
    ("user_sw", 3, Pins("H21"), IOStandard("LVCMOS33")),

    # Buttons
    ("user_btn",   0, Pins("M6"),   IOStandard("LVCMOS33")), # Key0
    ("user_btn",   1, Pins("H7"),   IOStandard("LVCMOS33")), # Key1


    # Clk / Rst
    ("clk50",      0, Pins("M21"), IOStandard("LVCMOS33")),
    ("cpu_reset",  0, Pins("H26"), IOStandard("LVCMOS33"), Misc("PULLUP True")),

    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("E3")),
        Subsignal("rx", Pins("F3")),
        IOStandard("LVCMOS33"),
    ),


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

# Create our soc (fpga description)
class BaseSoC(SoCCore):
    def __init__(self, platform):
        sys_clk_freq = int(50e6)

        # SoC with CPU
        SoCCore.__init__(self, platform,
            cpu_type                 = "vexriscv",
            clk_freq                 = 50e6,
            ident                    = "LiteX CPU Test SoC", ident_version=True,
            integrated_rom_size      = 0x8000,
            integrated_main_ram_size = 0x4000)

        # Clock Reset Generation
        self.submodules.crg = CRG(platform.request("clk50"), ~platform.request("cpu_reset"))

        # FPGA identification
        self.submodules.dna = dna.DNA()
        self.add_csr("dna")

        # FPGA Temperature/Voltage
        self.submodules.xadc = xadc.XADC()
        self.add_csr("xadc")

        # Led
        user_leds = Cat(*[platform.request("user_led", i) for i in range(10)])
        self.submodules.leds = Led(user_leds)
        self.add_csr("leds")

        # Switches
        user_switches = Cat(*[platform.request("user_sw", i) for i in range(4)])
        self.submodules.switches = Switch(user_switches)
        self.add_csr("switches")

        # Buttons
        user_buttons = Cat(*[platform.request("user_btn", i) for i in range(2)])
        self.submodules.buttons = Button(user_buttons)
        self.add_csr("buttons")


soc = BaseSoC(platform)

# Build --------------------------------------------------------------------------------------------

builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
builder.build(build_name="top")
