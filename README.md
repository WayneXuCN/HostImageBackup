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
  <img src="https://img.shields.io/github/actions/workflow/status/WayneXuCN/HostImageBackup/ci.yml?branch=main" alt="CI">
  <img src="https://img.shields.io/codecov/c/github/WayneXuCN/HostImageBackup?label=coverage" alt="Coverage">
</p>

> **Host Image Backup** is a modular Python CLI tool for backing up images from various image hosting services to your local machine with ease.

---

## ✨ Features

- 🏗️ **Modular Architecture** - Easy to extend with new providers
- 🌐 **Multi-Provider Support** - Aliyun OSS, Tencent COS, SM.MS, Imgur, GitHub
- 📊 **Visual Progress** - Beautiful progress bars for backup operations
- 🎨 **Rich CLI Interface** - Intuitive command-line experience
- ⚙️ **Flexible Configuration** - YAML-based configuration management
- 🔄 **Resume Support** - Continue interrupted transfers seamlessly
- 📝 **Comprehensive Logging** - Detailed operation logs
- 🧪 **Well Tested** - Comprehensive test coverage for reliability

---

## 🚀 Supported Providers

| Provider   | Features                         | Notes                            |
|------------|----------------------------------|----------------------------------|
| **OSS**    | ✅ List, backup, resume, skip   | Requires Aliyun credentials      |
| **COS**    | ✅ List, backup, resume, skip   | Requires Tencent credentials     |
| **SM.MS**  | ✅ List, backup                 | Public API, rate limits apply   |
| **Imgur**  | ✅ List, backup                 | Requires Imgur client ID/secret |
| **GitHub** | ✅ List, backup                 | Requires GitHub token & access  |

---

## 📦 Installation

### Requirements

- **Python 3.10+** (Latest stable versions recommended)
- **pip** or **uv** package manager

### Quick Install

```bash
# Install from PyPI
pip install host-image-backup

# Or upgrade to latest version
pip install --upgrade host-image-backup

# Verify installation
host-image-backup --help
# Or use the short alias
hib --help
```

### Development Install

```bash
# Clone repository
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup

# Install development dependencies with uv (recommended)
uv lock  # generate lock file
uv sync --all-extras # install all extras (dev)

# Or use pip if you prefer
pip install -e ".[dev]"
```

---

## ⚙️ Configuration

### Quick Start

```bash
# Initialize configuration file
host-image-backup init

# Edit the generated config file
# Linux/macOS: ~/.config/host-image-backup/config.yaml
# Windows: %APPDATA%/host-image-backup/config.yaml
```

### Configuration Structure

```yaml
# Global settings
default_output_dir: "./backup"
max_concurrent_downloads: 5
timeout: 30
retry_count: 3
log_level: "INFO"

# Provider configurations
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
    path: "images"  # optional: specific folder path
```

### Configuration Fields Reference

| Field                     | Description                        | Required | Default |
|---------------------------|------------------------------------|----------|---------|
| **Global Settings**       |                                    |          |         |
| `default_output_dir`      | Default backup directory           | No       | "./backup" |
| `max_concurrent_downloads`| Maximum parallel downloads         | No       | 5       |
| `timeout`                 | Request timeout (seconds)          | No       | 30      |
| `retry_count`             | Retry attempts for failed downloads| No       | 3       |
| `log_level`               | Logging level                      | No       | "INFO"  |
| **OSS Provider**          |                                    |          |         |
| `access_key_id`           | Aliyun OSS access key ID           | Yes      | -       |
| `access_key_secret`       | Aliyun OSS access key secret       | Yes      | -       |
| `bucket`                  | OSS bucket name                    | Yes      | -       |
| `endpoint`                | OSS endpoint URL                   | Yes      | -       |
| `prefix`                  | Path prefix for images             | No       | ""      |
| **COS Provider**          |                                    |          |         |
| `secret_id`               | Tencent COS secret ID              | Yes      | -       |
| `secret_key`              | Tencent COS secret key             | Yes      | -       |
| `bucket`                  | COS bucket name                    | Yes      | -       |
| `region`                  | COS region                         | Yes      | -       |
| **SM.MS Provider**        |                                    |          |         |
| `api_token`               | SM.MS API token                    | Yes      | -       |
| **Imgur Provider**        |                                    |          |         |
| `client_id`               | Imgur application client ID        | Yes      | -       |
| `client_secret`           | Imgur application client secret    | Yes      | -       |
| `access_token`            | Imgur user access token            | Yes      | -       |
| `refresh_token`           | Imgur refresh token                | No       | -       |
| **GitHub Provider**       |                                    |          |         |
| `token`                   | GitHub personal access token       | Yes      | -       |
| `owner`                   | Repository owner username          | Yes      | -       |
| `repo`                    | Repository name                    | Yes      | -       |
| `path`                    | Specific folder path in repository | No       | ""      |

---

## 🛠️ CLI Usage

### Quick Start Commands

```bash
# 1. Initialize configuration
host-image-backup init
# Or use short alias
hib init

# 2. Test provider connection
host-image-backup test oss
# Or use short alias
hib test oss

# 3. List available providers
host-image-backup list
# Or use short alias
hib list

# 4. Backup images from a provider
host-image-backup backup oss --output ./my-backup
# Or use short alias
hib backup oss --output ./my-backup

# 5. Backup from all enabled providers
host-image-backup backup-all --output ./full-backup
# Or use short alias
hib backup-all --output ./full-backup
```

### Command Reference

| Command         | Description                           | Aliases |
|-----------------|---------------------------------------|---------|
| `init`          | Initialize default configuration file | -       |
| `backup`        | Backup images from specific provider  | -       |
| `backup-all`    | Backup from all enabled providers     | -       |
| `list`          | List all available providers          | `list-providers` |
| `test`          | Test provider connection              | -       |
| `info`          | Show detailed provider information    | -       |

### Detailed Command Usage

#### `init` - Initialize Configuration

Create a default configuration file with all providers.

```bash
host-image-backup init
```

**Options:**

- Automatically creates config directory if needed
- Prompts before overwriting existing configuration
- Generates template with all supported providers

#### `backup` - Backup from Provider

Backup images from a specific provider to local storage.

```bash
host-image-backup backup <provider> [OPTIONS]
```

**Arguments:**

- `<provider>`: Provider name (oss, cos, sms, imgur, github)

**Options:**

```bash
-o, --output PATH           Output directory (default: ./backup)
-l, --limit INTEGER         Limit number of images to download
-c, --config PATH          Custom configuration file path
--skip-existing / --no-skip-existing  Skip existing files (default: skip)
-v, --verbose              Show detailed logs
```

**Examples:**

```bash
# Basic backup
host-image-backup backup oss
# Or use short alias
hib backup oss

# Custom output directory with limit
host-image-backup backup oss --output ~/Pictures/backup --limit 100
# Or use short alias
hib backup oss --output ~/Pictures/backup --limit 100

# Verbose backup with custom config
host-image-backup backup imgur --config ./my-config.yaml --verbose
# Or use short alias
hib backup imgur --config ./my-config.yaml --verbose

# Don't skip existing files
host-image-backup backup github --no-skip-existing
# Or use short alias
hib backup github --no-skip-existing
```

#### `backup-all` - Backup All Providers

Backup images from all enabled providers in sequence.

```bash
host-image-backup backup-all [OPTIONS]
```

**Options:**

```bash
-o, --output PATH           Output directory for all providers
-l, --limit INTEGER         Limit per provider (not total)
--skip-existing / --no-skip-existing  
                           Skip existing files for all providers
-v, --verbose              Show detailed logs
```

**Example:**

```bash
host-image-backup backup-all --output ~/backup --limit 50 --verbose
# Or use short alias
hib backup-all --output ~/backup --limit 50 --verbose
```

#### `list` - List Providers

Display all available providers and their status.

```bash
host-image-backup list
```

**Output includes:**

- Provider name
- Enabled/Disabled status
- Configuration validation status

#### `test` - Test Connection

Test connection and authentication for a specific provider.

```bash
host-image-backup test <provider>
```

**Example:**

```bash
host-image-backup test oss
host-image-backup test github
# Or use short alias
hib test oss
hib test github
```

#### `info` - Provider Information

Show detailed information about a specific provider.

```bash
host-image-backup info <provider>
```

**Information includes:**

- Provider status
- Configuration validation
- Connection test results
- Total image count (if available)

### Global Options

All commands support these global options:

```bash
-c, --config PATH          Custom configuration file path
-v, --verbose              Enable verbose logging
--help                     Show help message
```

---

## 💡 Use Cases & Examples

### Common Scenarios

- **📦 Backup & Migration**: Mirror images from cloud providers to local storage
- **🔄 Multi-Provider Aggregation**: Consolidate images from multiple services
- **⏰ Scheduled Backups**: Automate backups via cron jobs or CI/CD pipelines
- **🗂️ Archive Management**: Create organized local image archives
- **🚀 Disaster Recovery**: Maintain offline copies for business continuity

### Real-World Examples

#### Personal Photo Backup

```bash
# Backup all your personal photos from multiple services
host-image-backup backup-all --output ~/PhotoBackup
# Or use short alias
hib backup-all --output ~/PhotoBackup
```

#### Scheduled Backup (Cron)

```bash
# Add to crontab for daily backups
0 2 * * * /usr/local/bin/host-image-backup backup-all --output /backup/images --limit 100
# Or use short alias
0 2 * * * /usr/local/bin/hib backup-all --output /backup/images --limit 100
```

#### Migration Between Providers

```bash
# Step 1: Backup from old provider
host-image-backup backup old-provider --output ./migration-temp
# Or use short alias
hib backup old-provider --output ./migration-temp

# Step 2: Upload to new provider (manual or script-based)
# TODO
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### ❌ Authentication Errors

**Problem**: Invalid credentials or tokens

**Solutions**:

- Verify configuration file format and credentials
- Check token expiration dates
- Ensure proper permissions for API access
- Test individual providers: `host-image-backup test <provider>`

#### ❌ Network & Connectivity Issues

**Problem**: Connection timeouts or failures

**Solutions**:

- Check internet connectivity
- Increase timeout in configuration
- Use `--verbose` flag for detailed error information
- Verify provider service status

#### ❌ Permission & File System Errors

**Problem**: Cannot write to output directory

**Solutions**:

```bash
# Create output directory with proper permissions
mkdir -p ~/backup && chmod 755 ~/backup

# Set config file permissions for security
chmod 600 ~/.config/host-image-backup/config.yaml
```

#### ❌ Rate Limiting

**Problem**: Too many requests to provider APIs

**Solutions**:

- Reduce `max_concurrent_downloads` in configuration
- Add delays between requests
- Use `--limit` option to control download volume
- Check provider-specific rate limits

### Debug Commands

```bash
# Test specific provider connection
host-image-backup test oss --verbose
# Or use short alias
hib test oss --verbose

# Show provider detailed information
host-image-backup info github
# Or use short alias
hib info github

# Run backup with maximum verbosity
host-image-backup backup imgur --verbose --limit 5
# Or use short alias
hib backup imgur --verbose --limit 5
```

### Log Analysis

```bash
# Check recent logs
tail -f logs/host_image_backup_*.log

# Search for errors
grep -i error logs/host_image_backup_*.log

# Monitor backup progress
grep -E "(Successfully|Failed)" logs/host_image_backup_*.log
```

---

## 🔒 Security & Best Practices

### Credential Security

- **Never commit credentials** to version control
- **Use environment variables** for sensitive data when possible
- **Set restrictive file permissions** on configuration files:

```bash
chmod 600 ~/.config/host-image-backup/config.yaml
```

### Environment Variables Support

```bash
# Set credentials via environment variables
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
export GITHUB_TOKEN="ghp_your_token"

# Reference in config file
providers:
  oss:
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
```

### Network Security

- Use HTTPS endpoints only (enabled by default)
- Consider VPN or private networks for sensitive data
- Monitor network traffic for unusual patterns

---

## 🏗️ Development & Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install development dependencies with uv (recommended)
uv lock  # generate lock file
uv sync --all-extras # install all extras (dev)

# Setup pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/host_image_backup

# Run specific test file
pytest tests/test_config.py

# Run tests with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
ruff format src tests

# Type checking
mypy src

# Lint code
ruff check src tests

# Run all quality checks
make lint  # or your preferred task runner
```

### Adding New Providers

1. **Create provider class** in `src/host_image_backup/providers/`
2. **Implement required methods** from `BaseProvider`
3. **Add configuration class** in `src/host_image_backup/config.py`
4. **Update provider registry** in service and CLI modules
5. **Add comprehensive tests**
6. **Update documentation**

See [Contributing Guide](CONTRIBUTING.md) for detailed instructions.

---

## 🗺️ Roadmap

### Version 0.2.0

- [ ] **Enhanced Error Handling**: Better error messages and recovery
- [ ] **Configuration Validation**: Real-time config validation
- [ ] **Progress Persistence**: Resume interrupted backups
- [ ] **Performance Optimization**: Faster concurrent downloads

### Version 0.3.0

- [ ] **Web UI**: Browser-based configuration and monitoring
- [ ] **Database Support**: SQLite for backup metadata
- [ ] **Advanced Filtering**: Date ranges, file types, size limits
- [ ] **Cloud Integration**: Direct cloud-to-cloud transfers

### Additional Providers

- [ ] **Cloudinary**: Image management platform
- [ ] **AWS S3**: Amazon cloud storage
- [ ] **Google Drive**: Google cloud storage  
- [ ] **Dropbox**: File hosting service
- [ ] **OneDrive**: Microsoft cloud storage

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- 🐛 **Report bugs** and request features
- 📝 **Improve documentation** and examples
- 🔧 **Add new providers** or enhance existing ones
- 🧪 **Write tests** and improve code coverage
- 🎨 **Improve user experience** and CLI interface

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- All dependencies maintain their respective licenses
- See [pyproject.toml](pyproject.toml) for complete dependency list
