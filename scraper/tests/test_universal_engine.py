import pytest
from universal_engine import UniversalEngine
from models import SiteConfig

@pytest.mark.asyncio
async def test_get_config(pool):
    """Verify that UniversalEngine can fetch a seeded configuration."""
    engine = UniversalEngine(pool)
    
    # Get any active university_id from site_configs
    async with pool.connection() as conn:
        row = await conn.execute("SELECT university_id FROM site_configs LIMIT 1")
        res = await row.fetchone()
        uni_id = str(res[0])
    
    config = await engine.get_config(uni_id)
    
    assert isinstance(config, SiteConfig)
    assert str(config.university_id) == uni_id
    assert config.is_active is True
    assert config.extraction_map is not None

@pytest.mark.asyncio
async def test_get_config_not_found(pool):
    """Verify that get_config raises ValueError for missing/inactive IDs."""
    engine = UniversalEngine(pool)
    
    # Use a random UUID that doesn't exist
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    with pytest.raises(ValueError, match="No active SiteConfig found"):
        await engine.get_config(fake_id)

@pytest.mark.asyncio
async def test_visual_anchor(pool):
    """Verify that find_by_anchor can locate data near a label."""
    from bs4 import BeautifulSoup
    engine = UniversalEngine(pool)
    
    html = """
    <div>
        <span class="label">ATAR</span>
        <span class="value">85.00</span>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    result = engine.find_by_anchor(soup, "ATAR")
    assert result == "85.00"

@pytest.mark.asyncio
async def test_extract_admissions_codes(pool):
    """Verify that extract_admissions_codes finds codes via anchor or regex."""
    from bs4 import BeautifulSoup
    engine = UniversalEngine(pool)
    
    html = "<div>VTAC code: 3200345678</div>"
    soup = BeautifulSoup(html, "lxml")
    config = {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
    
    results = engine.extract_admissions_codes(soup, config)
    assert results == ["3200345678"]
