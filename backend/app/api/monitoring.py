from fastapi import APIRouter
from app.monitoring.system import MonitoringService
from app.schemas.monitoring import MonitoringOverview, AudioEngineStatus, StorageUsage

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/overview", response_model=MonitoringOverview)
def get_overview():
    return MonitoringService.get_overview()

@router.get("/engine", response_model=AudioEngineStatus)
def get_engine_status():
    return MonitoringService.get_engine_status()

@router.get("/storage", response_model=StorageUsage)
def get_storage_usage():
    return MonitoringService.get_storage_usage()
