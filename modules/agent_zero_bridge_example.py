"""
Agent Zero Bridge Example Script

Demonstrates how to use the Agent Zero Bridge to submit tasks and retrieve results.
Shows connection testing, task submission, and result polling.

Created by The Collective Borg.tools
"""

import sys
import json
import logging
from pathlib import Path
from agent_zero_bridge import (
    AgentZeroBridge,
    create_bridge,
    ConnectionError,
    TaskSubmissionError,
    TaskResultError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_connection_test():
    """Example 1: Test basic connection to Agent Zero."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Connection Test")
    print("=" * 70)

    try:
        # Create bridge instance
        bridge = AgentZeroBridge()

        # Test connection with health check
        print("\n🔌 Testing connection to Agent Zero...")
        health = bridge.health_check()

        print("\n✅ Connection successful!")
        print(f"Health check response: {json.dumps(health, indent=2)}")

        bridge.close()

    except ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        print("Make sure Agent Zero is running on borg.tools:50001")
        return False

    return True


def example_2_submit_code_audit():
    """Example 2: Submit a code audit task."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Submit Code Audit Task")
    print("=" * 70)

    # Use current directory as example project
    project_path = Path.cwd()
    print(f"\n📁 Project path: {project_path}")

    try:
        with AgentZeroBridge() as bridge:
            print("\n🔍 Submitting code audit task (without polling)...")

            # Submit without polling to get task_id immediately
            result = bridge.run_code_audit(
                project_path=str(project_path),
                tools=['pylint', 'eslint'],
                poll=False
            )

            print(f"\n✅ Task submitted successfully!")
            print(f"Task ID: {result['task_id']}")
            print(f"Status: {result['status']}")

            return result['task_id']

    except TaskSubmissionError as e:
        print(f"\n❌ Task submission failed: {e}")
        return None
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        return None


def example_3_poll_task_result(task_id: str):
    """Example 3: Poll for task result."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Poll for Task Result")
    print("=" * 70)

    if not task_id:
        print("\n⚠️ No task_id provided, skipping...")
        return

    try:
        with AgentZeroBridge() as bridge:
            print(f"\n🔄 Polling for task {task_id}...")

            # Poll with limited attempts for demo
            result = bridge.get_result(task_id, poll=True, max_attempts=5)

            print(f"\n✅ Result retrieved!")
            print(f"Status: {result.get('status')}")

            if result.get('status') == 'completed':
                print("\n📊 Task completed successfully!")
                print(f"Result: {json.dumps(result.get('result', {}), indent=2)}")
            elif result.get('status') == 'timeout':
                print("\n⏱️ Polling timeout - task still running")
                print("You can poll again later with bridge.get_result(task_id)")
            elif result.get('status') == 'failed':
                print(f"\n❌ Task failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"\n⚠️ Unexpected status: {result.get('status')}")

    except TaskResultError as e:
        print(f"\n❌ Failed to retrieve result: {e}")
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")


def example_4_submit_with_polling():
    """Example 4: Submit task and wait for completion."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Submit Task with Automatic Polling")
    print("=" * 70)

    project_path = Path.cwd()
    print(f"\n📁 Project path: {project_path}")

    try:
        with AgentZeroBridge(poll_interval=2) as bridge:
            print("\n🔍 Submitting code audit with automatic polling...")
            print("(Will poll every 2 seconds for up to 5 minutes)")

            result = bridge.run_code_audit(
                project_path=str(project_path),
                poll=True  # Will wait for completion
            )

            if result.get('status') == 'completed':
                print("\n✅ Task completed successfully!")
                print(f"Result: {json.dumps(result.get('result', {}), indent=2)}")
            elif result.get('status') == 'timeout':
                print("\n⏱️ Task is taking longer than expected")
                print(f"Task ID: {result.get('task_id')}")
                print("You can check status later")
            else:
                print(f"\n⚠️ Task finished with status: {result.get('status')}")

    except (TaskSubmissionError, TaskResultError) as e:
        print(f"\n❌ Error: {e}")
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")


def example_5_security_scan():
    """Example 5: Run security scan."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Security Scan")
    print("=" * 70)

    project_path = Path.cwd()
    print(f"\n📁 Project path: {project_path}")

    try:
        with AgentZeroBridge() as bridge:
            print("\n🔒 Submitting security scan...")

            result = bridge.run_security_scan(
                project_path=str(project_path),
                tools=['bandit', 'safety'],
                poll=False
            )

            print(f"\n✅ Security scan submitted!")
            print(f"Task ID: {result['task_id']}")

    except (TaskSubmissionError, ConnectionError) as e:
        print(f"\n❌ Error: {e}")


def example_6_custom_task():
    """Example 6: Submit custom task with YAML definition."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Custom Task Submission")
    print("=" * 70)

    project_path = Path.cwd()
    print(f"\n📁 Project path: {project_path}")

    # Define custom task
    custom_task = {
        'name': 'run_tests',
        'command': 'pytest',
        'args': ['--verbose', '--cov'],
        'timeout': 300,
        'env': {
            'PYTHONPATH': str(project_path)
        }
    }

    print(f"\n🎯 Custom task definition:")
    print(json.dumps(custom_task, indent=2))

    try:
        with AgentZeroBridge() as bridge:
            print("\n📡 Submitting custom task...")

            result = bridge.submit_custom_task(
                project_path=str(project_path),
                task_definition=custom_task,
                poll=False
            )

            print(f"\n✅ Custom task submitted!")
            print(f"Task ID: {result['task_id']}")

    except (TaskSubmissionError, ConnectionError) as e:
        print(f"\n❌ Error: {e}")


def example_7_error_handling():
    """Example 7: Graceful error handling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Error Handling")
    print("=" * 70)

    try:
        # Try to submit task for non-existent path
        print("\n🧪 Testing with invalid project path...")

        with AgentZeroBridge() as bridge:
            bridge.run_code_audit('/nonexistent/path', poll=False)

    except TaskSubmissionError as e:
        print(f"\n✅ Correctly caught error: {e}")
    except Exception as e:
        print(f"\n⚠️ Unexpected error: {type(e).__name__}: {e}")


def example_8_factory_function():
    """Example 8: Using factory function."""
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Using Factory Function")
    print("=" * 70)

    try:
        # Create bridge with custom settings using factory
        bridge = create_bridge(
            base_url='http://borg.tools:50001',
            timeout=60
        )

        print("\n🔌 Testing bridge created with factory...")
        health = bridge.health_check()

        print(f"\n✅ Factory-created bridge works!")
        print(f"Health: {json.dumps(health, indent=2)}")

        bridge.close()

    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")


def example_9_check_task_status():
    """Example 9: Check task status without polling."""
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Check Task Status (No Polling)")
    print("=" * 70)

    # This would use a real task_id from a previous submission
    task_id = "example-task-123"
    print(f"\n🔍 Checking status of task: {task_id}")

    try:
        with AgentZeroBridge() as bridge:
            status = bridge.get_task_status(task_id)
            print(f"\n📊 Task status:")
            print(json.dumps(status, indent=2))

    except TaskResultError as e:
        print(f"\n⚠️ Could not get status (task may not exist): {e}")
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")


def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "=" * 70)
    print("AGENT ZERO BRIDGE - COMPLETE DEMO")
    print("=" * 70)
    print("\nThis demo shows all features of the Agent Zero Bridge.")
    print("Some examples may fail if Agent Zero is not available.")

    # Example 1: Connection test (required for others)
    if not example_1_basic_connection_test():
        print("\n⚠️ Cannot continue without connection to Agent Zero")
        print("Please make sure Agent Zero is running on borg.tools:50001")
        return

    # Example 2: Submit task without polling
    task_id = example_2_submit_code_audit()

    # Example 3: Poll for result of submitted task
    if task_id:
        example_3_poll_task_result(task_id)

    # Example 4: Submit with automatic polling (commented out to save time)
    # example_4_submit_with_polling()

    # Example 5: Security scan
    example_5_security_scan()

    # Example 6: Custom task
    example_6_custom_task()

    # Example 7: Error handling
    example_7_error_handling()

    # Example 8: Factory function
    example_8_factory_function()

    # Example 9: Check status
    example_9_check_task_status()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)


def run_quick_test():
    """Run a quick connection test."""
    print("\n" + "=" * 70)
    print("QUICK CONNECTION TEST")
    print("=" * 70)

    try:
        bridge = AgentZeroBridge()
        health = bridge.health_check()
        print("\n✅ Connection successful!")
        print(f"Response: {json.dumps(health, indent=2)}")
        bridge.close()
        return True
    except ConnectionError as e:
        print(f"\n❌ Connection failed: {e}")
        return False


if __name__ == '__main__':
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'test':
            run_quick_test()
        elif command == 'health':
            example_1_basic_connection_test()
        elif command == 'audit':
            example_2_submit_code_audit()
        elif command == 'security':
            example_5_security_scan()
        elif command == 'custom':
            example_6_custom_task()
        elif command == 'all':
            run_all_examples()
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  test      - Quick connection test")
            print("  health    - Health check example")
            print("  audit     - Code audit example")
            print("  security  - Security scan example")
            print("  custom    - Custom task example")
            print("  all       - Run all examples")
    else:
        # Default: run connection test
        print("\nNo command specified, running quick connection test...")
        print("Use 'python agent_zero_bridge_example.py all' to see all examples")
        run_quick_test()
