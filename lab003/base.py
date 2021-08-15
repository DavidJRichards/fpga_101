#!/usr/bin/env python3

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.cores import dna, xadc

from ios import Led, Button, Switch

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
class BaseSoC(SoCMini):
    def __init__(self, platform, **kwargs):
        sys_clk_freq = int(50e6)

        # SoCMini (No CPU, we are controlling the SoC over UART)
        SoCMini.__init__(self, platform, sys_clk_freq, csr_data_width=32,
            ident="My first LiteX System On Chip", ident_version=True)

        # Clock Reset Generation
        self.submodules.crg = CRG(platform.request("clk50"), ~platform.request("cpu_reset"))

        # No CPU, use Serial to control Wishbone bus
        self.submodules.serial_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq)
        self.add_wb_master(self.serial_bridge.wishbone)

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
builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
builder.build(build_name="top")
