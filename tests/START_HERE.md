# ✅ TESTBENCH SUITE COMPLETE

## What Was Created

**Location**: `C:\Users\Lenovo\Desktop\hw_testbench\tests\`

### 📦 9 Files Total:

**Testbenches (3)**:
- `sccb_controller_test.py` - Test SCCB I2C protocol for camera config
- `camera_capture_test.py` - Test pixel capture to BRAM
- `vga_controller_test.py` - Test VGA timing and RGB decode

**Runners (3)**:
- `tb.py` - Master runner (run all 13 tests)
- `quickstart.py` - Setup helper + run tools
- `SETUP.bat` / `SETUP.sh` - Platform-specific setup

**Documentation (3)**:
- `README.md` - Complete reference (how to run, what each test does)
- `STRATEGY.md` - **START HERE** (why testbenches matter, debugging guide)
- `INDEX.md` - Quick reference guide

---

## 🚀 Quick Start (90 seconds)

```bash
# 1. Install cocotb
pip install cocotb cocotb-tools

# 2. Run setup
python quickstart.py --setup

# 3. Run all tests
python tb.py
```

**Expected**: 13 tests run, all PASS (6-7 seconds)

---

## 📖 Read This First

**→ Open `STRATEGY.md`** (12 min read)

It explains:
- Why testbenches matter for YOUR green/rotation issues
- How each test helps isolate problems
- Decision tree: "If color is wrong, check this..."
- How to use tests to drive fixes

---

## 🎯 What Tests Cover

| Module | Tests | Purpose |
|--------|-------|---------|
| **SCCB** | 3 | Verify camera config protocol (register writes) |
| **Camera Capture** | 5 | Verify pixel buffering & QVGA frame sync |
| **VGA** | 5 | Verify VGA timing (640×480), RGB decode |

**Total**: 13 comprehensive tests

---

## 🔍 For Your Issues

### Green Color Tone?
→ Run `camera_capture_test.py` + `vga_controller_test.py`
→ Tests will show if byte order or RGB channels are wrong

### Image Rotation?
→ Run `sccb_controller_test.py`
→ Test will show if MVFP register is being written correctly

---

## 📁 Files in This Directory

```
tests/
├── Core Tests
│   ├── sccb_controller_test.py
│   ├── camera_capture_test.py
│   └── vga_controller_test.py
├── Runners
│   ├── tb.py
│   ├── quickstart.py
│   ├── SETUP.bat
│   └── SETUP.sh
├── Documentation
│   ├── README.md (reference)
│   ├── STRATEGY.md (start here)
│   ├── INDEX.md (quick ref)
│   └── THIS_FILE
└── Generated (after first run)
    ├── sim_build/verilog.vcd (waveforms)
    └── __pycache__/
```

---

## ✅ Checklist

- [ ] Read `STRATEGY.md`
- [ ] Run `python quickstart.py --setup`
- [ ] Run `python tb.py`
- [ ] All tests PASS?
  - Yes → Build FPGA, test hardware
  - No → Check README.md for failing test, debug

---

## 💡 Key Insight

**Testbenches test LOGIC (not appearance)**:
- ✓ Can verify bytes are in correct order
- ✓ Can verify RGB channels are correctly extracted
- ✓ Can verify SCCB protocol sends registers
- ✗ Cannot tell if video looks green (need hardware for that)

**But**: If testbenches pass → Logic is correct → Hardware should work

---

## 🎓 Next Steps

1. **Read**: Open `STRATEGY.md` (why these matter for your issues)
2. **Setup**: Run `python quickstart.py --setup`
3. **Test**: Run `python tb.py`
4. **Understand**: Check `README.md` for any failing tests
5. **Debug**: Use `sim_build/verilog.vcd` waveforms if needed
6. **Fix**: Edit Verilog, re-run tests
7. **Deploy**: Rebuild FPGA with corrected code

---

## 📞 Troubleshooting

**Tests won't run?**
→ Check `README.md` section "Prerequisites"

**Don't understand what a test does?**
→ Check `README.md` section for that module

**Tests fail, don't know why?**
→ Read error message → Check `README.md` → View waveforms

**Need overall strategy?**
→ Read `STRATEGY.md` section "Debugging Decision Tree"

---

**Ready? Open `STRATEGY.md` now!** 👈

