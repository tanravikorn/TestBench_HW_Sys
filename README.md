# OV7670 VGA FPGA Project

This repository contains an OV7670 camera-to-VGA pipeline on FPGA, plus cocotb testbenches.

## Project Structure

```
hw_testbench/
├── rtl/                    # Verilog RTL (main design)
│   ├── top_module.v
│   ├── camera_config.v
│   ├── sccb_controller.v
│   ├── camera_capture.v
│   ├── vga_controller.v
│   └── debouncer.v
├── ip/                     # Vivado IP cores (.xci)
│   ├── clk_wiz_0/
│   └── frame_buffer/
├── tests/                  # cocotb simulation testbenches
│   ├── sccb_controller_test.py
│   ├── camera_capture_test.py
│   ├── vga_controller_test.py
│   └── tb.py
├── TESTBENCH_README.md     # Detailed simulation guide
├── requirements.txt        # Python simulation dependencies
└── .gitignore
```

## What each RTL file does

- `top_module.v`: top-level integration (clock/IP/capture/SCCB/VGA/LED)
- `camera_config.v`: OV7670 SCCB register sequence and done flag
- `sccb_controller.v`: SCCB write state machine (`sio_c`, `sio_d`)
- `camera_capture.v`: captures camera byte stream into 16-bit pixels + write address
- `vga_controller.v`: VGA timing + frame read addressing + RGB output mapping
- `debouncer.v`: reset button clean-up

## Quick Start (Simulation)

```powershell
cd C:\Users\Lenovo\Desktop\hw_testbench
python -m pip install -r requirements.txt
cd tests
python tb.py
```

## Notes before push

- Current cocotb tests require Python package install first (`cocotb`, `cocotb-tools`).
- No `.xdc` constraints file is currently present in this folder tree. Add your board constraints before full Vivado bitstream flow.
