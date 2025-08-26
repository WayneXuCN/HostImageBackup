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

> **Host Image Backup** 是一个模块化的 Python CLI 工具，可以轻松地将图像从各种图像托管（图床）服务备份到本地机器。

## 功能特性

- 模块化架构：轻松扩展新提供商
- 多提供商支持：阿里云 OSS、腾讯 COS、SM.MS、Imgur、GitHub
- 可视化进度：备份操作的进度条
- 丰富的 CLI 界面：直观的命令行体验
- 灵活配置：基于 YAML 的配置管理
- 断点续传：继续中断的传输
- 全面日志：详细的操作日志
- 完善测试：具有测试覆盖率的可靠工具
- 上传支持：将图像上传到云存储
- 数据管理：跟踪备份操作和文件
- 批量操作：一次上传多个文件
- 重复检测：查找和管理重复文件
- 图像压缩：高质量压缩与质量控制

---

## 支持的提供商

| 提供商     | 功能                                        | 备注                              |
|------------|---------------------------------------------|-----------------------------------|
| OSS        | 列表、备份、上传、删除、文件信息            | 需要阿里云凭证                    |
| COS        | 列表、备份、上传、删除、文件信息            | 需要腾讯云凭证                    |
| SM.MS      | 列表、备份                                  | 公共 API，适用速率限制            |
| Imgur      | 列表、备份                                  | 需要 Imgur 客户端 ID/密钥         |
| GitHub     | 列表、备份                                  | 需要 GitHub 令牌和访问权限        |

---

## 安装

**要求：**

- Python 3.10 或更高版本
- pip 或 uv 包管理器

**从 PyPI 安装：**

```bash
pip install host-image-backup
pip install --upgrade host-image-backup
host-image-backup --help
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

## 配置

**快速开始：**

```bash
host-image-backup init
# 编辑配置文件：
# Linux/macOS: ~/.config/host-image-backup/config.yaml
# Windows: %APPDATA%/host-image-backup/config.yaml
```

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
    refresh_token: "your_refresh_token"
  github:
    enabled: false
    token: "ghp_your_personal_access_token"
    owner: "your_username"
    repo: "your_repository"
    path: "images"
```

**配置字段：**

| 字段                      | 描述                           | 必需 | 默认值      |
|---------------------------|--------------------------------|------|-------------|
| default_output_dir        | 备份目录                       | 否   | "./backup"  |
| max_concurrent_downloads  | 并行下载数                     | 否   | 5           |
| timeout                   | 请求超时（秒）                 | 否   | 30          |
| retry_count               | 重试次数                       | 否   | 3           |
| log_level                 | 日志级别                       | 否   | "INFO"      |
| access_key_id             | 阿里云 OSS 访问密钥 ID         | 是   | -           |
| access_key_secret         | 阿里云 OSS 访问密钥密钥        | 是   | -           |
| bucket                    | OSS/COS 存储桶名称             | 是   | -           |
| endpoint                  | OSS 端点 URL                   | 是   | -           |
| region                    | COS 区域                       | 是   | -           |
| secret_id                 | 腾讯云 COS 密钥 ID             | 是   | -           |
| secret_key                | 腾讯云 COS 密钥密钥            | 是   | -           |
| api_token                 | SM.MS API 令牌                 | 是   | -           |
| client_id                 | Imgur 客户端 ID                | 是   | -           |
| client_secret             | Imgur 客户端密钥               | 是   | -           |
| access_token              | Imgur 访问令牌                 | 是   | -           |
| refresh_token             | Imgur 刷新令牌                 | 否   | -           |
| token                     | GitHub 令牌                    | 是   | -           |
| owner                     | GitHub 仓库所有者              | 是   | -           |
| repo                      | GitHub 仓库名称                | 是   | -           |
| path                      | 仓库中的文件夹路径             | 否   | ""          |

---

## CLI 使用

**快速开始：**

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

**命令组：**

| 组         | 命令                   | 描述                               |
|------------|------------------------|------------------------------------|
| 配置       | config init            | 初始化配置文件                     |
| 提供商     | provider list          | 列出提供商                         |
|            | provider test          | 测试提供商连接                     |
|            | provider info          | 显示提供商信息                     |
| 备份       | backup start           | 从特定提供商备份                   |
|            | backup all             | 从所有启用的提供商备份             |
| 上传       | upload file            | 上传单个图像                       |
|            | upload directory       | 上传多个图像                       |
| 数据       | data stats             | 显示备份统计信息                   |
|            | data history           | 显示备份历史                       |
|            | data duplicates        | 查找重复文件                       |
|            | data cleanup           | 清理备份文件                       |
|            | data verify            | 验证备份文件完整性                 |
|            | data compress          | 压缩图像                           |

**示例：**

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

**全局选项：**

```bash
-c, --config PATH    自定义配置文件路径
-v, --verbose        启用详细日志
--help               显示帮助信息
```

---

## 使用场景

- 将图像从云提供商备份并迁移到本地存储
- 聚合来自多个服务的图像
- 自动化计划备份（cron 作业，CI/CD）
- 存档管理以组织本地图像存储
- 灾难恢复：维护离线副本

**示例：**

```bash
host-image-backup backup all --output ~/PhotoBackup
hib backup all --output ~/PhotoBackup

# 计划备份（cron）
0 2 * * * /usr/local/bin/host-image-backup backup all --output /backup/images --limit 100
0 2 * * * /usr/local/bin/hib backup all --output /backup/images --limit 100

# 提供商之间迁移
host-image-backup backup start old-provider --output ./migration-temp
hib backup start old-provider --output ./migration-temp
```

---

## 故障排除

**认证错误：**

- 检查凭据和配置文件格式
- 验证令牌过期和权限
- 测试提供商：`host-image-backup provider test <provider>`

**网络问题：**

- 检查网络连接
- 在配置中增加超时时间
- 使用 `--verbose` 获取详细信息
- 检查提供商服务状态

**文件系统错误：**

- 确保输出目录存在且可写

```bash
mkdir -p ~/backup && chmod 755 ~/backup
chmod 600 ~/.config/host-image-backup/config.yaml
```

**速率限制：**

- 降低 [max_concurrent_downloads](file:///Volumes/Work/DevSpace/01_APP/HostImageBackup/src/host_image_backup/config.py#L29-L29)
- 在请求之间添加延迟
- 使用 `--limit` 控制下载量

**调试：**

```bash
host-image-backup provider test oss --verbose
hib provider test oss --verbose
host-image-backup provider info github
hib provider info github
host-image-backup backup start imgur --verbose --limit 5
hib backup start imgur --verbose --limit 5
```

**日志分析：**

```bash
tail -f logs/host_image_backup_*.log
grep -i error logs/host_image_backup_*.log
grep -E "(Successfully|Failed)" logs/host_image_backup_*.log
```

---

## 安全性

- 切勿将凭据提交到版本控制
- 使用环境变量存储敏感数据
- 设置配置文件的限制性权限：

```bash
chmod 600 ~/.config/host-image-backup/config.yaml
```

**环境变量示例：**

```bash
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
export GITHUB_TOKEN="ghp_your_token"
```

在配置中引用：

```yaml
providers:
  oss:
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
```

- 使用 HTTPS 端点
- 考虑使用 VPN/私有网络处理敏感数据

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
pytest --cov=src/host_image_backup
pytest tests/test_config.py
pytest -v
```

**代码质量：**

```bash
ruff format src tests
mypy src
ruff check src tests
make lint
```

**添加新提供商：**

1. 在 `src/host_image_backup/providers/` 中创建提供商类
2. 实现来自 `BaseProvider` 的必需方法
3. 在 `src/host_image_backup/config/config_models.py` 中添加配置类
4. 在 `src/host_image_backup/providers/provider_manager.py` 中更新提供商注册表
5. 添加测试

---

## 路线图

**计划功能：**

- 增强的错误处理
- 配置验证
- 中断备份的进度持久化
- 性能优化

**未来版本：**

- 用于配置和监控的 Web UI
- 高级过滤（日期、类型、大小）
- 云到云传输
- 增量备份

**其他提供商：**

- Cloudinary
- AWS S3
- Google Drive
- Dropbox
- OneDrive

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
