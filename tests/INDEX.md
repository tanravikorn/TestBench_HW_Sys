# OV7670→VGA Pipeline Testbench Suite - Index

## 📚 Documentation

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[README.md](README.md)** | Complete test documentation | First-time setup, understanding tests |
| **[STRATEGY.md](STRATEGY.md)** | Debugging strategy + decision trees | Planning fixes, understanding why tests matter |
| **[INDEX.md](INDEX.md)** | This file | Navigation |

## 🧪 Testbench Files

| Test | File | Module | Coverage |
|------|------|--------|----------|
| **SCCB Controller** | `sccb_controller_test.py` | `sccb_controller.v` | I2C protocol, register writes, bus timing |
| **Camera Capture** | `camera_capture_test.py` | `camera_capture.v` | Pixel ingest, QVGA buffering, frame sync |
| **VGA Controller** | `vga_controller_test.py` | `vga_controller.v` | VGA timing, address generation, RGB decode |

## 🚀 How to Run

### Option 1: Quick Start (Recommended)
```bash
cd tests/
python quickstart.py
```

### Option 2: Run All Tests
```bash
python tb.py
```

### Option 3: Run Individual Test
```bash
python sccb_controller_test.py       # SCCB only
python camera_capture_test.py        # Camera capture only
python vga_controller_test.py        # VGA only
```

### Option 4: Manual Setup + Run
```bash
# Setup (one-time)
python quickstart.py --setup

# Run tests
export SIM=icarus  (Linux) or set SIM=icarus (Windows)
python tb.py
```

## 📋 What Each Test Does

### SCCB Controller (`sccb_controller_test.py`)
Tests the Serial Camera Control Bus protocol for configuring OV7670.

**Tests:**
1. `sccb_basic_write_test` - Single transaction (Dev, Register, Data)
2. `sccb_multiple_writes_test` - Three consecutive writes (COM7, CLKRC, DBLV)
3. `sccb_bus_idle_test` - Bus line idle state (SIO_C, SIO_D)

**Expected Output:**
```
✓ SCCB basic write test PASSED
✓ SCCB multiple writes test PASSED
✓ SCCB bus idle test PASSED
```

**If it fails:** Check `README.md` section "SCCB Controller Tests"

---

### Camera Capture (`camera_capture_test.py`)
Tests pixel capture from OV7670 into BRAM.

**Tests:**
1. `camera_capture_reset_test` - Reset state (addr=0, we=0)
2. `camera_capture_single_pixel_test` - One 16-bit word
3. `camera_capture_line_test` - 320 pixels (one line)
4. `camera_capture_frame_test` - 10×10 pixels (frame structure)
5. `camera_capture_write_timing_test` - Write-enable pulse timing

**Expected Output:**
```
✓ Camera capture reset test PASSED
✓ Camera capture single pixel test PASSED
✓ Camera capture line test PASSED (addr=320)
✓ Camera capture frame test PASSED (addr=100, expected=100)
✓ Camera capture write timing test PASSED
```

**If it fails:** 
- Check byte pairing (odd/even pixels)
- Check VSYNC/HREF edge detection
- See README.md section "Camera Capture Tests"

---

### VGA Controller (`vga_controller_test.py`)
Tests VGA timing and BRAM read addressing.

**Tests:**
1. `vga_timing_test` - HSYNC/VSYNC pulse widths (800×525)
2. `vga_address_generation_test` - BRAM read address calculation
3. `vga_rgb565_decode_test` - Color channel extraction
4. `vga_active_region_test` - Active area detection (640×480)
5. `vga_full_frame_test` - Full frame generation (3 frames, 60Hz check)

**Expected Output:**
```
✓ VGA timing test PASSED (verified 1050 HSYNC pulses)
✓ VGA address generation test PASSED (checked 100+ addresses)
✓ VGA RGB565 decode test PASSED
✓ VGA active region test PASSED (active=..., blank=...)
✓ VGA full frame test PASSED (3 frames verified)
```

**If it fails:** Check README.md section "VGA Controller Tests"

---

## 🔍 Troubleshooting

### Test Timeouts
```
Timeout waiting for busy signal
```
→ Check SCCB clk_cnt divider. Should be 250 (249 in code).

### Address Generation Wrong
```
addr=1, expected=0
```
→ Check VSYNC edge detection or address reset logic.

### RGB Values Inverted/Swapped
```
Expected 0xF (red), got 0x0
```
→ Check RGB565 bit extraction in vga_controller.v

See **STRATEGY.md** for full decision tree.

---

## 📊 Test Results Guide

| Status | Meaning | Action |
|--------|---------|--------|
| ✓ PASS | Test passed | ✓ Module is correct, move to hardware |
| ✗ FAIL | Test failed | Debug: see error message + README + waveforms |
| ⚠ ERROR | Crash/exception | Check Python/cocotb installation |
| ⊘ SKIP | Test file missing | Install missing files |

---

## 🛠️ Setup Requirements

### Required (One-Time)
```bash
pip install cocotb cocotb-tools
```

### Simulator (Choose One)
- **Icarus Verilog** (free, fast): http://bleyer.org/icarus/
- **Vivado xsim** (installed): `C:\Xilinx\Vivado\2025.2\bin\xsim.bat`

### Optional (Debugging)
- **GTKWave** (view waveforms): http://gtkwave.sourceforge.net/

---

## 📁 File Structure

```
hw_testbench/
├── rtl/                              ← Verilog modules
│   ├── sccb_controller.v             ← Module under test
│   ├── camera_capture.v              ← Module under test
│   ├── vga_controller.v              ← Module under test
│   └── ...
│
└── tests/                            ← This directory
    ├── sccb_controller_test.py       ← Test harness
    ├── camera_capture_test.py        ← Test harness
    ├── vga_controller_test.py        ← Test harness
    ├── tb.py                         ← Master runner
    ├── quickstart.py                 ← Setup helper
    ├── README.md                     ← Full documentation
    ├── STRATEGY.md                   ← Debugging guide
    ├── INDEX.md                      ← This file
    ├── sim_build/                    ← Generated (simulator artifacts)
    │   ├── verilog.vcd               ← Waveforms
    │   ├── *.o                       ← Compiled objects
    │   └── ...
    └── __pycache__/                  ← Python cache
```

---

## 🎯 Common Workflows

### Workflow 1: "First Time Setup"
```
1. Read README.md (15 min)
2. Read STRATEGY.md (10 min)
3. Run quickstart.py --setup (5 min)
4. Run tb.py (1 min)
```

### Workflow 2: "Fix Color Issue"
```
1. Read STRATEGY.md section "Fix 1: Color Issues"
2. Run camera_capture_test.py
3. If fail: byte order problem (see README.md)
4. If pass: check RGB decode in VGA test
5. Run vga_controller_test.py
6. If fail: channel swap problem (edit vga_controller.v)
7. Re-run test to verify fix
```

### Workflow 3: "Debug After Hardware Failure"
```
1. Read STRATEGY.md "Debugging Decision Tree"
2. Run tb.py to get baseline
3. Run failing test in isolation
4. Check README.md for that test
5. View waveforms: gtkwave sim_build/verilog.vcd
6. Fix Verilog based on waveform analysis
7. Re-run test
8. Rebuild hardware bitstream
9. Test on FPGA
```

### Workflow 4: "Add New Test"
```
1. Copy existing_test_template.py
2. Create @cocotb.test() function
3. Add to test list in tb.py
4. Run: python tb.py
```

---

## 📞 Support

### Quick Questions
- See **README.md** for module-specific help
- See **STRATEGY.md** for "why" questions

### Test Fails?
- Read the assertion error message
- Check README.md for that test
- View waveforms in GTKWave
- Try manual stimulus in REPL

### Can't Find Something?
| Looking For | File |
|-------------|------|
| Overview | README.md |
| Debugging help | STRATEGY.md |
| Installation | quickstart.py |
| Running tests | tb.py |

---

## 🎓 Learning Resources

- **cocotb Documentation**: https://docs.cocotb.org/
- **OV7670 Datasheet**: https://www.ov.com/datasheet/OV7670
- **VGA Timing**: https://en.wikipedia.org/wiki/Video_Graphics_Array#Timings
- **RGB565 Format**: https://en.wikipedia.org/wiki/High_color

---

## 📝 Test Checklist

Before moving to hardware:

- [ ] Read README.md + STRATEGY.md
- [ ] Install cocotb + simulator
- [ ] Run quickstart.py --setup (no errors)
- [ ] Run tb.py (all tests PASS)
- [ ] Understand what each test does
- [ ] Know what to check if test fails
- [ ] Ready for hardware validation

---

## 🚀 Next Steps

1. **Start Here**: `python quickstart.py`
2. **Then Read**: `STRATEGY.md` (understand the approach)
3. **Then Run**: `python tb.py` (verify testbenches work)
4. **Then Fix**: Use failed tests to drive fixes
5. **Then Deploy**: Rebuild hardware with corrected code

Good luck! 🎯
