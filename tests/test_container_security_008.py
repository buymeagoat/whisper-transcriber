#!/usr/bin/env python3

"""
Comprehensive Container Security Tests for Whisper Transcriber
Tests container security configurations, hardening, and compliance
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest


class ContainerSecurityTester:
    """Tests for container security configurations"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.compose_file = self.project_root / "docker-compose.yml"
        self.dockerfile = self.project_root / "Dockerfile"
        
    def load_compose_config(self) -> Dict:
        """Load and parse docker-compose.yml"""
        with open(self.compose_file) as f:
            return yaml.safe_load(f)
    
    def run_docker_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run docker command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)


class TestDockerfileSecurityHardening:
    """Test Dockerfile security configurations"""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is readable"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile not found"
        assert dockerfile.is_file(), "Dockerfile is not a file"
        
    def test_non_root_user(self):
        """Test that Dockerfile specifies non-root user"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        
        # Should have USER directive
        assert "USER " in content, "Dockerfile must specify USER directive"
        
        # Should not run as root
        assert "USER root" not in content, "Should not explicitly run as root"
        assert "USER 0" not in content, "Should not run as UID 0"
        
    def test_secure_base_image(self):
        """Test that base image uses secure versioning"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        
        # Find FROM statements
        from_lines = [line for line in content.split('\n') if line.strip().startswith('FROM')]
        assert len(from_lines) > 0, "No FROM statements found"
        
        for line in from_lines:
            # Should not use 'latest' tag
            assert ":latest" not in line, f"FROM statement should not use 'latest' tag: {line}"
            
            # Should use specific version or SHA256
            assert (":" in line and line.count(":") >= 1) or "@sha256:" in line, \
                f"FROM statement should specify version or SHA256: {line}"
                
    def test_no_sensitive_files(self):
        """Test that Dockerfile doesn't copy sensitive files"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        
        sensitive_patterns = [".env", ".key", ".pem", "id_rsa", "password"]
        copy_lines = [line for line in content.split('\n') 
                     if line.strip().startswith(('COPY', 'ADD'))]
        
        for line in copy_lines:
            for pattern in sensitive_patterns:
                assert pattern not in line.lower(), \
                    f"Dockerfile should not copy sensitive files: {line}"
                    
    def test_security_labels(self):
        """Test that Dockerfile includes security metadata"""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()
        
        # Should have some security-related labels
        assert "LABEL" in content, "Dockerfile should include metadata labels"


class TestDockerComposeSecurityContext:
    """Test docker-compose.yml security contexts"""
    
    @pytest.fixture
    def compose_config(self):
        """Load docker-compose configuration"""
        tester = ContainerSecurityTester(Path(__file__).parent.parent)
        return tester.load_compose_config()
        
    def test_compose_file_exists(self):
        """Test that docker-compose.yml exists"""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml not found"
        
    def test_no_privileged_containers(self, compose_config):
        """Test that no containers run in privileged mode"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            privileged = service_config.get('privileged', False)
            assert not privileged, f"Service {service_name} should not run in privileged mode"
            
    def test_security_options_configured(self, compose_config):
        """Test that security options are configured for services"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            # Skip nginx in non-production profile
            if service_name == 'nginx':
                continue
                
            security_opt = service_config.get('security_opt', [])
            assert len(security_opt) > 0, f"Service {service_name} should have security_opt configured"
            
            # Should have no-new-privileges
            assert any('no-new-privileges:true' in opt for opt in security_opt), \
                f"Service {service_name} should have no-new-privileges security option"
                
    def test_capability_dropping(self, compose_config):
        """Test that capabilities are properly dropped"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            if service_name == 'nginx':
                continue
                
            cap_drop = service_config.get('cap_drop', [])
            assert 'ALL' in cap_drop, f"Service {service_name} should drop ALL capabilities"
            
            # Should have minimal cap_add
            cap_add = service_config.get('cap_add', [])
            dangerous_caps = ['SYS_ADMIN', 'NET_ADMIN', 'SYS_PTRACE', 'DAC_READ_SEARCH']
            
            for cap in cap_add:
                assert cap not in dangerous_caps, \
                    f"Service {service_name} should not add dangerous capability: {cap}"
                    
    def test_non_root_users(self, compose_config):
        """Test that services run as non-root users"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            if service_name == 'nginx':
                continue  # nginx might need special handling
                
            user = service_config.get('user')
            if user:
                # Should not be root
                assert user not in ['root', '0', '0:0'], \
                    f"Service {service_name} should not run as root user"
                    
    def test_read_only_filesystems(self, compose_config):
        """Test that containers use read-only filesystems where possible"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            read_only = service_config.get('read_only', False)
            
            # Should have read-only filesystem
            assert read_only, f"Service {service_name} should use read-only filesystem"
            
            # Should have appropriate tmpfs mounts
            tmpfs = service_config.get('tmpfs', [])
            assert len(tmpfs) > 0, f"Service {service_name} should have tmpfs mounts for writable areas"
            
    def test_resource_limits(self, compose_config):
        """Test that resource limits are configured"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            deploy = service_config.get('deploy', {})
            resources = deploy.get('resources', {})
            limits = resources.get('limits', {})
            
            assert 'memory' in limits, f"Service {service_name} should have memory limits"
            assert 'cpus' in limits, f"Service {service_name} should have CPU limits"
            
    def test_network_security(self, compose_config):
        """Test network security configuration"""
        networks = compose_config.get('networks', {})
        services = compose_config.get('services', {})
        
        # Should have custom networks defined
        assert len(networks) > 0, "Should have custom networks defined"
        
        # Should have network isolation
        backend_network = networks.get('backend', {})
        assert backend_network.get('internal', False), "Backend network should be internal"
        
        # Services should be on appropriate networks
        for service_name, service_config in services.items():
            service_networks = service_config.get('networks', [])
            
            if service_name in ['redis', 'worker']:
                assert 'backend' in service_networks, \
                    f"Service {service_name} should be on backend network"
                assert 'frontend' not in service_networks, \
                    f"Service {service_name} should not be on frontend network"
                    
    def test_volume_security(self, compose_config):
        """Test volume security configuration"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            volumes = service_config.get('volumes', [])
            
            for volume in volumes:
                if isinstance(volume, str):
                    # Check for read-only mounts where appropriate
                    if any(keyword in volume for keyword in ['models', 'config']):
                        assert ':ro' in volume, \
                            f"Service {service_name} should mount read-only volumes as :ro"
                            
    def test_environment_security(self, compose_config):
        """Test environment variable security"""
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            environment = service_config.get('environment', [])
            
            if isinstance(environment, list):
                env_vars = environment
            elif isinstance(environment, dict):
                env_vars = [f"{k}={v}" for k, v in environment.items()]
            else:
                continue
                
            for env_var in env_vars:
                # Should not have hardcoded secrets
                sensitive_keys = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']
                
                if any(key in env_var.upper() for key in sensitive_keys):
                    # Should use variable substitution, not hardcoded values
                    assert '${' in env_var or env_var.endswith(':-default_password}'), \
                        f"Service {service_name} should not have hardcoded secrets: {env_var}"


class TestRuntimeContainerSecurity:
    """Test running container security (requires containers to be running)"""
    
    @pytest.fixture(scope="class")
    def container_tester(self):
        """Initialize container security tester"""
        return ContainerSecurityTester(Path(__file__).parent.parent)
        
    def test_container_user_id(self, container_tester):
        """Test that running containers use non-root UIDs"""
        # Get running whisper containers
        exit_code, stdout, stderr = container_tester.run_docker_command([
            'docker', 'ps', '--filter', 'name=whisper', '--format', '{{.Names}}'
        ])
        
        if exit_code != 0 or not stdout.strip():
            pytest.skip("No running whisper containers found")
            
        container_names = stdout.strip().split('\n')
        
        for container_name in container_names:
            # Check user ID
            exit_code, stdout, stderr = container_tester.run_docker_command([
                'docker', 'exec', container_name, 'id', '-u'
            ])
            
            if exit_code == 0:
                uid = int(stdout.strip())
                assert uid != 0, f"Container {container_name} should not run as root (UID 0)"
                assert uid >= 1000, f"Container {container_name} should use high UID (>=1000)"
                
    def test_container_capabilities(self, container_tester):
        """Test that running containers have minimal capabilities"""
        exit_code, stdout, stderr = container_tester.run_docker_command([
            'docker', 'ps', '--filter', 'name=whisper', '--format', '{{.Names}}'
        ])
        
        if exit_code != 0 or not stdout.strip():
            pytest.skip("No running whisper containers found")
            
        container_names = stdout.strip().split('\n')
        
        for container_name in container_names:
            # Check effective capabilities
            exit_code, stdout, stderr = container_tester.run_docker_command([
                'docker', 'exec', container_name, 'cat', '/proc/1/status'
            ])
            
            if exit_code == 0:
                # Look for CapEff line (effective capabilities)
                for line in stdout.split('\n'):
                    if line.startswith('CapEff:'):
                        cap_value = line.split()[1]
                        # Should have minimal capabilities (not all bits set)
                        assert cap_value != 'ffffffffffffffff', \
                            f"Container {container_name} has too many capabilities"
                            
    def test_container_filesystem_readonly(self, container_tester):
        """Test that containers use read-only filesystem"""
        exit_code, stdout, stderr = container_tester.run_docker_command([
            'docker', 'ps', '--filter', 'name=whisper', '--format', '{{.Names}}'
        ])
        
        if exit_code != 0 or not stdout.strip():
            pytest.skip("No running whisper containers found")
            
        container_names = stdout.strip().split('\n')
        
        for container_name in container_names:
            # Try to write to root filesystem
            exit_code, stdout, stderr = container_tester.run_docker_command([
                'docker', 'exec', container_name, 'touch', '/test_write'
            ])
            
            # Should fail (read-only filesystem)
            assert exit_code != 0, \
                f"Container {container_name} filesystem should be read-only"


class TestContainerNetworkSecurity:
    """Test container network security"""
    
    def test_network_isolation(self):
        """Test that networks are properly isolated"""
        tester = ContainerSecurityTester(Path(__file__).parent.parent)
        compose_config = tester.load_compose_config()
        
        networks = compose_config.get('networks', {})
        
        # Backend network should be internal
        backend = networks.get('backend', {})
        assert backend.get('internal', False), "Backend network should be internal"
        
        # Networks should have custom subnets
        for network_name, network_config in networks.items():
            ipam = network_config.get('ipam', {})
            config = ipam.get('config', [])
            
            if config:
                subnet = config[0].get('subnet')
                assert subnet, f"Network {network_name} should have defined subnet"
                
    def test_port_exposure_minimal(self):
        """Test that only necessary ports are exposed"""
        tester = ContainerSecurityTester(Path(__file__).parent.parent)
        compose_config = tester.load_compose_config()
        
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            ports = service_config.get('ports', [])
            
            # Backend services should not expose ports directly
            if service_name in ['redis', 'worker']:
                assert len(ports) == 0, f"Service {service_name} should not expose ports"
                
            # App should bind to localhost only
            if service_name == 'app':
                for port in ports:
                    if isinstance(port, str) and ':' in port:
                        bind_address = port.split(':')[0]
                        assert bind_address in ['127.0.0.1', 'localhost'], \
                            f"Service {service_name} should bind to localhost only"


def main():
    """Run container security tests"""
    print("Running Container Security Tests for Whisper Transcriber")
    print("=" * 60)
    
    # Run tests
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '--color=yes',
        '-x'  # Stop on first failure for security tests
    ])
    
    if exit_code == 0:
        print("\n✅ All container security tests passed!")
    else:
        print("\n❌ Container security tests failed!")
        
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
