#!/usr/bin/env python3
"""
MigrateX Manual Testing Script

This script helps you test MigrateX functionality on CRUST-bench repositories.
Run this to verify your setup and see MigrateX in action!
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 MigrateX Manual Testing Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("CRUST-bench").exists():
        print("❌ Error: CRUST-bench directory not found!")
        print("Please run this script from the MigrateX root directory.")
        print("Make sure CRUST-bench/ exists in the current directory.")
        return 1
    
    # Check if API key is set
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set!")
        print("Please set it by running:")
        print("export GOOGLE_API_KEY='your-api-key-here'")
        print("Or add it to your .env file")
        return 1
    
    print("✅ Environment setup looks good!")
    print(f"✅ API key found: {api_key[:10]}...")
    print(f"✅ CRUST-bench directory exists")
    
    # Show available repositories
    crust_bench_path = Path("CRUST-bench/datasets/CBench")
    if crust_bench_path.exists():
        repos = [d for d in crust_bench_path.iterdir() if d.is_dir()]
        print(f"✅ Found {len(repos)} repositories in CRUST-bench")
    
    print("\n🧪 Available Test Commands:")
    print("-" * 30)
    
    print("\n1️⃣ Quick Analysis (No API calls):")
    print("   uv run python -m migratex analyze CRUST-bench/datasets/CBench/CircularBuffer")
    
    print("\n2️⃣ Function Extraction + Test Generation:")
    print("   uv run python -m migratex test-extract CRUST-bench/datasets/CBench/CircularBuffer --generate")
    
    print("\n3️⃣ Test Multiple Repositories:")
    print("   uv run pytest tests/test_crust_bench_integration.py -v -s")
    
    print("\n4️⃣ Generate Full Report:")
    print("   uv run pytest tests/test_integration_summary_generator.py -v -s")
    
    print("\n📚 Recommended Test Repositories:")
    print("-" * 35)
    
    recommended_repos = [
        ("CircularBuffer", "Simple data structure (11 functions)"),
        ("Linear-Algebra-C", "Multi-file library (87 functions)"), 
        ("SimpleXML", "XML parser (24 functions)"),
        ("cJSON", "JSON library"),
        ("leftpad", "Simple string utility"),
    ]
    
    for repo, desc in recommended_repos:
        repo_path = crust_bench_path / repo
        status = "✅" if repo_path.exists() else "❌"
        print(f"   {status} {repo:<20} - {desc}")
    
    print("\n🎯 Quick Start:")
    print("-" * 15)
    print("Try this command to see MigrateX in action:")
    print()
    print("uv run python -m migratex test-extract CRUST-bench/datasets/CBench/CircularBuffer --generate --max-functions 2")
    print()
    print("This will:")
    print("• Parse the CircularBuffer C code")
    print("• Extract all functions")
    print("• Generate AI tests for 2 functions (to control costs)")
    print("• Show you the generated test code")
    
    print("\n💡 Pro Tips:")
    print("• Use --max-functions to control API costs")
    print("• Check generated tests in the terminal output")
    print("• Run integration tests to see full capabilities")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())