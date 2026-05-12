from app.core.meta_stats import META_STATS


def test_meta_stats_shape_when_loaded():
    for key, stat in META_STATS.items():
        assert "p05" in stat
        assert "p95" in stat
        assert stat["p05"] < stat["p95"], key
