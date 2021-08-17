#!/usr/bin/env python3

from migen import *

from litex.build.generic_platform import *
from litex.build.xilinx import XilinxPlatform, VivadoProgrammer

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.cores.uart import UARTWishboneBridge
from litex.soc.cores import dna 

from ios import Led, Button, Switch

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # LEDs
    ("user_led", 0, Pins("W14"), IOStandard("LVCMOS33")),
    ("user_led", 1, Pins("W13"), IOStandard("LVCMOS33")),

    # Clk
    ("clk33_333",  0, Pins("N18"), IOStandard("LVCMOS33")),

    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("V12")),
        Subsignal("rx", Pins("V15")),
        IOStandard("LVCMOS33")
    )

]

# This is currently untested on this EBAZ4205 board
_ps7_io = [
    # PS7
    ("ps7_clk",   0, Pins(1)),
    ("ps7_porb",  0, Pins(1)),
    ("ps7_srstb", 0, Pins(1)),
    ("ps7_mio",   0, Pins(54)),
    ("ps7_ddram", 0,
        Subsignal("addr",    Pins(15)),
        Subsignal("ba",      Pins(3)),
        Subsignal("cas_n",   Pins(1)),
        Subsignal("ck_n",    Pins(1)),
        Subsignal("ck_p",    Pins(1)),
        Subsignal("cke",     Pins(1)),
        Subsignal("cs_n",    Pins(1)),
        Subsignal("dm",      Pins(4)),
        Subsignal("dq",      Pins(32)),
        Subsignal("dqs_n",   Pins(4)),
        Subsignal("dqs_p",   Pins(4)),
        Subsignal("odt",     Pins(1)),
        Subsignal("ras_n",   Pins(1)),
        Subsignal("reset_n", Pins(1)),
        Subsignal("we_n",    Pins(1)),
        Subsignal("vrn",     Pins(1)),
        Subsignal("vrp",     Pins(1)),
    ),
]


# Connectors ---------------------------------------------------------------------------------------

_connectors = [
    ("data1", "A20 H16 B19 B20 C20 H17 D20 D18 H18 D19 F20 E19 F19 K17"),
    ("data2", "G20 J18 G19 H20 J19 K18 K19 J20 L16 L19 M18 L20 M20 L17"),
    ("date3", "M19 N20 P18 M17 N17 P20 R18 R19 P19 T20 U20 T19 V20 U19"),
    ("j3",    "V13 U12"), # DATA CLK
#    ("j5",    "V15 V12"), # RXD TXD
    ("I2C",   "A15 D13"), # SCL SDA
]

# Platform -----------------------------------------------------------------------------------------

class Platform(XilinxPlatform):
    default_clk_name   = "clk33_333"
    default_clk_period = 1e9/33.333e6

    def __init__(self):
        XilinxPlatform.__init__(self, "xc7z010-clg400-1", _io,  _connectors, toolchain="vivado")
        self.add_extension(_ps7_io)

    def create_programmer(self):
        return VivadoProgrammer()

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk33_333", loose=True), 1e9/33.333e6)
# Design -------------------------------------------------------------------------------------------

# Create our platform (fpga interface)
platform = Platform()

# Create our soc (fpga description)
class BaseSoC(SoCMini):
    def __init__(self, platform, **kwargs):
        sys_clk_freq = int(33.333e6)

        # SoCMini (No CPU, we are controlling the SoC over UART)
        SoCMini.__init__(self, platform, sys_clk_freq, csr_data_width=32,
            ident="Ebaz 4205 LiteX System On Chip", ident_version=True)

        # Clock Reset Generation
        self.submodules.crg = CRG(platform.request("clk33_333"))

        # No CPU, use Serial to control Wishbone bus
        self.submodules.serial_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq)
        self.add_wb_master(self.serial_bridge.wishbone)

        # FPGA identification
        self.submodules.dna = dna.DNA()
        self.add_csr("dna")

        # Led
        user_leds = Cat(*[platform.request("user_led", i) for i in range(2)])
        self.submodules.leds = Led(user_leds)
        self.add_csr("leds")


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
