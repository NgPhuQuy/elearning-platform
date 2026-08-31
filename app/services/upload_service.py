import cloudinary.uploader


def upload_file(file_storage, folder="elearning-platform", public_id=None):
    if not file_storage or not getattr(file_storage, "filename", None):
        return None, None
    try:
        kwargs = {"folder": folder, "resource_type": "auto"}
        if public_id:
            kwargs["public_id"] = public_id
        res = cloudinary.uploader.upload(file_storage, **kwargs)
        return res.get("secure_url"), None
    except Exception as ex:
        return None, str(ex)

