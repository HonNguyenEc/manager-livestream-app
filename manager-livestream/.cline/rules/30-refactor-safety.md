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
