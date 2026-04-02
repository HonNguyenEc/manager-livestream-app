class ErrorCode:
    # Runtime/module-level
    MODULE_START_FAILED = "MODULE_START_FAILED"
    MODULE_STOP_FAILED = "MODULE_STOP_FAILED"
    MODULE_NOT_FOUND = "MODULE_NOT_FOUND"

    # Livestream business-level
    CONFIG_MISSING = "CONFIG_MISSING"
    USER_ID_REQUIRED = "USER_ID_REQUIRED"
    TITLE_REQUIRED = "TITLE_REQUIRED"
    COVER_URL_REQUIRED = "COVER_URL_REQUIRED"
    EXTRA_JSON_INVALID = "EXTRA_JSON_INVALID"
    REFRESH_CONFIG_MISSING = "REFRESH_CONFIG_MISSING"


ERROR_MESSAGES = {
    ErrorCode.MODULE_START_FAILED: "Không thể khởi động module",
    ErrorCode.MODULE_STOP_FAILED: "Không thể dừng module",
    ErrorCode.MODULE_NOT_FOUND: "Không tìm thấy module",
    ErrorCode.CONFIG_MISSING: "Thiếu config: Host / Partner ID / Partner Key / Shop ID / Access Token",
    ErrorCode.USER_ID_REQUIRED: "Create Session yêu cầu USER_ID theo tài liệu API",
    ErrorCode.TITLE_REQUIRED: "Thiếu title (bắt buộc)",
    ErrorCode.COVER_URL_REQUIRED: "Thiếu cover_image_url (bắt buộc)",
    ErrorCode.EXTRA_JSON_INVALID: "Extra JSON phải là object",
    ErrorCode.REFRESH_CONFIG_MISSING: "Thiếu config refresh: Host / Partner ID / Partner Key / Shop ID / Refresh Token",
}


UI_MESSAGES = {
    "save_success": "Đã lưu cấu hình .env",
    "token_refresh_success": "Đã refresh token và cập nhật .env",
}


def err(code: str) -> str:
    return ERROR_MESSAGES.get(code, code)
