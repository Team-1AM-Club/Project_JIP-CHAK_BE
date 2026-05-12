def test_repository_modules_importable():
    from app.repositories import congestion_repo, flood_repo, medical_repo, noise_repo, security_repo

    assert congestion_repo
    assert flood_repo
    assert medical_repo
    assert noise_repo
    assert security_repo
