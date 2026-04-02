# Manager Livestream - Modular Architecture

Ứng dụng desktop (Tkinter) để quản lý Shopee Livestream theo mô hình module, hỗ trợ multi-brand (mỗi brand có env và data riêng).

## Mục tiêu kiến trúc

Project được tách theo hướng **module-based** để giảm phụ thuộc chéo:

- `system_main.py` là runtime quản lý module.
- Mỗi module chạy độc lập (module chết không bắt buộc làm chết toàn hệ thống).
- Mỗi feature được gom vào thư mục riêng.
- Shared/common utilities nằm ở thư mục `shared/`.
- Dữ liệu runtime nằm ở thư mục `data/`.

## Cấu trúc thư mục

```text
manager-livestream/
  app.py                        # Entrypoint UI livestream
  run_app.py                    # Chạy app UI trực tiếp
  system_main.py                # Entrypoint hệ module

  core/
    runtime.py                  # ModuleRuntime (register/start/stop/status)

  modules/
    base.py                     # Interface module chuẩn
    livestream_module.py        # Module adapter để chạy livestream process

  features/
    livestream/
      config.py                 # AppConfig + load/save .env
      api.py                    # API client + sign + singleton
      service.py                # Business logic
      ui/
        main_window.py          # Ghép các UI component thành cửa sổ chính
        components/
          config_panel.py       # Panel config
          action_tabs.py        # Tabs create/end/comment
          output_panel.py       # Khu output log/result

  shared/
    logger.py                   # Logger dùng chung
    messages.py                 # Error code + messages + UI messages
    helpers.py                  # Helper hàm chung
    storage.py                  # Read/write JSON cho runtime

  data/
    system_state.json           # State module runtime
```

## Cách chạy

## Yêu cầu môi trường

- Python 3.10+
- Quyền ghi file trong thư mục `manager-livestream/` (để lưu env/data)

## Cài đặt nhanh

```bash
python -m pip install -U pip
```

(Project hiện dùng thư viện chuẩn Python, chưa có dependency ngoài bắt buộc.)

### 1) Chạy UI livestream trực tiếp

```bash
python manager-livestream/run_app.py
```

### 2) Chạy hệ module runtime

```bash
python manager-livestream/system_main.py
```

Runtime sẽ:
- register module livestream
- start module livestream
- ghi trạng thái vào `manager-livestream/data/system_state.json`

## Multi-brand profiles (chạy song song)

Hệ thống hỗ trợ nhiều brand độc lập:

- Env theo brand: `manager-livestream/envs/<brand_id>.env`
- State brand active: `manager-livestream/data/brand_state.json`
- Data theo brand: `manager-livestream/data/brands/<brand_id>/`
  - `shop_info.json`

### Cách dùng

1. Trên thanh trên cùng, chọn **Active Brand**.
2. Trong tab Config, dùng phần **Brand Management** để:
   - Create Brand
   - Delete Active Brand
3. Mỗi brand lưu config riêng, chuyển qua lại không mất dữ liệu form/output.
4. Khi gọi **Get Shop Info**, kết quả sẽ lưu vào thư mục data đúng brand.

### Migration

- Nếu trước đây chỉ có `.env`, hệ thống sẽ tự migrate sang `envs/default.env` lần đầu chạy.

## Lưu ý bảo mật

- Không commit token/partner key lên git.
- Các file env theo brand nằm ở `envs/*.env` và đã được đưa vào `.gitignore`.

## API đã tích hợp trong UI

- `v2.livestream.create_session`
- `v2.livestream.end_session`
- `v2.livestream.get_comment`
- `v2.auth.access_token/get`
- `v2.shop.get_shop_info` (GET)

### get_shop_info

- Endpoint: `/api/v2/shop/get_shop_info`
- Method: `GET`
- Query: `partner_id`, `timestamp`, `access_token`, `shop_id`, `sign`
- Công thức sign:
  - `partner_id + path + timestamp + access_token + shop_id`

## Ghi chú phát triển

- UI đã được tách thành component để dễ mở rộng và test.
- Các message/lỗi tập trung tại `shared/messages.py`.
- Hạn chế đặt logic nghiệp vụ trong UI; business logic nằm ở `features/livestream/service.py`.


