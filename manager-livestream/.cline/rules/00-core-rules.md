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
