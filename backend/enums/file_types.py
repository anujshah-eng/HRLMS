from enum import Enum

class FileType(str, Enum):
    JPEG = "jpeg"
    JPG = "jpg"
    PNG = "png"
    JSON = "json"
    WEBP = "webp"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

FILE_TYPE_TO_MIME_TYPE = {
    FileType.JPEG: "image/jpeg",
    FileType.JPG: "image/jpeg",
    FileType.PNG: "image/png",
    FileType.JSON: "application/json",
    FileType.WEBP: "image/webp",
    FileType.PDF: "application/pdf",
    FileType.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    FileType.TXT: "text/plain",
}
