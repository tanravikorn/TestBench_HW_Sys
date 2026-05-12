#!/usr/bin/env bash
# OV7670→VGA Pipeline Testbench Suite
# Quick Setup & Run Guide

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================================================="
echo "OV7670→VGA Pipeline Testbench Suite - Setup Guide"
echo "======================================================================="
echo ""

# Step 1: Check Python
echo -e "${YELLOW}Step 1: Checking Python...${NC}"
python --version
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Python not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found${NC}"
echo ""

# Step 2: Install cocotb (if not present)
echo -e "${YELLOW}Step 2: Checking cocotb...${NC}"
python -c "import cocotb" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "cocotb not found. Installing..."
    pip install -U cocotb cocotb-tools
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to install cocotb${NC}"
        echo "Try: pip install cocotb cocotb-tools"
        exit 1
    fi
fi
echo -e "${GREEN}✓ cocotb installed${NC}"
cocotb_version=$(python -c "import cocotb; print(cocotb.__version__)")
echo "   Version: $cocotb_version"
echo ""

# Step 3: Check simulator
echo -e "${YELLOW}Step 3: Checking simulator...${NC}"
SIM_FOUND=0

# Check Icarus Verilog
if command -v iverilog &> /dev/null; then
    echo -e "${GREEN}✓ Icarus Verilog found${NC}"
    iverilog --version | head -1
    SIM_FOUND=1
    export SIM=icarus
fi

# Check Vivado xsim
if command -v xsim &> /dev/null; then
    echo -e "${GREEN}✓ Vivado xsim found${NC}"
    SIM_FOUND=1
    export SIM=xsim
fi

if [ $SIM_FOUND -eq 0 ]; then
    echo -e "${YELLOW}⚠ No simulator found${NC}"
    echo "Install one of:"
    echo "  - Icarus Verilog: http://bleyer.org/icarus/ (recommended, free)"
    echo "  - Vivado xsim: https://www.xilinx.com/ (already have it)"
    echo ""
    echo "Continuing anyway... (tests will fail without simulator)"
fi
echo ""

# Step 4: Navigate to tests directory
cd "$(dirname "$0")"

# Step 5: Display options
echo "======================================================================="
echo "Setup Complete! Now you can run:"
echo "======================================================================="
echo ""
echo -e "${GREEN}Option 1: Run all tests${NC}"
echo "  python tb.py"
echo ""
echo -e "${GREEN}Option 2: Run specific test${NC}"
echo "  python sccb_controller_test.py"
echo "  python camera_capture_test.py"
echo "  python vga_controller_test.py"
echo ""
echo -e "${GREEN}Option 3: Run with helper${NC}"
echo "  python quickstart.py"
echo "  python quickstart.py --setup"
echo "  python quickstart.py --test sccb"
echo ""
echo -e "${GREEN}Option 4: Read documentation first${NC}"
echo "  README.md       - Complete test documentation"
echo "  STRATEGY.md     - Debugging strategy & decision trees"
echo "  INDEX.md        - File index & workflows"
echo ""
echo "======================================================================="
echo "Next Step: Read STRATEGY.md (explains why testbenches matter)"
echo "======================================================================="
echo ""
