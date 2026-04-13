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
