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
