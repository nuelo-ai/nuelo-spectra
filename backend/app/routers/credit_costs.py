"""GET /credit-costs — live credit cost config for frontend consumption."""
import json
from fastapi import APIRouter
from pydantic import BaseModel

from app.dependencies import CurrentUser, DbSession
from app.services import platform_settings as ps

router = APIRouter(prefix="/credit-costs", tags=["Credit Costs"])


class CreditCostsResponse(BaseModel):
    """Credit costs for frontend consumption.

    Designed for extensibility — v0.9+ adds investigate and whatif keys
    to this response without a breaking change.
    """

    chat: float
    pulse_run: float


@router.get("", response_model=CreditCostsResponse)
async def get_credit_costs(
    current_user: CurrentUser,
    db: DbSession,
) -> CreditCostsResponse:
    """Return current credit costs for chat and Pulse run.

    Values are read from platform_settings (30-second TTL cache).
    Stored as JSON-encoded strings — json.loads() is required.
    """
    settings = await ps.get_all(db)
    chat = float(json.loads(settings.get("default_credit_cost", '"1.0"')))
    pulse_run = float(json.loads(settings.get("workspace_credit_cost_pulse", '"5.0"')))
    return CreditCostsResponse(chat=chat, pulse_run=pulse_run)
