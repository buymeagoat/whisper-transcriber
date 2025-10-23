"""
Transcript Search Service for T021: Implement transcript search functionality

This service provides comprehensive search capabilities across transcripts including:
- Full-text search within transcript content
- Metadata-based filtering (keywords, language, duration, etc.)
- Advanced query parsing with boolean operators
- Search result ranking and relevance scoring
- Performance-optimized search with caching
"""

import os
import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text, desc

from api.models import Job, JobStatusEnum, TranscriptMetadata, User
from api.settings import settings
from api.utils.logger import get_system_logger

logger = get_system_logger("transcript_search")


class SearchType(str, Enum):
    """Types of search operations"""
    FULL_TEXT = "full_text"
    METADATA = "metadata"
    COMBINED = "combined"
    ADVANCED = "advanced"


class SortOrder(str, Enum):
    """Sort order options for search results"""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    DURATION_DESC = "duration_desc"
    DURATION_ASC = "duration_asc"
    FILENAME = "filename"


@dataclass
class SearchFilters:
    """Search filters for advanced queries"""
    languages: Optional[List[str]] = None
    models: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    duration_min: Optional[int] = None  # seconds
    duration_max: Optional[int] = None  # seconds
    sentiment_min: Optional[float] = None
    sentiment_max: Optional[float] = None
    has_keywords: Optional[bool] = None
    has_summary: Optional[bool] = None


@dataclass
class SearchResult:
    """Individual search result with metadata and relevance scoring"""
    job_id: str
    filename: str
    transcript_snippet: str
    full_transcript: Optional[str] = None
    relevance_score: float = 0.0
    created_at: datetime = None
    model: str = None
    language: Optional[str] = None
    duration: Optional[int] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    sentiment: Optional[float] = None
    matches: List[Dict[str, Any]] = None  # Highlighted text matches
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        return result


@dataclass
class SearchResponse:
    """Complete search response with results and metadata"""
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    query: str
    filters: Dict[str, Any]
    page: int
    page_size: int
    sort_order: SortOrder


class TranscriptSearchService:
    """
    Comprehensive transcript search service with full-text search,
    metadata filtering, and advanced query capabilities.
    """
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache for frequent searches
        self.cache_ttl = 300  # 5 minutes cache TTL
        
    def search(
        self, 
        query: str,
        db: Session,
        user_id: Optional[int] = None,
        search_type: SearchType = SearchType.COMBINED,
        filters: Optional[SearchFilters] = None,
        sort_order: SortOrder = SortOrder.RELEVANCE,
        page: int = 1,
        page_size: int = 20
    ) -> SearchResponse:
        """
        Main search method that orchestrates different search types
        
        Args:
            query: Search query string
            db: Database session
            user_id: Optional user ID for user-specific searches
            search_type: Type of search to perform
            filters: Optional search filters
            sort_order: Sort order for results
            page: Page number (1-based)
            page_size: Number of results per page
            
        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(
                query, user_id, search_type, filters, sort_order, page, page_size
            )
            
            # Check cache first
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for search query: {query[:50]}")
                return cached_result
            
            # Perform search based on type
            if search_type == SearchType.FULL_TEXT:
                results, total = self._search_full_text(query, db, user_id, filters)
            elif search_type == SearchType.METADATA:
                results, total = self._search_metadata(query, db, user_id, filters)
            elif search_type == SearchType.ADVANCED:
                results, total = self._search_advanced(query, db, user_id, filters)
            else:  # COMBINED
                results, total = self._search_combined(query, db, user_id, filters)
            
            # Sort results
            results = self._sort_results(results, sort_order)
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            paginated_results = results[start_idx:start_idx + page_size]
            
            # Create response
            search_time = (time.time() - start_time) * 1000  # Convert to ms
            response = SearchResponse(
                results=paginated_results,
                total_results=total,
                search_time_ms=search_time,
                query=query,
                filters=asdict(filters) if filters else {},
                page=page,
                page_size=page_size,
                sort_order=sort_order
            )
            
            # Cache the result
            self._cache_result(cache_key, response)
            
            logger.info(f"Search completed: {total} results in {search_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            # Return empty results on error
            return SearchResponse(
                results=[],
                total_results=0,
                search_time_ms=(time.time() - start_time) * 1000,
                query=query,
                filters=asdict(filters) if filters else {},
                page=page,
                page_size=page_size,
                sort_order=sort_order
            )
    
    def _search_combined(
        self, 
        query: str, 
        db: Session, 
        user_id: Optional[int], 
        filters: Optional[SearchFilters]
    ) -> Tuple[List[SearchResult], int]:
        """
        Combined search across transcript content and metadata
        """
        # Get base query with joins
        base_query = self._get_base_query(db, user_id, filters)
        
        # Prepare search terms
        search_terms = self._parse_search_terms(query)
        
        results = []
        
        # Execute query
        jobs = base_query.all()
        
        for job in jobs:
            # Calculate relevance score
            relevance_score = 0.0
            matches = []
            
            # Search in transcript file content
            transcript_content = self._get_transcript_content(job.transcript_path)
            if transcript_content:
                content_score, content_matches = self._search_text_content(
                    transcript_content, search_terms
                )
                relevance_score += content_score * 0.7  # Weight content highly
                matches.extend(content_matches)
            
            # Search in metadata
            metadata_score, metadata_matches = self._search_job_metadata(
                job, search_terms
            )
            relevance_score += metadata_score * 0.3
            matches.extend(metadata_matches)
            
            # Only include results with matches
            if relevance_score > 0:
                # Create search result
                result = SearchResult(
                    job_id=job.id,
                    filename=job.original_filename,
                    transcript_snippet=self._create_snippet(transcript_content, search_terms),
                    relevance_score=relevance_score,
                    created_at=job.created_at,
                    model=job.model,
                    language=job.transcript_metadata[0].language if job.transcript_metadata else None,
                    duration=job.transcript_metadata[0].duration if job.transcript_metadata else None,
                    keywords=self._parse_keywords(job.transcript_metadata[0].keywords) if job.transcript_metadata else None,
                    summary=job.transcript_metadata[0].summary if job.transcript_metadata else None,
                    sentiment=job.transcript_metadata[0].sentiment if job.transcript_metadata else None,
                    matches=matches
                )
                results.append(result)
        
        return results, len(results)
    
    def _search_full_text(
        self, 
        query: str, 
        db: Session, 
        user_id: Optional[int], 
        filters: Optional[SearchFilters]
    ) -> Tuple[List[SearchResult], int]:
        """
        Full-text search within transcript content
        """
        base_query = self._get_base_query(db, user_id, filters)
        jobs = base_query.all()
        
        search_terms = self._parse_search_terms(query)
        results = []
        
        for job in jobs:
            transcript_content = self._get_transcript_content(job.transcript_path)
            if not transcript_content:
                continue
                
            score, matches = self._search_text_content(transcript_content, search_terms)
            if score > 0:
                result = SearchResult(
                    job_id=job.id,
                    filename=job.original_filename,
                    transcript_snippet=self._create_snippet(transcript_content, search_terms),
                    full_transcript=transcript_content,
                    relevance_score=score,
                    created_at=job.created_at,
                    model=job.model,
                    language=job.transcript_metadata[0].language if job.transcript_metadata else None,
                    duration=job.transcript_metadata[0].duration if job.transcript_metadata else None,
                    matches=matches
                )
                results.append(result)
        
        return results, len(results)
    
    def _search_metadata(
        self, 
        query: str, 
        db: Session, 
        user_id: Optional[int], 
        filters: Optional[SearchFilters]
    ) -> Tuple[List[SearchResult], int]:
        """
        Search within metadata fields (keywords, summary, etc.)
        """
        base_query = self._get_base_query(db, user_id, filters)
        jobs = base_query.all()
        
        search_terms = self._parse_search_terms(query)
        results = []
        
        for job in jobs:
            score, matches = self._search_job_metadata(job, search_terms)
            if score > 0:
                result = SearchResult(
                    job_id=job.id,
                    filename=job.original_filename,
                    transcript_snippet=self._create_metadata_snippet(job, search_terms),
                    relevance_score=score,
                    created_at=job.created_at,
                    model=job.model,
                    language=job.transcript_metadata[0].language if job.transcript_metadata else None,
                    duration=job.transcript_metadata[0].duration if job.transcript_metadata else None,
                    keywords=self._parse_keywords(job.transcript_metadata[0].keywords) if job.transcript_metadata else None,
                    summary=job.transcript_metadata[0].summary if job.transcript_metadata else None,
                    sentiment=job.transcript_metadata[0].sentiment if job.transcript_metadata else None,
                    matches=matches
                )
                results.append(result)
        
        return results, len(results)
    
    def _search_advanced(
        self, 
        query: str, 
        db: Session, 
        user_id: Optional[int], 
        filters: Optional[SearchFilters]
    ) -> Tuple[List[SearchResult], int]:
        """
        Advanced search with boolean operators and phrase matching
        """
        # Parse advanced query syntax
        parsed_query = self._parse_advanced_query(query)
        
        # Use combined search but with advanced query parsing
        return self._search_combined_advanced(parsed_query, db, user_id, filters)
    
    def _get_base_query(self, db: Session, user_id: Optional[int], filters: Optional[SearchFilters]):
        """
        Build base SQL query with filters and joins
        """
        query = db.query(Job).options(joinedload(Job.transcript_metadata)).filter(
            Job.status == JobStatusEnum.COMPLETED,
            Job.transcript_path.isnot(None)
        )
        
        # Apply user filter if provided (for user-specific searches)
        if user_id:
            # Note: Need to add user_id to Job model if implementing user-specific transcripts
            pass
        
        # Apply filters
        if filters:
            if filters.languages:
                query = query.join(TranscriptMetadata).filter(
                    TranscriptMetadata.language.in_(filters.languages)
                )
            
            if filters.models:
                query = query.filter(Job.model.in_(filters.models))
            
            if filters.date_from:
                query = query.filter(Job.created_at >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(Job.created_at <= filters.date_to)
            
            if filters.duration_min or filters.duration_max:
                query = query.join(TranscriptMetadata)
                if filters.duration_min:
                    query = query.filter(TranscriptMetadata.duration >= filters.duration_min)
                if filters.duration_max:
                    query = query.filter(TranscriptMetadata.duration <= filters.duration_max)
            
            if filters.sentiment_min is not None or filters.sentiment_max is not None:
                query = query.join(TranscriptMetadata)
                if filters.sentiment_min is not None:
                    query = query.filter(TranscriptMetadata.sentiment >= filters.sentiment_min)
                if filters.sentiment_max is not None:
                    query = query.filter(TranscriptMetadata.sentiment <= filters.sentiment_max)
            
            if filters.has_keywords is not None:
                query = query.join(TranscriptMetadata)
                if filters.has_keywords:
                    query = query.filter(TranscriptMetadata.keywords.isnot(None))
                else:
                    query = query.filter(TranscriptMetadata.keywords.is_(None))
            
            if filters.has_summary is not None:
                query = query.join(TranscriptMetadata)
                if filters.has_summary:
                    query = query.filter(TranscriptMetadata.summary.isnot(None))
                else:
                    query = query.filter(TranscriptMetadata.summary.is_(None))
        
        return query
    
    def _get_transcript_content(self, transcript_path: Optional[str]) -> Optional[str]:
        """
        Read transcript content from file
        """
        if not transcript_path or not os.path.exists(transcript_path):
            return None
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading transcript file {transcript_path}: {e}")
            return None
    
    def _parse_search_terms(self, query: str) -> List[str]:
        """
        Parse search query into terms, handling quotes for phrases
        """
        # Handle quoted phrases
        phrases = re.findall(r'"([^"]*)"', query)
        
        # Remove quoted phrases from query and split remaining terms
        remaining_query = re.sub(r'"[^"]*"', '', query)
        terms = remaining_query.strip().split()
        
        # Combine phrases and individual terms
        return phrases + [term.lower() for term in terms if len(term) > 1]
    
    def _search_text_content(self, content: str, search_terms: List[str]) -> Tuple[float, List[Dict]]:
        """
        Search for terms in text content and calculate relevance score
        """
        if not content or not search_terms:
            return 0.0, []
        
        content_lower = content.lower()
        matches = []
        total_score = 0.0
        
        for term in search_terms:
            term_lower = term.lower()
            count = content_lower.count(term_lower)
            if count > 0:
                # Calculate TF-IDF-like score
                term_score = min(count * 0.1, 1.0)  # Cap at 1.0
                total_score += term_score
                
                # Find match positions for highlighting
                match_positions = []
                start = 0
                while True:
                    pos = content_lower.find(term_lower, start)
                    if pos == -1:
                        break
                    match_positions.append({
                        'term': term,
                        'position': pos,
                        'length': len(term)
                    })
                    start = pos + 1
                
                matches.append({
                    'term': term,
                    'count': count,
                    'positions': match_positions[:10]  # Limit to first 10 matches
                })
        
        return total_score, matches
    
    def _search_job_metadata(self, job: Job, search_terms: List[str]) -> Tuple[float, List[Dict]]:
        """
        Search within job metadata fields
        """
        matches = []
        total_score = 0.0
        
        if not job.transcript_metadata:
            return 0.0, []
        
        metadata = job.transcript_metadata[0]
        
        # Search in keywords
        if metadata.keywords:
            keywords_score, keywords_matches = self._search_text_content(
                metadata.keywords, search_terms
            )
            total_score += keywords_score * 2.0  # Weight keywords higher
            if keywords_matches:
                matches.append({
                    'field': 'keywords',
                    'matches': keywords_matches
                })
        
        # Search in summary
        if metadata.summary:
            summary_score, summary_matches = self._search_text_content(
                metadata.summary, search_terms
            )
            total_score += summary_score * 1.5  # Weight summary moderately
            if summary_matches:
                matches.append({
                    'field': 'summary',
                    'matches': summary_matches
                })
        
        # Search in filename
        filename_score, filename_matches = self._search_text_content(
            job.original_filename, search_terms
        )
        total_score += filename_score * 0.8
        if filename_matches:
            matches.append({
                'field': 'filename',
                'matches': filename_matches
            })
        
        return total_score, matches
    
    def _create_snippet(self, content: str, search_terms: List[str], max_length: int = 300) -> str:
        """
        Create a snippet of text around the first match
        """
        if not content or not search_terms:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        content_lower = content.lower()
        
        # Find first match position
        first_match_pos = float('inf')
        for term in search_terms:
            pos = content_lower.find(term.lower())
            if pos != -1 and pos < first_match_pos:
                first_match_pos = pos
        
        if first_match_pos == float('inf'):
            # No matches found, return beginning
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # Create snippet around first match
        start = max(0, first_match_pos - max_length // 3)
        end = min(len(content), start + max_length)
        
        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _create_metadata_snippet(self, job: Job, search_terms: List[str]) -> str:
        """
        Create snippet from metadata fields
        """
        if not job.transcript_metadata:
            return f"File: {job.original_filename}"
        
        metadata = job.transcript_metadata[0]
        
        # Prioritize summary if available
        if metadata.summary:
            return self._create_snippet(metadata.summary, search_terms, 200)
        
        # Fall back to keywords
        if metadata.keywords:
            return f"Keywords: {metadata.keywords}"
        
        return f"File: {job.original_filename} ({metadata.duration}s)"
    
    def _parse_keywords(self, keywords_str: Optional[str]) -> Optional[List[str]]:
        """
        Parse keywords string into list
        """
        if not keywords_str:
            return None
        
        # Handle different formats (comma-separated, JSON, etc.)
        try:
            # Try JSON first
            return json.loads(keywords_str)
        except:
            # Fall back to comma-separated
            return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
    
    def _sort_results(self, results: List[SearchResult], sort_order: SortOrder) -> List[SearchResult]:
        """
        Sort search results based on specified order
        """
        if sort_order == SortOrder.RELEVANCE:
            return sorted(results, key=lambda r: r.relevance_score, reverse=True)
        elif sort_order == SortOrder.DATE_DESC:
            return sorted(results, key=lambda r: r.created_at or datetime.min, reverse=True)
        elif sort_order == SortOrder.DATE_ASC:
            return sorted(results, key=lambda r: r.created_at or datetime.max)
        elif sort_order == SortOrder.DURATION_DESC:
            return sorted(results, key=lambda r: r.duration or 0, reverse=True)
        elif sort_order == SortOrder.DURATION_ASC:
            return sorted(results, key=lambda r: r.duration or float('inf'))
        elif sort_order == SortOrder.FILENAME:
            return sorted(results, key=lambda r: r.filename.lower())
        else:
            return results
    
    def _parse_advanced_query(self, query: str) -> Dict[str, Any]:
        """
        Parse advanced query syntax (AND, OR, NOT, phrases)
        """
        # Placeholder for advanced query parsing
        # This would implement boolean logic parsing
        return {
            'terms': self._parse_search_terms(query),
            'operators': [],
            'phrases': re.findall(r'"([^"]*)"', query)
        }
    
    def _search_combined_advanced(
        self, 
        parsed_query: Dict[str, Any], 
        db: Session, 
        user_id: Optional[int], 
        filters: Optional[SearchFilters]
    ) -> Tuple[List[SearchResult], int]:
        """
        Perform advanced search with parsed boolean query
        """
        # For now, fall back to combined search
        # This would implement advanced boolean logic
        query_str = ' '.join(parsed_query['terms'])
        return self._search_combined(query_str, db, user_id, filters)
    
    def _generate_cache_key(self, *args) -> str:
        """
        Generate cache key from search parameters
        """
        return str(hash(str(args)))
    
    def _get_cached_result(self, cache_key: str) -> Optional[SearchResponse]:
        """
        Get cached search result if still valid
        """
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, response: SearchResponse):
        """
        Cache search result
        """
        self.cache[cache_key] = (response, time.time())
        
        # Simple cache cleanup - remove oldest entries if cache gets too large
        if len(self.cache) > 100:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def get_search_suggestions(self, partial_query: str, db: Session, limit: int = 10) -> List[str]:
        """
        Get search suggestions based on partial query
        """
        suggestions = set()
        
        # Get keywords from metadata
        keyword_results = db.query(TranscriptMetadata.keywords).filter(
            TranscriptMetadata.keywords.isnot(None)
        ).limit(100).all()
        
        for result in keyword_results:
            if result.keywords:
                keywords = self._parse_keywords(result.keywords)
                if keywords:
                    for keyword in keywords:
                        if partial_query.lower() in keyword.lower():
                            suggestions.add(keyword)
        
        # Get common words from filenames
        filename_results = db.query(Job.original_filename).filter(
            Job.original_filename.contains(partial_query)
        ).limit(50).all()
        
        for result in filename_results:
            # Extract words from filename
            words = re.findall(r'\b\w+\b', result.original_filename.lower())
            for word in words:
                if partial_query.lower() in word and len(word) > 2:
                    suggestions.add(word)
        
        return sorted(list(suggestions))[:limit]


# Global search service instance
transcript_search_service = TranscriptSearchService()