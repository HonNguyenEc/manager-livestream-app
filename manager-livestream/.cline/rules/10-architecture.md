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
