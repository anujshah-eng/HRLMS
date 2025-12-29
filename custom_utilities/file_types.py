class FileTypes:
    allowed_image_types = {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
    }

    allowed_document_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/json"
    }

    allowed_types = allowed_document_types | allowed_image_types

    @staticmethod
    def is_allowed(content_type: str) -> bool:
        return content_type in FileTypes.allowed_types
