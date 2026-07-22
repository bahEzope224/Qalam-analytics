"""
Export centralisé des schémas Pydantic.
"""

from app.schemas.site import (
    SiteBase,
    SiteCreate,
    SiteUpdate,
    SiteSchema,
    SiteDashboardCard,
    SiteStatusUpdate,
)
from app.schemas.metrics import (
    AcquisitionSources,
    TopPage,
    TrafficDataPoint,
    SiteKPIs,
    SiteDetailMetrics,
    GlobalMetrics,
    SiteListMetrics,
    ReportSiteSummary,
    ReportResponse,
)
from app.schemas.auth import (
    TokenSchema,
    TokenPayload,
    LoginRequest,
    UserSchema,
)

__all__ = [
    # Site
    "SiteBase", "SiteCreate", "SiteUpdate",
    "SiteSchema", "SiteDashboardCard", "SiteStatusUpdate",
    # Metrics
    "AcquisitionSources", "TopPage", "TrafficDataPoint",
    "SiteKPIs", "SiteDetailMetrics", "GlobalMetrics",
    "SiteListMetrics", "ReportSiteSummary", "ReportResponse",
    # Auth
    "TokenSchema", "TokenPayload", "LoginRequest", "UserSchema",
]
