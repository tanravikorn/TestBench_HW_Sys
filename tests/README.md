# OV7670→VGA Pipeline Testbench Suite

Comprehensive cocotb-based testbenches for the video capture pipeline: OV7670 camera → SCCB config → QVGA capture → BRAM → VGA output.

## Overview

This testbench suite validates three critical components:

| Module | Purpose | Tests |
|--------|---------|-------|
| **sccb_controller.v** | I2C-like serial protocol for OV7670 register writes | SCCB protocol, bus timing, multi-transaction sequencing |
| **camera_capture.v** | Pixel acquisition (8-bit stream → 16-bit RGB565 BRAM writes) | Reset behavior, single/multiple pixel capture, line/frame sync, write timing |
| **vga_controller.v** | VGA output generation (640×480 @60Hz) + BRAM read addressing | Sync timing, active region, address generation, RGB565 decode, frame rate |

---

## Prerequisites

```bash
# Install cocotb and simulator
pip install cocotb cocotb-tools
pip install pypy3-wheel  # Optional: faster simulation

# Install Icarus Verilog (free simulator) or use Vivado simulator
# Windows: 
#   - Download from http://bleyer.org/icarus/
#   - Add to PATH
# Linux:
#   - sudo apt install iverilog vvp
```

---

## Test Structure

### SCCB Controller Tests (`sccb_controller_test.py`)

**Module**: `sccb_controller.v`
- **Clock**: 100 MHz (clk_cnt divides to 200 kHz SCCB clock)
- **Protocol**: START → ADDR → ACK → REG → ACK → DATA → ACK → STOP

#### Test Cases:

1. **sccb_basic_write_test**
   - Single transaction: Dev=0x42, Reg=0x12, Data=0x04
   - Validates: START/STOP conditions, ready/busy handshake, bus idle state
   - Duration: ~50k cycles (~500 µs)

2. **sccb_multiple_writes_test**
   - Three consecutive writes (COM7 reset, CLKRC, DBLV)
   - Validates: Transaction sequencing, state machine continuity
   - Duration: ~150k cycles (~1.5 ms)

3. **sccb_bus_idle_test**
   - Verifies bus lines (SIO_C, SIO_D) behavior
   - Validates: Idle high, active low control, tri-state management
   - Duration: ~50k cycles (~500 µs)

**Expected Results**: All transactions complete with ready=1, busy=0, SIO_C/D idle high.

---

### Camera Capture Tests (`camera_capture_test.py`)

**Module**: `camera_capture.v`
- **Clock**: 50 MHz pixel clock (PCLK)
- **Sensors**: VSYNC (frame sync), HREF (line sync), D[7:0] (pixel data)
- **Output**: 17-bit BRAM address, 16-bit data, write-enable pulse

#### Test Cases:

1. **camera_capture_reset_test**
   - Verify reset state: addr=0, we=0, dout=0
   - Validates: Reset logic, signal initialization
   - Duration: ~10 cycles (~200 ns)

2. **camera_capture_single_pixel_test**
   - Send 2 bytes (R8G8 format) with HREF active
   - Validates: Byte pairing, single write trigger
   - Duration: ~50 cycles (~1 µs)

3. **camera_capture_line_test**
   - Simulate 320 pixels (640 bytes) in one HREF pulse
   - Validates: Address increment to 320, sustained HREF
   - Duration: ~1.3k cycles (~26 µs)

4. **camera_capture_frame_test**
   - 10 lines × 10 pixels (reduced for speed)
   - Validates: Frame-level address progression, VSYNC edge detection
   - Duration: ~2k cycles (~40 µs)

5. **camera_capture_write_timing_test**
   - Verify WE pulse alignment with byte boundaries
   - Validates: Timing accuracy, write synchronization
   - Duration: ~100 cycles (~2 µs)

**Expected Results**: Correct frame addressing (0 to 76800), write pulses aligned to 16-bit boundaries.

---

### VGA Controller Tests (`vga_controller_test.py`)

**Module**: `vga_controller.v`
- **Clock**: 25 MHz (for 640×480 @60Hz)
- **Output**: HSYNC, VSYNC, RGB[3:0], read_addr, active_d2
- **Timing**: 800 clocks/line, 525 lines/frame

#### Test Cases:

1. **vga_timing_test**
   - Verify HSYNC/VSYNC pulse timing over 2 frames
   - Validates: 
     - HSYNC low: cycles 656–752 (96 clocks = ~3.84 µs)
     - VSYNC low: lines 490–492 (2 lines)
   - Duration: ~400k cycles (~16 ms)

2. **vga_address_generation_test**
   - Check BRAM read address calculation
   - Formula: `addr = (row<<8) + (row<<6) + col` (for QVGA downsampling)
   - Validates: Correct row/column mapping
   - Duration: ~2k cycles (~80 µs)

3. **vga_rgb565_decode_test**
   - Verify RGB565 → 4-bit RGB extraction
   - Test patterns: Red (0xF800), Green (0x07E0), Blue (0x001F), White (0xFFFF)
   - Extraction:
     - R[4:0] → vga_r[3:0] (upper 4 bits)
     - G[5:0] → vga_g[3:0] (upper 4 bits)
     - B[4:0] → vga_b[3:0] (upper 4 bits)
   - Duration: ~100 cycles (~4 µs)

4. **vga_active_region_test**
   - Verify active region detection (h_cnt < 640, v_cnt < 480)
   - Validates: Pipeline delays (active_d1, active_d2), blanking intervals
   - Duration: ~840k cycles (~33.6 ms for 2 frames)

5. **vga_full_frame_test**
   - Generate 3 complete frames, verify frame rate stability
   - Expected: ~420k cycles per frame (800 × 525 @ 25 MHz)
   - Validates: Counter wrap-around, frame synchronization
   - Duration: ~1.26M cycles (~50 ms)

**Expected Results**: 
- HSYNC/VSYNC timing matches VGA spec (640×480 @60Hz)
- Address increments smoothly through frame
- RGB output valid only during active_d2
- Frame rate stable at 60 Hz

---

## Running the Tests

### Run All Tests

```bash
cd C:\Users\Lenovo\Desktop\hw_testbench\tests
python tb.py
```

### Run Individual Test Suite

```bash
# SCCB only
python sccb_controller_test.py

# Camera capture only
python camera_capture_test.py

# VGA controller only
python vga_controller_test.py
```

### Run Specific Test

```bash
# Set environment variable
set SIM=icarus    # or "vivado", "xsim", "verilator"

# Run with debug output
python sccb_controller_test.py -v
```

### With Waveform Capture

```bash
# All simulators (cocotb-tools) capture VCD automatically
# View with:
#   - GTKWave: gtkwave sim_build/verilog.vcd
#   - Vivado xsim: waveform.wcdb
#   - Icarus vvp: generated VCD files in sim_build/
```

---

## Output Interpretation

### Successful Test
```
Running sccb_controller_test...
------...
✓ SCCB basic write test PASSED
✓ SCCB multiple writes test PASSED
✓ SCCB bus idle test PASSED
```

### Failed Test
```
AssertionError: Ready should return to 1 after transaction
  at cycle 50000+
  Expected: ready=1
  Got: ready=0
```

### Test Summary
```
======================================================================
Test Summary
======================================================================
✓ sccb_controller_test: PASS
✓ camera_capture_test: PASS
✓ vga_controller_test: PASS

Total: 3 | Passed: 3 | Failed: 0 | Errors: 0 | Skipped: 0
```

---

## Debugging Tips

### If Tests Timeout

1. **Check Clock Dividers**: SCCB uses `clk_cnt == 249` (250 divider); verify against module
2. **Check Reset Sequencing**: Reset must be held for ≥2 clock cycles
3. **Check HREF/VSYNC Timing**: Must align with falling edge of PCLK in real camera

### If Address Generation Fails

```verilog
// Expected formula in vga_controller:
wire [16:0] row_addr = ({8'b0, row} << 8) + ({8'b0, row} << 6);
// = row * 256 + row * 64 = row * 320
```

### If RGB565 Decode is Wrong

Check bit extraction in `vga_controller.v`:
```verilog
vga_r <= frame_data[15:12];  // R[4:0] from bits [15:11] → take [15:12]
vga_g <= frame_data[10:7];   // G[5:0] from bits [10:5] → take [10:7]
vga_b <= frame_data[4:1];    // B[4:0] from bits [4:0] → take [4:1]
```

---

## Integration with Hardware

Once testbenches pass:

1. **Build bitstream** in Vivado with constraints validated
2. **Program FPGA** (Basys3)
3. **Verify hardware**:
   - LED "done" indicator lights when camera_config completes
   - BRAM fills with pixel data (HREF pulses trigger writes)
   - VGA output displays live video at 640×480 @60Hz

---

## File Locations

```
hw_testbench/
├── rtl/
│   ├── sccb_controller.v         ← Module under test
│   ├── camera_capture.v          ← Module under test
│   ├── vga_controller.v          ← Module under test
│   └── ...
└── tests/
    ├── sccb_controller_test.py   ← Test harness
    ├── camera_capture_test.py    ← Test harness
    ├── vga_controller_test.py    ← Test harness
    ├── tb.py                     ← Master runner
    └── sim_build/                ← Generated artifacts
```

---

## Testbench Architecture

Each testbench follows this pattern:

```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, Timer

@cocotb.test()
async def my_test(dut):
    # 1. Start clock(s)
    clock = Clock(dut.clk, period_ns, unit="ns")
    clock.start()
    
    # 2. Reset device under test (DUT)
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    
    # 3. Apply stimuli
    dut.input_signal.value = test_value
    await RisingEdge(dut.clk)
    
    # 4. Check outputs
    await ReadOnly()  # Wait for combinatorial logic to settle
    assert int(dut.output_signal.value) == expected_value
    
    cocotb.log.info("✓ Test passed")
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Timeout waiting for ready" | SCCB FSM stuck | Check reset, verify tick generation (clk_cnt divider) |
| Address stuck at 0 | VSYNC edge not detected | Verify VSYNC pulse timing (must go low then high) |
| RGB565 values wrong | Bit extraction order | Check vga_r/g/b assignments match RGB565 format |
| Simulator can't find Verilog | Path issue | Use `proj_path / Path(f)` to make paths relative to test file |

---

## Next Steps

1. ✅ **Run testbenches locally** (Icarus/VCS/etc.) to verify modules
2. 🔲 **Fix any failing tests** by adjusting Verilog or test expectations
3. 🔲 **Implement integration test** between all three modules (sccb → capture → vga)
4. 🔲 **Validate on hardware** (FPGA + camera + VGA monitor)

---

## References

- **cocotb Documentation**: https://docs.cocotb.org/
- **OV7670 SCCB Protocol**: https://www.ov.com/datasheet/OV7670
- **VGA Timing**: https://en.wikipedia.org/wiki/Video_Graphics_Array#Timings
- **RGB565 Format**: https://en.wikipedia.org/wiki/High_color#16-bit

