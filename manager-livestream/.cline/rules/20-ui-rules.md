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
