"""Admin API endpoints."""
from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate-demo-data")
async def generate_demo_data():
    """Generate demo data. Runs the seed script."""
    try:
        from app.scripts.seed_demo_data import seed_database
        await seed_database(num_transactions=10000)
        return {"status": "success", "message": "Demo data generated successfully (10,000 transactions)"}
    except Exception as e:
        logger.error(f"Failed to generate demo data: {e}")
        return {"status": "error", "message": str(e)}
