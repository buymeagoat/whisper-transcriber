"""
T035: Audio Processing Pipeline Enhancement
Comprehensive audio processing service for noise reduction, normalization, and format conversion.
"""

import os
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from enum import Enum
import asyncio
from dataclasses import dataclass

import librosa
import soundfile as sf
import numpy as np
from scipy import signal
from pydub import AudioSegment
from pydub.effects import normalize, low_pass_filter, high_pass_filter

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"
    AAC = "aac"
    OPUS = "opus"


class NoiseReductionMethod(Enum):
    """Available noise reduction methods."""
    SPECTRAL_GATING = "spectral_gating"
    WIENER_FILTER = "wiener_filter"
    BANDPASS_FILTER = "bandpass_filter"
    ADAPTIVE_FILTER = "adaptive_filter"


class AudioQualityLevel(Enum):
    """Audio quality levels."""
    LOW = "low"      # 16 kHz, 16-bit
    MEDIUM = "medium"  # 22.05 kHz, 16-bit
    HIGH = "high"    # 44.1 kHz, 16-bit
    ULTRA = "ultra"  # 48 kHz, 24-bit


@dataclass
class AudioProcessingConfig:
    """Configuration for audio processing pipeline."""
    
    # Target format settings
    target_format: AudioFormat = AudioFormat.WAV
    target_sample_rate: int = 16000
    target_channels: int = 1
    target_bitrate: Optional[int] = None
    
    # Quality settings
    quality_level: AudioQualityLevel = AudioQualityLevel.MEDIUM
    
    # Noise reduction settings
    enable_noise_reduction: bool = True
    noise_reduction_method: NoiseReductionMethod = NoiseReductionMethod.SPECTRAL_GATING
    noise_reduction_strength: float = 0.5  # 0.0 to 1.0
    
    # Audio enhancement settings
    enable_normalization: bool = True
    enable_compression: bool = True
    enable_eq: bool = False
    preserve_dynamics: bool = True
    
    # Filtering settings
    high_pass_cutoff: float = 80.0  # Hz
    low_pass_cutoff: float = 8000.0  # Hz
    
    # Advanced settings
    frame_length: int = 2048
    hop_length: int = 512
    spectral_gate_stationary: bool = True
    spectral_gate_alpha: float = 2.0
    spectral_gate_threshold: float = 0.02


@dataclass
class AudioAnalysis:
    """Audio analysis results."""
    duration: float
    sample_rate: int
    channels: int
    format: str
    bitrate: Optional[int]
    
    # Quality metrics
    rms_level: float
    peak_level: float
    dynamic_range: float
    snr_estimate: float
    frequency_range: Tuple[float, float]
    
    # Processing recommendations
    recommended_noise_reduction: bool
    recommended_normalization: bool
    quality_score: float  # 0.0 to 1.0


class AudioProcessingPipeline:
    """Main audio processing pipeline for enhanced transcription."""
    
    def __init__(self, config: AudioProcessingConfig):
        self.config = config
        self.temp_dir = tempfile.mkdtemp(prefix="audio_processing_")
        
    def __del__(self):
        """Cleanup temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass
    
    async def process_audio_file(self, input_path: str, output_path: Optional[str] = None) -> Tuple[str, AudioAnalysis]:
        """
        Process audio file through the complete enhancement pipeline.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path (will generate if not provided)
            
        Returns:
            Tuple of (processed_file_path, analysis_results)
        """
        logger.info(f"Starting audio processing pipeline for: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            input_name = Path(input_path).stem
            output_path = os.path.join(self.temp_dir, f"{input_name}_processed.wav")
        
        # Step 1: Analyze input audio
        analysis = await self.analyze_audio(input_path)
        logger.info(f"Audio analysis complete. Quality score: {analysis.quality_score:.2f}")
        
        # Step 2: Load and convert format if necessary
        audio_data, sample_rate = await self.load_and_convert_audio(input_path)
        
        # Step 3: Apply preprocessing pipeline
        processed_audio = await self.apply_processing_pipeline(audio_data, sample_rate, analysis)
        
        # Step 4: Save processed audio
        await self.save_processed_audio(processed_audio, sample_rate, output_path)
        
        logger.info(f"Audio processing complete. Output: {output_path}")
        return output_path, analysis
    
    async def analyze_audio(self, file_path: str) -> AudioAnalysis:
        """Analyze audio file and provide processing recommendations."""
        try:
            # Load audio for analysis
            audio_data, sr = librosa.load(file_path, sr=None, mono=False)
            
            # Handle mono/stereo
            if audio_data.ndim > 1:
                channels = audio_data.shape[0]
                mono_audio = librosa.to_mono(audio_data)
            else:
                channels = 1
                mono_audio = audio_data
            
            # Basic properties
            duration = len(mono_audio) / sr
            
            # Quality metrics
            rms_level = np.sqrt(np.mean(mono_audio ** 2))
            peak_level = np.max(np.abs(mono_audio))
            dynamic_range = peak_level - rms_level if peak_level > 0 else 0
            
            # Estimate SNR (simplified)
            snr_estimate = self._estimate_snr(mono_audio, sr)
            
            # Frequency analysis
            fft = np.fft.fft(mono_audio)
            freqs = np.fft.fftfreq(len(fft), 1/sr)
            magnitude = np.abs(fft)
            
            # Find frequency range with significant content
            freq_range = self._find_frequency_range(freqs, magnitude)
            
            # Processing recommendations
            recommended_noise_reduction = snr_estimate < 20.0  # dB
            recommended_normalization = peak_level < 0.5 or peak_level > 0.95
            
            # Overall quality score
            quality_score = self._calculate_quality_score(
                snr_estimate, dynamic_range, peak_level, rms_level
            )
            
            # Get file format info
            try:
                audio_segment = AudioSegment.from_file(file_path)
                format_info = audio_segment.frame_rate, audio_segment.frame_width * 8
                bitrate = getattr(audio_segment, 'bitrate', None)
            except Exception:
                format_info = sr, 16
                bitrate = None
            
            return AudioAnalysis(
                duration=duration,
                sample_rate=sr,
                channels=channels,
                format=Path(file_path).suffix.lower(),
                bitrate=bitrate,
                rms_level=float(rms_level),
                peak_level=float(peak_level),
                dynamic_range=float(dynamic_range),
                snr_estimate=float(snr_estimate),
                frequency_range=freq_range,
                recommended_noise_reduction=recommended_noise_reduction,
                recommended_normalization=recommended_normalization,
                quality_score=float(quality_score)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            # Return basic analysis with defaults
            return AudioAnalysis(
                duration=0.0, sample_rate=16000, channels=1, format=".wav",
                bitrate=None, rms_level=0.0, peak_level=0.0, dynamic_range=0.0,
                snr_estimate=0.0, frequency_range=(0.0, 8000.0),
                recommended_noise_reduction=True, recommended_normalization=True,
                quality_score=0.0
            )
    
    async def load_and_convert_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and convert to target format."""
        try:
            # Load with librosa for consistency
            audio_data, sr = librosa.load(
                file_path,
                sr=self.config.target_sample_rate,
                mono=(self.config.target_channels == 1)
            )
            
            logger.info(f"Loaded audio: {len(audio_data)/sr:.2f}s at {sr}Hz")
            return audio_data, sr
            
        except Exception as e:
            logger.error(f"Error loading audio file: {e}")
            # Try with pydub as fallback
            try:
                audio_segment = AudioSegment.from_file(file_path)
                
                # Convert to target format
                if self.config.target_channels == 1:
                    audio_segment = audio_segment.set_channels(1)
                
                audio_segment = audio_segment.set_frame_rate(self.config.target_sample_rate)
                
                # Convert to numpy array
                audio_data = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
                audio_data = audio_data / (2**15)  # Normalize to [-1, 1]
                
                return audio_data, self.config.target_sample_rate
                
            except Exception as fallback_error:
                logger.error(f"Fallback audio loading failed: {fallback_error}")
                raise
    
    async def apply_processing_pipeline(self, audio_data: np.ndarray, sample_rate: int, analysis: AudioAnalysis) -> np.ndarray:
        """Apply the complete audio processing pipeline."""
        processed = audio_data.copy()
        
        # Step 1: High-pass filter to remove low-frequency noise
        if self.config.high_pass_cutoff:
            processed = self._apply_high_pass_filter(processed, sample_rate, self.config.high_pass_cutoff)
            logger.debug(f"Applied high-pass filter at {self.config.high_pass_cutoff}Hz")
        
        # Step 2: Low-pass filter to remove high-frequency noise
        if self.config.low_pass_cutoff:
            processed = self._apply_low_pass_filter(processed, sample_rate, self.config.low_pass_cutoff)
            logger.debug(f"Applied low-pass filter at {self.config.low_pass_cutoff}Hz")
        
        # Step 3: Noise reduction
        if self.config.enable_noise_reduction and analysis.recommended_noise_reduction:
            processed = await self._apply_noise_reduction(processed, sample_rate)
            logger.debug(f"Applied noise reduction: {self.config.noise_reduction_method.value}")
        
        # Step 4: Normalization
        if self.config.enable_normalization and analysis.recommended_normalization:
            processed = self._normalize_audio(processed)
            logger.debug("Applied audio normalization")
        
        # Step 5: Dynamic range compression (optional)
        if self.config.enable_compression:
            processed = self._apply_compression(processed)
            logger.debug("Applied dynamic range compression")
        
        # Step 6: EQ adjustments (optional)
        if self.config.enable_eq:
            processed = self._apply_eq(processed, sample_rate)
            logger.debug("Applied EQ adjustments")
        
        return processed
    
    def _apply_high_pass_filter(self, audio: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
        """Apply high-pass filter to remove low-frequency noise."""
        nyquist = sr / 2
        normalized_cutoff = cutoff / nyquist
        
        # Design filter
        b, a = signal.butter(4, normalized_cutoff, btype='high')
        
        # Apply filter
        return signal.filtfilt(b, a, audio)
    
    def _apply_low_pass_filter(self, audio: np.ndarray, sr: int, cutoff: float) -> np.ndarray:
        """Apply low-pass filter to remove high-frequency noise."""
        nyquist = sr / 2
        normalized_cutoff = min(cutoff / nyquist, 0.99)  # Ensure it's below Nyquist
        
        # Design filter
        b, a = signal.butter(4, normalized_cutoff, btype='low')
        
        # Apply filter
        return signal.filtfilt(b, a, audio)
    
    async def _apply_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply noise reduction based on selected method."""
        method = self.config.noise_reduction_method
        
        if method == NoiseReductionMethod.SPECTRAL_GATING:
            return self._spectral_gating_noise_reduction(audio, sr)
        elif method == NoiseReductionMethod.WIENER_FILTER:
            return self._wiener_filter_noise_reduction(audio, sr)
        elif method == NoiseReductionMethod.BANDPASS_FILTER:
            return self._bandpass_filter_noise_reduction(audio, sr)
        elif method == NoiseReductionMethod.ADAPTIVE_FILTER:
            return self._adaptive_filter_noise_reduction(audio, sr)
        else:
            logger.warning(f"Unknown noise reduction method: {method}")
            return audio
    
    def _spectral_gating_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply spectral gating noise reduction."""
        # Convert to spectrogram
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise floor (use first 0.5 seconds as noise sample)
        noise_frames = int(0.5 * sr / 512)  # Convert to frame count
        noise_floor = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Create spectral gate
        gate_threshold = noise_floor * (1 + self.config.noise_reduction_strength * 2)
        gate_ratio = 0.1  # Suppress to 10% of original when below threshold
        
        # Apply gating
        mask = magnitude > gate_threshold
        gated_magnitude = magnitude * mask + magnitude * gate_ratio * (~mask)
        
        # Reconstruct audio
        gated_stft = gated_magnitude * np.exp(1j * phase)
        return librosa.istft(gated_stft, hop_length=512)
    
    def _wiener_filter_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply Wiener filter for noise reduction."""
        # Simple Wiener filter implementation
        # This is a basic version - could be enhanced with more sophisticated methods
        
        # Convert to frequency domain
        fft = np.fft.fft(audio)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Estimate noise power (using silence detection)
        power = magnitude ** 2
        noise_power = np.percentile(power, 10)  # Assume 10th percentile is noise
        
        # Wiener filter
        wiener_filter = power / (power + noise_power * self.config.noise_reduction_strength)
        filtered_magnitude = magnitude * wiener_filter
        
        # Reconstruct
        filtered_fft = filtered_magnitude * np.exp(1j * phase)
        return np.real(np.fft.ifft(filtered_fft))
    
    def _bandpass_filter_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply bandpass filter focusing on speech frequencies."""
        # Speech frequency range (approximately 85-255 Hz for fundamental, up to 8000 Hz for formants)
        low_cutoff = 85.0
        high_cutoff = 8000.0
        
        nyquist = sr / 2
        low = low_cutoff / nyquist
        high = min(high_cutoff / nyquist, 0.99)
        
        # Design bandpass filter
        b, a = signal.butter(6, [low, high], btype='band')
        
        # Apply filter
        return signal.filtfilt(b, a, audio)
    
    def _adaptive_filter_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply adaptive noise reduction."""
        # Simplified adaptive filter
        # In practice, this would use more sophisticated algorithms like LMS or RLS
        
        # Use spectral subtraction with adaptive parameters
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Adaptive noise estimation
        noise_estimate = np.zeros_like(magnitude)
        alpha = 0.95  # Smoothing factor
        
        for i in range(magnitude.shape[1]):
            if i == 0:
                noise_estimate[:, i] = magnitude[:, i]
            else:
                # Update noise estimate when signal is low
                signal_power = np.sum(magnitude[:, i] ** 2)
                if signal_power < np.percentile(magnitude ** 2, 20):
                    noise_estimate[:, i] = alpha * noise_estimate[:, i-1] + (1-alpha) * magnitude[:, i]
                else:
                    noise_estimate[:, i] = noise_estimate[:, i-1]
        
        # Spectral subtraction
        enhanced_magnitude = magnitude - self.config.noise_reduction_strength * noise_estimate
        enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)  # Floor
        
        # Reconstruct
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        return librosa.istft(enhanced_stft, hop_length=512)
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to optimal level."""
        if self.config.preserve_dynamics:
            # Peak normalization
            peak = np.max(np.abs(audio))
            if peak > 0:
                return audio * (0.95 / peak)  # Normalize to 95% to avoid clipping
            return audio
        else:
            # RMS normalization
            rms = np.sqrt(np.mean(audio ** 2))
            if rms > 0:
                target_rms = 0.2  # Target RMS level
                return audio * (target_rms / rms)
            return audio
    
    def _apply_compression(self, audio: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression."""
        # Simple soft-knee compressor
        threshold = 0.7
        ratio = 4.0
        
        # Calculate envelope
        envelope = np.abs(audio)
        
        # Apply compression above threshold
        compressed = audio.copy()
        above_threshold = envelope > threshold
        
        if np.any(above_threshold):
            # Compression formula
            excess = envelope[above_threshold] - threshold
            compressed_excess = excess / ratio
            compressed_envelope = threshold + compressed_excess
            
            # Apply compression while preserving sign
            gain = compressed_envelope / envelope[above_threshold]
            compressed[above_threshold] = audio[above_threshold] * gain
        
        return compressed
    
    def _apply_eq(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """Apply EQ adjustments optimized for speech."""
        # Simple 3-band EQ with speech-optimized settings
        
        # Low cut (reduce rumble)
        audio = self._apply_high_pass_filter(audio, sr, 80.0)
        
        # Mid boost (enhance speech clarity)
        mid_freq = 1000.0
        mid_gain = 1.2
        audio = self._apply_peaking_eq(audio, sr, mid_freq, mid_gain, 1.0)
        
        # High shelf (enhance consonants)
        high_freq = 5000.0
        high_gain = 1.1
        audio = self._apply_high_shelf(audio, sr, high_freq, high_gain)
        
        return audio
    
    def _apply_peaking_eq(self, audio: np.ndarray, sr: int, freq: float, gain: float, q: float) -> np.ndarray:
        """Apply peaking EQ filter."""
        # Design peaking filter
        w0 = 2 * np.pi * freq / sr
        A = np.sqrt(gain)
        alpha = np.sin(w0) / (2 * q)
        
        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A
        
        # Normalize
        b = [b0/a0, b1/a0, b2/a0]
        a = [1, a1/a0, a2/a0]
        
        return signal.filtfilt(b, a, audio)
    
    def _apply_high_shelf(self, audio: np.ndarray, sr: int, freq: float, gain: float) -> np.ndarray:
        """Apply high shelf filter."""
        w0 = 2 * np.pi * freq / sr
        A = np.sqrt(gain)
        S = 1  # Shelf slope
        beta = np.sqrt(A) / S
        
        cos_w0 = np.cos(w0)
        sin_w0 = np.sin(w0)
        
        b0 = A * ((A + 1) + (A - 1) * cos_w0 + beta * sin_w0)
        b1 = -2 * A * ((A - 1) + (A + 1) * cos_w0)
        b2 = A * ((A + 1) + (A - 1) * cos_w0 - beta * sin_w0)
        a0 = (A + 1) - (A - 1) * cos_w0 + beta * sin_w0
        a1 = 2 * ((A - 1) - (A + 1) * cos_w0)
        a2 = (A + 1) - (A - 1) * cos_w0 - beta * sin_w0
        
        # Normalize
        b = [b0/a0, b1/a0, b2/a0]
        a = [1, a1/a0, a2/a0]
        
        return signal.filtfilt(b, a, audio)
    
    async def save_processed_audio(self, audio: np.ndarray, sample_rate: int, output_path: str) -> None:
        """Save processed audio to file."""
        try:
            # Ensure audio is in valid range
            audio = np.clip(audio, -1.0, 1.0)
            
            # Save using soundfile for high quality
            sf.write(output_path, audio, sample_rate, subtype='PCM_16')
            logger.info(f"Saved processed audio to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving processed audio: {e}")
            raise
    
    def _estimate_snr(self, audio: np.ndarray, sr: int) -> float:
        """Estimate signal-to-noise ratio."""
        # Simple SNR estimation using energy-based voice activity detection
        
        # Frame the audio
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop
        
        frames = librosa.util.frame(audio, frame_length=frame_length, hop_length=hop_length)
        
        # Calculate frame energy
        frame_energy = np.sum(frames ** 2, axis=0)
        
        # Voice activity detection (simple energy threshold)
        energy_threshold = np.percentile(frame_energy, 60)
        voice_frames = frame_energy > energy_threshold
        
        if np.sum(voice_frames) == 0:
            return 0.0  # No voice detected
        
        # Estimate signal and noise power
        signal_power = np.mean(frame_energy[voice_frames])
        noise_power = np.mean(frame_energy[~voice_frames]) if np.sum(~voice_frames) > 0 else signal_power * 0.1
        
        # Convert to dB
        snr_db = 10 * np.log10(signal_power / noise_power) if noise_power > 0 else 60.0
        
        return max(0.0, min(60.0, snr_db))  # Clamp to reasonable range
    
    def _find_frequency_range(self, freqs: np.ndarray, magnitude: np.ndarray) -> Tuple[float, float]:
        """Find the frequency range with significant content."""
        # Only consider positive frequencies
        positive_freqs = freqs[freqs >= 0]
        positive_magnitude = magnitude[freqs >= 0]
        
        # Find frequencies with significant energy (above threshold)
        threshold = np.max(positive_magnitude) * 0.01  # 1% of peak
        significant_indices = positive_magnitude > threshold
        
        if not np.any(significant_indices):
            return (0.0, 8000.0)  # Default range
        
        significant_freqs = positive_freqs[significant_indices]
        
        return (float(np.min(significant_freqs)), float(np.max(significant_freqs)))
    
    def _calculate_quality_score(self, snr: float, dynamic_range: float, peak_level: float, rms_level: float) -> float:
        """Calculate overall audio quality score."""
        # Normalize each metric to 0-1 scale
        snr_score = min(snr / 30.0, 1.0)  # Assume 30dB is excellent
        dynamic_score = min(dynamic_range / 0.5, 1.0)  # Good dynamic range
        peak_score = 1.0 - abs(peak_level - 0.8) / 0.8  # Optimal around 0.8
        rms_score = min(rms_level / 0.3, 1.0)  # Good RMS level
        
        # Weighted average
        quality_score = (
            snr_score * 0.4 +
            dynamic_score * 0.2 +
            peak_score * 0.2 +
            rms_score * 0.2
        )
        
        return max(0.0, min(1.0, quality_score))


class AudioProcessingService:
    """High-level service for audio processing operations."""
    
    def __init__(self):
        self.default_config = AudioProcessingConfig()
        
    async def process_for_transcription(self, input_path: str, custom_config: Optional[Dict[str, Any]] = None) -> Tuple[str, AudioAnalysis]:
        """
        Process audio file optimized for transcription quality.
        
        Args:
            input_path: Path to input audio file
            custom_config: Optional custom configuration overrides
            
        Returns:
            Tuple of (processed_file_path, analysis_results)
        """
        # Create config with custom overrides
        config = self.default_config
        if custom_config:
            config = self._apply_config_overrides(config, custom_config)
        
        # Create processing pipeline
        pipeline = AudioProcessingPipeline(config)
        
        try:
            return await pipeline.process_audio_file(input_path)
        finally:
            # Cleanup pipeline resources
            del pipeline
    
    async def analyze_audio_quality(self, file_path: str) -> AudioAnalysis:
        """Analyze audio file quality without processing."""
        pipeline = AudioProcessingPipeline(self.default_config)
        try:
            return await pipeline.analyze_audio(file_path)
        finally:
            del pipeline
    
    def get_optimal_config_for_analysis(self, analysis: AudioAnalysis) -> AudioProcessingConfig:
        """Get optimal processing configuration based on audio analysis."""
        config = AudioProcessingConfig()
        
        # Adjust noise reduction based on SNR
        if analysis.snr_estimate < 10:
            config.noise_reduction_strength = 0.8
            config.noise_reduction_method = NoiseReductionMethod.SPECTRAL_GATING
        elif analysis.snr_estimate < 20:
            config.noise_reduction_strength = 0.5
            config.noise_reduction_method = NoiseReductionMethod.WIENER_FILTER
        else:
            config.enable_noise_reduction = False
        
        # Adjust normalization based on levels
        if analysis.peak_level < 0.3 or analysis.peak_level > 0.95:
            config.enable_normalization = True
        
        # Adjust compression based on dynamic range
        if analysis.dynamic_range > 0.7:
            config.enable_compression = True
        
        # Adjust quality level based on input
        if analysis.sample_rate >= 44100:
            config.quality_level = AudioQualityLevel.HIGH
        elif analysis.sample_rate >= 22050:
            config.quality_level = AudioQualityLevel.MEDIUM
        else:
            config.quality_level = AudioQualityLevel.LOW
        
        return config
    
    def _apply_config_overrides(self, base_config: AudioProcessingConfig, overrides: Dict[str, Any]) -> AudioProcessingConfig:
        """Apply custom configuration overrides."""
        import copy
        config = copy.deepcopy(base_config)
        
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"Unknown config parameter: {key}")
        
        return config


# Utility functions for format conversion
class AudioFormatConverter:
    """Utility class for audio format conversion."""
    
    @staticmethod
    def convert_to_wav(input_path: str, output_path: str, sample_rate: int = 16000, channels: int = 1) -> bool:
        """Convert any audio format to WAV."""
        try:
            audio = AudioSegment.from_file(input_path)
            
            # Apply conversions
            if channels == 1:
                audio = audio.set_channels(1)
            audio = audio.set_frame_rate(sample_rate)
            
            # Export as WAV
            audio.export(output_path, format="wav")
            return True
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return False
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported input formats."""
        return [fmt.value for fmt in AudioFormat]
    
    @staticmethod
    def detect_format(file_path: str) -> Optional[str]:
        """Detect audio format from file."""
        try:
            audio = AudioSegment.from_file(file_path)
            return Path(file_path).suffix.lower().lstrip('.')
        except Exception:
            return None
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """Check if file format is supported."""
        try:
            extension = Path(file_path).suffix.lower().lstrip('.')
            supported_formats = AudioFormatConverter.get_supported_formats()
            return extension in supported_formats
        except Exception:
            return False