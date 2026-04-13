# Cline Python App Ruleset

# Cline Ruleset for Python App Development

Bộ file này dùng để đưa vào workspace VS Code để Cline hoặc coding agent đọc và bám theo khi sinh code.

## Cấu trúc
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

## Cách dùng với Cline
1. Copy toàn bộ thư mục này vào root project của bạn.
2. Giữ nguyên thư mục `.cline/rules/`.
3. Có thể chỉnh wording theo framework bạn dùng: PySide6, Tkinter, CustomTkinter, FastAPI desktop hybrid...
4. Khi giao task cho Cline, kèm thêm `prompts/task_template.md` hoặc paste vào custom instruction.

## Mục tiêu
- sinh code Python an toàn, hợp lệ, maintainable
- module hóa, thay thế được, ít phá feature cũ
- tách UI / application / domain / infrastructure
- tuân thủ SOLID, DRY, OOP hợp lý
- function không quá 100 dòng
- không gom toàn bộ logic hoặc UI vào 1 file

# Core Rules

## Mục tiêu bắt buộc
Mọi code sinh ra phải:
- an toàn khi mở rộng
- không làm hỏng flow cũ
- ưu tiên tái sử dụng code hiện có
- tách rõ trách nhiệm
- dễ test, dễ thay thế implementation
- không tạo duplicated logic

## Quy tắc bắt buộc
- Tuân thủ SOLID, DRY, separation of concerns.
- Không viết business logic trong UI.
- Không viết data access trực tiếp trong UI.
- Không nhồi toàn bộ logic vào một file.
- Không nhồi toàn bộ UI vào một file.
- Mỗi function tối đa 100 dòng.
- Mỗi file chỉ chứa một nhóm trách nhiệm liên quan.
- Mọi public function và method phải có type hints đầy đủ.
- Ưu tiên composition và dependency injection hợp lý.
- Không copy-paste logic; phải tách helper/service/reusable component khi logic được dùng lại.
- Không dùng `except Exception: pass`.
- Không hardcode token, password, endpoint môi trường, đường dẫn đặc thù máy.
- Mọi thay đổi shared code phải đánh giá impact tới caller hiện có.
- Ưu tiên sửa tối thiểu nhưng an toàn, không refactor lan rộng khi chưa cần.
- Khi thêm tính năng mới phải đảm bảo backward compatibility tối đa.

## Yêu cầu khi trả code
Trước khi trả code, agent phải tự kiểm tra:
- Tính năng nằm đúng layer chưa?
- Có tái sử dụng code cũ được không?
- Có function nào vượt 100 dòng không?
- Có chỗ nào business logic nằm trong UI không?
- Có phá interface cũ không?
- Có xử lý lỗi, log, validate input chưa?

# Architecture Rules

## Kiến trúc khuyến nghị
Tách theo các lớp:
- presentation
- application
- domain
- infrastructure
- shared
- config
- bootstrap
- tests

## Trách nhiệm từng lớp

### presentation
- windows, dialogs, widgets, viewmodels, controllers
- chỉ nhận input, hiển thị state, trigger action
- không chứa business logic phức tạp
- không truy cập DB, file, HTTP trực tiếp

### application
- use cases, commands, queries, DTO
- điều phối luồng xử lý
- gọi domain + interfaces của repository/client

### domain
- entity, value object, domain service, interface
- chứa rule nghiệp vụ cốt lõi
- không phụ thuộc UI, DB, framework

### infrastructure
- repository implementation
- http client
- file system
- scheduler
- cache
- third-party adapter

### shared
- utility dùng chung thật sự
- validator
- common exception
- type alias
- không biến shared thành nơi chứa mọi thứ

## Rule về thay thế implementation
- Các thành phần dễ đổi phải đi qua abstraction/interface.
- Ví dụ: storage, scheduler, automation engine, API client.
- Không để business logic phụ thuộc trực tiếp implementation cụ thể.

# UI Rules

## Tách UI bắt buộc
UI phải tách rõ:
- windows/pages
- dialogs
- reusable widgets
- controllers hoặc viewmodels
- state model

## Không được phép
- không gom mọi widget vào một file
- không để event handler dài hàng trăm dòng
- không để UI gọi trực tiếp database hoặc API phức tạp
- không chứa xử lý parsing nặng trong lớp giao diện
- không block UI thread bằng task nặng

## Phải làm
- task nặng phải chạy qua worker/thread/process phù hợp
- update UI từ background phải đi qua cơ chế an toàn của framework
- state phải có object hoặc model rõ ràng
- component tái sử dụng phải tách file riêng
- dialog xác nhận/lỗi nên là component độc lập

## Gợi ý thư mục
presentation/ui/windows/
presentation/ui/dialogs/
presentation/ui/widgets/
presentation/ui/viewmodels/
presentation/controllers/

# Refactor Safety Rules

## Mục tiêu
Sửa code cũ an toàn, không làm hỏng tính năng đang chạy.

## Quy tắc
- Ưu tiên thay đổi tối thiểu.
- Không refactor kiến trúc lớn cùng lúc với đổi behavior lớn.
- Nếu function quá dài, tách nhỏ trước rồi mới sửa logic.
- Không đổi public contract cũ nếu chưa có migration plan.
- Nếu buộc phải đổi interface, phải tạo adapter hoặc compatibility layer.
- Shared utility chỉ được sửa sau khi kiểm tra nơi đang dùng.
- Bug đã sửa nên có regression test tương ứng nếu có thể.

## Khi tạo code mới
- tìm code tương tự hiện có
- tái sử dụng trước khi tạo mới
- nếu chưa phù hợp, trích abstraction chung
- không duplicate logic

# Testing and Quality Rules

## Testability
- Business logic phải test được mà không cần khởi chạy UI.
- I/O nên được inject để mock được.
- Service, repository, client phải tách để test độc lập.
- Bug fix phải cố gắng kèm regression test.

## Quality Gates
- không lỗi import
- không lỗi typing cơ bản
- không unused code rõ ràng
- không circular import
- log đủ để debug
- exception không bị nuốt im lặng

## Logging
- dùng log level rõ ràng: debug/info/warning/error
- log có ngữ cảnh đủ để debug
- không log secret, token, password
- UI báo lỗi thân thiện, log giữ thông tin kỹ thuật chi tiết

# Performance and Security Rules

## Performance
- Không load toàn bộ dữ liệu nếu chỉ cần một phần.
- Không lặp thừa hoặc query dư thừa.
- Không đọc file/network nhiều lần khi có thể tái sử dụng kết quả.
- Không block UI thread với tác vụ nặng.
- Chỉ dùng caching khi có chiến lược invalidation rõ ràng.

## Security
- Không hardcode credential.
- Tất cả config nhạy cảm phải lấy từ env hoặc file config riêng.
- Validate input ở biên hệ thống.
- File I/O, network I/O cần timeout và error handling.
- Mọi thao tác ghi phải tránh ghi đè sai hoặc mất dữ liệu.

# Project Structure Recommendation

```text
app/
├─ main.py
├─ bootstrap/
│  ├─ app_factory.py
│  ├─ dependency_container.py
│  └─ startup_checks.py
├─ config/
│  ├─ settings.py
│  ├─ constants.py
│  └─ logging_config.py
├─ domain/
│  ├─ entities/
│  ├─ value_objects/
│  ├─ interfaces/
│  └─ services/
├─ application/
│  ├─ use_cases/
│  ├─ dto/
│  ├─ commands/
│  └─ queries/
├─ infrastructure/
│  ├─ persistence/
│  │  ├─ repositories/
│  │  ├─ models/
│  │  └─ migrations/
│  ├─ clients/
│  ├─ filesystem/
│  ├─ cache/
│  └─ schedulers/
├─ presentation/
│  ├─ ui/
│  │  ├─ windows/
│  │  ├─ dialogs/
│  │  ├─ widgets/
│  │  ├─ viewmodels/
│  │  └─ themes/
│  ├─ controllers/
│  └─ presenters/
├─ shared/
│  ├─ utils/
│  ├─ exceptions/
│  ├─ validators/
│  ├─ decorators/
│  └─ types/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  └─ regression/
└─ scripts/
   ├─ dev/
   └─ release/
```

## Nguyên tắc
- `main.py` chỉ bootstrap ứng dụng.
- Không đặt logic nghiệp vụ lớn trong entrypoint.
- UI, use case, domain, infrastructure phải tách.
- Có thể thay SQLite bằng PostgreSQL hoặc file storage bằng service khác mà ít ảnh hưởng business layer.

# Review Checklist

## Kiến trúc
- Tính năng mới nằm đúng layer chưa?
- Có tách UI / application / domain / infrastructure chưa?
- Có chỗ nào coupling quá chặt không?

## Chất lượng code
- Có duplicated logic không?
- Function nào vượt 100 dòng không?
- File nào đang ôm quá nhiều trách nhiệm không?
- Có import vòng tròn không?
- Type hints đã đủ chưa?

## An toàn thay đổi
- Có phá interface cũ không?
- Có cần compatibility layer không?
- Có kiểm tra flow cũ bị ảnh hưởng không?

## UI
- UI đã tách component chưa?
- Có business logic trong UI không?
- Có chỗ nào block UI thread không?

## Hiệu năng và an toàn
- Có query hoặc xử lý dư thừa không?
- Có validate input chưa?
- Có timeout/retry/error handling chưa?
- Có log đủ mà không lộ secret không?

## Test
- Có test mới hoặc regression test phù hợp chưa?
- Có cách verify thủ công rõ ràng không?

# System Prompt for API-based Coding Agent

You are a senior Python software engineer working on a production-oriented application.

Always generate code that is safe to extend, modular, and backward-compatible whenever possible.

Mandatory rules:
- Follow SOLID, DRY, separation of concerns, and sensible OOP.
- Do not place all logic in one file.
- Do not place all UI in one file.
- Separate presentation, application, domain, infrastructure, config, and shared concerns.
- Do not put business logic in UI code.
- Do not put direct database, file, or HTTP access in UI code.
- Each function must be at most 100 lines.
- Each file must have a focused responsibility.
- Reuse existing code first before creating new code.
- Avoid duplicated logic by extracting helpers/services/components.
- Use type hints for all public functions and methods.
- Add concise docstrings for public classes and public functions.
- Never swallow exceptions silently.
- Do not hardcode credentials, secrets, machine-specific paths, or environment-specific URLs.
- Heavy tasks must not block the UI thread.
- Any change to shared code must consider impact on existing callers.
- New features must not break old features.
- Prefer minimal, safe changes over broad refactors.
- If interface changes are required, provide a compatibility layer whenever practical.

Before returning code, verify:
- correct layer placement
- no duplicated logic
- no oversized functions
- no business logic in UI
- input validation and error handling exist
- old flows are still safe

# Task Template for Cline / API Agent

Use the existing project structure and follow all files under `.cline/rules/`.

Task:
[Describe the feature or bug here]

Constraints:
- Keep backward compatibility unless explicitly instructed otherwise.
- Reuse existing code whenever possible.
- Do not create duplicated logic.
- Keep each function under 100 lines.
- Do not put business logic in UI.
- Do not block UI thread for heavy tasks.
- Keep file responsibilities focused.

Expected output:
1. Brief impact analysis
2. Proposed files to change
3. Implementation
4. Risk notes
5. Test or verification steps
