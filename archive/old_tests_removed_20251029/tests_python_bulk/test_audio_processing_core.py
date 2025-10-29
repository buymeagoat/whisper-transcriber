#!/usr/bin/env python3
"""
Core functionality test for T035 Audio Processing Pipeline Enhancement.
Tests only the essential components without complex imports.
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_core_imports():
    """Test core audio processing imports."""
    try:
        from api.services.audio_processing import (
            AudioFormat, AudioQualityLevel, NoiseReductionMethod,
            AudioProcessingConfig, AudioAnalysis, AudioProcessingService
        )
        print("✅ Core audio processing imports successful")
        return True
    except Exception as e:
        print(f"❌ Core imports failed: {e}")
        return False


def test_audio_enums():
    """Test audio enum definitions."""
    try:
        from api.services.audio_processing import AudioFormat, AudioQualityLevel, NoiseReductionMethod
        
        # Test AudioFormat
        assert AudioFormat.WAV.value == 'wav'
        assert AudioFormat.MP3.value == 'mp3'
        assert len(list(AudioFormat)) == 7
        
        # Test AudioQualityLevel
        assert AudioQualityLevel.LOW.value == 'low'
        assert AudioQualityLevel.MEDIUM.value == 'medium'
        assert AudioQualityLevel.HIGH.value == 'high'
        
        # Test NoiseReductionMethod
        assert NoiseReductionMethod.SPECTRAL_GATING.value == 'spectral_gating'
        assert NoiseReductionMethod.WIENER_FILTER.value == 'wiener_filter'
        
        print("✅ Audio enums test passed")
        return True
    except Exception as e:
        print(f"❌ Audio enums test failed: {e}")
        return False


def test_audio_config():
    """Test AudioProcessingConfig."""
    try:
        from api.services.audio_processing import AudioProcessingConfig, AudioFormat, AudioQualityLevel
        
        # Test default config
        config = AudioProcessingConfig()
        assert config.target_sample_rate == 16000
        assert config.target_channels == 1
        assert config.quality_level == AudioQualityLevel.MEDIUM
        assert config.enable_noise_reduction == True
        
        # Test custom config
        custom_config = AudioProcessingConfig(
            target_format=AudioFormat.MP3,
            target_sample_rate=22050,
            quality_level=AudioQualityLevel.HIGH
        )
        assert custom_config.target_format == AudioFormat.MP3
        assert custom_config.target_sample_rate == 22050
        assert custom_config.quality_level == AudioQualityLevel.HIGH
        
        print("✅ AudioProcessingConfig test passed")
        return True
    except Exception as e:
        print(f"❌ AudioProcessingConfig test failed: {e}")
        return False


def test_audio_analysis():
    """Test AudioAnalysis dataclass."""
    try:
        from api.services.audio_processing import AudioAnalysis
        
        analysis = AudioAnalysis(
            duration=10.0,
            sample_rate=16000,
            channels=1,
            format='.wav',
            bitrate=256,
            rms_level=0.3,
            peak_level=0.8,
            dynamic_range=0.5,
            snr_estimate=20.0,
            frequency_range=(80.0, 8000.0),
            recommended_noise_reduction=True,
            recommended_normalization=False,
            quality_score=0.7
        )
        
        assert analysis.duration == 10.0
        assert analysis.sample_rate == 16000
        assert analysis.quality_score == 0.7
        assert len(analysis.frequency_range) == 2
        
        print("✅ AudioAnalysis test passed")
        return True
    except Exception as e:
        print(f"❌ AudioAnalysis test failed: {e}")
        return False


def test_audio_service_basic():
    """Test basic AudioProcessingService functionality."""
    try:
        from api.services.audio_processing import AudioProcessingService, AudioProcessingConfig
        
        service = AudioProcessingService()
        assert service.default_config is not None
        assert service.default_config.target_sample_rate == 16000
        
        # Test config overrides
        overrides = {
            'target_sample_rate': 22050,
            'enable_noise_reduction': False
        }
        
        custom_config = service._apply_config_overrides(service.default_config, overrides)
        assert custom_config.target_sample_rate == 22050
        assert custom_config.enable_noise_reduction == False
        
        print("✅ AudioProcessingService basic test passed")
        return True
    except Exception as e:
        print(f"❌ AudioProcessingService basic test failed: {e}")
        return False


def test_format_converter_logic():
    """Test format converter logic."""
    try:
        from api.services.audio_processing import AudioFormatConverter
        
        # Test supported formats
        supported = AudioFormatConverter.get_supported_formats()
        assert 'wav' in supported
        assert 'mp3' in supported
        assert len(supported) == 7
        
        # Test format validation logic
        assert AudioFormatConverter.is_supported_format('test.wav')
        assert AudioFormatConverter.is_supported_format('audio.MP3')  # Case insensitive
        assert not AudioFormatConverter.is_supported_format('file.txt')
        
        print("✅ AudioFormatConverter logic test passed")
        return True
    except Exception as e:
        print(f"❌ AudioFormatConverter logic test failed: {e}")
        return False


def test_mathematical_operations():
    """Test mathematical operations for audio processing."""
    try:
        # Test numpy operations that audio processing relies on
        sample_rate = 16000
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate test signal
        signal = 0.5 * np.sin(2 * np.pi * 440 * t)  # 440Hz sine wave
        
        # Test RMS calculation
        rms = np.sqrt(np.mean(signal ** 2))
        assert 0.3 < rms < 0.4, f"RMS calculation failed: {rms}"
        
        # Test peak detection
        peak = np.max(np.abs(signal))
        assert 0.49 < peak < 0.51, f"Peak detection failed: {peak}"
        
        # Test FFT operations
        fft_result = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1/sample_rate)
        magnitude = np.abs(fft_result)
        
        # Find dominant frequency
        positive_freqs = freqs[:len(freqs)//2]
        positive_magnitude = magnitude[:len(magnitude)//2]
        dominant_freq_idx = np.argmax(positive_magnitude[1:]) + 1
        dominant_freq = positive_freqs[dominant_freq_idx]
        
        assert 430 < dominant_freq < 450, f"FFT frequency detection failed: {dominant_freq}"
        
        print("✅ Mathematical operations test passed")
        return True
    except Exception as e:
        print(f"❌ Mathematical operations test failed: {e}")
        return False


def test_optimal_config_generation():
    """Test optimal configuration generation."""
    try:
        from api.services.audio_processing import AudioProcessingService, AudioAnalysis
        
        service = AudioProcessingService()
        
        # High quality analysis
        high_quality = AudioAnalysis(
            duration=10.0, sample_rate=44100, channels=2, format='.wav',
            bitrate=1411, rms_level=0.3, peak_level=0.8, dynamic_range=0.6,
            snr_estimate=30.0, frequency_range=(20.0, 20000.0),
            recommended_noise_reduction=False, recommended_normalization=False,
            quality_score=0.9
        )
        
        config = service.get_optimal_config_for_analysis(high_quality)
        assert config.enable_noise_reduction == False
        assert config.quality_level.value == 'high'
        
        # Low quality analysis
        low_quality = AudioAnalysis(
            duration=5.0, sample_rate=8000, channels=1, format='.mp3',
            bitrate=64, rms_level=0.1, peak_level=0.3, dynamic_range=0.1,
            snr_estimate=5.0, frequency_range=(200.0, 3500.0),
            recommended_noise_reduction=True, recommended_normalization=True,
            quality_score=0.2
        )
        
        config = service.get_optimal_config_for_analysis(low_quality)
        assert config.enable_noise_reduction == True
        assert config.noise_reduction_strength >= 0.7
        
        print("✅ Optimal config generation test passed")
        return True
    except Exception as e:
        print(f"❌ Optimal config generation test failed: {e}")
        return False


def run_core_tests():
    """Run core functionality tests."""
    tests = [
        ("Core Imports", test_core_imports),
        ("Audio Enums", test_audio_enums),
        ("Audio Config", test_audio_config),
        ("Audio Analysis", test_audio_analysis),
        ("Audio Service Basic", test_audio_service_basic),
        ("Format Converter Logic", test_format_converter_logic),
        ("Mathematical Operations", test_mathematical_operations),
        ("Optimal Config Generation", test_optimal_config_generation)
    ]
    
    print("🧪 T035 Audio Processing Pipeline - Core Functionality Tests")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Running: {test_name}")
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} failed with exception: {e}")
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📊 Test Results Summary:")
    print(f"   Total tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success rate: {success_rate:.1f}%")
    
    if failed == 0:
        print("\n🎉 All T035 core functionality tests passed!")
        print("\n📝 Validated Core Components:")
        print("   ✅ Audio format enums and definitions")
        print("   ✅ Configuration management system")
        print("   ✅ Audio analysis data structures")
        print("   ✅ Service initialization and config overrides")
        print("   ✅ Format conversion logic")
        print("   ✅ Mathematical foundations for audio processing")
        print("   ✅ Intelligent configuration optimization")
        print("\n🚀 T035 Audio Processing Pipeline core is validated and ready!")
        print("\n💡 Next Steps:")
        print("   • Backend API integration testing")
        print("   • Frontend component functionality validation")
        print("   • End-to-end audio processing workflow testing")
        print("   • Performance optimization and benchmarking")
        return True
    else:
        print(f"\n⚠️  {failed} core tests failed. Implementation needs review.")
        return False


if __name__ == "__main__":
    success = run_core_tests()
    exit(0 if success else 1)