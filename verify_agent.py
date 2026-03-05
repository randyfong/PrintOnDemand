import os
from staples_agent import run_print_flow

def test_imports():
    try:
        from tools import SendEmailTool, WaitAndExtractReleaseCodeTool
        print("✅ Tools imported successfully.")
    except ImportError as e:
        print(f"❌ Failed to import tools: {e}")

def test_agent_definition():
    try:
        from staples_agent import print_specialist
        print(f"✅ Agent '{print_specialist.role}' defined successfully.")
        print(f"✅ Agent has {len(print_specialist.tools)} tools.")
    except Exception as e:
        print(f"❌ Failed to verify agent: {e}")

if __name__ == "__main__":
    print("--- Running Verification ---")
    test_imports()
    test_agent_definition()
    print("--- Verification Complete ---")
    print("\nTo run the actual flow, set your credentials in environment variables and call run_print_flow(pdf_path, user_email).")
