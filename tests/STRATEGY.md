# Testbench Strategy: OV7670→VGA Video Pipeline

## Executive Summary

This testbench suite provides **unit and integration testing** for your video capture pipeline before FPGA deployment. Each module is tested independently, then can be tested together.

---

## Why Testbenches Matter

### Without Testbenches (Current Situation)
- ❌ Build → Program → "Video doesn't work" → Debug on hardware (slow)
- ❌ "Is it SCCB? Camera capture? VGA output?" → Guess
- ❌ Color/rotation issues → Unknown root cause
- ❌ Hard to isolate problems (everything coupled on FPGA)

### With Testbenches (New Approach)
- ✓ Test each module in isolation (fast simulation)
- ✓ Know exactly which component is broken
- ✓ Verify timing/protocol correctness before hardware
- ✓ Catch logic errors during development
- ✓ Regression testing after fixes

---

## Testbench Coverage Map

```
OV7670 Camera
     │
     │ [SIO_C, SIO_D] ← SCCB Protocol
     │
   ┌─────────────────────┐
   │ SCCB Controller     │ ← Testbench 1: Protocol validation
   │ (camera_config.v)   │    • Register writes
   │                     │    • Timing accuracy
   └─────────────────────┘
     │
     │ [PCLK, VSYNC, HREF, D[7:0]]
     │
   ┌─────────────────────┐
   │ Camera Capture      │ ← Testbench 2: Data acquisition
   │ (camera_capture.v)  │    • Pixel buffering
   │     ↓ BRAM Write    │    • Frame synchronization
   └─────────────────────┘
     │
     │ [BRAM Port A: write]
     │ [BRAM Port B: read]
     │
   ┌─────────────────────┐
   │ VGA Controller      │ ← Testbench 3: Output generation
   │ (vga_controller.v)  │    • Sync timing
   │     ↓ VGA Output    │    • Color decode
   └─────────────────────┘
     │
     ▼ [HSYNC, VSYNC, RGB[3:0]]
   Monitor (640×480 @60Hz)
```

---

## Module-Level Testing Strategy

### 1. SCCB Controller (Lowest Layer)

**Purpose**: Verify I2C-like protocol for configuring OV7670

**Key Signals**:
- Input: `clk` (100 MHz), `reset`, `start`, `dev_addr`, `reg_addr`, `data`
- Output: `sio_c`, `sio_d`, `busy`, `ready`

**Test Approach**:
```
[PASS] → Basic single write
        → Multiple consecutive writes
        → Bus line idle state (SIO_C, SIO_D high after transaction)
        → Timing accuracy (tick generation, phase counter)

[FAIL] → Check FSM states (START → ID_ADDR → ACK1 → ... → STOP)
        → Verify clk_cnt divider (should generate ~200 kHz from 100 MHz)
        → Confirm reset clears all state
```

**Why This Layer Matters**:
- If SCCB fails → camera_config can't send MVFP/MTX registers
- Result: Wrong color/orientation even if capture/VGA work

---

### 2. Camera Capture (Middle Layer)

**Purpose**: Capture OV7670 pixel stream (QVGA) into BRAM

**Key Signals**:
- Input: `pclk` (50 MHz), `reset`, `vsync`, `href`, `d[7:0]`
- Output: `addr[16:0]`, `dout[15:0]`, `we` (write enable)

**Test Approach**:
```
[PASS] → Reset clears address/data/we
        → Single pixel write (2 bytes → 16-bit RGB565)
        → Full line (320 pixels)
        → Full frame (76800 pixels = 38400 words)
        → VSYNC frame boundary resets addr to 0
        → HREF line boundary is respected

[FAIL] → Check byte_cnt logic (even/odd byte pairing)
        → Verify VSYNC/HREF edge detection (falling edge on pclk)
        → Confirm RGB565 packing: [R8|G8], [B8|x] → not standard 565
        → Address calculation: should increment on every complete word
```

**Why This Layer Matters**:
- If capture fails → BRAM stays empty or contains junk
- Result: Black screen or green/colorful noise
- This is likely source of your color issues (byte order wrong?)

---

### 3. VGA Controller (Top Layer)

**Purpose**: Generate standard VGA timing + read BRAM for display

**Key Signals**:
- Input: `clk_vga` (25 MHz), `frame_data[15:0]` (from BRAM)
- Output: `hsync`, `vsync`, `vga_r/g/b[3:0]`, `read_addr[16:0]`

**Test Approach**:
```
[PASS] → HSYNC timing: 96 clocks low (656–752) per 800-clock line
        → VSYNC timing: 2 lines low (490–492) per 525-line frame
        → Active region: 640×480 pixels, blanking outside
        → Address generation: row_addr = row*320, addr = row_addr + col
        → RGB565 decode: extract R/G/B and upscale to 4-bit
        → Pipeline delays: active_d1, active_d2 (2-cycle latency)

[FAIL] → Check counter wrap-around (h_cnt 799→0, v_cnt 524→0)
        → Verify sync polarity (active-low)
        → Confirm address matches QVGA layout (320 cols per row)
        → RGB565 extraction might have channel order wrong
```

**Why This Layer Matters**:
- If VGA fails → monitor shows no sync / garbled image
- If timing wrong → monitor loses sync → black screen
- If address wrong → wrong pixels read → image jumbled
- If RGB decode wrong → color channel swap (likely your issue!)

---

## Debugging Decision Tree

When hardware fails, use testbenches to isolate:

```
Hardware Problem
├─ "No image at all"
│  ├─ [Test VGA] → Sync timing wrong?
│  ├─ [Test BRAM] → Empty memory?
│  └─ [Test SCCB] → Camera not configured?
│
├─ "Green/colorful image"
│  ├─ [Test camera_capture] → Byte order wrong?
│  ├─ [Test VGA RGB decode] → Channel swap?
│  └─ [Test SCCB] → Color matrix registers not set?
│
├─ "Image upside-down / sideways"
│  ├─ [Test SCCB] → MVFP register not applied?
│  └─ [Test camera_capture] → Address calculation wrong?
│
└─ "Screen flicker / sync loss"
   ├─ [Test VGA timing] → HSYNC/VSYNC wrong?
   └─ [Test address generation] → Reading invalid memory?
```

---

## How to Use Testbenches for Your Fixes

### Fix 1: Color Issues (Green Tone)

**Hypothesis**: RGB565 byte order or channel swap

**Test Steps**:
```bash
1. Run camera_capture_test.py
   - Check if pixel data flows through correctly
   - If write timing is wrong → pixels scrambled

2. Run vga_controller_test.py
   - Check RGB decode (red/green/blue extraction)
   - If bits [15:12] ≠ Red → explain green tint
   - If bits [4:1] ≠ Blue → channel swap

3. If both pass:
   - Testbench is correct, hardware setup is wrong
   - Check TSLB register (0x3A) for byte order
   - Check MVFP register (0x1E) for flip/mirror
```

### Fix 2: Rotation Issues (Portrait instead of Landscape)

**Hypothesis**: MVFP register not applied or wrong value

**Test Steps**:
```bash
1. Run sccb_controller_test.py
   - Verify SCCB can write registers
   - Check camera_config ROM for correct MVFP value
   - If test passes → SCCB protocol OK, issue is register value

2. Check camera_config.v:
   - Find MVFP entry in ROM (usually 0x1E register)
   - Current value causing portrait? Try different values
   - Expected for landscape: 0x26 or 0x27 (flip + mirror)
```

---

## Running Testbenches Iteratively

### Workflow for Fixing Color Issue:

```
Step 1: Baseline
  python tb.py → All tests PASS or FAIL?

Step 2: If FAIL → Run individually
  python sccb_controller_test.py
  python camera_capture_test.py  ← Check byte order here
  python vga_controller_test.py  ← Check RGB decode here

Step 3: Identify failing test
  If camera_capture_test fails:
    → Problem in byte pairing or pixel format
    → Edit camera_capture.v, re-run

Step 4: Once unit tests pass
  Rebuild hardware bitstream with same Verilog
  Expected: Color issue fixed!

Step 5: If still not fixed
  → Problem is in software layer (camera_config registers)
  → Use SCCB test to verify what registers were sent
  → Check OV7670 datasheet for correct register values
```

---

## Test Results Interpretation

### Example: All Tests Pass ✓

```
✓ sccb_controller_test: PASS
  ✓ sccb_basic_write_test
  ✓ sccb_multiple_writes_test
  ✓ sccb_bus_idle_test

✓ camera_capture_test: PASS
  ✓ camera_capture_reset_test
  ✓ camera_capture_single_pixel_test
  ✓ camera_capture_line_test
  ✓ camera_capture_frame_test
  ✓ camera_capture_write_timing_test

✓ vga_controller_test: PASS
  ✓ vga_timing_test
  ✓ vga_address_generation_test
  ✓ vga_rgb565_decode_test
  ✓ vga_active_region_test
  ✓ vga_full_frame_test
```

**Interpretation**: All modules work correctly in simulation.
- If hardware still fails → Issue is integration (BRAM routing, clock domain crossing, constraints)
- Check Vivado implementation errors / warnings

---

### Example: VGA Timing Test Fails ✗

```
AssertionError: HSYNC should go high at 752, got 753
```

**Interpretation**: HSYNC pulse width is 1 clock too long.

**Fix**:
```verilog
// vga_controller.v, line 39 (current)
hsync <= (h_cnt >= 656 && h_cnt < 752) ? 1'b0 : 1'b1;

// Try:
hsync <= (h_cnt >= 656 && h_cnt < 751) ? 1'b0 : 1'b1;
```

Re-run test to verify fix.

---

### Example: Camera Capture Address Wrong ✗

```
AssertionError at v=0, h=0: addr=1, expected=0
```

**Interpretation**: Address not resetting when frame starts.

**Fix**: Check VSYNC edge detection in camera_capture.v:
```verilog
// Likely issue: not detecting VSYNC low-to-high transition
if (vsync && !vsync_prev) begin  // Rising edge
    addr <= 0;  // Reset frame address
end
```

---

## Files Generated During Testing

```
tests/
├── sim_build/          ← Simulator artifacts
│   ├── verilog.vcd     ← Waveforms (open in GTKWave)
│   ├── *.o, *.a        ← Compiled objects
│   └── ...
├── __pycache__/        ← Python cache (can delete)
└── results.xml         ← Test report (for CI/CD)
```

**View Waveforms** (if test fails):
```bash
# After test runs (even if fails), waveforms are captured
gtkwave tests/sim_build/verilog.vcd &
```

In GTKWave:
- Expand signal tree (left)
- Drag signals to main window
- Scroll to see timing
- Zoom in/out with scroll wheel
- Useful for seeing exact cycle when assertion failed

---

## Next Steps for Your Project

### Immediate (This Session)
1. ✅ **Create testbenches** (done above)
2. 🔲 **Install cocotb + simulator** (icarus or Vivado)
3. 🔲 **Run testbenches locally** (Linux/WSL recommended, or Windows with icarus)
4. 🔲 **Fix any failing unit tests**

### Short Term (Next Session)
5. 🔲 **Create integration test** (all 3 modules together with simulated BRAM)
6. 🔲 **Validate testbench predictions against hardware**
7. 🔲 **Use testbenches to drive fixes** (color, rotation issues)

### Medium Term
8. 🔲 **Build behavioral model of OV7670** (to simulate camera input)
9. 🔲 **End-to-end testbench** (camera → SCCB → capture → VGA in simulation)
10. 🔲 **Automated CI/CD** (run testbenches on every commit)

---

## Testbench Limitations

What testbenches **CANNOT** verify:
- ❌ Actual image content (need real or modeled camera)
- ❌ FPGA resource usage / timing closure
- ❌ Pin assignment / voltage levels
- ❌ BRAM initialization / power-on state
- ❌ Electrical noise / signal integrity

What testbenches **CAN** verify:
- ✓ RTL logic correctness
- ✓ Timing/protocol accuracy
- ✓ State machine behavior
- ✓ Data flow / addressing
- ✓ Synchronization (clock domains)

---

## Quick Reference: Testbench Commands

```bash
# Setup
python quickstart.py --setup

# Run all
python tb.py

# Run specific
python quickstart.py --test sccb
python quickstart.py --test camera
python quickstart.py --test vga

# Clean up
rm -rf sim_build __pycache__ *.o *.a
```

---

## Support

If testbenches don't run or seem wrong:

1. **Check cocotb installation**:
   ```bash
   python -c "import cocotb; print(cocotb.__version__)"
   ```

2. **Check simulator installed**:
   ```bash
   iverilog --version    # Icarus
   xsim -version         # Vivado (Windows only, need PATH set)
   ```

3. **Check Verilog files in correct paths**:
   ```bash
   ls -l ../rtl/sccb_controller.v
   ```

4. **Run with verbose output**:
   ```bash
   SIM=icarus python sccb_controller_test.py -v
   ```

---

## Summary

Testbenches are your **first line of defense** against hardware failures. Use them to:

1. **Verify each module works independently** ← Isolate failures
2. **Catch logic errors early** ← Before FPGA synthesis
3. **Validate timing/protocol** ← Match hardware requirements
4. **Drive iterative fixes** ← Test → Fix → Re-test
5. **Build confidence** ← "Tested code is more likely to work"

For your color/rotation issues:
- Run camera_capture & VGA testbenches first
- They will show if the problem is byte order, channel swap, or register timing
- Fix Verilog based on test results
- Re-run tests to verify fix
- Build FPGA with corrected code

Good luck! 🚀
