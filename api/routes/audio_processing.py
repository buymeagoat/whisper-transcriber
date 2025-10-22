"""
T035: Audio Processing API Routes
RESTful API endpoints for audio processing pipeline functionality.
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..orm_bootstrap import get_db
from ..services.audio_processing import (
    AudioProcessingService, AudioProcessingConfig, AudioAnalysis,
    AudioFormat, NoiseReductionMethod, AudioQualityLevel
)
from ..services.users import get_current_user
from ..utils.logger import get_logger

logger = get_logger("audio_processing_api")

router = APIRouter(prefix="/audio-processing", tags=["audio-processing"])

# Pydantic models for API
class AudioProcessingRequest(BaseModel):
    """Request model for audio processing."""
    enable_noise_reduction: bool = True
    noise_reduction_method: str = "spectral_gating"
    noise_reduction_strength: float = Field(0.5, ge=0.0, le=1.0)
    enable_normalization: bool = True
    enable_compression: bool = True
    enable_eq: bool = False
    high_pass_cutoff: Optional[float] = Field(80.0, ge=20.0, le=200.0)
    low_pass_cutoff: Optional[float] = Field(8000.0, ge=4000.0, le=20000.0)
    target_sample_rate: int = Field(16000, ge=8000, le=48000)
    target_channels: int = Field(1, ge=1, le=2)
    quality_level: str = "medium"
    preserve_dynamics: bool = True


class AudioAnalysisResponse(BaseModel):
    """Response model for audio analysis."""
    duration: float
    sample_rate: int
    channels: int
    format: str
    bitrate: Optional[int]
    rms_level: float
    peak_level: float
    dynamic_range: float
    snr_estimate: float
    frequency_range: tuple[float, float]
    recommended_noise_reduction: bool
    recommended_normalization: bool
    quality_score: float


class AudioProcessingResponse(BaseModel):
    """Response model for audio processing results."""
    success: bool
    processed_file_id: Optional[str] = None
    download_url: Optional[str] = None
    analysis: AudioAnalysisResponse
    processing_time: float
    file_size_original: int
    file_size_processed: int
    improvements: Dict[str, Any]


class ProcessingConfigResponse(BaseModel):
    """Response model for processing configuration."""
    supported_formats: list[str]
    noise_reduction_methods: list[str]
    quality_levels: list[str]
    default_config: Dict[str, Any]
    recommended_config: Optional[Dict[str, Any]] = None


# Global service instance
audio_service = AudioProcessingService()


@router.get("/config", response_model=ProcessingConfigResponse)
async def get_processing_config():
    """Get audio processing configuration options and defaults."""
    try:
        return ProcessingConfigResponse(
            supported_formats=[fmt.value for fmt in AudioFormat],
            noise_reduction_methods=[method.value for method in NoiseReductionMethod],
            quality_levels=[level.value for level in AudioQuality],
            default_config={
                "enable_noise_reduction": True,
                "noise_reduction_method": "spectral_gating",
                "noise_reduction_strength": 0.5,
                "enable_normalization": True,
                "enable_compression": True,
                "enable_eq": False,
                "high_pass_cutoff": 80.0,
                "low_pass_cutoff": 8000.0,
                "target_sample_rate": 16000,
                "target_channels": 1,
                "quality_level": "medium",
                "preserve_dynamics": True
            }
        )
    except Exception as e:
        logger.error(f"Error getting processing config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing configuration")


@router.post("/analyze", response_model=AudioAnalysisResponse)
async def analyze_audio_file(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Analyze audio file quality and get processing recommendations."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file format
    file_extension = Path(file.filename).suffix.lower()
    supported_extensions = [f".{fmt.value}" for fmt in AudioFormat]
    
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Supported formats: {', '.join(supported_extensions)}"
        )
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp(prefix="audio_analysis_")
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Analyzing audio file: {file.filename} for user: {current_user}")
        
        # Perform analysis
        analysis = await audio_service.analyze_audio_quality(temp_file_path)
        
        return AudioAnalysisResponse(
            duration=analysis.duration,
            sample_rate=analysis.sample_rate,
            channels=analysis.channels,
            format=analysis.format,
            bitrate=analysis.bitrate,
            rms_level=analysis.rms_level,
            peak_level=analysis.peak_level,
            dynamic_range=analysis.dynamic_range,
            snr_estimate=analysis.snr_estimate,
            frequency_range=analysis.frequency_range,
            recommended_noise_reduction=analysis.recommended_noise_reduction,
            recommended_normalization=analysis.recommended_normalization,
            quality_score=analysis.quality_score
        )
        
    except Exception as e:
        logger.error(f"Error analyzing audio file: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze audio file")
    
    finally:
        # Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


@router.post("/analyze/recommendations", response_model=ProcessingConfigResponse)
async def get_processing_recommendations(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    """Analyze audio file and get optimal processing configuration recommendations."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp(prefix="audio_recommendations_")
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Getting processing recommendations for: {file.filename}")
        
        # Analyze audio
        analysis = await audio_service.analyze_audio_quality(temp_file_path)
        
        # Get optimal configuration
        optimal_config = audio_service.get_optimal_config_for_analysis(analysis)
        
        # Convert to dict
        recommended_config = {
            "enable_noise_reduction": optimal_config.enable_noise_reduction,
            "noise_reduction_method": optimal_config.noise_reduction_method.value,
            "noise_reduction_strength": optimal_config.noise_reduction_strength,
            "enable_normalization": optimal_config.enable_normalization,
            "enable_compression": optimal_config.enable_compression,
            "enable_eq": optimal_config.enable_eq,
            "high_pass_cutoff": optimal_config.high_pass_cutoff,
            "low_pass_cutoff": optimal_config.low_pass_cutoff,
            "target_sample_rate": optimal_config.target_sample_rate,
            "target_channels": optimal_config.target_channels,
            "quality_level": optimal_config.quality_level.value,
            "preserve_dynamics": optimal_config.preserve_dynamics
        }
        
        base_config = get_processing_config()
        base_config.recommended_config = recommended_config
        
        return base_config
        
    except Exception as e:
        logger.error(f"Error getting processing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing recommendations")
    
    finally:
        # Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


@router.post("/process", response_model=AudioProcessingResponse)
async def process_audio_file(
    file: UploadFile = File(...),
    config: str = Form(...),  # JSON string of AudioProcessingRequest
    current_user: str = Depends(get_current_user)
):
    """Process audio file with specified configuration."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Parse configuration
    try:
        import json
        config_dict = json.loads(config)
        processing_request = AudioProcessingRequest(**config_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {e}")
    
    # Validate file format
    file_extension = Path(file.filename).suffix.lower()
    supported_extensions = [f".{fmt.value}" for fmt in AudioFormat]
    
    if file_extension not in supported_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Supported formats: {', '.join(supported_extensions)}"
        )
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp(prefix="audio_processing_")
    input_file_path = os.path.join(temp_dir, file.filename)
    processed_file_path = os.path.join(temp_dir, f"processed_{file.filename}")
    
    try:
        import time
        start_time = time.time()
        
        # Save uploaded file
        with open(input_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        original_size = os.path.getsize(input_file_path)
        
        logger.info(f"Processing audio file: {file.filename} for user: {current_user}")
        
        # Convert processing request to service config
        custom_config = {
            "enable_noise_reduction": processing_request.enable_noise_reduction,
            "noise_reduction_method": NoiseReductionMethod(processing_request.noise_reduction_method),
            "noise_reduction_strength": processing_request.noise_reduction_strength,
            "enable_normalization": processing_request.enable_normalization,
            "enable_compression": processing_request.enable_compression,
            "enable_eq": processing_request.enable_eq,
            "high_pass_cutoff": processing_request.high_pass_cutoff,
            "low_pass_cutoff": processing_request.low_pass_cutoff,
            "target_sample_rate": processing_request.target_sample_rate,
            "target_channels": processing_request.target_channels,
            "quality_level": AudioQuality(processing_request.quality_level),
            "preserve_dynamics": processing_request.preserve_dynamics
        }
        
        # Process audio
        processed_path, analysis = await audio_service.process_for_transcription(
            input_file_path, custom_config
        )
        
        processing_time = time.time() - start_time
        processed_size = os.path.getsize(processed_path)
        
        # Generate file ID and move to persistent storage
        import uuid
        file_id = str(uuid.uuid4())
        
        # In a real implementation, you'd store this in persistent storage
        # For now, we'll just provide a download URL
        download_url = f"/audio-processing/download/{file_id}"
        
        # Calculate improvements
        improvements = {
            "quality_score_improvement": max(0, analysis.quality_score - 0.5),  # Baseline assumption
            "noise_reduction_applied": custom_config["enable_noise_reduction"],
            "normalization_applied": custom_config["enable_normalization"],
            "compression_applied": custom_config["enable_compression"],
            "eq_applied": custom_config["enable_eq"],
            "processing_time_seconds": processing_time,
            "size_change_percent": ((processed_size - original_size) / original_size) * 100
        }
        
        # Store processed file temporarily (in production, use persistent storage)
        # This is a simplified implementation
        
        return AudioProcessingResponse(
            success=True,
            processed_file_id=file_id,
            download_url=download_url,
            analysis=AudioAnalysisResponse(
                duration=analysis.duration,
                sample_rate=analysis.sample_rate,
                channels=analysis.channels,
                format=analysis.format,
                bitrate=analysis.bitrate,
                rms_level=analysis.rms_level,
                peak_level=analysis.peak_level,
                dynamic_range=analysis.dynamic_range,
                snr_estimate=analysis.snr_estimate,
                frequency_range=analysis.frequency_range,
                recommended_noise_reduction=analysis.recommended_noise_reduction,
                recommended_normalization=analysis.recommended_normalization,
                quality_score=analysis.quality_score
            ),
            processing_time=processing_time,
            file_size_original=original_size,
            file_size_processed=processed_size,
            improvements=improvements
        )
        
    except Exception as e:
        logger.error(f"Error processing audio file: {e}")
        raise HTTPException(status_code=500, detail="Failed to process audio file")
    
    finally:
        # Cleanup temporary files
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


@router.get("/download/{file_id}")
async def download_processed_file(
    file_id: str,
    current_user: str = Depends(get_current_user)
):
    """Download processed audio file."""
    # In a real implementation, you'd retrieve the file from persistent storage
    # This is a simplified placeholder
    
    try:
        # Validate file_id and check user permissions
        # For now, we'll return a placeholder response
        
        raise HTTPException(
            status_code=501, 
            detail="File download not implemented in this demo. In production, this would serve the processed audio file."
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


@router.get("/formats", response_model=Dict[str, Any])
async def get_supported_formats():
    """Get supported audio formats and their properties."""
    try:
        formats = {}
        
        for fmt in AudioFormat:
            formats[fmt.value] = {
                "extension": f".{fmt.value}",
                "description": _get_format_description(fmt),
                "quality": _get_format_quality(fmt),
                "compression": _get_format_compression(fmt)
            }
        
        return {
            "supported_formats": formats,
            "recommended_input_formats": ["wav", "flac", "m4a"],
            "optimal_output_format": "wav",
            "transcription_requirements": {
                "sample_rate": 16000,
                "channels": 1,
                "bit_depth": 16,
                "format": "wav"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting format information: {e}")
        raise HTTPException(status_code=500, detail="Failed to get format information")


@router.get("/quality-metrics", response_model=Dict[str, Any])
async def get_quality_metrics_info():
    """Get information about audio quality metrics and their meanings."""
    try:
        return {
            "quality_metrics": {
                "quality_score": {
                    "description": "Overall audio quality score from 0.0 to 1.0",
                    "excellent": "> 0.8",
                    "good": "0.6 - 0.8",
                    "fair": "0.4 - 0.6",
                    "poor": "< 0.4"
                },
                "snr_estimate": {
                    "description": "Estimated Signal-to-Noise Ratio in decibels",
                    "excellent": "> 30 dB",
                    "good": "20 - 30 dB",
                    "fair": "10 - 20 dB",
                    "poor": "< 10 dB"
                },
                "dynamic_range": {
                    "description": "Difference between peak and RMS levels",
                    "excellent": "> 0.5",
                    "good": "0.3 - 0.5",
                    "fair": "0.1 - 0.3",
                    "poor": "< 0.1"
                },
                "peak_level": {
                    "description": "Maximum audio level (0.0 to 1.0)",
                    "optimal": "0.7 - 0.9",
                    "acceptable": "0.5 - 0.95",
                    "too_quiet": "< 0.5",
                    "clipping_risk": "> 0.95"
                }
            },
            "processing_recommendations": {
                "noise_reduction": "Recommended when SNR < 20 dB",
                "normalization": "Recommended when peak level < 0.5 or > 0.95",
                "compression": "Recommended when dynamic range > 0.7",
                "eq": "Optional for speech enhancement"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting quality metrics info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quality metrics information")


def _get_format_description(fmt: AudioFormat) -> str:
    """Get description for audio format."""
    descriptions = {
        AudioFormat.WAV: "Uncompressed, highest quality",
        AudioFormat.FLAC: "Lossless compression, high quality",
        AudioFormat.MP3: "Lossy compression, widely supported",
        AudioFormat.M4A: "Modern lossy compression, good quality",
        AudioFormat.OGG: "Open source lossy compression",
        AudioFormat.AAC: "Advanced lossy compression",
        AudioFormat.OPUS: "Modern low-latency compression"
    }
    return descriptions.get(fmt, "Audio format")


def _get_format_quality(fmt: AudioFormat) -> str:
    """Get quality rating for audio format."""
    quality_ratings = {
        AudioFormat.WAV: "excellent",
        AudioFormat.FLAC: "excellent", 
        AudioFormat.M4A: "good",
        AudioFormat.AAC: "good",
        AudioFormat.MP3: "fair",
        AudioFormat.OGG: "fair",
        AudioFormat.OPUS: "good"
    }
    return quality_ratings.get(fmt, "unknown")


def _get_format_compression(fmt: AudioFormat) -> str:
    """Get compression type for audio format."""
    compression_types = {
        AudioFormat.WAV: "none",
        AudioFormat.FLAC: "lossless",
        AudioFormat.MP3: "lossy",
        AudioFormat.M4A: "lossy",
        AudioFormat.AAC: "lossy", 
        AudioFormat.OGG: "lossy",
        AudioFormat.OPUS: "lossy"
    }
    return compression_types.get(fmt, "unknown")