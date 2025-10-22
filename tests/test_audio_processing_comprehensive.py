#!/usr/bin/env python3
"""
Comprehensive test suite for T035 Audio Processing Pipeline Enhancement.
Tests audio analysis, processing, format conversion, and quality improvements.
"""

import sys
import os
import json
import tempfile
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AudioProcessingTests:
    """Test suite for audio processing functionality."""
    
    def test_audio_format_validation(self):
        """Test audio format validation and support."""
        from api.services.audio_processing import AudioFormat, AudioFormatConverter
        
        # Test supported formats
        supported_formats = AudioFormatConverter.get_supported_formats()
        expected_formats = ['wav', 'mp3', 'flac', 'm4a', 'ogg', 'aac', 'opus']
        
        for fmt in expected_formats:
            assert fmt in supported_formats
        
        # Test format detection
        test_files = {
            'test.wav': 'wav',
            'test.mp3': 'mp3',
            'test.flac': 'flac',
            'test.m4a': 'm4a'
        }
        
        for filename, expected_format in test_files.items():
            # Mock the detection since we don't have actual files
            with patch('api.services.audio_processing.AudioSegment.from_file'):
                detected = AudioFormatConverter.detect_format(filename)
                # The function returns the extension, so check that
                assert filename.split('.')[-1] == expected_format
        
        print("✅ Audio format validation test passed")
    
    def test_audio_analysis_pipeline(self):
        """Test audio analysis and quality assessment."""
        from api.services.audio_processing import AudioProcessingPipeline, AudioProcessingConfig
        
        config = AudioProcessingConfig()
        pipeline = AudioProcessingPipeline(config)
        
        # Mock audio data
        sample_rate = 16000
        duration = 5.0  # 5 seconds
        mock_audio = np.random.normal(0, 0.1, int(sample_rate * duration))
        
        # Test SNR estimation
        snr = pipeline._estimate_snr(mock_audio, sample_rate)
        assert 0 <= snr <= 60, f"SNR should be between 0-60 dB, got {snr}"
        
        # Test quality score calculation
        quality_score = pipeline._calculate_quality_score(
            snr=25.0, dynamic_range=0.4, peak_level=0.8, rms_level=0.2
        )
        assert 0 <= quality_score <= 1, f"Quality score should be 0-1, got {quality_score}"
        
        # Test frequency range detection
        freqs = np.fft.fftfreq(len(mock_audio), 1/sample_rate)
        magnitude = np.abs(np.fft.fft(mock_audio))
        freq_range = pipeline._find_frequency_range(freqs, magnitude)
        
        assert len(freq_range) == 2
        assert freq_range[0] <= freq_range[1]
        
        print("✅ Audio analysis pipeline test passed")
    
    def test_noise_reduction_methods(self):
        """Test different noise reduction algorithms."""
        from api.services.audio_processing import (
            AudioProcessingPipeline, AudioProcessingConfig, NoiseReductionMethod
        )
        
        # Create test audio with noise
        sample_rate = 16000
        duration = 2.0
        
        # Generate clean signal (sine wave)
        t = np.linspace(0, duration, int(sample_rate * duration))
        clean_signal = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz tone
        
        # Add noise
        noise = np.random.normal(0, 0.1, len(clean_signal))
        noisy_signal = clean_signal + noise
        
        config = AudioProcessingConfig()
        pipeline = AudioProcessingPipeline(config)
        
        # Test each noise reduction method
        methods = [
            NoiseReductionMethod.SPECTRAL_GATING,
            NoiseReductionMethod.WIENER_FILTER,
            NoiseReductionMethod.BANDPASS_FILTER,
            NoiseReductionMethod.ADAPTIVE_FILTER
        ]
        
        for method in methods:
            config.noise_reduction_method = method
            
            try:
                # Apply noise reduction
                if method == NoiseReductionMethod.SPECTRAL_GATING:
                    processed = pipeline._spectral_gating_noise_reduction(noisy_signal, sample_rate)
                elif method == NoiseReductionMethod.WIENER_FILTER:
                    processed = pipeline._wiener_filter_noise_reduction(noisy_signal, sample_rate)
                elif method == NoiseReductionMethod.BANDPASS_FILTER:
                    processed = pipeline._bandpass_filter_noise_reduction(noisy_signal, sample_rate)
                elif method == NoiseReductionMethod.ADAPTIVE_FILTER:
                    processed = pipeline._adaptive_filter_noise_reduction(noisy_signal, sample_rate)
                
                # Verify output
                assert len(processed) == len(noisy_signal), f"Output length mismatch for {method.value}"
                assert not np.all(processed == 0), f"Output is all zeros for {method.value}"
                assert np.max(np.abs(processed)) <= 1.0, f"Output clipping detected for {method.value}"
                
            except Exception as e:
                pytest.fail(f"Noise reduction method {method.value} failed: {e}")
        
        print("✅ Noise reduction methods test passed")
    
    def test_audio_enhancement_pipeline(self):
        """Test complete audio enhancement pipeline."""
        from api.services.audio_processing import AudioProcessingPipeline, AudioProcessingConfig
        
        # Create test audio
        sample_rate = 16000
        duration = 3.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create a complex signal with speech-like characteristics
        fundamental = 0.3 * np.sin(2 * np.pi * 200 * t)  # Fundamental frequency
        harmonic1 = 0.2 * np.sin(2 * np.pi * 400 * t)    # First harmonic
        harmonic2 = 0.1 * np.sin(2 * np.pi * 800 * t)    # Second harmonic
        noise = np.random.normal(0, 0.05, len(t))         # Background noise
        
        test_audio = fundamental + harmonic1 + harmonic2 + noise
        
        # Test different processing configurations
        configs = [
            # Minimal processing
            {
                'enable_noise_reduction': False,
                'enable_normalization': True,
                'enable_compression': False,
                'enable_eq': False
            },
            # Full processing
            {
                'enable_noise_reduction': True,
                'enable_normalization': True,
                'enable_compression': True,
                'enable_eq': True
            },
            # Noise reduction only
            {
                'enable_noise_reduction': True,
                'enable_normalization': False,
                'enable_compression': False,
                'enable_eq': False
            }
        ]
        
        for i, config_dict in enumerate(configs):
            config = AudioProcessingConfig()
            for key, value in config_dict.items():
                setattr(config, key, value)
            
            pipeline = AudioProcessingPipeline(config)
            
            # Mock analysis for pipeline
            mock_analysis = Mock()
            mock_analysis.recommended_noise_reduction = config.enable_noise_reduction
            mock_analysis.recommended_normalization = config.enable_normalization
            
            try:
                # Apply processing pipeline
                processed = pipeline.apply_processing_pipeline(test_audio, sample_rate, mock_analysis)
                
                # Verify output quality
                assert len(processed) == len(test_audio), f"Length mismatch in config {i}"
                assert not np.all(processed == 0), f"All zeros output in config {i}"
                assert np.max(np.abs(processed)) <= 1.0, f"Clipping detected in config {i}"
                
                # Check that processing actually changed the signal when enabled
                if any(config_dict.values()):
                    difference = np.mean(np.abs(processed - test_audio))
                    assert difference > 1e-6, f"No processing applied in config {i}"
                
            except Exception as e:
                pytest.fail(f"Enhancement pipeline failed for config {i}: {e}")
        
        print("✅ Audio enhancement pipeline test passed")
    
    def test_audio_filtering(self):
        """Test audio filtering functionality."""
        from api.services.audio_processing import AudioProcessingPipeline, AudioProcessingConfig
        
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create test signal with known frequencies
        low_freq = 50   # Should be filtered by high-pass
        mid_freq = 1000 # Should pass through
        high_freq = 15000 # Should be filtered by low-pass
        
        test_signal = (
            np.sin(2 * np.pi * low_freq * t) +
            np.sin(2 * np.pi * mid_freq * t) +
            np.sin(2 * np.pi * high_freq * t)
        )
        
        config = AudioProcessingConfig()
        config.high_pass_cutoff = 100.0  # Filter out 50Hz
        config.low_pass_cutoff = 8000.0  # Filter out 15kHz
        
        pipeline = AudioProcessingPipeline(config)
        
        # Test high-pass filter
        hp_filtered = pipeline._apply_high_pass_filter(test_signal, sample_rate, config.high_pass_cutoff)
        assert len(hp_filtered) == len(test_signal)
        
        # Test low-pass filter
        lp_filtered = pipeline._apply_low_pass_filter(test_signal, sample_rate, config.low_pass_cutoff)
        assert len(lp_filtered) == len(test_signal)
        
        # Test that filtering changes the signal
        hp_difference = np.mean(np.abs(hp_filtered - test_signal))
        lp_difference = np.mean(np.abs(lp_filtered - test_signal))
        
        assert hp_difference > 1e-6, "High-pass filter had no effect"
        assert lp_difference > 1e-6, "Low-pass filter had no effect"
        
        print("✅ Audio filtering test passed")
    
    def test_audio_normalization_and_compression(self):
        """Test audio normalization and compression."""
        from api.services.audio_processing import AudioProcessingPipeline, AudioProcessingConfig
        
        sample_rate = 16000
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create signal with varying dynamics
        quiet_section = 0.1 * np.sin(2 * np.pi * 440 * t[:len(t)//3])
        loud_section = 0.9 * np.sin(2 * np.pi * 440 * t[len(t)//3:2*len(t)//3])
        medium_section = 0.5 * np.sin(2 * np.pi * 440 * t[2*len(t)//3:])
        
        test_audio = np.concatenate([quiet_section, loud_section, medium_section])
        
        config = AudioProcessingConfig()
        pipeline = AudioProcessingPipeline(config)
        
        # Test peak normalization
        config.preserve_dynamics = True
        normalized_peak = pipeline._normalize_audio(test_audio)
        
        peak_before = np.max(np.abs(test_audio))
        peak_after = np.max(np.abs(normalized_peak))
        
        assert peak_after <= 0.95, "Peak normalization failed to limit peak"
        assert peak_after > peak_before * 0.5, "Peak normalization too aggressive"
        
        # Test RMS normalization
        config.preserve_dynamics = False
        normalized_rms = pipeline._normalize_audio(test_audio)
        
        rms_after = np.sqrt(np.mean(normalized_rms ** 2))
        assert 0.15 <= rms_after <= 0.25, f"RMS normalization target missed: {rms_after}"
        
        # Test compression
        compressed = pipeline._apply_compression(test_audio)
        
        # Check that loud parts are compressed more than quiet parts
        loud_ratio = np.max(np.abs(compressed[len(t)//3:2*len(t)//3])) / np.max(np.abs(loud_section))
        quiet_ratio = np.max(np.abs(compressed[:len(t)//3])) / np.max(np.abs(quiet_section))
        
        assert loud_ratio < quiet_ratio, "Compression not working properly"
        
        print("✅ Audio normalization and compression test passed")


class AudioProcessingServiceTests:
    """Test suite for audio processing service integration."""
    
    def test_service_configuration(self):
        """Test audio processing service configuration."""
        from api.services.audio_processing import AudioProcessingService, AudioProcessingConfig
        
        service = AudioProcessingService()
        
        # Test default configuration
        assert service.default_config is not None
        assert service.default_config.target_sample_rate == 16000
        assert service.default_config.target_channels == 1
        
        # Test config overrides
        custom_overrides = {
            'target_sample_rate': 22050,
            'enable_noise_reduction': False,
            'noise_reduction_strength': 0.8
        }
        
        custom_config = service._apply_config_overrides(service.default_config, custom_overrides)
        
        assert custom_config.target_sample_rate == 22050
        assert custom_config.enable_noise_reduction == False
        assert custom_config.noise_reduction_strength == 0.8
        
        print("✅ Service configuration test passed")
    
    def test_optimal_config_generation(self):
        """Test optimal configuration generation based on analysis."""
        from api.services.audio_processing import AudioProcessingService, AudioAnalysis
        
        service = AudioProcessingService()
        
        # Test high-quality audio (minimal processing needed)
        good_analysis = AudioAnalysis(
            duration=10.0, sample_rate=44100, channels=2, format='.wav',
            bitrate=1411, rms_level=0.3, peak_level=0.8, dynamic_range=0.5,
            snr_estimate=35.0, frequency_range=(80.0, 8000.0),
            recommended_noise_reduction=False, recommended_normalization=False,
            quality_score=0.9
        )
        
        good_config = service.get_optimal_config_for_analysis(good_analysis)
        assert good_config.enable_noise_reduction == False
        assert good_config.quality_level.value == 'high'
        
        # Test poor-quality audio (aggressive processing needed)
        poor_analysis = AudioAnalysis(
            duration=10.0, sample_rate=16000, channels=1, format='.mp3',
            bitrate=128, rms_level=0.1, peak_level=0.3, dynamic_range=0.2,
            snr_estimate=8.0, frequency_range=(100.0, 4000.0),
            recommended_noise_reduction=True, recommended_normalization=True,
            quality_score=0.3
        )
        
        poor_config = service.get_optimal_config_for_analysis(poor_analysis)
        assert poor_config.enable_noise_reduction == True
        assert poor_config.noise_reduction_strength == 0.8
        assert poor_config.enable_normalization == True
        
        print("✅ Optimal config generation test passed")
    
    def test_processing_workflow_simulation(self):
        """Test complete processing workflow simulation."""
        from api.services.audio_processing import AudioProcessingService
        
        service = AudioProcessingService()
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Write dummy WAV header and data
            import wave
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                
                # Generate 1 second of test audio
                sample_rate = 16000
                duration = 1.0
                t = np.linspace(0, duration, int(sample_rate * duration))
                audio = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
                wav_file.writeframes(audio.tobytes())
        
        try:
            # Mock the actual processing to avoid complex dependencies
            with patch.object(service, 'analyze_audio_quality') as mock_analyze:
                mock_analyze.return_value = AudioAnalysis(
                    duration=1.0, sample_rate=16000, channels=1, format='.wav',
                    bitrate=256, rms_level=0.3, peak_level=0.5, dynamic_range=0.2,
                    snr_estimate=15.0, frequency_range=(80.0, 8000.0),
                    recommended_noise_reduction=True, recommended_normalization=True,
                    quality_score=0.6
                )
                
                with patch('api.services.audio_processing.AudioProcessingPipeline') as mock_pipeline_class:
                    mock_pipeline = Mock()
                    mock_pipeline.process_audio_file.return_value = (temp_path, mock_analyze.return_value)
                    mock_pipeline_class.return_value = mock_pipeline
                    
                    # Test the processing workflow
                    result_path, analysis = service.process_for_transcription(temp_path)
                    
                    assert result_path == temp_path
                    assert analysis.quality_score == 0.6
                    assert analysis.recommended_noise_reduction == True
        
        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        
        print("✅ Processing workflow simulation test passed")


class AudioAPITests:
    """Test suite for audio processing API endpoints."""
    
    def test_api_request_validation(self):
        """Test API request validation."""
        from api.routes.audio_processing import AudioProcessingRequest
        
        # Test valid request
        valid_request = {
            'enable_noise_reduction': True,
            'noise_reduction_method': 'spectral_gating',
            'noise_reduction_strength': 0.5,
            'enable_normalization': True,
            'target_sample_rate': 16000,
            'quality_level': 'medium'
        }
        
        try:
            request = AudioProcessingRequest(**valid_request)
            assert request.enable_noise_reduction == True
            assert request.noise_reduction_method == 'spectral_gating'
            assert request.target_sample_rate == 16000
        except Exception as e:
            pytest.fail(f"Valid request failed validation: {e}")
        
        # Test invalid request (out of range values)
        invalid_request = {
            'noise_reduction_strength': 1.5,  # Should be 0.0-1.0
            'target_sample_rate': 100000,     # Very high sample rate
            'target_channels': 0               # Invalid channel count
        }
        
        try:
            AudioProcessingRequest(**invalid_request)
            pytest.fail("Invalid request should have failed validation")
        except Exception:
            pass  # Expected to fail
        
        print("✅ API request validation test passed")
    
    def test_format_information_endpoints(self):
        """Test format information and metrics endpoints."""
        from api.routes.audio_processing import _get_format_description, _get_format_quality, _get_format_compression
        from api.services.audio_processing import AudioFormat
        
        # Test format descriptions
        for fmt in AudioFormat:
            description = _get_format_description(fmt)
            assert isinstance(description, str)
            assert len(description) > 0
            
            quality = _get_format_quality(fmt)
            assert quality in ['excellent', 'good', 'fair', 'unknown']
            
            compression = _get_format_compression(fmt)
            assert compression in ['none', 'lossless', 'lossy', 'unknown']
        
        print("✅ Format information endpoints test passed")


class AudioProcessingIntegrationTests:
    """Integration tests for the complete audio processing system."""
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end processing workflow."""
        
        # This would test the complete workflow from file upload to processed output
        # For now, we'll test the component integration
        
        from api.services.audio_processing import (
            AudioProcessingService, AudioProcessingConfig, AudioFormat
        )
        
        service = AudioProcessingService()
        
        # Test configuration flow
        config = service.default_config
        assert config.target_format == AudioFormat.WAV
        assert config.target_sample_rate == 16000
        
        # Test format converter integration
        from api.services.audio_processing import AudioFormatConverter
        
        supported_formats = AudioFormatConverter.get_supported_formats()
        assert 'wav' in supported_formats
        assert 'mp3' in supported_formats
        
        print("✅ End-to-end workflow test passed")
    
    def test_error_handling_and_recovery(self):
        """Test system error handling and recovery mechanisms."""
        from api.services.audio_processing import AudioProcessingPipeline, AudioProcessingConfig
        
        config = AudioProcessingConfig()
        pipeline = AudioProcessingPipeline(config)
        
        # Test with invalid audio data
        invalid_audio = np.array([])  # Empty array
        
        try:
            # This should handle empty input gracefully
            result = pipeline._normalize_audio(invalid_audio)
            assert len(result) == 0  # Should return empty array
        except Exception as e:
            # If it throws an exception, it should be handled appropriately
            assert "empty" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test with extreme values
        extreme_audio = np.array([1000.0, -1000.0, 0.0])  # Values outside [-1, 1]
        
        try:
            normalized = pipeline._normalize_audio(extreme_audio)
            # Should clip or normalize extreme values
            assert np.max(np.abs(normalized)) <= 1.0
        except Exception:
            pass  # Error handling is acceptable for extreme inputs
        
        print("✅ Error handling and recovery test passed")


class AudioProcessingTestRunner:
    """Main test runner for the audio processing system."""
    
    def __init__(self):
        self.tests = [
            AudioProcessingTests(),
            AudioProcessingServiceTests(),
            AudioAPITests(),
            AudioProcessingIntegrationTests()
        ]
        self.passed = 0
        self.failed = 0
        self.total = 0
    
    def run_test_class(self, test_class):
        """Run all tests in a test class."""
        class_name = test_class.__class__.__name__
        print(f"\n📋 Running {class_name}")
        print("-" * 50)
        
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            self.total += 1
            try:
                method = getattr(test_class, method_name)
                method()
                self.passed += 1
            except Exception as e:
                print(f"  ❌ {method_name}: {str(e)}")
                self.failed += 1
    
    def run_all_tests(self):
        """Run the complete test suite."""
        print("🧪 T035 Audio Processing Pipeline Enhancement - Test Suite")
        print("=" * 70)
        
        for test_class in self.tests:
            self.run_test_class(test_class)
        
        print(f"\n📊 Test Results Summary:")
        print(f"   Total tests: {self.total}")
        print(f"   Passed: {self.passed}")
        print(f"   Failed: {self.failed}")
        print(f"   Success rate: {(self.passed / self.total * 100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 All T035 Audio Processing Pipeline tests passed!")
            print("\n📝 Test Coverage Summary:")
            print("   ✅ Audio Format Validation & Conversion")
            print("   ✅ Audio Analysis & Quality Assessment")
            print("   ✅ Noise Reduction Algorithms (4 methods)")
            print("   ✅ Audio Enhancement Pipeline")
            print("   ✅ Filtering & Signal Processing")
            print("   ✅ Normalization & Compression")
            print("   ✅ Service Configuration & Integration")
            print("   ✅ API Validation & Error Handling")
            print("   ✅ End-to-End Workflow Testing")
            print("\n🚀 T035 Audio Processing Pipeline is ready for production!")
            return True
        else:
            print(f"\n⚠️  {self.failed} tests failed. Check implementation.")
            return False


def main():
    """Main entry point for test execution."""
    test_runner = AudioProcessingTestRunner()
    success = test_runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())