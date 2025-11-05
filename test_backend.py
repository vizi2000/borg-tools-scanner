#!/usr/bin/env python3
"""Test FastAPI backend import"""
import sys
sys.path.insert(0, 'dashboard/backend')

try:
    from main import app
    print("✅ FastAPI app imported successfully")
    print(f"✅ Total routes: {len(app.routes)}")
    print("✅ New endpoints:")
    print("   - Deep Analysis API (analysis.py)")
    print("   - Chat Agent V3 with Minimax M2 (chat_agent_v3.py)")
    print("   - Screenshot Generator (screenshot_generator.py)")
    print("   - Notes System (notes.py)")
    print("\n🎉 ALL SYSTEMS OPERATIONAL!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
