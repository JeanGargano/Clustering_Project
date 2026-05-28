from typing import Any, Optional
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    job_id:    str
    filename:  str
    status:    str               


class RunClusteringResponse(BaseModel):
    job_id:      str
    model_type:  str
    status:      str                


class JobStatusResponse(BaseModel):
    job_id:          str
    status:          str
    filename:        Optional[str] = None
    minio_path:      Optional[str] = None
    error:           Optional[str] = None
    runs:            Optional[dict[str, Any]] = None


class AnalysisResponse(BaseModel):
    job_id:      str
    model_type:  str
    status:      str
    analysis:    Optional[str] = None