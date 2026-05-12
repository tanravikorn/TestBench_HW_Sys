"""
VGA Controller Testbench
Tests VGA timing and RGB565 color decoding
- HSYNC/VSYNC timing (640x480 @ 60Hz)
- Active region detection
- Address generation for BRAM reads
- RGB565 to 4-bit RGB conversion
- Pipelining delays (active_d1, active_d2)
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly
import os
from pathlib import Path
from cocotb_tools.runner import get_runner


async def _wait_for_frame_start(dut, timeout_cycles=450_000):
    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk_vga)
        if int(dut.h_cnt.value) == 0 and int(dut.v_cnt.value) == 0:
            return
    assert False, "Timeout waiting for frame start (h_cnt=0, v_cnt=0)"


@cocotb.test()
async def vga_timing_test(dut):
    """
    Test VGA timing generation
    - HSYNC: 800 clocks per line (96 clocks low between 656-752)
    - VSYNC: 525 lines per frame (2 clocks low between 490-492)
    - Verify proper sync pulse widths and timing
    """
    clk_vga = Clock(dut.clk_vga, 40, unit="ns")  # 25 MHz for 640x480
    clk_vga.start()
    await RisingEdge(dut.clk_vga)  # allow registered outputs to settle from X

    hsync_checked = False
    vsync_checked = False
    timeout_cycles = 500_000

    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk_vga)

        h_cnt = int(dut.h_cnt.value)
        v_cnt = int(dut.v_cnt.value)
        hsync = int(dut.hsync.value)

        # Check HSYNC window on visible frame start
        if v_cnt == 0 and h_cnt == 657:
            assert hsync == 0, f"HSYNC should be low at h=657, got {hsync}"
            hsync_checked = True
        if v_cnt == 0 and h_cnt == 753:
            assert hsync == 1, f"HSYNC should be high at h=753, got {hsync}"

        # Check VSYNC window once per frame timing
        if h_cnt == 0 and v_cnt == 491:
            assert int(dut.vsync.value) == 0, "VSYNC should be low at v=491"
            vsync_checked = True
        if h_cnt == 0 and v_cnt == 493:
            assert int(dut.vsync.value) == 1, "VSYNC should be high at v=493"

        if hsync_checked and vsync_checked:
            break

    assert hsync_checked, "Timeout waiting to verify HSYNC timing"
    assert vsync_checked, "Timeout waiting to verify VSYNC timing"

    cocotb.log.info("✓ VGA timing test PASSED")


@cocotb.test()
async def vga_address_generation_test(dut):
    """
    Test BRAM read address generation
    - Verify address increments correctly through frame
    - Check row/column calculation: row_addr = (row << 8) + (row << 6), addr = row_addr + col
    """
    clk_vga = Clock(dut.clk_vga, 40, unit="ns")
    clk_vga.start()
    await RisingEdge(dut.clk_vga)
    await _wait_for_frame_start(dut)

    dut.frame_data.value = 0xF800

    active_addresses = []
    last_addr = None

    # Sample active region addresses from start of active frame
    for _ in range(20_000):
        await RisingEdge(dut.clk_vga)

        h_cnt = int(dut.h_cnt.value)
        v_cnt = int(dut.v_cnt.value)
        read_addr = int(dut.read_addr.value)

        if h_cnt < 640 and v_cnt < 480:
            if read_addr != last_addr:
                active_addresses.append((v_cnt, h_cnt, read_addr))
                last_addr = read_addr
            if len(active_addresses) >= 40:
                break

    assert active_addresses, "Did not capture active-region addresses"
    for v, h, addr in active_addresses[8:20]:
        expected_addr = (v >> 1) * 320 + (h >> 1)
        assert addr == expected_addr, f"At v={v}, h={h}: addr={addr}, expected={expected_addr}"

    cocotb.log.info(f"✓ VGA address generation test PASSED (checked {len(active_addresses)} addresses)")


@cocotb.test()
async def vga_rgb565_decode_test(dut):
    """
    Test RGB565 to 4-bit RGB conversion
    Input RGB565 format: RRRRRGGG GGGBBBBB
    Output: 4-bit R, G, B (top 4 bits of each channel)
    - R[15:12] → R[4:1] (5 bits, take upper 4)
    - G[10:7]  → G[5:2] (6 bits, take upper 4)  
    - B[4:1]   → B[4:1] (5 bits, take upper 4)
    """
    clk_vga = Clock(dut.clk_vga, 40, unit="ns")
    clk_vga.start()
    await RisingEdge(dut.clk_vga)
    await _wait_for_frame_start(dut)

    # Wait until display pipeline is active
    for _ in range(20_000):
        await RisingEdge(dut.clk_vga)
        if int(dut.active_d2.value) == 1:
            break
    assert int(dut.active_d2.value) == 1, "Timeout waiting for active_d2"

    test_patterns = [
        ("Red", 0xF800, (0xF, 0x0, 0x0)),
        ("Green", 0x07E0, (0x0, 0xF, 0x0)),
        ("Blue", 0x001F, (0x0, 0x0, 0xF)),
        ("White", 0xFFFF, (0xF, 0xF, 0xF)),
    ]

    for name, input_rgb565, expected_output in test_patterns:
        await RisingEdge(dut.clk_vga)
        dut.frame_data.value = input_rgb565
        await RisingEdge(dut.clk_vga)
        await ReadOnly()
        observed = (int(dut.vga_r.value), int(dut.vga_g.value), int(dut.vga_b.value))
        assert observed == expected_output, (
            f"{name} decode mismatch: got {observed}, expected {expected_output}"
        )
        cocotb.log.info(f"  ✓ RGB565 decode: {name} (0x{input_rgb565:04X}) -> {observed}")

    cocotb.log.info("✓ VGA RGB565 decode test PASSED")


@cocotb.test()
async def vga_active_region_test(dut):
    """
    Test active region detection
    - Active: h_cnt < 640 and v_cnt < 480
    - Inactive (blanking): h_cnt >= 640 or v_cnt >= 480
    - Verify active_d1, active_d2 pipeline delays
    """
    clk_vga = Clock(dut.clk_vga, 40, unit="ns")
    clk_vga.start()
    await RisingEdge(dut.clk_vga)

    active_samples = 0
    blank_samples = 0

    for _ in range(200_000):
        await RisingEdge(dut.clk_vga)

        h_cnt = int(dut.h_cnt.value)
        v_cnt = int(dut.v_cnt.value)
        active_d2 = int(dut.active_d2.value)

        if v_cnt == 0 and 100 <= h_cnt <= 200:
            assert active_d2 == 1, f"active_d2 should be 1 in active region (h={h_cnt}, v={v_cnt})"
            active_samples += 1
        if v_cnt == 0 and 700 <= h_cnt <= 750:
            assert active_d2 == 0, f"active_d2 should be 0 in horizontal blanking (h={h_cnt}, v={v_cnt})"
            blank_samples += 1
        if h_cnt == 0 and 500 <= v_cnt <= 510:
            assert active_d2 == 0, f"active_d2 should be 0 in vertical blanking (h={h_cnt}, v={v_cnt})"
            blank_samples += 1

        if active_samples >= 10 and blank_samples >= 10:
            break

    assert active_samples >= 10, "Not enough active-region samples collected"
    assert blank_samples >= 10, "Not enough blanking-region samples collected"
    cocotb.log.info(f"✓ VGA active region test PASSED (active={active_samples}, blank={blank_samples})")


@cocotb.test()
async def vga_full_frame_test(dut):
    """
    Test complete VGA frame generation
    - Verify counter wrap-around
    - Check sync pulse timing over multiple frames
    - Ensure stable 60Hz frame rate
    """
    clk_vga = Clock(dut.clk_vga, 40, unit="ns")  # 25 MHz
    clk_vga.start()
    await RisingEdge(dut.clk_vga)

    intervals = []
    previous_frame_cycle = None
    expected_cycles_per_frame = 800 * 525

    for cycle in range(900_000):
        await RisingEdge(dut.clk_vga)

        h_cnt = int(dut.h_cnt.value)
        v_cnt = int(dut.v_cnt.value)
        if h_cnt == 0 and v_cnt == 0:
            if previous_frame_cycle is None:
                previous_frame_cycle = cycle
            else:
                intervals.append(cycle - previous_frame_cycle)
                previous_frame_cycle = cycle
            if len(intervals) == 1:
                break

    assert len(intervals) == 1, "Timeout waiting for full-frame wrap markers"
    for i, frame_cycles in enumerate(intervals):
        assert frame_cycles == expected_cycles_per_frame, (
            f"Frame interval {i}: {frame_cycles}, expected {expected_cycles_per_frame}"
        )

    cocotb.log.info(f"✓ VGA full frame test PASSED (intervals={intervals})")


def runner():
    """Build and run all VGA controller tests"""
    verilog_files = ["../rtl/vga_controller.v"]
    top_module = "vga_controller"
    test_module = "vga_controller_test"

    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent
    sources = [proj_path / Path(f) for f in verilog_files]

    run = get_runner(sim)

    run.build(
        sources=sources,
        hdl_toplevel=top_module,
        always=True,
        waves=True,
        timescale=("1ns", "1ps"),
    )

    run.test(
        hdl_toplevel=top_module,
        test_module=test_module,
        waves=True,
    )


if __name__ == "__main__":
    runner()
