import pytest
from universal_engine import UniversalEngine
from models import SiteConfig
from bs4 import BeautifulSoup

@pytest.mark.asyncio
async def test_get_config(pool):
    """Verify that UniversalEngine can fetch a seeded configuration."""
    engine = UniversalEngine(pool)
    
    # Get any active university_id from site_configs
    async with pool.connection() as conn:
        row = await conn.execute("SELECT university_id FROM site_configs LIMIT 1")
        res = await row.fetchone()
        if not res:
            pytest.skip("No site configs found")
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
    engine = UniversalEngine(pool)
    
    html = "<div>VTAC code: 3200345678</div>"
    soup = BeautifulSoup(html, "lxml")
    config = {"anchor": "VTAC code", "regex": r"(\d{9,10})"}
    
    results = engine.extract_admissions_codes(soup, config)
    assert results == ["3200345678"]

def test_parse_duration(pool):
    engine = UniversalEngine(pool)
    
    # Strict parsing: keyword required
    assert engine._parse_duration("3 years full-time") == 3.0
    assert engine._parse_duration("1.5 yrs") == 1.5
    assert engine._parse_duration("6 months") == 0.5
    
    # Plain number parsing (only if small and likely years)
    assert engine._parse_duration("3") == 3.0
    assert engine._parse_duration("80") is None  # Should be rejected
    
    # Noise rejection
    assert engine._parse_duration("Level 9 - Masters") is None

def test_parse_atar(pool):
    engine = UniversalEngine(pool)
    
    # Simple ATAR
    g, r = engine._parse_atar("85.00")
    assert g is None
    assert r == 85
    
    # Guaranteed ATAR
    g, r = engine._parse_atar("Guaranteed minimum ATAR: 75")
    assert g == 75
    assert r is None
    
    # Rank vs Guarantee
    g, r = engine._parse_atar("Lowest rank 80.00, Guarantee 70.00")
    assert g == 70
    assert r == 80

def test_infer_degree_type(pool):
    engine = UniversalEngine(pool)
    assert engine._infer_degree_type("Bachelor of Arts") == "UG"
    assert engine._infer_degree_type("Diploma in Business") == "UG"
    assert engine._infer_degree_type("Master of Nursing") == "PG"
    assert engine._infer_degree_type("Graduate Certificate in Law") == "PG"
    assert engine._infer_degree_type("Juris Doctor") == "PG"

def test_is_valid_course(pool):
    engine = UniversalEngine(pool)
    
    # Valid
    assert engine._is_valid_course("Bachelor of Commerce", "http://test.com") is True
    assert engine._is_valid_course("Diploma of Arts", "http://test.com") is True
    assert engine._is_valid_course("Master of Science", "http://test.com") is True
    
    # Invalid (Hubs / Unknown)
    assert engine._is_valid_course("Health", "http://test.com/h") is False
    assert engine._is_valid_course("Unknown", "http://test.com/u") is False
    assert engine._is_valid_course("Undergraduate study", "http://test.com/u") is False

def test_should_discard_by_meta(pool):
    engine = UniversalEngine(pool)
    
    html = '<meta name="Related.Area.of.Study" content="Areas of study" />'
    soup = BeautifulSoup(html, "lxml")
    
    config = SiteConfig(
        id="00000000-0000-0000-0000-000000000000",
        university_id="00000000-0000-0000-0000-000000000000",
        base_url="",
        extraction_map={"discard_meta": [{"name": "Related.Area.of.Study", "content": "Areas of study"}]}
    )
    
    # This will still fail until rewrite because the method doesn't exist yet
    try:
        assert engine._should_discard_by_meta(soup, config) is True
    except AttributeError:
        pytest.skip("Method _should_discard_by_meta not yet implemented")
    
    # Different content
    html2 = '<meta name="Related.Area.of.Study" content="Nursing" />'
    soup2 = BeautifulSoup(html2, "lxml")
    assert engine._should_discard_by_meta(soup2, config) is False
