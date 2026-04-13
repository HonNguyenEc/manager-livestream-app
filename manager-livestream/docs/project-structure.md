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
