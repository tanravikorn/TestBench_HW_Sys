@echo off
REM OV7670->VGA Pipeline Testbench Suite
REM Quick Setup & Run Guide for Windows

setlocal enabledelayedexpansion

echo.
echo =========================================================================
echo OV7670 -^> VGA Pipeline Testbench Suite - Setup Guide (Windows)
echo =========================================================================
echo.

REM Step 1: Check Python
echo Step 1: Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python found: %PYTHON_VERSION%
echo.

REM Step 2: Install cocotb
echo Step 2: Checking cocotb...
python -c "import cocotb" >nul 2>&1
if errorlevel 1 (
    echo cocotb not found. Installing...
    python -m pip install -U cocotb cocotb-tools
    if errorlevel 1 (
        echo [X] Failed to install cocotb
        echo Try: pip install cocotb cocotb-tools
        exit /b 1
    )
)
for /f "tokens=*" %%i in ('python -c "import cocotb; print(cocotb.__version__)"') do set COCOTB_VERSION=%%i
echo [OK] cocotb installed: %COCOTB_VERSION%
echo.

REM Step 3: Check simulator
echo Step 3: Checking simulator...
set SIM_FOUND=0

REM Check Icarus Verilog
where /Q iverilog
if not errorlevel 1 (
    echo [OK] Icarus Verilog found
    set SIM_FOUND=1
    set SIM=icarus
)

REM Check Vivado xsim
where /Q xsim
if not errorlevel 1 (
    echo [OK] Vivado xsim found
    set SIM_FOUND=1
    set SIM=xsim
)

if %SIM_FOUND% equ 0 (
    echo [!] No simulator found
    echo Install one of:
    echo   - Icarus Verilog: http://bleyer.org/icarus/ (recommended, free^)
    echo   - Vivado xsim: https://www.xilinx.com/ (already have it^)
    echo.
    echo Continuing anyway... (tests will fail without simulator^)
)
echo.

REM Step 4: Show summary
echo =========================================================================
echo Setup Complete! Now you can run:
echo =========================================================================
echo.
echo [1] Run all tests:
echo     python tb.py
echo.
echo [2] Run specific test:
echo     python sccb_controller_test.py
echo     python camera_capture_test.py
echo     python vga_controller_test.py
echo.
echo [3] Run with helper:
echo     python quickstart.py
echo     python quickstart.py --setup
echo     python quickstart.py --test sccb
echo.
echo [4] Read documentation first:
echo     README.md       - Complete test documentation
echo     STRATEGY.md     - Debugging strategy
echo     INDEX.md        - File index
echo.
echo =========================================================================
echo Next Step: Read STRATEGY.md
echo =========================================================================
echo.

pause
