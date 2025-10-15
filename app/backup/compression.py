"""
Compression Engine - High-Performance File Compression

Provides ZSTD compression optimized for backup workflows with
configurable compression levels and integrity validation.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
import hashlib

logger = logging.getLogger(__name__)

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False
    logger.warning("zstandard library not available, falling back to gzip")

try:
    import gzip
    GZIP_AVAILABLE = True
except ImportError:
    GZIP_AVAILABLE = False
    logger.error("Neither zstandard nor gzip available for compression")


class CompressionEngine:
    """
    High-performance compression engine with multiple backend support.
    
    Features:
    - ZSTD compression (primary) with configurable levels
    - Gzip fallback compression
    - Integrity validation with checksums
    - Compression ratio reporting
    - Stream compression for large files
    """
    
    def __init__(self, compression_level: int = 3, use_zstd: bool = True):
        """
        Initialize compression engine.
        
        Args:
            compression_level: Compression level (1-22 for ZSTD, 1-9 for gzip)
            use_zstd: Prefer ZSTD over gzip if available
        """
        self.compression_level = compression_level
        self.use_zstd = use_zstd and ZSTD_AVAILABLE
        
        if self.use_zstd:
            self.compressor = zstd.ZstdCompressor(level=compression_level)
            self.decompressor = zstd.ZstdDecompressor()
            self.extension = '.zst'
            logger.info(f"ZSTD compression engine initialized (level {compression_level})")
        elif GZIP_AVAILABLE:
            self.compression_level = min(compression_level, 9)  # Gzip max level is 9
            self.extension = '.gz'
            logger.info(f"Gzip compression engine initialized (level {self.compression_level})")
        else:
            raise RuntimeError("No compression library available")
    
    def compress_file(self, input_path: Path, output_path: Optional[Path] = None) -> Dict:
        """
        Compress a file and return compression statistics.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (auto-generated if None)
            
        Returns:
            Dict with compression statistics
        """
        try:
            input_path = Path(input_path)
            if output_path is None:
                output_path = input_path.with_suffix(input_path.suffix + self.extension)
            else:
                output_path = Path(output_path)
            
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            original_size = input_path.stat().st_size
            original_checksum = self._calculate_checksum(input_path)
            
            logger.debug(f"Compressing {input_path} -> {output_path}")
            
            if self.use_zstd:
                self._compress_zstd(input_path, output_path)
            else:
                self._compress_gzip(input_path, output_path)
            
            compressed_size = output_path.stat().st_size
            compressed_checksum = self._calculate_checksum(output_path)
            
            compression_ratio = compressed_size / original_size if original_size > 0 else 0
            space_saved = original_size - compressed_size
            
            stats = {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "space_saved": space_saved,
                "space_saved_percent": (space_saved / original_size * 100) if original_size > 0 else 0,
                "original_checksum": original_checksum,
                "compressed_checksum": compressed_checksum,
                "compression_method": "zstd" if self.use_zstd else "gzip",
                "compression_level": self.compression_level
            }
            
            logger.info(f"Compression complete: {original_size} -> {compressed_size} bytes "
                       f"({compression_ratio:.2%} ratio, {space_saved} bytes saved)")
            
            return stats
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise
    
    def decompress_file(self, input_path: Path, output_path: Optional[Path] = None) -> Dict:
        """
        Decompress a file and return decompression statistics.
        
        Args:
            input_path: Path to compressed file
            output_path: Path to output file (auto-generated if None)
            
        Returns:
            Dict with decompression statistics
        """
        try:
            input_path = Path(input_path)
            if output_path is None:
                # Remove compression extension
                if input_path.suffix == '.zst':
                    output_path = input_path.with_suffix('')
                elif input_path.suffix == '.gz':
                    output_path = input_path.with_suffix('')
                else:
                    output_path = input_path.with_suffix('.decompressed')
            else:
                output_path = Path(output_path)
            
            if not input_path.exists():
                raise FileNotFoundError(f"Compressed file not found: {input_path}")
            
            compressed_size = input_path.stat().st_size
            compressed_checksum = self._calculate_checksum(input_path)
            
            logger.debug(f"Decompressing {input_path} -> {output_path}")
            
            # Detect compression method from extension
            if input_path.suffix == '.zst':
                self._decompress_zstd(input_path, output_path)
            elif input_path.suffix == '.gz':
                self._decompress_gzip(input_path, output_path)
            else:
                raise ValueError(f"Unknown compression format: {input_path.suffix}")
            
            decompressed_size = output_path.stat().st_size
            decompressed_checksum = self._calculate_checksum(output_path)
            
            stats = {
                "input_file": str(input_path),
                "output_file": str(output_path),
                "compressed_size": compressed_size,
                "decompressed_size": decompressed_size,
                "compressed_checksum": compressed_checksum,
                "decompressed_checksum": decompressed_checksum,
                "compression_method": "zstd" if input_path.suffix == '.zst' else "gzip"
            }
            
            logger.info(f"Decompression complete: {compressed_size} -> {decompressed_size} bytes")
            
            return stats
            
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise
    
    def compress_data(self, data: bytes) -> bytes:
        """
        Compress data in memory.
        
        Args:
            data: Raw data to compress
            
        Returns:
            Compressed data
        """
        try:
            if self.use_zstd:
                return self.compressor.compress(data)
            else:
                return gzip.compress(data, compresslevel=self.compression_level)
        except Exception as e:
            logger.error(f"Data compression failed: {e}")
            raise
    
    def decompress_data(self, compressed_data: bytes) -> bytes:
        """
        Decompress data in memory.
        
        Args:
            compressed_data: Compressed data
            
        Returns:
            Decompressed data
        """
        try:
            if self.use_zstd:
                return self.decompressor.decompress(compressed_data)
            else:
                return gzip.decompress(compressed_data)
        except Exception as e:
            logger.error(f"Data decompression failed: {e}")
            raise
    
    def _compress_zstd(self, input_path: Path, output_path: Path):
        """Compress file using ZSTD."""
        with open(input_path, 'rb') as input_file:
            with open(output_path, 'wb') as output_file:
                self.compressor.copy_stream(input_file, output_file)
    
    def _decompress_zstd(self, input_path: Path, output_path: Path):
        """Decompress ZSTD file."""
        with open(input_path, 'rb') as input_file:
            with open(output_path, 'wb') as output_file:
                self.decompressor.copy_stream(input_file, output_file)
    
    def _compress_gzip(self, input_path: Path, output_path: Path):
        """Compress file using gzip."""
        with open(input_path, 'rb') as input_file:
            with gzip.open(output_path, 'wb', compresslevel=self.compression_level) as output_file:
                while chunk := input_file.read(64 * 1024):  # 64KB chunks
                    output_file.write(chunk)
    
    def _decompress_gzip(self, input_path: Path, output_path: Path):
        """Decompress gzip file."""
        with gzip.open(input_path, 'rb') as input_file:
            with open(output_path, 'wb') as output_file:
                while chunk := input_file.read(64 * 1024):  # 64KB chunks
                    output_file.write(chunk)
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(64 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def get_compression_info(self) -> Dict:
        """
        Get compression engine information.
        
        Returns:
            Dict with compression engine details
        """
        return {
            "compression_method": "zstd" if self.use_zstd else "gzip",
            "compression_level": self.compression_level,
            "extension": self.extension,
            "zstd_available": ZSTD_AVAILABLE,
            "gzip_available": GZIP_AVAILABLE
        }
