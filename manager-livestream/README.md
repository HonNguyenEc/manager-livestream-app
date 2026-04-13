# Manager Livestream - Modular Architecture

Ứng dụng desktop (Tkinter) để quản lý Shopee Livestream theo mô hình module, hỗ trợ multi-brand (mỗi brand có env và data riêng).

## New Chat Mandatory Rule Loading (Required)

When starting a **new chat/session** with Cline or any API-based coding agent, you must require the agent to read and apply the full rule set before handling any task.

### Mandatory files to load first
- `.cline/rules/00-core-rules.md`
- `.cline/rules/10-architecture.md`
- `.cline/rules/20-ui-rules.md`
- `.cline/rules/30-refactor-safety.md`
- `.cline/rules/40-testing-and-quality.md`
- `.cline/rules/50-performance-and-security.md`
- `prompts/system_prompt_for_api.md`
- `prompts/task_template.md`
- `prompts/new_chat_mandatory_context.md`
- `docs/project-structure.md`
- `docs/review-checklist.md`
- `cline_ruleset_full.md`

### Start New Chat Checklist
1. Paste the content from `prompts/new_chat_mandatory_context.md` as the first message.
2. Ask the agent to confirm it has read all required rule files.
3. Only then provide the implementation task.

### Quick copy block (first message in a new chat)
```text
Before doing any task, you must read and apply all governance files in this repository:
- .cline/rules/*
- prompts/*
- docs/*
- cline_ruleset_full.md

Then summarize the consolidated execution policy you will follow.
Do not implement anything until this confirmation is done.
```

## Mục tiêu kiến trúc

Project được tách theo hướng **module-based** để giảm phụ thuộc chéo:

- `system_main.py` là runtime quản lý module.
- Mỗi module chạy độc lập (module chết không bắt buộc làm chết toàn hệ thống).
- Mỗi feature được gom vào thư mục riêng.
- Shared/common utilities nằm ở thư mục `shared/`.
- Dữ liệu runtime nằm ở thư mục `data/`.

## Cấu trúc thư mục
- `.cline/rules/00-core-rules.md`: rule nền tảng bắt buộc
- `.cline/rules/10-architecture.md`: rule kiến trúc và module hóa
- `.cline/rules/20-ui-rules.md`: rule tách UI component
- `.cline/rules/30-refactor-safety.md`: rule sửa code an toàn
- `.cline/rules/40-testing-and-quality.md`: rule test, quality, logging
- `.cline/rules/50-performance-and-security.md`: rule hiệu năng và an toàn
- `docs/project-structure.md`: cấu trúc thư mục khuyến nghị
- `docs/review-checklist.md`: checklist review trước khi merge
- `prompts/system_prompt_for_api.md`: prompt tổng cho API-based coding agent
- `prompts/task_template.md`: mẫu prompt giao task cho agent

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
python -m pip install -r manager-livestream/requirements.txt
```

### OCR runtime note (quan trọng)

- `pytesseract` là Python wrapper, bạn cần cài thêm **Tesseract OCR binary** ở hệ điều hành.
- Để đọc tiếng Việt tốt, cần cài language pack `vie` cho Tesseract.
- Nếu thiếu Tesseract hoặc thiếu `vie`, app vẫn chạy nhưng OCR có thể không ra text.

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

## OBS Queue ID/Cooldown (mới)

Hệ thống OBS đã hỗ trợ queue theo **video ID** + **cooldown** + **ưu tiên phát theo ID**.

### UI flow

Trong tab **OBS**:

1. Vào `Scene & Sources`:
   - Chọn `Scene`
   - Chọn `Video Source A` và `Video Source B`
   - Cấu hình:
     - `Crossfade (s)`
     - `Cooldown mặc định (s)`
2. Vào `Playlist`:
   - Chọn thư mục video và `Import`
   - Queue 1 sẽ hiển thị dạng: `ID | tên_file`
3. Điều khiển queue:
   - `Move Up/Move Down/Remove` thao tác theo ID đã chọn trong Queue 1
   - `Priority ID` + `Prioritize`: đẩy video ID lên ưu tiên phát kế tiếp (Queue 2)
   - `Cooldown ID` + số giây + `Set Cooldown`: override cooldown riêng cho từng video

### Lưu trữ dữ liệu OBS theo brand

Mỗi brand có dữ liệu OBS riêng, nằm tại:

- `data/brands/<brand_id>/obs/config.json`
- `data/brands/<brand_id>/obs/video_catalog.json`

`video_catalog.json` chứa:

- `id_counter`: bộ đếm sinh ID (`V0001`, `V0002`, ...)
- `videos`: mapping ID -> path + cooldown metadata
- `priority_ids`: danh sách ID đang được ưu tiên

### Cách ly brand/env (quan trọng)

- Mỗi `OBSService` được khởi tạo theo `brand_id`.
- Catalog video và queue state được load/save theo đúng thư mục brand đó.
- ID của brand A không thể được resolve trong brand B.

## Public API cho feature khác (ưu tiên phát theo ID)

Bạn có thể gọi trực tiếp từ module/feature khác (không cần đi qua UI):

```python
from features.obs import (
    enqueue_priority_video,
    set_video_cooldown_by_id,
    get_video_catalog,
)

brand_id = "default"

# 1) Lấy catalog ID hiện có
catalog = get_video_catalog(brand_id)

# 2) Ưu tiên phát 1 ID
result = enqueue_priority_video(
    brand_id=brand_id,
    video_id="V0007",
    source="my_feature",


    
    trace_id="req-123",
)

# 3) Override cooldown cho 1 ID
set_video_cooldown_by_id(
    brand_id=brand_id,
    video_id="V0007",
    cooldown_seconds=180,
    source="my_feature",
    trace_id="req-124",
)
```

### API contract gợi ý

- Truyền `brand_id` rõ ràng cho mọi call cross-feature.
- Khuyến nghị gắn `source` và `trace_id` để debug/tracing dễ hơn.
- Nếu ID không tồn tại trong brand hiện tại, API sẽ raise lỗi để chặn nhầm môi trường.

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





