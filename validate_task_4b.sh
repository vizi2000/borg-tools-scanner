#!/bin/bash
echo "============================================================"
echo "Task 4B Validation Script"
echo "============================================================"
echo ""

# Check workflow files
echo "1. Checking workflow files..."
if [ -f "agent_zero_workflows/code_audit.yaml" ] && \
   [ -f "agent_zero_workflows/security_scan.yaml" ] && \
   [ -f "agent_zero_workflows/complexity_analysis.yaml" ]; then
    echo "   ✅ All 3 workflow YAMLs present"
else
    echo "   ❌ Missing workflow files"
    exit 1
fi

# Check Python modules
echo "2. Checking Python modules..."
if [ -f "modules/agent_zero_auditor.py" ] && \
   [ -f "modules/test_agent_zero_auditor.py" ]; then
    echo "   ✅ Core modules present"
else
    echo "   ❌ Missing Python modules"
    exit 1
fi

# Check documentation
echo "3. Checking documentation..."
if [ -f "AGENT_ZERO_AUDITOR_README.md" ] && \
   [ -f "TASK_4B_COMPLETION_REPORT.md" ] && \
   [ -f "QUICK_START_AGENT_ZERO_AUDITOR.md" ]; then
    echo "   ✅ All documentation present"
else
    echo "   ❌ Missing documentation"
    exit 1
fi

# Check integration example
echo "4. Checking integration example..."
if [ -f "agent_zero_integration_example.py" ]; then
    echo "   ✅ Integration example present"
else
    echo "   ❌ Missing integration example"
    exit 1
fi

# Run tests
echo "5. Running test suite..."
export PYTHONPATH=/Users/wojciechwiesner/ai/_Borg.tools_scan
if python3 modules/test_agent_zero_auditor.py 2>&1 | grep -q "All tests passed"; then
    echo "   ✅ All tests passed"
else
    echo "   ❌ Tests failed"
    exit 1
fi

# Count lines
echo ""
echo "6. Code Statistics..."
echo "   Workflow YAMLs: $(cat agent_zero_workflows/*.yaml | wc -l | tr -d ' ') lines"
echo "   Python Code: $(cat modules/agent_zero_auditor.py modules/test_agent_zero_auditor.py agent_zero_integration_example.py | wc -l | tr -d ' ') lines"
echo "   Documentation: $(cat *AGENT_ZERO*.md TASK_4B*.md | wc -l | tr -d ' ') lines"

echo ""
echo "============================================================"
echo "✅ Task 4B Validation: PASSED"
echo "============================================================"
