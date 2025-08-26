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

> **Host Image Backup** 是一个模块化的 Python CLI 工具，可以轻松地将图像从各种图像托管服务备份到本地机器。

## 功能特性

- **多提供商支持**：阿里云 OSS、腾讯 COS、SM.MS、Imgur、GitHub
- **灵活操作**：备份、上传、压缩图像
- **丰富 CLI 界面**：直观的命令行体验，带进度条
- **可配置**：基于 YAML 的配置，支持环境变量
- **可靠**：全面的日志记录、元数据跟踪和重复文件检测
- **可扩展**：插件系统支持添加新提供商

---

## 支持的提供商

| 提供商   | 操作                  | 备注                        |
|----------|-----------------------|-----------------------------|
| OSS      | 列表、备份、上传      | 需要阿里云凭证              |
| COS      | 列表、备份、上传      | 需要腾讯云凭证              |
| SM.MS    | 列表、备份            | 公共 API，有速率限制        |
| Imgur    | 列表、备份            | 需要 Imgur 客户端 ID/密钥   |
| GitHub   | 列表、备份            | 需要 GitHub 令牌            |

---

## 安装

**要求：**

- Python 3.10 或更高版本
- pip 或 uv 包管理器

**从 PyPI 安装：**

```bash
pip install host-image-backup
host-image-backup --help
# 或使用简短别名：
hib --help
```

**开发安装：**

```bash
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup
uv lock
uv sync --all-extras
# 或使用 pip：
pip install -e ".[dev]"
```

---

## 快速开始

1. **初始化配置：**
   ```bash
   host-image-backup config init
   ```

2. **编辑配置文件：**
   - Linux/macOS: `~/.config/host-image-backup/config.yaml`
   - Windows: `%APPDATA%/host-image-backup/config.yaml`

3. **测试提供商连接：**
   ```bash
   host-image-backup provider test oss
   ```

4. **备份图像：**
   ```bash
   host-image-backup backup start oss --output ./my-backup
   ```

---

## CLI 使用

```bash
# 列出所有提供商
host-image-backup provider list

# 从特定提供商备份
host-image-backup backup start oss

# 从所有启用的提供商备份
host-image-backup backup all

# 上传单个图像
host-image-backup upload file oss /path/to/image.jpg

# 上传多个图像
host-image-backup upload directory oss /path/to/images/

# 压缩图像
host-image-backup data compress /path/to/images/ --quality 85

# 查看备份统计信息
host-image-backup data stats

# 查找重复文件
host-image-backup data duplicates
```

---

## 配置

**配置示例：**

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

**使用环境变量：**

```bash
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
```

在配置中引用：
```yaml
providers:
  oss:
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
```

---

## 开发

**设置：**

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

**运行：**

```bash
uv run -m host_image_backup.cli
```

**测试：**

```bash
pytest
```

**代码质量：**

```bash
ruff format src tests
mypy src
ruff check src tests
```

---

## 贡献

欢迎贡献！

- 报告错误和请求功能
- 改进文档和示例
- 添加或增强提供商
- 编写测试并提高覆盖率
- 改进 CLI 和用户体验

---

## 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。