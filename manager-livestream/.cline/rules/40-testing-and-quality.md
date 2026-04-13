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
