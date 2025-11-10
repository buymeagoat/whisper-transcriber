"""Legacy upload endpoint aliases for frontend compatibility."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from api.orm_bootstrap import get_db
from api.routes import jobs as jobs_routes
from api.routes.dependencies import get_authenticated_user_id

router = APIRouter(tags=["uploads"])


@router.post("/upload", response_model=Dict[str, Any], include_in_schema=False)
async def legacy_upload_endpoint(
	request: Request,
	file: UploadFile = File(...),
	model: str = Form(default="small"),
	language: Optional[str] = Form(default=None),
	db: Session = Depends(get_db),
	user_id: str = Depends(get_authenticated_user_id)
) -> Dict[str, Any]:
	"""Compatibility endpoint forwarding to the canonical jobs upload route."""

	return await jobs_routes.create_job(request, file, model, language, db, user_id)


@router.post("/api/upload", response_model=Dict[str, Any], include_in_schema=False)
async def legacy_api_upload_endpoint(
	request: Request,
	file: UploadFile = File(...),
	model: str = Form(default="small"),
	language: Optional[str] = Form(default=None),
	db: Session = Depends(get_db),
	user_id: str = Depends(get_authenticated_user_id)
) -> Dict[str, Any]:
	"""Compatibility endpoint under the historical /api prefix."""

	return await jobs_routes.create_job(request, file, model, language, db, user_id)

