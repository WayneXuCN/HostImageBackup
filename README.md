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

> **Host Image Backup** is a modular Python CLI tool for backing up images from various image hosting services to your local machine.

## Features

- **Multi-provider support**: Aliyun OSS, Tencent COS, SM.MS, Imgur, GitHub
- **Flexible operations**: Backup, upload, compress images
- **Rich CLI interface**: Intuitive command-line experience with progress bars
- **Configurable**: YAML-based configuration with environment variable support
- **Reliable**: Comprehensive logging, metadata tracking, and duplicate detection
- **Extensible**: Plugin system for adding new providers

---

## Supported Providers

| Provider | Operations            | Notes                          |
|----------|-----------------------|--------------------------------|
| OSS      | List, backup, upload  | Requires Aliyun credentials    |
| COS      | List, backup, upload  | Requires Tencent credentials   |
| SM.MS    | List, backup          | Public API with rate limits    |
| Imgur    | List, backup          | Requires Imgur client ID/secret|
| GitHub   | List, backup          | Requires GitHub token          |

---

## Installation

**Requirements:**

- Python 3.10 or newer
- pip or uv package manager

**Install from PyPI:**

```bash
pip install host-image-backup
host-image-backup --help
# Or use the shorter alias:
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

## Quick Start

1. **Initialize configuration:**
   ```bash
   host-image-backup config init
   ```

2. **Edit configuration file:**
   - Linux/macOS: `~/.config/host-image-backup/config.yaml`
   - Windows: `%APPDATA%/host-image-backup/config.yaml`

3. **Test provider connection:**
   ```bash
   host-image-backup provider test oss
   ```

4. **Backup images:**
   ```bash
   host-image-backup backup start oss --output ./my-backup
   ```

---

## CLI Usage

```bash
# List all providers
host-image-backup provider list

# Backup from a specific provider
host-image-backup backup start oss

# Backup from all enabled providers
host-image-backup backup all

# Upload a single image
host-image-backup upload file oss /path/to/image.jpg

# Upload multiple images
host-image-backup upload directory oss /path/to/images/

# Compress images
host-image-backup data compress /path/to/images/ --quality 85

# View backup statistics
host-image-backup data stats

# Find duplicate files
host-image-backup data duplicates
```

---

## Configuration

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
  github:
    enabled: false
    token: "ghp_your_personal_access_token"
    owner: "your_username"
    repo: "your_repository"
    path: "images"
```

**Using environment variables:**

```bash
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
```

Reference in config:
```yaml
providers:
  oss:
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
```

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
```

**Code quality:**

```bash
ruff format src tests
mypy src
ruff check src tests
```

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