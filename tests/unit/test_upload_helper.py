from app.services.upload_service import upload_file


def test_upload_helper_handles_empty():
    url, err = upload_file(None)
    assert url is None
    assert err is None
