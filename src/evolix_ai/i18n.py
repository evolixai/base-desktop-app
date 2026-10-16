"""In-app translation for the supported UI languages (English, Vietnamese).

English is the source language and the fallback: a key missing from the active
catalogue is looked up in English, and a key missing everywhere is returned
verbatim. The active language is set once at startup (from the saved setting,
or the OS locale) and can be changed at runtime from the settings dialog.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "en"
SETTING_KEY = "ui.language"

# Language code -> name shown in its own language.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "vi": "Tiếng Việt",
}

_EN: dict[str, str] = {
    # Shared -----------------------------------------------------------------
    "button.ok": "OK",
    "button.cancel": "Cancel",
    "button.yes": "Yes",
    "button.no": "No",
    "dialog.missing_info": "Missing information",
    "common.error": "Error: {message}",
    "field.name": "Name",
    "field.description": "Description",
    "field.updated": "Updated",
    "field.type": "Type",
    "field.base_url": "Base URL",
    "field.api_key": "API key",
    "field.model": "Model",
    "action.open": "Open",
    "action.add": "Add",
    "action.add_project": "Add project",
    "action.edit": "Edit",
    "action.delete": "Delete",
    "action.close": "Close",
    "action.send": "Send",
    "action.ai_settings": "AI settings",
    "action.back_projects": "← Projects",
    # Main window ------------------------------------------------------------
    "main.projects_title": "Projects",
    "main.project_count.one": "{count} project",
    "main.project_count.other": "{count} projects",
    "main.empty": "No projects yet.\nClick “Add project” to get started.",
    "projects.delete.title": "Delete project",
    "projects.delete.text": "Are you sure you want to delete “{name}”?",
    # Project dialog ---------------------------------------------------------
    "project.add_title": "Add project",
    "project.edit_title": "Edit project",
    "project.name_placeholder": "Project name",
    "project.description_placeholder": "Short description (optional)",
    "project.name_required": "Project name is required.",
    # Workspace --------------------------------------------------------------
    "tab.chat": "Chat",
    "tab.browser": "Browser",
    # Chat panel -------------------------------------------------------------
    "chat.provider": "Provider",
    "chat.model_placeholder": "Model",
    "chat.input_placeholder": "Type a message… (Ctrl+Enter to send)",
    "chat.no_connection": "No AI connection yet. Add one in “AI settings”.",
    "chat.no_model": "No model selected for this connection.",
    "chat.waiting": "Waiting for reply…",
    "chat.you": "You:",
    "chat.ai": "AI:",
    # Browser ----------------------------------------------------------------
    "browser.address_placeholder": "Enter an address and press Enter…",
    "browser.webengine_missing": (
        "The embedded browser requires the PySide6-WebEngine package.\n"
        "Install it with: uv sync (or pip install PySide6-WebEngine)."
    ),
    # Settings ---------------------------------------------------------------
    "settings.title": "AI connection settings",
    "settings.header": "AI providers",
    "settings.hint": (
        "Connections use an OpenAI-compatible chat endpoint. "
        "For Cloudflare Workers AI, enter the account base URL."
    ),
    "settings.language": "Language",
    "provider.add_title": "Add connection",
    "provider.edit_title": "Edit connection",
    "provider.name_placeholder": "e.g. OpenCode Zen",
    "provider.base_url_placeholder": "https://…/v1",
    "provider.api_key_placeholder": "API key",
    "provider.model_placeholder": "Default model (optional)",
    "provider.test_button": "Test connection",
    "provider.no_base_url": "No base URL to test.",
    "provider.testing": "Testing…",
    "provider.ok": "Connection OK · {count} {label}{detail}",
    "provider.model.one": "model",
    "provider.model.other": "models",
    "provider.name_required": "Connection name is required.",
    "provider.base_url_required": "Base URL is required.",
    "provider.delete.title": "Delete connection",
    "provider.delete.text": "Are you sure you want to delete “{name}”?",
    "provider.kind.custom": "Custom",
}

_VI: dict[str, str] = {
    # Shared -----------------------------------------------------------------
    "button.ok": "OK",
    "button.cancel": "Huỷ",
    "button.yes": "Có",
    "button.no": "Không",
    "dialog.missing_info": "Thiếu thông tin",
    "common.error": "Lỗi: {message}",
    "field.name": "Tên",
    "field.description": "Mô tả",
    "field.updated": "Cập nhật",
    "field.type": "Loại",
    "field.base_url": "Base URL",
    "field.api_key": "API key",
    "field.model": "Mô hình",
    "action.open": "Mở",
    "action.add": "Thêm",
    "action.add_project": "Thêm dự án",
    "action.edit": "Sửa",
    "action.delete": "Xóa",
    "action.close": "Đóng",
    "action.send": "Gửi",
    "action.ai_settings": "Cài đặt AI",
    "action.back_projects": "← Dự án",
    # Main window ------------------------------------------------------------
    "main.projects_title": "Dự án",
    "main.project_count.one": "{count} dự án",
    "main.project_count.other": "{count} dự án",
    "main.empty": "Chưa có dự án nào.\nNhấn “Thêm dự án” để bắt đầu.",
    "projects.delete.title": "Xóa dự án",
    "projects.delete.text": "Bạn có chắc muốn xóa “{name}” không?",
    # Project dialog ---------------------------------------------------------
    "project.add_title": "Thêm dự án",
    "project.edit_title": "Sửa dự án",
    "project.name_placeholder": "Tên dự án",
    "project.description_placeholder": "Mô tả ngắn (không bắt buộc)",
    "project.name_required": "Vui lòng nhập tên dự án.",
    # Workspace --------------------------------------------------------------
    "tab.chat": "Trò chuyện",
    "tab.browser": "Trình duyệt",
    # Chat panel -------------------------------------------------------------
    "chat.provider": "Nhà cung cấp",
    "chat.model_placeholder": "Mô hình",
    "chat.input_placeholder": "Nhập tin nhắn… (Ctrl+Enter để gửi)",
    "chat.no_connection": "Chưa có kết nối AI. Thêm trong “Cài đặt AI”.",
    "chat.no_model": "Chưa chọn mô hình cho kết nối này.",
    "chat.waiting": "Đang chờ trả lời…",
    "chat.you": "Bạn:",
    "chat.ai": "AI:",
    # Browser ----------------------------------------------------------------
    "browser.address_placeholder": "Nhập địa chỉ rồi nhấn Enter…",
    "browser.webengine_missing": (
        "Trình duyệt nhúng cần gói PySide6-WebEngine.\n"
        "Cài đặt bằng: uv sync (hoặc pip install PySide6-WebEngine)."
    ),
    # Settings ---------------------------------------------------------------
    "settings.title": "Cài đặt kết nối AI",
    "settings.header": "Nhà cung cấp AI",
    "settings.hint": (
        "Kết nối dùng endpoint chat tương thích OpenAI. "
        "Với Cloudflare Workers AI, nhập base URL của tài khoản."
    ),
    "settings.language": "Ngôn ngữ",
    "provider.add_title": "Thêm kết nối",
    "provider.edit_title": "Sửa kết nối",
    "provider.name_placeholder": "ví dụ: OpenCode Zen",
    "provider.base_url_placeholder": "https://…/v1",
    "provider.api_key_placeholder": "API key",
    "provider.model_placeholder": "Mô hình mặc định (không bắt buộc)",
    "provider.test_button": "Kiểm tra kết nối",
    "provider.no_base_url": "Không có base URL để kiểm tra.",
    "provider.testing": "Đang kiểm tra…",
    "provider.ok": "Kết nối OK · {count} {label}{detail}",
    "provider.model.one": "mô hình",
    "provider.model.other": "mô hình",
    "provider.name_required": "Vui lòng nhập tên kết nối.",
    "provider.base_url_required": "Vui lòng nhập base URL.",
    "provider.delete.title": "Xóa kết nối",
    "provider.delete.text": "Bạn có chắc muốn xóa “{name}” không?",
    "provider.kind.custom": "Tuỳ chỉnh",
}

_CATALOG: dict[str, dict[str, str]] = {
    "en": _EN,
    "vi": _VI,
}

_current = DEFAULT_LANGUAGE


def available_languages() -> list[tuple[str, str]]:
    """Return ``(code, label)`` pairs for every supported language."""
    return list(LANGUAGES.items())


def current_language() -> str:
    """Return the active language code."""
    return _current


def set_language(code: str | None) -> str:
    """Activate ``code`` (falling back to English) and return the active code."""
    global _current
    _current = code if code in LANGUAGES else DEFAULT_LANGUAGE
    return _current


def normalize_language(name: str | None) -> str:
    """Map a locale name such as ``vi_VN`` or ``en-US`` to a supported code."""
    code = (name or "").replace("-", "_").split("_", 1)[0].strip().lower()
    return code if code in LANGUAGES else DEFAULT_LANGUAGE


def tr(key: str, /, **fmt: object) -> str:
    """Translate ``key`` into the active language, applying ``fmt`` fields."""
    text = _lookup(key)
    return text.format(**fmt) if fmt else text


def trn(key: str, count: int, /, **fmt: object) -> str:
    """Translate a plural ``key``: ``<key>.one`` for 1, else ``<key>.other``."""
    suffix = "one" if count == 1 else "other"
    return tr(f"{key}.{suffix}", count=count, **fmt)


def _lookup(key: str) -> str:
    catalog = _CATALOG.get(_current, _EN)
    if key in catalog:
        return catalog[key]
    return _EN.get(key, key)
