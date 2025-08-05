"""Generate comprehensive integration test summary with actual generated test examples."""

import os
from pathlib import Path
from typing import Dict, List
import pytest
from dotenv import load_dotenv

from migratex.analysis.language_parser import LanguageParser
from migratex.analysis.test_extractor import TestExtractor
from migratex.analysis.test_generator import TestGenerator
from migratex.directory_mapping.metadata_manager import MetadataManager

# Load environment variables
load_dotenv()

CRUST_BENCH_PATH = Path(__file__).parent.parent / "CRUST-bench" / "datasets" / "CBench"


class TestIntegrationSummary:
    """Generate comprehensive integration test summary report."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LanguageParser()
        self.test_extractor = TestExtractor()
        self.test_generator = TestGenerator()
        self.metadata_manager = MetadataManager()
    
    @pytest.mark.skipif(not os.getenv('GOOGLE_API_KEY'), reason="No API key available")
    def test_generate_comprehensive_summary_report(self):
        """Generate comprehensive summary of MigrateX integration test results."""
        
        print("\n" + "="*80)
        print("🚀 MigrateX CRUST-bench Integration Test Summary Report")
        print("="*80)
        
        # Test multiple repositories with detailed analysis
        repos_to_test = [
            ("CircularBuffer", "Data structure with memory management"),
            ("Linear-Algebra-C", "Multi-file mathematical library"),
            ("SimpleXML", "XML parser with vector operations")
        ]
        
        total_stats = {
            "repositories_tested": 0,
            "total_functions_extracted": 0,
            "total_tests_generated": 0,
            "total_api_calls": 0,
            "successful_generations": 0,
            "failed_generations": 0
        }
        
        detailed_results = []
        
        for repo_name, description in repos_to_test:
            print(f"\n📁 Testing Repository: {repo_name}")
            print(f"   Description: {description}")
            
            repo_path = CRUST_BENCH_PATH / repo_name
            if not repo_path.exists():
                print(f"   ❌ Repository not found at {repo_path}")
                continue
            
            # Parse repository
            source_files = [f for f in repo_path.rglob("*.c") if "test" not in f.name.lower()]
            all_functions = []
            
            for source_file in source_files:
                with open(source_file, 'r') as f:
                    content = f.read()
                
                modules = self.parser.extract_modules(content, "c", str(source_file))
                functions = [{"name": m.name, "content": m.source_code, "dependencies": m.dependencies, "language": "c", "file": str(source_file)} for m in modules]
                all_functions.extend(functions)
            
            print(f"   ✅ Extracted {len(all_functions)} functions from {len(source_files)} files")
            
            # Generate tests for first 2 functions (cost control)
            generated_tests = []
            generation_results = []
            
            for func in all_functions[:2]:
                print(f"   🤖 Generating test for {func['name']}...")
                result = self.test_generator.generate_test(func)
                
                if result:
                    generated_tests.append(result)
                    generation_results.append({
                        "function_name": func['name'],
                        "test_content": result['test_content'],
                        "success": True
                    })
                    total_stats["successful_generations"] += 1
                    print(f"      ✅ Generated successfully")
                else:
                    generation_results.append({
                        "function_name": func['name'],
                        "success": False
                    })
                    total_stats["failed_generations"] += 1
                    print(f"      ❌ Generation failed")
                
                total_stats["total_api_calls"] += 1
            
            # Store detailed results
            repo_result = {
                "name": repo_name,
                "description": description,
                "functions_extracted": len(all_functions),
                "tests_generated": len(generated_tests),
                "generation_results": generation_results,
                "function_names": [f["name"] for f in all_functions]
            }
            detailed_results.append(repo_result)
            
            # Update totals
            total_stats["repositories_tested"] += 1
            total_stats["total_functions_extracted"] += len(all_functions)
            total_stats["total_tests_generated"] += len(generated_tests)
        
        # Generate comprehensive report
        self._print_comprehensive_report(total_stats, detailed_results)
        
        # Show examples of generated tests
        self._print_generated_test_examples(detailed_results)
        
        return True
    
    def _print_comprehensive_report(self, stats: Dict, results: List[Dict]):
        """Print comprehensive integration test report."""
        print(f"\n" + "="*80)
        print("📊 OVERALL INTEGRATION TEST RESULTS")
        print("="*80)
        
        print(f"🔍 Testing Scope:")
        print(f"   • Repositories Tested: {stats['repositories_tested']}")
        print(f"   • Total Functions Extracted: {stats['total_functions_extracted']}")
        print(f"   • Average Functions per Repository: {stats['total_functions_extracted'] / max(stats['repositories_tested'], 1):.1f}")
        
        print(f"\n🤖 AI Test Generation Performance:")
        print(f"   • Total API Calls Made: {stats['total_api_calls']}")
        print(f"   • Successful Generations: {stats['successful_generations']}")
        print(f"   • Failed Generations: {stats['failed_generations']}")
        
        if stats['total_api_calls'] > 0:
            success_rate = (stats['successful_generations'] / stats['total_api_calls']) * 100
            print(f"   • Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 Detailed Repository Results:")
        for result in results:
            print(f"   📁 {result['name']}:")
            print(f"      • Functions Extracted: {result['functions_extracted']}")
            print(f"      • Tests Generated: {result['tests_generated']}")
            if result['functions_extracted'] > 0:
                coverage = (result['tests_generated'] / result['functions_extracted']) * 100
                print(f"      • Test Coverage: {coverage:.1f}%")
        
        print(f"\n✅ SUCCESS CRITERIA ASSESSMENT:")
        
        # Language Parser Success
        parser_success = stats['total_functions_extracted'] >= 50  # Should extract at least 50 functions total
        print(f"   🔍 Language Parser: {'✅ PASS' if parser_success else '❌ FAIL'}")
        print(f"      • Target: Extract ≥50 functions across repositories")
        print(f"      • Actual: {stats['total_functions_extracted']} functions extracted")
        
        # AI Generator Success
        generator_success = stats['successful_generations'] >= 3  # Should generate at least 3 tests
        success_rate = (stats['successful_generations'] / max(stats['total_api_calls'], 1)) * 100
        generator_rate_success = success_rate >= 80  # Should have ≥80% success rate
        
        print(f"   🤖 AI Test Generator: {'✅ PASS' if generator_success and generator_rate_success else '❌ FAIL'}")
        print(f"      • Target: Generate ≥3 tests with ≥80% success rate")
        print(f"      • Actual: {stats['successful_generations']} tests, {success_rate:.1f}% success rate")
        
        # Integration Success
        integration_success = parser_success and generator_success and generator_rate_success
        print(f"   🔗 Overall Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
        
        print("="*80)
    
    def _print_generated_test_examples(self, results: List[Dict]):
        """Print examples of generated tests."""
        print(f"\n" + "="*80)
        print("📝 GENERATED TEST EXAMPLES")
        print("="*80)
        
        example_count = 0
        for result in results:
            for gen_result in result['generation_results']:
                if gen_result['success'] and example_count < 2:  # Show first 2 successful examples
                    print(f"\n🔧 Function: {gen_result['function_name']} (from {result['name']})")
                    print("📋 Generated Test:")
                    print("-" * 40)
                    print(gen_result['test_content'])
                    print("-" * 40)
                    example_count += 1
        
        if example_count == 0:
            print("   ℹ️ No successful test generations to display")
        
        print("="*80)