"""
Transcript Search API Endpoints for T021: Implement transcript search functionality

Provides RESTful API endpoints for searching transcripts with:
- Basic text search
- Advanced filtering and search options
- Search suggestions and autocomplete
- Search analytics and performance metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from api.orm_bootstrap import get_db
from api.services.transcript_search import (
    transcript_search_service,
    SearchType,
    SortOrder,
    SearchFilters,
    SearchResponse
)
from api.utils.logger import get_system_logger
from api.utils.log_sanitization import safe_log_format, sanitize_for_log

# T026 Security Hardening - Audit logging integration
from api.audit.integration import (
    audit_data_operation,
    extract_request_context
)

logger = get_system_logger("search_api")

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    """Request model for transcript search"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_type: SearchType = Field(default=SearchType.COMBINED, description="Type of search to perform")
    sort_order: SortOrder = Field(default=SortOrder.RELEVANCE, description="Sort order for results")
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of results per page")
    
    # Filter options
    languages: Optional[List[str]] = Field(default=None, description="Filter by languages")
    models: Optional[List[str]] = Field(default=None, description="Filter by Whisper models")
    date_from: Optional[datetime] = Field(default=None, description="Filter results from this date")
    date_to: Optional[datetime] = Field(default=None, description="Filter results until this date")
    duration_min: Optional[int] = Field(default=None, ge=0, description="Minimum duration in seconds")
    duration_max: Optional[int] = Field(default=None, ge=0, description="Maximum duration in seconds")
    sentiment_min: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Minimum sentiment score")
    sentiment_max: Optional[float] = Field(default=None, ge=-1.0, le=1.0, description="Maximum sentiment score")
    has_keywords: Optional[bool] = Field(default=None, description="Filter by presence of keywords")
    has_summary: Optional[bool] = Field(default=None, description="Filter by presence of summary")


class SearchResultResponse(BaseModel):
    """Response model for search results"""
    job_id: str
    filename: str
    transcript_snippet: str
    relevance_score: float
    created_at: Optional[datetime]
    model: Optional[str]
    language: Optional[str]
    duration: Optional[int]
    keywords: Optional[List[str]]
    summary: Optional[str]
    sentiment: Optional[float]
    matches: Optional[List[Dict[str, Any]]]


class SearchResponse(BaseModel):
    """Complete search response model"""
    results: List[SearchResultResponse]
    total_results: int
    search_time_ms: float
    query: str
    filters: Dict[str, Any]
    page: int
    page_size: int
    sort_order: SortOrder
    
    # Additional metadata
    suggested_queries: Optional[List[str]] = None
    search_id: Optional[str] = None  # For analytics tracking


class SearchSuggestionsResponse(BaseModel):
    """Response model for search suggestions"""
    suggestions: List[str]
    query: str


class SearchStatsResponse(BaseModel):
    """Response model for search statistics"""
    total_searchable_transcripts: int
    total_search_volume: int
    average_search_time_ms: float
    popular_terms: List[Dict[str, Any]]
    recent_searches: List[str]


@router.post("/", response_model=SearchResponse)
async def search_transcripts(
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Search transcripts with advanced filtering and sorting options
    
    Supports multiple search types:
    - **combined**: Search both content and metadata (default)
    - **full_text**: Search only within transcript content  
    - **metadata**: Search only within metadata fields
    - **advanced**: Advanced search with boolean operators
    
    Returns paginated results with relevance scoring and match highlighting.
    """
    try:
        # Extract user context for auditing
        user_context = extract_request_context(request)
        user_id = user_context.get("user_id")
        
        # Create search filters
        filters = SearchFilters(
            languages=search_request.languages,
            models=search_request.models,
            date_from=search_request.date_from,
            date_to=search_request.date_to,
            duration_min=search_request.duration_min,
            duration_max=search_request.duration_max,
            sentiment_min=search_request.sentiment_min,
            sentiment_max=search_request.sentiment_max,
            has_keywords=search_request.has_keywords,
            has_summary=search_request.has_summary
        )
        
        # Perform search
        search_response = transcript_search_service.search(
            query=search_request.query,
            db=db,
            user_id=user_id,
            search_type=search_request.search_type,
            filters=filters,
            sort_order=search_request.sort_order,
            page=search_request.page,
            page_size=search_request.page_size
        )
        
        # Audit the search operation
        audit_data_operation(
            user_id=user_id or "anonymous",
            action="search",
            resource=f"transcripts",
            request=request,
            success=True,
            details={
                "query": search_request.query[:100],  # Limit query length in logs
                "search_type": search_request.search_type.value,
                "results_count": search_response.total_results,
                "search_time_ms": search_response.search_time_ms
            }
        )
        
        # Convert results to response format
        response_results = []
        for result in search_response.results:
            response_results.append(SearchResultResponse(**result.to_dict()))
        
        # Get search suggestions for improved UX
        suggestions = transcript_search_service.get_search_suggestions(
            search_request.query, db, limit=5
        )
        
        logger.info(safe_log_format(
            "Search completed: query='{}' results={} time={:.2f}ms",
            sanitize_for_log(search_request.query[:50]),
            sanitize_for_log(search_response.total_results),
            sanitize_for_log(search_response.search_time_ms)
        ))
        
        return SearchResponse(
            results=response_results,
            total_results=search_response.total_results,
            search_time_ms=search_response.search_time_ms,
            query=search_response.query,
            filters=search_response.filters,
            page=search_response.page,
            page_size=search_response.page_size,
            sort_order=search_response.sort_order,
            suggested_queries=suggestions,
            search_id=f"search_{int(datetime.now().timestamp())}"
        )
        
    except Exception as e:
        logger.error(safe_log_format("Search error: {}", sanitize_for_log(str(e))))
        
        # Audit the failed search
        audit_data_operation(
            user_id=user_context.get("user_id", "anonymous"),
            action="search",
            resource="transcripts",
            request=request,
            success=False,
            details={"error": str(e)[:200]}
        )
        
        raise HTTPException(
            status_code=500,
            detail="Search operation failed. Please try again."
        )


@router.get("/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=2, max_length=100, description="Partial query for suggestions"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """
    Get search suggestions based on partial query
    
    Returns relevant keywords, terms, and phrases from:
    - Transcript metadata keywords
    - Common words in filenames  
    - Popular search terms
    """
    try:
        suggestions = transcript_search_service.get_search_suggestions(q, db, limit)
        
        logger.debug(safe_log_format(
            "Search suggestions: query='{}' suggestions={}",
            sanitize_for_log(q),
            sanitize_for_log(len(suggestions))
        ))
        
        return SearchSuggestionsResponse(
            suggestions=suggestions,
            query=q
        )
        
    except Exception as e:
        logger.error(safe_log_format("Search suggestions error: {}", sanitize_for_log(str(e))))
        raise HTTPException(
            status_code=500,
            detail="Failed to get search suggestions"
        )


@router.get("/quick")
async def quick_search(
    q: str = Query(..., min_length=1, max_length=200, description="Quick search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Quick search endpoint for autocomplete and instant results
    
    Optimized for speed with:
    - Smaller result limit
    - Metadata-only search  
    - Minimal response fields
    - Aggressive caching
    """
    try:
        # Use metadata search for speed
        search_response = transcript_search_service.search(
            query=q,
            db=db,
            search_type=SearchType.METADATA,
            sort_order=SortOrder.RELEVANCE,
            page=1,
            page_size=limit
        )
        
        # Return simplified results for speed
        quick_results = []
        for result in search_response.results:
            quick_results.append({
                "job_id": result.job_id,
                "filename": result.filename,
                "snippet": result.transcript_snippet,
                "relevance": round(result.relevance_score, 2)
            })
        
        return {
            "results": quick_results,
            "total": search_response.total_results,
            "search_time_ms": search_response.search_time_ms,
            "query": q
        }
        
    except Exception as e:
        logger.error(safe_log_format("Quick search error: {}", sanitize_for_log(str(e))))
        raise HTTPException(
            status_code=500,
            detail="Quick search failed"
        )


@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_statistics(
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Get search system statistics and analytics
    
    Returns:
    - Total searchable transcripts
    - Search performance metrics
    - Popular search terms
    - System health indicators
    """
    try:
        # Extract user context for authorization
        user_context = extract_request_context(request)
        
        # Get searchable transcript count
        from api.models import Job, JobStatusEnum
        searchable_count = db.query(Job).filter(
            Job.status == JobStatusEnum.COMPLETED,
            Job.transcript_path.isnot(None)
        ).count()
        
        # Placeholder for additional statistics
        # In a production system, you'd track these metrics in a dedicated table
        stats = SearchStatsResponse(
            total_searchable_transcripts=searchable_count,
            total_search_volume=0,  # Would track in analytics table
            average_search_time_ms=0.0,  # Would calculate from metrics
            popular_terms=[],  # Would extract from search logs
            recent_searches=[]  # Would get from recent search history
        )
        
        logger.info(safe_log_format(
            "Search stats requested: searchable_transcripts={}",
            sanitize_for_log(searchable_count)
        ))
        
        return stats
        
    except Exception as e:
        logger.error(safe_log_format("Search stats error: {}", sanitize_for_log(str(e))))
        raise HTTPException(
            status_code=500,
            detail="Failed to get search statistics"
        )


@router.get("/filters")
async def get_search_filters(db: Session = Depends(get_db)):
    """
    Get available filter options for search
    
    Returns dynamic filter options based on available data:
    - Available languages
    - Available Whisper models
    - Date ranges
    - Duration ranges
    """
    try:
        from api.models import Job, TranscriptMetadata
        from sqlalchemy import func
        
        # Get available languages
        languages = db.query(TranscriptMetadata.language).distinct().filter(
            TranscriptMetadata.language.isnot(None)
        ).all()
        available_languages = [lang[0] for lang in languages if lang[0]]
        
        # Get available models
        models = db.query(Job.model).distinct().all()
        available_models = [model[0] for model in models if model[0]]
        
        # Get date range
        date_range = db.query(
            func.min(Job.created_at).label('min_date'),
            func.max(Job.created_at).label('max_date')
        ).first()
        
        # Get duration range
        duration_range = db.query(
            func.min(TranscriptMetadata.duration).label('min_duration'),
            func.max(TranscriptMetadata.duration).label('max_duration')
        ).first()
        
        return {
            "languages": sorted(available_languages),
            "models": sorted(available_models),
            "date_range": {
                "min": date_range.min_date.isoformat() if date_range.min_date else None,
                "max": date_range.max_date.isoformat() if date_range.max_date else None
            },
            "duration_range": {
                "min": duration_range.min_duration if duration_range.min_duration else 0,
                "max": duration_range.max_duration if duration_range.max_duration else 0
            },
            "search_types": [
                {"value": "combined", "label": "Combined (Content + Metadata)"},
                {"value": "full_text", "label": "Full Text Search"},
                {"value": "metadata", "label": "Metadata Only"},
                {"value": "advanced", "label": "Advanced Search"}
            ],
            "sort_options": [
                {"value": "relevance", "label": "Relevance"},
                {"value": "date_desc", "label": "Newest First"},
                {"value": "date_asc", "label": "Oldest First"},
                {"value": "duration_desc", "label": "Longest First"},
                {"value": "duration_asc", "label": "Shortest First"},
                {"value": "filename", "label": "Filename A-Z"}
            ]
        }
        
    except Exception as e:
        logger.error(safe_log_format("Get search filters error: {}", sanitize_for_log(str(e))))
        raise HTTPException(
            status_code=500,
            detail="Failed to get search filter options"
        )