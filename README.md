# Host Image Backup

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

> **Host Image Backup** is a modular Python CLI tool for backing up images from various image hosting services to your local machine.

---

## Features

- Modular architecture, easy to extend
- Supports Aliyun OSS, Tencent COS, SM.MS, Imgur, GitHub
- Progress bar for backup
- Rich command-line interface
- Flexible configuration management
- Resume interrupted transfers
- Detailed logging

---

## Supported Providers

| Provider   | Supported Features                | Limitations / Notes                  |
|------------|----------------------------------|--------------------------------------|
| OSS        | List, backup, resume, skip       | Requires valid Aliyun credentials    |
| COS        | List, backup, resume, skip       | Requires valid Tencent credentials   |
| SM.MS      | List, backup                     | Public API, rate limits may apply    |
| Imgur      | List, backup                     | Requires Imgur client ID/secret      |
| GitHub     | List, backup                     | Requires GitHub token, repo access   |

---

## Installation

### Requirements

- Python 3.8+
- pip or uv
- (Recommended) virtual environment

### Dependencies

- See [pyproject.toml](pyproject.toml) for all dependencies.
- Compatible with Linux, macOS, Windows.

### Install from Source

```bash
pip install -e .
# or
uv pip install -e .
```

### Install via PyPI

```bash
pip install host-image-backup
# Or upgrade to the latest version
pip install --upgrade host-image-backup
```

---

## Configuration

The config file is located at `~/.config/host-image-backup/config.yaml`.  
Each provider section must be filled with valid credentials.

### Configuration Fields

| Field             | Description                                   |
|-------------------|-----------------------------------------------|
| access_key_id     | Aliyun OSS access key                         |
| access_key_secret | Aliyun OSS secret key                         |
| bucket            | Bucket name                                   |
| endpoint          | OSS endpoint                                  |
| prefix            | Path prefix for images                        |
| secret_id         | Tencent COS secret ID                         |
| secret_key        | Tencent COS secret key                        |
| region            | COS region                                    |
| client_id         | Imgur client ID                               |
| client_secret     | Imgur client secret                           |
| token             | GitHub token                                  |
| repo              | GitHub repository name                        |

#### Example: Aliyun OSS

```yaml
providers:
  oss:
    access_key_id: "your_access_key"
    access_key_secret: "your_secret_key"
    bucket: "your_bucket_name"
    endpoint: "oss-cn-hangzhou.aliyuncs.com"
    prefix: "images/"
```

#### Example: Tencent COS

```yaml
providers:
  cos:
    secret_id: "your_secret_id"
    secret_key: "your_secret_key"
    bucket: "your_bucket_name"
    region: "ap-guangzhou"
    prefix: "images/"
```

---

## CLI Usage

### Command Overview

| Command                | Description                                      |
|------------------------|--------------------------------------------------|
| `init`                 | Initialize config file                           |
| `backup`               | Backup images from provider                      |
| `list-providers`       | List available providers                         |
| `test`                 | Test provider connection                         |

### Command Details

#### `init`

Initialize a default config file.

```bash
host-image-backup init
```

#### `backup`

Backup images from a provider.

```bash
host-image-backup backup --provider oss --output ./backup
```

**Options:**

- `--provider <name>`: Specify provider (oss, cos, smms, imgur, github)
- `--output <dir>`: Output directory for backups
- `--config <path>`: Use custom config file
- `--limit <n>`: Limit number of images to download
- `--skip-existing`: Skip files already downloaded
- `--verbose`: Show detailed logs

#### `list-providers`

List all available providers.

```bash
host-image-backup list-providers
```

#### `test`

Test connection to a provider.

```bash
host-image-backup test --provider oss
```

---

## Typical Use Cases

- Mirror images from cloud providers to local disk for backup or migration.
- Aggregate images from multiple providers into a unified local archive.
- Automate scheduled backups via cron or CI/CD.

---

## Error Handling & FAQ

### Common Issues

- **Invalid credentials**: Check your config file for typos.
- **Network errors**: Ensure internet connectivity.
- **Rate limits**: Some providers (SM.MS, Imgur) may restrict requests.
- **Permission denied**: Verify access rights for output directory.

### Troubleshooting

- Run with `--verbose` for detailed logs.
- Check log files in the output directory.
- For provider-specific issues, consult their official docs.

---

## Security Notes

- **Credential Protection**: Never share your config file or credentials publicly.
- Use environment variables or secret managers for sensitive data if possible.
- Restrict file permissions for config files (`chmod 600 ~/.config/host-image-backup/config.yaml`).

---

## Extending & Custom Providers

- To add a new provider, implement a subclass in `src/host_image_backup/providers/`.
- See [src/host_image_backup/providers/base.py](src/host_image_backup/providers/base.py) for the provider interface.
- Contributions for new providers are welcome!

---

## Project Roadmap

- [ ] Add more image hosting providers
- [ ] Web UI for configuration and monitoring
- [ ] Scheduled backup support
- [ ] Enhanced error reporting
- [ ] Multi-threaded download

---

## Development

### Environment Setup

```bash
git clone git@github.com:WayneXuCN/HostImageBackup.git
cd HostImageBackup
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -e ".[dev]"
pre-commit install
```

### Testing

```bash
pytest
```

### Formatting

```bash
black src tests
```

### Type Checking

```bash
mypy src
```

---

## Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/foo`)
3. Commit your changes (`git commit -am 'Add foo feature'`)
4. Push to the branch (`git push origin feature/foo`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Community & Support

- GitHub Issues: [Submit here](https://github.com/WayneXuCN/HostImageBackup/issues)
- Discussions: [GitHub Discussions](https://github.com/WayneXuCN/HostImageBackup/discussions)
- Email: [wayne.xu.cn@gmail.com](mailto:wayne.xu.cn@gmail.com)

---

## License

MIT License
