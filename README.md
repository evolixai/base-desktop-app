# Sg

Ứng dụng desktop viết bằng Python (PySide6/Qt), hỗ trợ build cho **macOS** và **Windows**.

## Yêu cầu

- [uv](https://docs.astral.sh/uv/) (quản lý môi trường & dependency)
- [Make](https://www.gnu.org/software/make/) (tùy chọn, cho các lệnh tắt)

## Bắt đầu

```bash
uv sync          # cài đặt môi trường + dependency
make run         # hoặc: uv run sg
```

## Phát triển

```bash
make test        # chạy test (pytest + pytest-qt)
make lint        # kiểm tra code (ruff)
make fmt         # format code (ruff)
```

## Build

Đóng gói bằng PyInstaller. Chạy trên **chính hệ điều hành đích** (PyInstaller không cross-compile).

```bash
make build       # hoặc: uv run pyinstaller packaging/sg.spec --noconfirm --clean
```

Kết quả trong `dist/`:

| Nền tảng | Sản phẩm |
| -------- | -------- |
| macOS    | `dist/Sg.app` |
| Windows  | `dist/Sg/Sg.exe` |

> Ứng dụng phải được build trên Windows để tạo `.exe`, và trên macOS để tạo `.app`.

## CI/CD

GitHub Actions (`.github/workflows/build.yml`) tự động build song song trên `macos-14` và
`windows-latest`, upload artifact. Khi push tag `v*`, các file zip được đính kèm vào Release.

```bash
git tag v0.1.0 && git push origin v0.1.0
```

## Cấu trúc

```
src/sg/              # mã nguồn chính
├── __main__.py      # entry point
└── ui/              # giao diện PySide6
packaging/sg.spec    # cấu hình PyInstaller (macOS + Windows)
resources/           # icon, tài nguyên (đặt icon.icns / icon.ico vào đây)
tests/               # pytest + pytest-qt
```

### Icon

Đặt icon tùy nền tảng vào `resources/`:

- macOS: `resources/icon.icns`
- Windows: `resources/icon.ico`

`packaging/sg.spec` tự động dùng icon nếu file tồn tại.
