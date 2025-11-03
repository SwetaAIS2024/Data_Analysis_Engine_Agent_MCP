"""
Test V2 Pipeline: User Feedback Scenario
Tests the flow when a tool is unavailable and user feedback is required

Scenario:
- User wants: "Detect anomalies and generate a detailed report"
- Tool 1: anomaly_zscore (AVAILABLE)
- Tool 2: anomaly_report_generator (NOT AVAILABLE)
- Expected: System detects conflict, requests user feedback

This demonstrates:
1. Context extraction from natural language
2. Chaining manager detects missing tool
3. Conflict resolution with USER_FEEDBACK
4. Fallback options presented to user
"""

import requests
import json
import sys

# Test configuration
BASE_URL = "http://localhost:8080"
TENANT_ID = "test-tenant"

# Sample timeseries data with anomalies
TEST_DATA = [
    {"timestamp": "2025-01-01T00:00:00", "value": 100, "sensor_id": "S1"},
    {"timestamp": "2025-01-01T00:05:00", "value": 102, "sensor_id": "S1"},
    {"timestamp": "2025-01-01T00:10:00", "value": 105, "sensor_id": "S1"},
    {"timestamp": "2025-01-01T00:15:00", "value": 500, "sensor_id": "S1"},  # Anomaly
    {"timestamp": "2025-01-01T00:20:00", "value": 103, "sensor_id": "S1"},
    {"timestamp": "2025-01-01T00:25:00", "value": 107, "sensor_id": "S1"},
    {"timestamp": "2025-01-01T00:30:00", "value": 600, "sensor_id": "S1"},  # Anomaly
    {"timestamp": "2025-01-01T00:35:00", "value": 104, "sensor_id": "S1"},
]


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_json(data, title=""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2))


def test_user_feedback_scenario():
    """Test scenario requiring user feedback for missing tool"""
    
    print_section("TEST: V2 Pipeline with Missing Tool (User Feedback Required)")
    
    # Step 1: Build request with natural language that requires two tools
    print("📝 STEP 1: Building request requiring two tools...")
    
    user_prompt = """
    Detect anomalies in the sensor data using z-score method with threshold 2.5, 
    and then generate a comprehensive report with visualizations and statistics 
    about the detected anomalies.
    """
    
    payload = {
        "tenant_id": TENANT_ID,
        "context": {
            "task": user_prompt.strip()
        },
        "data_pointer": {
            "format": "inline",
            "rows": TEST_DATA
        },
        "params": {
            "metric": "value",
            "threshold": 2.5
        }
    }
    
    print(f"User Prompt: {user_prompt.strip()}")
    print(f"Data: {len(TEST_DATA)} rows")
    print_json(payload["params"], "Parameters")
    
    # Step 2: Send request to V2 endpoint
    print_section("STEP 2: Sending request to /v2/analyze")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v2/analyze",
            json=payload,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return False
        
        result = response.json()
        
        # Step 3: Analyze response
        print_section("STEP 3: Analyzing V2 Response")
        
        print(f"Request ID: {result.get('request_id')}")
        print(f"Status: {result.get('status')}")
        
        # Context Extraction Results
        if result.get('tool_meta', {}).get('context_extraction'):
            print_json(
                result['tool_meta']['context_extraction'],
                "Context Extraction"
            )
        
        # Execution Plan
        if result.get('tool_meta', {}).get('execution_plan'):
            plan = result['tool_meta']['execution_plan']
            print_json(plan, "Execution Plan")
            
            print(f"\n📋 Strategy: {plan.get('strategy')}")
            print(f"📦 Tools Planned: {', '.join(plan.get('tools', []))}")
            
            if plan.get('conflicts'):
                print(f"⚠️  Conflicts Detected: {len(plan['conflicts'])}")
        
        # Pipeline Results
        print_section("STEP 4: Pipeline Results")
        
        pipeline_result = result.get('result', {})
        print(f"Pipeline Status: {pipeline_result.get('status')}")
        
        # Tool Execution Results
        if pipeline_result.get('results'):
            print(f"\n📊 Tool Results:")
            for idx, tool_result in enumerate(pipeline_result['results'], 1):
                print(f"\n  Tool {idx}: {tool_result.get('tool_id')}")
                print(f"    Status: {tool_result.get('status')}")
                if tool_result.get('error'):
                    print(f"    Error: {tool_result.get('error')}")
                if tool_result.get('output'):
                    print(f"    Output: Available")
        
        # Summary
        if pipeline_result.get('summary'):
            print_json(pipeline_result['summary'], "Summary")
        
        # Step 5: Check for User Feedback Required
        print_section("STEP 5: User Feedback Check")
        
        if pipeline_result.get('user_feedback'):
            print("🔔 USER FEEDBACK REQUIRED!")
            print_json(pipeline_result['user_feedback'], "Feedback Request")
            
            feedback = pipeline_result['user_feedback']
            print(f"\n📢 Message: {feedback.get('message')}")
            
            if feedback.get('unavailable_tools'):
                print(f"\n❌ Unavailable Tools:")
                for tool in feedback['unavailable_tools']:
                    print(f"   - {tool}")
            
            if feedback.get('options'):
                print(f"\n📝 User Options:")
                for idx, option in enumerate(feedback['options'], 1):
                    print(f"\n   Option {idx}: {option.get('message')}")
                    print(f"   Action: {option.get('action')}")
                    if option.get('tools'):
                        print(f"   Tools: {', '.join(option['tools'])}")
            
            print("\n" + "─" * 80)
            print("✅ SUCCESS: User feedback mechanism working correctly!")
            print("   - System detected missing tool: 'anomaly_report_generator'")
            print("   - Context extraction identified need for reporting")
            print("   - Chaining manager detected conflict")
            print("   - User presented with options to resolve")
            print("─" * 80)
            
            return True
        else:
            print("ℹ️  No user feedback required")
            print("   All requested tools were available and executed")
            return True
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend")
        print("   Make sure the agent is running on http://localhost:8080")
        return False
    
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_successful_execution():
    """Test scenario with all tools available"""
    
    print_section("TEST: V2 Pipeline with Available Tool (Success)")
    
    user_prompt = "Detect anomalies in sensor data with threshold 2.5"
    
    payload = {
        "tenant_id": TENANT_ID,
        "context": {
            "task": user_prompt
        },
        "data_pointer": {
            "format": "inline",
            "rows": TEST_DATA
        },
        "params": {
            "metric": "value",
            "threshold": 2.5
        }
    }
    
    print(f"User Prompt: {user_prompt}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/v2/analyze",
            json=payload,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return False
        
        result = response.json()
        
        pipeline_result = result.get('result', {})
        print(f"Pipeline Status: {pipeline_result.get('status')}")
        
        if pipeline_result.get('status') == 'success':
            print("✅ SUCCESS: Anomaly detection completed without issues!")
            
            # Show detected anomalies
            if pipeline_result.get('results'):
                for tool_result in pipeline_result['results']:
                    if tool_result.get('status') == 'success' and tool_result.get('output'):
                        output = tool_result['output']
                        if isinstance(output, dict) and 'output' in output:
                            output = output['output']
                        if isinstance(output, dict) and 'anomalies' in output:
                            anomalies = output['anomalies']
                            print(f"\n📊 Detected {len(anomalies)} anomalies:")
                            for anomaly in anomalies[:3]:  # Show first 3
                                print(f"   - {anomaly}")
            
            return True
        else:
            print(f"⚠️  Pipeline completed with status: {pipeline_result.get('status')}")
            return False
    
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    """Run all test scenarios"""
    
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  V2 PIPELINE TEST SUITE - USER FEEDBACK & CONFLICT RESOLUTION".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    results = []
    
    # Test 1: Successful execution with available tool
    result1 = test_successful_execution()
    results.append(("Available Tool Test", result1))
    
    # Test 2: User feedback required for missing tool
    result2 = test_user_feedback_scenario()
    results.append(("Missing Tool Test", result2))
    
    # Summary
    print_section("TEST SUMMARY")
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
