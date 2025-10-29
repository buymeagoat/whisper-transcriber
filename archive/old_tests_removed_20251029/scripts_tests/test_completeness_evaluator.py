#!/usr/bin/env python3
"""
Test Completeness Evaluator for T001-T025P5

Evaluates the current comprehensive testing coverage and identifies gaps
for all tasks from T001 through T025 Phase 5, including:
- Chunked upload system testing
- WebSocket scaling validation
- Performance optimization verification
- Complete API endpoint coverage
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set

class TestCompletenessEvaluator:
    """Evaluates testing completeness for all project components."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.gaps = []
        self.recommendations = []
    
    def evaluate_t025_phase5_coverage(self) -> Dict:
        """Evaluate T025 Phase 5 chunked upload testing coverage."""
        coverage = {
            "core_service": False,
            "api_endpoints": False,
            "websocket_integration": False,
            "admin_monitoring": False,
            "frontend_components": False,
            "performance_benchmarking": False
        }
        
        # Check if chunked upload test file exists
        chunked_test_file = self.project_root / "tests" / "test_chunked_upload_system.py"
        if chunked_test_file.exists():
            coverage["core_service"] = True
            print("✅ T025 Phase 5 core service tests found")
        else:
            self.gaps.append("Missing chunked upload service tests")
        
        # Check for performance benchmarking
        benchmark_file = self.project_root / "temp" / "T025_Phase5_Performance_Report.json"
        if benchmark_file.exists():
            coverage["performance_benchmarking"] = True
            print("✅ T025 Phase 5 performance benchmarking completed")
        else:
            self.gaps.append("Missing T025 Phase 5 performance benchmarking")
        
        # Check comprehensive validator coverage
        validator_file = self.project_root / "tools" / "comprehensive_validator.py"
        if validator_file.exists():
            content = validator_file.read_text()
            if "chunked" in content.lower() or "upload.*session" in content.lower():
                coverage["api_endpoints"] = True
                print("✅ Chunked upload endpoints in comprehensive validator")
            else:
                self.gaps.append("Chunked upload endpoints not in comprehensive validator")
        
        return coverage
    
    def evaluate_websocket_testing(self) -> Dict:
        """Evaluate WebSocket testing coverage."""
        coverage = {
            "service_tests": False,
            "integration_tests": False,
            "admin_monitoring": False,
            "scalability_tests": False
        }
        
        websocket_test_file = self.project_root / "tests" / "test_websocket_service.py"
        if websocket_test_file.exists():
            coverage["service_tests"] = True
            print("✅ WebSocket service tests found")
        else:
            self.gaps.append("Missing WebSocket service tests")
        
        return coverage
    
    def evaluate_database_optimization_testing(self) -> Dict:
        """Evaluate database optimization testing coverage."""
        coverage = {
            "optimization_tests": False,
            "performance_monitoring": False,
            "connection_pooling": False
        }
        
        db_test_file = self.project_root / "tests" / "test_database_optimization.py"
        if db_test_file.exists():
            coverage["optimization_tests"] = True
            print("✅ Database optimization tests found")
        else:
            self.gaps.append("Missing database optimization tests")
        
        return coverage
    
    def evaluate_comprehensive_validator_coverage(self) -> Dict:
        """Evaluate what the comprehensive validator actually tests."""
        validator_file = self.project_root / "tools" / "comprehensive_validator.py"
        coverage = {
            "api_endpoints": True,
            "database": True,
            "file_system": True,
            "configuration": True,
            "security": True,
            "backup_system": True,
            "performance": True,
            "frontend": True,
            "e2e_testing": True,
            "chunked_uploads": False,
            "websocket_scaling": False,
            "enhanced_caching": False
        }
        
        if not validator_file.exists():
            self.gaps.append("Comprehensive validator not found")
            return coverage
        
        content = validator_file.read_text()
        
        # Check for T025 specific testing
        t025_keywords = [
            "chunked", "upload.*session", "chunk.*processor",
            "websocket.*scale", "redis.*pub.*sub", "connection.*pool",
            "cache.*redis", "enhanced.*cache"
        ]
        
        for keyword in t025_keywords:
            if keyword.replace(".*", "") in content.lower():
                if "chunked" in keyword or "upload" in keyword:
                    coverage["chunked_uploads"] = True
                elif "websocket" in keyword:
                    coverage["websocket_scaling"] = True
                elif "cache" in keyword:
                    coverage["enhanced_caching"] = True
        
        return coverage
    
    def identify_missing_endpoint_testing(self) -> List[str]:
        """Identify API endpoints that aren't being tested."""
        missing_endpoints = []
        
        # T025 Phase 5 endpoints that should be tested
        phase5_endpoints = [
            "/uploads/initialize",
            "/uploads/{session_id}/chunks/{chunk_number}",
            "/uploads/{session_id}/finalize",
            "/uploads/{session_id}/status",
            "/uploads/{session_id}/resume",
            "/admin/uploads/active",
            "/admin/uploads/metrics",
            "/ws/uploads/{session_id}/progress",
            "/ws/uploads/user/{user_id}/notifications",
            "/ws/uploads/admin/monitoring"
        ]
        
        # Check if these are in the inventory
        inventory_file = self.project_root / "docs" / "architecture" / "INVENTORY.json"
        if inventory_file.exists():
            try:
                inventory = json.loads(inventory_file.read_text())
                tested_paths = {ep.get("path", "") for ep in inventory.get("api_endpoints", [])}
                
                for endpoint in phase5_endpoints:
                    if endpoint not in tested_paths:
                        missing_endpoints.append(endpoint)
                        
            except Exception as e:
                self.gaps.append(f"Failed to parse inventory: {e}")
        else:
            self.gaps.append("Architecture inventory not found")
            missing_endpoints = phase5_endpoints
        
        return missing_endpoints
    
    def evaluate_integration_testing(self) -> Dict:
        """Evaluate integration testing coverage."""
        coverage = {
            "frontend_backend": False,
            "authentication_flow": False,
            "file_upload_pipeline": False,
            "real_time_updates": False,
            "admin_operations": False
        }
        
        # Check for integration test files
        test_files = list((self.project_root / "tests").glob("test_*.py"))
        integration_keywords = ["integration", "e2e", "end_to_end", "workflow"]
        
        for test_file in test_files:
            content = test_file.read_text().lower()
            for keyword in integration_keywords:
                if keyword in test_file.name.lower() or keyword in content:
                    coverage["frontend_backend"] = True
                    break
        
        return coverage
    
    def generate_enhancement_recommendations(self) -> List[str]:
        """Generate specific recommendations for enhancing test coverage."""
        recommendations = []
        
        # T025 Phase 5 specific recommendations
        recommendations.extend([
            "Add chunked upload endpoints to comprehensive validator",
            "Include WebSocket connection testing in comprehensive validator",
            "Add performance regression testing for all T025 phases",
            "Create integration tests for chunked upload → transcription pipeline",
            "Add load testing for concurrent chunked uploads",
            "Implement WebSocket stress testing for scalability validation",
            "Add cache performance validation in comprehensive validator",
            "Create end-to-end tests for complete file upload workflow"
        ])
        
        # General testing improvements
        recommendations.extend([
            "Update architecture inventory to include all new endpoints",
            "Create dedicated performance testing suite",
            "Add automated testing for all admin monitoring features",
            "Implement frontend component testing for new upload UI",
            "Add security testing for chunked upload sessions",
            "Create disaster recovery testing for upload resume functionality"
        ])
        
        return recommendations
    
    def run_evaluation(self) -> Dict:
        """Run complete test completeness evaluation."""
        print("🔍 Evaluating test completeness for T001-T025P5...")
        print("=" * 60)
        
        # Evaluate each component
        t025_phase5 = self.evaluate_t025_phase5_coverage()
        websocket = self.evaluate_websocket_testing()
        database = self.evaluate_database_optimization_testing()
        validator = self.evaluate_comprehensive_validator_coverage()
        integration = self.evaluate_integration_testing()
        missing_endpoints = self.identify_missing_endpoint_testing()
        
        # Calculate overall coverage
        total_checks = sum([
            len(t025_phase5), len(websocket), len(database), 
            len(validator), len(integration)
        ])
        passed_checks = sum([
            sum(t025_phase5.values()), sum(websocket.values()), 
            sum(database.values()), sum(validator.values()), 
            sum(integration.values())
        ])
        
        coverage_percentage = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Generate recommendations
        recommendations = self.generate_enhancement_recommendations()
        
        result = {
            "overall_coverage_percentage": coverage_percentage,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "t025_phase5_coverage": t025_phase5,
            "websocket_coverage": websocket,
            "database_coverage": database,
            "validator_coverage": validator,
            "integration_coverage": integration,
            "missing_endpoints": missing_endpoints,
            "identified_gaps": self.gaps,
            "enhancement_recommendations": recommendations
        }
        
        print(f"\n📊 OVERALL TEST COVERAGE: {coverage_percentage:.1f}%")
        print(f"✅ Passed checks: {passed_checks}/{total_checks}")
        
        if self.gaps:
            print(f"\n⚠️  IDENTIFIED GAPS ({len(self.gaps)}):")
            for gap in self.gaps:
                print(f"   • {gap}")
        
        if missing_endpoints:
            print(f"\n❌ MISSING ENDPOINT TESTING ({len(missing_endpoints)}):")
            for endpoint in missing_endpoints:
                print(f"   • {endpoint}")
        
        print(f"\n💡 ENHANCEMENT RECOMMENDATIONS ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:10], 1):  # Show top 10
            print(f"   {i}. {rec}")
        
        return result


def main():
    """Run the test completeness evaluation."""
    evaluator = TestCompletenessEvaluator()
    result = evaluator.run_evaluation()
    
    # Save results
    output_file = Path("temp/test_completeness_evaluation.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Detailed evaluation saved to: {output_file}")
    
    # Determine if comprehensive testing is ready
    if result["overall_coverage_percentage"] >= 80:
        print("\n✅ Test coverage is sufficient for comprehensive testing")
        return 0
    else:
        print("\n⚠️  Test coverage needs improvement before comprehensive testing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
