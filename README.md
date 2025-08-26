<div align="center">
  <h1>Host Image Backup</h1>
</div>

<div align="center">
  <a href="README.md"><b>English</b></a> | <a href="README.zh-CN.md"><b>简体中文</b></a>
</div>

<p align="center">
  <a href="https://pypi.org/project/host-image-backup/">
    <img src="https://img.shields.io/pypi/v/host-image-backup?color=blue" alt="PyPI">
  </a>
  <img src="https://img.shields.io/github/stars/WayneXuCN/HostImageBackup?style=social" alt="GitHub stars">
  <img src="https://img.shields.io/github/license/WayneXuCN/HostImageBackup" alt="License">
</p>

> **Host Image Backup** is a modular Python CLI tool for backing up images from various image hosting services to your local machine with ease.

## Features

- Modular architecture: Easily extend with new providers
- Multi-provider support: Aliyun OSS, Tencent COS, SM.MS, Imgur, GitHub
- Visual progress: Progress bars for backup operations
- Rich CLI interface: Intuitive command-line experience
- Flexible configuration: YAML-based config management
- Resume support: Continue interrupted transfers
- Comprehensive logging: Detailed operation logs
- Well tested: Reliable with test coverage
- Upload support: Upload images to cloud storage
- Metadata management: Track backup operations and files
- Batch operations: Upload multiple files at once
- Duplicate detection: Find and manage duplicate files
- Image compression: High fidelity compression with quality control

---

## Supported Providers

| Provider   | Features                                    | Notes                            |
|------------|---------------------------------------------|----------------------------------|
| OSS        | List, backup, upload, delete, file info     | Requires Aliyun credentials      |
| COS        | List, backup, upload, delete, file info     | Requires Tencent credentials     |
| SM.MS      | List, backup                               | Public API, rate limits apply    |
| Imgur      | List, backup                               | Requires Imgur client ID/secret  |
| GitHub     | List, backup                               | Requires GitHub token & access   |

---

## Installation

**Requirements:**

- Python 3.10 or newer
- pip or uv package manager

**Install from PyPI:**

```bash
pip install host-image-backup
pip install --upgrade host-image-backup
host-image-backup --help
hib --help
```

**Development install:**

```bash
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup
uv lock
uv sync --all-extras
# Or use pip:
pip install -e ".[dev]"
```

---

## Configuration

**Quick start:**

```bash
host-image-backup init
# Edit config file:
# Linux/macOS: ~/.config/host-image-backup/config.yaml
# Windows: %APPDATA%/host-image-backup/config.yaml
```

**Example configuration:**

```yaml
default_output_dir: "./backup"
max_concurrent_downloads: 5
timeout: 30
retry_count: 3
log_level: "INFO"
providers:
  oss:
    enabled: true
    access_key_id: "your_access_key"
    access_key_secret: "your_secret_key"
    bucket: "your_bucket_name"
    endpoint: "oss-cn-hangzhou.aliyuncs.com"
    prefix: "images/"
  cos:
    enabled: false
    secret_id: "your_secret_id"
    secret_key: "your_secret_key"
    bucket: "your_bucket_name"
    region: "ap-guangzhou"
    prefix: "images/"
  sms:
    enabled: false
    api_token: "your_api_token"
  imgur:
    enabled: false
    client_id: "your_client_id"
    client_secret: "your_client_secret"
    access_token: "your_access_token"
    refresh_token: "your_refresh_token"
  github:
    enabled: false
    token: "ghp_your_personal_access_token"
    owner: "your_username"
    repo: "your_repository"
    path: "images"
```

**Configuration fields:**

| Field                     | Description                        | Required | Default     |
|---------------------------|------------------------------------|----------|-------------|
| default_output_dir        | Backup directory                   | No       | "./backup"  |
| max_concurrent_downloads  | Parallel downloads                 | No       | 5           |
| timeout                   | Request timeout (seconds)          | No       | 30          |
| retry_count               | Retry attempts                     | No       | 3           |
| log_level                 | Logging level                      | No       | "INFO"      |
| access_key_id             | Aliyun OSS access key ID           | Yes      | -           |
| access_key_secret         | Aliyun OSS access key secret       | Yes      | -           |
| bucket                    | OSS/COS bucket name                | Yes      | -           |
| endpoint                  | OSS endpoint URL                   | Yes      | -           |
| region                    | COS region                         | Yes      | -           |
| secret_id                 | Tencent COS secret ID              | Yes      | -           |
| secret_key                | Tencent COS secret key             | Yes      | -           |
| api_token                 | SM.MS API token                    | Yes      | -           |
| client_id                 | Imgur client ID                    | Yes      | -           |
| client_secret             | Imgur client secret                | Yes      | -           |
| access_token              | Imgur access token                 | Yes      | -           |
| refresh_token             | Imgur refresh token                | No       | -           |
| token                     | GitHub token                       | Yes      | -           |
| owner                     | GitHub repo owner                  | Yes      | -           |
| repo                      | GitHub repo name                   | Yes      | -           |
| path                      | Folder path in repo                | No       | ""          |

---

## CLI Usage

**Quick start:**

```bash
host-image-backup config init
hib config init
host-image-backup provider test oss
hib provider test oss
host-image-backup provider list
hib provider list
host-image-backup backup start oss --output ./my-backup
hib backup start oss --output ./my-backup
host-image-backup backup all --output ./full-backup
hib backup all --output ./full-backup
```

**Command groups:**

| Group      | Command                | Description                        |
|------------|------------------------|------------------------------------|
| Config     | config init            | Initialize configuration file      |
| Provider   | provider list          | List providers                     |
|            | provider test          | Test provider connection           |
|            | provider info          | Show provider info                 |
| Backup     | backup start           | Backup from specific provider      |
|            | backup all             | Backup from all enabled providers  |
| Upload     | upload file            | Upload single image                |
|            | upload directory       | Upload multiple images             |
| Data       | data stats             | Show backup statistics             |
|            | data history           | Show backup history                |
|            | data duplicates        | Find duplicate files               |
|            | data cleanup           | Clean up backup files              |
|            | data verify            | Verify backup file integrity       |
|            | data compress          | Compress images                    |

**Examples:**

```bash
host-image-backup backup start oss
hib backup start oss
host-image-backup backup start oss --output ~/Pictures/backup --limit 100
hib backup start oss --output ~/Pictures/backup --limit 100
host-image-backup backup start imgur --config ./my-config.yaml --verbose
hib backup start imgur --config ./my-config.yaml --verbose
host-image-backup backup start github --no-skip-existing
hib backup start github --no-skip-existing
host-image-backup backup all --output ~/backup --limit 50 --verbose
hib backup all --output ~/backup --limit 50 --verbose
```

**Global options:**

```bash
-c, --config PATH    Custom config file path
-v, --verbose        Enable verbose logging
--help               Show help message
```

---

## Use Cases

- Backup and migrate images from cloud providers to local storage
- Aggregate images from multiple services
- Automate scheduled backups (cron jobs, CI/CD)
- Archive management for organized local image storage
- Disaster recovery: maintain offline copies

**Examples:**

```bash
host-image-backup backup all --output ~/PhotoBackup
hib backup all --output ~/PhotoBackup

# Scheduled backup (cron)
0 2 * * * /usr/local/bin/host-image-backup backup all --output /backup/images --limit 100
0 2 * * * /usr/local/bin/hib backup all --output /backup/images --limit 100

# Migration between providers
host-image-backup backup start old-provider --output ./migration-temp
hib backup start old-provider --output ./migration-temp
```

---

## Troubleshooting

**Authentication errors:**

- Check credentials and config file format
- Verify token expiration and permissions
- Test providers: `host-image-backup provider test <provider>`

**Network issues:**

- Check internet connection
- Increase timeout in config
- Use `--verbose` for details
- Check provider service status

**File system errors:**

- Ensure output directory exists and is writable

```bash
mkdir -p ~/backup && chmod 755 ~/backup
chmod 600 ~/.config/host-image-backup/config.yaml
```

**Rate limiting:**

- Lower `max_concurrent_downloads`
- Add delays between requests
- Use `--limit` to control download volume

**Debugging:**

```bash
host-image-backup provider test oss --verbose
hib provider test oss --verbose
host-image-backup provider info github
hib provider info github
host-image-backup backup start imgur --verbose --limit 5
hib backup start imgur --verbose --limit 5
```

**Log analysis:**

```bash
tail -f logs/host_image_backup_*.log
grep -i error logs/host_image_backup_*.log
grep -E "(Successfully|Failed)" logs/host_image_backup_*.log
```

---

## Security

- Never commit credentials to version control
- Use environment variables for sensitive data
- Set restrictive permissions on config files:

```bash
chmod 600 ~/.config/host-image-backup/config.yaml
```

**Environment variable example:**

```bash
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
export GITHUB_TOKEN="ghp_your_token"
```

Reference in config:

```yaml
providers:
  oss:
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
```

- Use HTTPS endpoints
- Consider VPN/private networks for sensitive data

---

## Development

**Setup:**

```bash
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
uv lock
uv sync --all-extras
pre-commit install
```

**Running:**

```bash
uv run -m host_image_backup.cli
```

**Testing:**

```bash
pytest
pytest --cov=src/host_image_backup
pytest tests/test_config.py
pytest -v
```

**Code quality:**

```bash
ruff format src tests
mypy src
ruff check src tests
make lint
```

**Add new providers:**

1. Create provider class in `src/host_image_backup/providers/`
2. Implement required methods from `BaseProvider`
3. Add config class in `src/host_image_backup/config/config_models.py`
4. Update provider registry in `src/host_image_backup/providers/provider_manager.py`
5. Add tests
6. Update documentation

---

## Roadmap

**Planned features:**

- Enhanced error handling
- Configuration validation
- Progress persistence for interrupted backups
- Performance optimization

**Future versions:**

- Web UI for configuration and monitoring
- Advanced filtering (date, type, size)
- Cloud-to-cloud transfers
- Incremental backups

**Additional providers:**

- Cloudinary
- AWS S3
- Google Drive
- Dropbox
- OneDrive

---

## Contributing

Contributions are welcome!

- Report bugs and request features
- Improve documentation and examples
- Add or enhance providers
- Write tests and improve coverage
- Improve CLI and user experience

---

## License

MIT License. See [LICENSE](LICENSE) for details.
