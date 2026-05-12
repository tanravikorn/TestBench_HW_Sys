"""
SCCB Controller Testbench
Tests the SCCB (Serial Camera Control Bus) protocol implementation
- START condition
- Device address write
- Register address write
- Data write
- ACK sequence
- STOP condition
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly
import os
from pathlib import Path
from cocotb_tools.runner import get_runner


async def start_transaction(dut, dev_addr, reg_addr, data, timeout_cycles=3000):
    dut.dev_addr.value = dev_addr
    dut.reg_addr.value = reg_addr
    dut.data.value = data
    dut.start.value = 1

    for _ in range(timeout_cycles):
        await RisingEdge(dut.clk)
        if int(dut.busy.value) == 1:
            break
    else:
        dut.start.value = 0
        assert False, "Timeout waiting for busy signal"

    dut.start.value = 0


def _is_high_or_z(sig_value):
    s = str(sig_value)
    return s in ("1", "Z", "z")


@cocotb.test()
async def sccb_basic_write_test(dut):
    """
    Test a complete SCCB write transaction:
    Device: 0x42, Register: 0x12, Data: 0x04
    Expected: START -> DEV_ADDR -> ACK1 -> REG_ADDR -> ACK2 -> DATA -> ACK3 -> STOP -> DONE
    """
    clock = Clock(dut.clk, 10, unit="ns")  # 100 MHz clock
    clock.start()

    # Reset
    dut.reset.value = 1
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    # Verify initial state: ready=1, busy=0
    await ReadOnly()
    assert int(dut.ready.value) == 1, "Ready should be 1 after reset"
    assert int(dut.busy.value) == 0, "Busy should be 0 after reset"
    await RisingEdge(dut.clk)

    # Start SCCB transaction (hold start until busy is seen)
    await start_transaction(dut, 0x42, 0x12, 0x04)
    assert int(dut.busy.value) == 1, "Busy should be 1 when transaction starts"

    # Wait for transaction to complete (ready goes back to 1)
    timeout = 0
    while int(dut.ready.value) == 0 and timeout < 50000:
        await RisingEdge(dut.clk)
        timeout += 1
    
    assert timeout < 50000, f"Timeout waiting for transaction complete (waited {timeout} cycles)"
    assert int(dut.ready.value) == 1, "Ready should return to 1 after transaction"

    # busy is cleared when FSM returns to IDLE on the next SCCB tick
    timeout = 0
    while int(dut.busy.value) != 0 and timeout < 1000:
        await RisingEdge(dut.clk)
        timeout += 1
    assert timeout < 1000, "Busy should return to 0 after transaction"

    # Verify SIO_C and SIO_D returned to idle (high)
    timeout = 0
    while timeout < 1000:
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.sio_c.value) == 1 and _is_high_or_z(dut.sio_d.value):
            break
        timeout += 1
    assert timeout < 1000, "Bus lines did not return to idle high"

    cocotb.log.info("✓ SCCB basic write test PASSED")


@cocotb.test()
async def sccb_multiple_writes_test(dut):
    """
    Test multiple consecutive SCCB transactions
    - Write 1: COM7 (0x12) = 0x80 (reset)
    - Write 2: CLKRC (0x11) = 0x00
    - Write 3: DBLV (0x6B) = 0x4A
    """
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    # Reset
    dut.reset.value = 1
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    transactions = [
        (0x42, 0x12, 0x80),  # COM7 reset
        (0x42, 0x11, 0x00),  # CLKRC
        (0x42, 0x6B, 0x4A),  # DBLV
    ]

    for dev_addr, reg_addr, data in transactions:
        # Setup transaction
        await start_transaction(dut, dev_addr, reg_addr, data)

        # Wait for completion
        timeout = 0
        while int(dut.ready.value) == 0 and timeout < 50000:
            await RisingEdge(dut.clk)
            timeout += 1

        assert timeout < 50000, f"Timeout on transaction: dev={hex(dev_addr)}, reg={hex(reg_addr)}, data={hex(data)}"
        assert int(dut.ready.value) == 1, f"Ready not asserted for {hex(reg_addr)}"
        
        cocotb.log.info(f"  ✓ Transaction {hex(reg_addr)}={hex(data)} complete")

    cocotb.log.info("✓ SCCB multiple writes test PASSED")


@cocotb.test()
async def sccb_bus_idle_test(dut):
    """
    Verify SIO_C and SIO_D bus behavior during idle and after transactions
    - Both should be high during idle
    - SIO_D should be controlled (driven low) during START/DATA/STOP
    - SIO_C should be controlled during entire transaction
    """
    clock = Clock(dut.clk, 10, unit="ns")
    clock.start()

    # Reset and verify idle state
    dut.reset.value = 1
    dut.start.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    await ReadOnly()
    assert int(dut.sio_c.value) == 1, "SIO_C should be high in idle"
    assert _is_high_or_z(dut.sio_d.value), "SIO_D should be high or Z in idle"
    await RisingEdge(dut.clk)

    # Start a transaction
    await start_transaction(dut, 0x42, 0x12, 0x80)

    # Wait for transaction completion
    timeout = 0
    while int(dut.ready.value) == 0 and timeout < 50000:
        await RisingEdge(dut.clk)
        timeout += 1
    assert timeout < 50000, "Timeout waiting for SCCB transaction complete"

    # After transaction, both should be high (allow one extra FSM tick)
    timeout = 0
    while timeout < 1000:
        await RisingEdge(dut.clk)
        await ReadOnly()
        if int(dut.sio_c.value) == 1 and _is_high_or_z(dut.sio_d.value):
            break
        timeout += 1
    assert timeout < 1000, "SIO lines did not return to idle"

    cocotb.log.info("✓ SCCB bus idle test PASSED")


def runner():
    """Build and run all SCCB tests"""
    verilog_files = ["../rtl/sccb_controller.v"]
    top_module = "sccb_controller"
    test_module = "sccb_controller_test"

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
