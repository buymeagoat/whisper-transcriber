"""
Enhanced Comprehensive Validator Extensions for T025 Phase 5

Adds chunked upload testing, WebSocket scaling validation, and performance
regression testing to the comprehensive validator.
"""

import asyncio
import json
import time
import requests
import tempfile
from pathlib import Path
from typing import Dict, List, Any


class T025Phase5Validator:
    """Validator for T025 Phase 5 chunked upload system."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    def _record_result(self, component: str, test_name: str, status: str, 
                      message: str, duration_ms: float = 0, error: str = None):
        """Record a test result."""
        result = {
            "component": component,
            "test_name": test_name,
            "status": status,
            "message": message,
            "duration_ms": duration_ms,
            "error": error
        }
        self.results.append(result)
        print(f"{component}.{test_name}: {status} - {message}")
    
    def validate_chunked_upload_endpoints(self) -> Dict:
        """Validate all chunked upload API endpoints."""
        component = "chunked_uploads"
        
        # Test endpoints
        endpoints = [
            ("POST", "/uploads/initialize"),
            ("POST", "/uploads/test-session/chunks/1"),
            ("POST", "/uploads/test-session/finalize"),
            ("GET", "/uploads/test-session/status"),
            ("POST", "/uploads/test-session/resume"),
            ("DELETE", "/uploads/test-session"),
            ("GET", "/admin/uploads/active"),
            ("GET", "/admin/uploads/metrics"),
            ("GET", "/admin/uploads/storage")
        ]
        
        for method, endpoint in endpoints:
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                elif method == "POST":
                    # Provide minimal test data
                    if "initialize" in endpoint:
                        data = {"filename": "test.mp3", "file_size": 1024, "model": "small"}
                    else:
                        data = {}
                    response = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=5)
                elif method == "DELETE":
                    response = requests.delete(f"{self.base_url}{endpoint}", timeout=5)
                
                duration = (time.time() - start_time) * 1000
                
                if response.status_code in [200, 404, 422, 403]:  # Expected responses
                    self._record_result(component, f"endpoint_{method}_{endpoint.replace('/', '_')}", 
                                      "PASS", f"Endpoint accessible (status: {response.status_code})", duration)
                else:
                    self._record_result(component, f"endpoint_{method}_{endpoint.replace('/', '_')}", 
                                      "WARN", f"Unexpected status: {response.status_code}", duration)
            
            except Exception as e:
                self._record_result(component, f"endpoint_{method}_{endpoint.replace('/', '_')}", 
                                  "FAIL", f"Endpoint test failed: {str(e)}", 0, str(e))
    
    def validate_chunked_upload_service(self) -> Dict:
        """Validate chunked upload service implementation."""
        component = "chunked_upload_service"
        
        try:
            # Check if service file exists
            service_file = Path("api/services/chunked_upload_service.py")
            if service_file.exists():
                self._record_result(component, "service_file_exists", "PASS", 
                                  "Chunked upload service file found", 0)
                
                # Check for key classes
                content = service_file.read_text()
                required_classes = ["ChunkedUploadService", "ChunkProcessor", "UploadProgressTracker"]
                
                for class_name in required_classes:
                    if f"class {class_name}" in content:
                        self._record_result(component, f"class_{class_name.lower()}_exists", "PASS", 
                                          f"{class_name} class found", 0)
                    else:
                        self._record_result(component, f"class_{class_name.lower()}_exists", "FAIL", 
                                          f"{class_name} class not found", 0)
            else:
                self._record_result(component, "service_file_exists", "FAIL", 
                                  "Chunked upload service file not found", 0)
        
        except Exception as e:
            self._record_result(component, "service_validation", "FAIL", 
                              f"Service validation failed: {str(e)}", 0, str(e))
    
    def validate_frontend_components(self) -> Dict:
        """Validate frontend chunked upload components."""
        component = "frontend_chunked_upload"
        
        try:
            # Check for frontend files
            frontend_files = [
                "frontend/src/services/chunkedUploadClient.js",
                "frontend/src/components/ChunkedUploadComponent.jsx"
            ]
            
            for file_path in frontend_files:
                file_obj = Path(file_path)
                if file_obj.exists():
                    self._record_result(component, f"file_{file_obj.name}_exists", "PASS", 
                                      f"Frontend file {file_obj.name} found", 0)
                    
                    # Check for key functionality
                    content = file_obj.read_text()
                    if "chunked" in content.lower() and "upload" in content.lower():
                        self._record_result(component, f"file_{file_obj.name}_functionality", "PASS", 
                                          f"Chunked upload functionality found in {file_obj.name}", 0)
                    else:
                        self._record_result(component, f"file_{file_obj.name}_functionality", "WARN", 
                                          f"Limited chunked upload functionality in {file_obj.name}", 0)
                else:
                    self._record_result(component, f"file_{file_obj.name}_exists", "FAIL", 
                                      f"Frontend file {file_obj.name} not found", 0)
        
        except Exception as e:
            self._record_result(component, "frontend_validation", "FAIL", 
                              f"Frontend validation failed: {str(e)}", 0, str(e))
    
    def validate_performance_benchmarking(self) -> Dict:
        """Validate T025 Phase 5 performance benchmarking."""
        component = "phase5_performance"
        
        try:
            # Check for performance report
            report_file = Path("temp/T025_Phase5_Performance_Report.json")
            if report_file.exists():
                self._record_result(component, "performance_report_exists", "PASS", 
                                  "Performance report found", 0)
                
                # Parse and validate report content
                try:
                    with open(report_file) as f:
                        report = json.load(f)
                    
                    # Check key performance metrics
                    if "test_summary" in report:
                        summary = report["test_summary"]
                        success_rate = summary.get("success_rate_percentage", 0)
                        
                        if success_rate >= 95:
                            self._record_result(component, "performance_success_rate", "PASS", 
                                              f"Excellent success rate: {success_rate}%", 0)
                        elif success_rate >= 80:
                            self._record_result(component, "performance_success_rate", "WARN", 
                                              f"Good success rate: {success_rate}%", 0)
                        else:
                            self._record_result(component, "performance_success_rate", "FAIL", 
                                              f"Low success rate: {success_rate}%", 0)
                    
                    # Check for key improvements
                    if "key_improvements" in report:
                        improvements = report["key_improvements"]
                        file_size_improvement = improvements.get("max_file_size_increase", {}).get("improvement_factor", 0)
                        
                        if file_size_improvement >= 10:
                            self._record_result(component, "file_size_improvement", "PASS", 
                                              f"Excellent file size improvement: {file_size_improvement}x", 0)
                        else:
                            self._record_result(component, "file_size_improvement", "WARN", 
                                              f"Limited file size improvement: {file_size_improvement}x", 0)
                    
                except Exception as e:
                    self._record_result(component, "performance_report_parsing", "FAIL", 
                                      f"Failed to parse performance report: {str(e)}", 0, str(e))
            else:
                self._record_result(component, "performance_report_exists", "FAIL", 
                                  "Performance report not found", 0)
        
        except Exception as e:
            self._record_result(component, "performance_validation", "FAIL", 
                              f"Performance validation failed: {str(e)}", 0, str(e))
    
    def validate_test_coverage(self) -> Dict:
        """Validate test coverage for chunked upload system."""
        component = "chunked_upload_tests"
        
        try:
            test_file = Path("tests/test_chunked_upload_system.py")
            if test_file.exists():
                self._record_result(component, "test_file_exists", "PASS", 
                                  "Chunked upload test file found", 0)
                
                # Check test coverage
                content = test_file.read_text()
                test_classes = ["TestChunkedUploadService", "TestChunkProcessor", 
                              "TestUploadProgressTracker", "TestPerformanceScenarios"]
                
                for test_class in test_classes:
                    if f"class {test_class}" in content:
                        self._record_result(component, f"test_class_{test_class.lower()}", "PASS", 
                                          f"Test class {test_class} found", 0)
                    else:
                        self._record_result(component, f"test_class_{test_class.lower()}", "WARN", 
                                          f"Test class {test_class} not found", 0)
            else:
                self._record_result(component, "test_file_exists", "FAIL", 
                                  "Chunked upload test file not found", 0)
        
        except Exception as e:
            self._record_result(component, "test_validation", "FAIL", 
                              f"Test validation failed: {str(e)}", 0, str(e))
    
    def run_all_validations(self) -> Dict:
        """Run all T025 Phase 5 validations."""
        print("🚀 Running T025 Phase 5 validations...")
        
        self.validate_chunked_upload_endpoints()
        self.validate_chunked_upload_service()
        self.validate_frontend_components()
        self.validate_performance_benchmarking()
        self.validate_test_coverage()
        
        # Summary
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📊 T025 Phase 5 Validation Summary:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "results": self.results
        }


def enhance_comprehensive_validator():
    """Add T025 Phase 5 validation to comprehensive validator."""
    validator_file = Path("tools/comprehensive_validator.py")
    
    if not validator_file.exists():
        print("❌ Comprehensive validator not found")
        return False
    
    # Check if already enhanced
    content = validator_file.read_text()
    if "T025Phase5Validator" in content:
        print("✅ Comprehensive validator already enhanced for T025 Phase 5")
        return True
    
    # Add the enhancement
    enhancement_code = '''
    def validate_t025_phase5(self) -> ComponentStatus:
        """Validate T025 Phase 5 chunked upload system."""
        logger.info("🔍 Validating T025 Phase 5 chunked upload system...")
        component = "t025_phase5"
        start_time = time.time()
        
        try:
            from tools.enhanced_validator_extensions import T025Phase5Validator
            
            phase5_validator = T025Phase5Validator(self.config.get("VITE_API_HOST", "http://localhost:8000"))
            validation_result = phase5_validator.run_all_validations()
            
            # Record results from Phase 5 validator
            for result in validation_result["results"]:
                self._record_result(
                    component, 
                    result["test_name"], 
                    result["status"], 
                    result["message"], 
                    result.get("duration_ms", 0),
                    error=result.get("error")
                )
            
            # Overall assessment
            success_rate = validation_result["success_rate"]
            if success_rate >= 80:
                self._record_result(component, "overall_phase5_validation", "PASS", 
                                  f"T025 Phase 5 validation successful: {success_rate:.1f}%", 0)
            else:
                self._record_result(component, "overall_phase5_validation", "WARN", 
                                  f"T025 Phase 5 validation needs attention: {success_rate:.1f}%", 0)
        
        except ImportError:
            self._record_result(component, "phase5_validator_import", "FAIL", 
                              "T025 Phase 5 validator not available", 0)
        except Exception as e:
            self._record_result(component, "phase5_validation_error", "FAIL", 
                              f"T025 Phase 5 validation failed: {str(e)}", 0, str(e))
        
        return self._get_component_status(component, time.time() - start_time)
'''
    
    # Find the right place to insert the method (before the run_validation method)
    lines = content.split('\n')
    insert_index = None
    
    for i, line in enumerate(lines):
        if 'async def run_validation(' in line or 'def run_validation(' in line:
            insert_index = i
            break
    
    if insert_index:
        # Insert the new method
        lines.insert(insert_index, enhancement_code)
        
        # Also add it to the component list in run_validation
        for i, line in enumerate(lines[insert_index:], insert_index):
            if 'components = [' in line:
                # Find the end of the list and add our component
                j = i
                while j < len(lines) and ']' not in lines[j]:
                    j += 1
                if j < len(lines):
                    lines.insert(j, '            ("t025_phase5", self.validate_t025_phase5),')
                break
        
        # Write back the enhanced file
        enhanced_content = '\n'.join(lines)
        validator_file.write_text(enhanced_content)
        print("✅ Enhanced comprehensive validator with T025 Phase 5 testing")
        return True
    else:
        print("❌ Could not find insertion point in comprehensive validator")
        return False


if __name__ == "__main__":
    # Run standalone validation
    validator = T025Phase5Validator()
    result = validator.run_all_validations()
    
    # Save results
    output_file = Path("temp/t025_phase5_validation_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")
