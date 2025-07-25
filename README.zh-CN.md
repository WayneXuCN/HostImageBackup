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

> **Host Image Backup** 是一个模块化的 Python CLI 工具，可轻松将图像从各种图像托管服务备份到您的本地机器。

---

## ✨ 特性

- 🏗️ **模块化架构** - 易于扩展新的提供商
- 🌐 **多提供商支持** - 阿里云 OSS、腾讯 COS、SM.MS、Imgur、GitHub
- 📊 **可视化进度** - 美观的备份操作进度条
- 🎨 **丰富的 CLI 界面** - 直观的命令行体验
- ⚙️ **灵活配置** - 基于 YAML 的配置管理
- 🔄 **断点续传支持** - 无缝继续中断的传输
- 📝 **全面日志记录** - 详细的操作日志
- 🧪 **良好测试** - 全面的测试覆盖以确保可靠性

---

## 🚀 支持的提供商

| 提供商     | 功能                             | 备注                              |
|------------|----------------------------------|-----------------------------------|
| **OSS**    | ✅ 列表、备份、恢复、跳过        | 需要阿里云凭证                    |
| **COS**    | ✅ 列表、备份、恢复、跳过        | 需要腾讯云凭证                    |
| **SM.MS**  | ✅ 列表、备份                    | 公共 API，适用速率限制            |
| **Imgur**  | ✅ 列表、备份                    | 需要 Imgur 客户端 ID/密钥         |
| **GitHub** | ✅ 列表、备份                    | 需要 GitHub 令牌和访问权限        |

---

## 📦 安装

### 要求

- **Python 3.10+** (推荐最新稳定版本)
- **pip** 或 **uv** 包管理器

### 快速安装

```bash
# 从 PyPI 安装
pip install host-image-backup

# 或升级到最新版本
pip install --upgrade host-image-backup

# 验证安装
host-image-backup --help
# 或使用短别名
hib --help
```

### 开发安装

```bash
# 克隆仓库
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup

# 使用 uv 安装开发依赖 (推荐)
uv lock  # 生成锁文件
uv sync --all-extras # 安装所有额外依赖 (dev)

# 或者如果您喜欢使用 pip
pip install -e ".[dev]"
```

---

## ⚙️ 配置

### 快速开始

```bash
# 初始化配置文件
host-image-backup init

# 编辑生成的配置文件
# Linux/macOS: ~/.config/host-image-backup/config.yaml
# Windows: %APPDATA%/host-image-backup/config.yaml
```

### 配置结构

```yaml
# 全局设置
default_output_dir: "./backup"
max_concurrent_downloads: 5
timeout: 30
retry_count: 3
log_level: "INFO"

# 提供商配置
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
    path: "images"  # 可选: 特定文件夹路径
```

### 配置字段参考

| 字段                      | 描述                              | 必需 | 默认值 |
|---------------------------|-----------------------------------|------|--------|
| **全局设置**              |                                   |      |        |
| `default_output_dir`      | 默认备份目录                      | 否   | "./backup" |
| `max_concurrent_downloads`| 最大并行下载数                    | 否   | 5       |
| `timeout`                 | 请求超时时间 (秒)                 | 否   | 30      |
| `retry_count`             | 下载失败重试次数                  | 否   | 3       |
| `log_level`               | 日志级别                          | 否   | "INFO"  |
| **OSS 提供商**            |                                   |      |        |
| `access_key_id`           | 阿里云 OSS 访问密钥 ID            | 是   | -       |
| `access_key_secret`       | 阿里云 OSS 访问密钥密钥           | 是   | -       |
| `bucket`                  | OSS 存储桶名称                    | 是   | -       |
| `endpoint`                | OSS 终端节点 URL                  | 是   | -       |
| `prefix`                  | 图像路径前缀                      | 否   | ""      |
| **COS 提供商**            |                                   |      |        |
| `secret_id`               | 腾讯云 COS 密钥 ID                | 是   | -       |
| `secret_key`              | 腾讯云 COS 密钥密钥               | 是   | -       |
| `bucket`                  | COS 存储桶名称                    | 是   | -       |
| `region`                  | COS 区域                          | 是   | -       |
| **SM.MS 提供商**          |                                   |      |        |
| `api_token`               | SM.MS API 令牌                    | 是   | -       |
| **Imgur 提供商**          |                                   |      |        |
| `client_id`               | Imgur 应用客户端 ID               | 是   | -       |
| `client_secret`           | Imgur 应用客户端密钥              | 是   | -       |
| `access_token`            | Imgur 用户访问令牌                | 是   | -       |
| `refresh_token`           | Imgur 刷新令牌                    | 否   | -       |
| **GitHub 提供商**         |                                   |      |        |
| `token`                   | GitHub 个人访问令牌               | 是   | -       |
| `owner`                   | 仓库所有者用户名                  | 是   | -       |
| `repo`                    | 仓库名称                          | 是   | -       |
| `path`                    | 仓库中的特定文件夹路径            | 否   | ""      |

---

## 🛠️ CLI 使用

### 快速开始命令

```bash
# 1. 初始化配置
host-image-backup init
# 或使用短别名
hib init

# 2. 测试提供商连接
host-image-backup test oss
# 或使用短别名
hib test oss

# 3. 列出可用提供商
host-image-backup list
# 或使用短别名
hib list

# 4. 从提供商备份图像
host-image-backup backup oss --output ./my-backup
# 或使用短别名
hib backup oss --output ./my-backup

# 5. 从所有启用的提供商备份
host-image-backup backup-all --output ./full-backup
# 或使用短别名
hib backup-all --output ./full-backup
```

### 命令参考

| 命令           | 描述                                | 别名 |
|----------------|-------------------------------------|------|
| `init`         | 初始化默认配置文件                  | -    |
| `backup`       | 从特定提供商备份图像                | -    |
| `backup-all`   | 从所有启用的提供商备份              | -    |
| `list`         | 列出所有可用提供商                  | `list-providers` |
| `test`         | 测试提供商连接                      | -    |
| `info`         | 显示详细的提供商信息                | -    |

### 详细命令使用

#### `init` - 初始化配置

创建包含所有提供商的默认配置文件。

```bash
host-image-backup init
```

**选项:**

- 如果需要，自动创建配置目录
- 覆盖现有配置前提示
- 生成包含所有支持提供商的模板

#### `backup` - 从提供商备份

从特定提供商备份图像到本地存储。

```bash
host-image-backup backup <provider> [OPTIONS]
```

**参数:**

- `<provider>`: 提供商名称 (oss, cos, sms, imgur, github)

**选项:**

```bash
-o, --output PATH           输出目录 (默认: ./backup)
-l, --limit INTEGER         限制下载图像数量
-c, --config PATH          自定义配置文件路径
--skip-existing / --no-skip-existing  跳过现有文件 (默认: 跳过)
-v, --verbose              显示详细日志
```

**示例:**

```bash
# 基本备份
host-image-backup backup oss
# 或使用短别名
hib backup oss

# 自定义输出目录和限制
host-image-backup backup oss --output ~/Pictures/backup --limit 100
# 或使用短别名
hib backup oss --output ~/Pictures/backup --limit 100

# 使用自定义配置的详细备份
host-image-backup backup imgur --config ./my-config.yaml --verbose
# 或使用短别名
hib backup imgur --config ./my-config.yaml --verbose

# 不跳过现有文件
host-image-backup backup github --no-skip-existing
# 或使用短别名
hib backup github --no-skip-existing
```

#### `backup-all` - 备份所有提供商

按顺序从所有启用的提供商备份图像。

```bash
host-image-backup backup-all [OPTIONS]
```

**选项:**

```bash
-o, --output PATH           所有提供商的输出目录
-l, --limit INTEGER         每个提供商的限制 (非总数)
--skip-existing / --no-skip-existing  
                           为所有提供商跳过现有文件
-v, --verbose              显示详细日志
```

**示例:**

```bash
host-image-backup backup-all --output ~/backup --limit 50 --verbose
# 或使用短别名
hib backup-all --output ~/backup --limit 50 --verbose
```

#### `list` - 列出提供商

显示所有可用提供商及其状态。

```bash
host-image-backup list
```

**输出包括:**

- 提供商名称
- 启用/禁用状态
- 配置验证状态

#### `test` - 测试连接

测试特定提供商的连接和身份验证。

```bash
host-image-backup test <provider>
```

**示例:**

```bash
host-image-backup test oss
host-image-backup test github
# 或使用短别名
hib test oss
hib test github
```

#### `info` - 提供商信息

显示特定提供商的详细信息。

```bash
host-image-backup info <provider>
```

**信息包括:**

- 提供商状态
- 配置验证
- 连接测试结果
- 总图像数量 (如果可用)

### 全局选项

所有命令都支持这些全局选项:

```bash
-c, --config PATH          自定义配置文件路径
-v, --verbose              启用详细日志记录
--help                     显示帮助信息
```

---

## 💡 使用场景和示例

### 常见场景

- **📦 备份和迁移**: 将图像从云提供商镜像到本地存储
- **🔄 多提供商聚合**: 整合来自多个服务的图像
- **⏰ 定时备份**: 通过 cron 作业或 CI/CD 管道自动备份
- **🗂️ 归档管理**: 创建有组织的本地图像归档
- **🚀 灾难恢复**: 维护离线副本以确保业务连续性

### 实际示例

#### 个人照片备份

```bash
# 从多个服务备份所有个人照片
host-image-backup backup-all --output ~/PhotoBackup
# 或使用短别名
hib backup-all --output ~/PhotoBackup
```

#### 定时备份 (Cron)

```bash
# 添加到 crontab 进行每日备份
0 2 * * * /usr/local/bin/host-image-backup backup-all --output /backup/images --limit 100
# 或使用短别名
0 2 * * * /usr/local/bin/hib backup-all --output /backup/images --limit 100
```

#### 提供商间迁移

```bash
# 步骤 1: 从旧提供商备份
host-image-backup backup old-provider --output ./migration-temp
# 或使用短别名
hib backup old-provider --output ./migration-temp

# 步骤 2: 上传到新提供商 (手动或基于脚本)
# TODO
```

---

## 🔧 故障排除

### 常见问题和解决方案

#### ❌ 身份验证错误

**问题**: 凭证或令牌无效

**解决方案**:

- 验证配置文件格式和凭证
- 检查令牌过期日期
- 确保 API 访问权限正确
- 测试单个提供商: `host-image-backup test <provider>`

#### ❌ 网络和连接问题

**问题**: 连接超时或失败

**解决方案**:

- 检查互联网连接
- 增加配置中的超时时间
- 使用 `--verbose` 标志获取详细错误信息
- 验证提供商服务状态

#### ❌ 权限和文件系统错误

**问题**: 无法写入输出目录

**解决方案**:

```bash
# 创建具有适当权限的输出目录
mkdir -p ~/backup && chmod 755 ~/backup

# 为安全起见设置配置文件权限
chmod 600 ~/.config/host-image-backup/config.yaml
```

#### ❌ 速率限制

**问题**: 对提供商 API 的请求过多

**解决方案**:

- 减少配置中的 `max_concurrent_downloads`
- 在请求之间添加延迟
- 使用 `--limit` 选项控制下载量
- 检查提供商特定的速率限制

### 调试命令

```bash
# 测试特定提供商连接
host-image-backup test oss --verbose
# 或使用短别名
hib test oss --verbose

# 显示提供商详细信息
host-image-backup info github
# 或使用短别名
hib info github

# 使用最大详细程度运行备份
host-image-backup backup imgur --verbose --limit 5
# 或使用短别名
hib backup imgur --verbose --limit 5
```

### 日志分析

```bash
# 检查最近日志
tail -f logs/host_image_backup_*.log

# 搜索错误
grep -i error logs/host_image_backup_*.log

# 监控备份进度
grep -E "(Successfully|Failed)" logs/host_image_backup_*.log
```

---

## 🔒 安全和最佳实践

### 凭证安全

- **切勿将凭证提交到版本控制**
- **尽可能使用环境变量存储敏感数据**
- **在配置文件上设置限制性文件权限**:

```bash
chmod 600 ~/.config/host-image-backup/config.yaml
```

### 环境变量支持

```bash
# 通过环境变量设置凭证
export OSS_ACCESS_KEY_ID="your_key"
export OSS_ACCESS_KEY_SECRET="your_secret"
export GITHUB_TOKEN="ghp_your_token"

# 在配置文件中引用
providers:
  oss:
    access_key_id: "${OSS_ACCESS_KEY_ID}"
    access_key_secret: "${OSS_ACCESS_KEY_SECRET}"
```

### 网络安全

- 仅使用 HTTPS 终端节点 (默认启用)
- 考虑为敏感数据使用 VPN 或私有网络
- 监控网络流量中的异常模式

---

## 🏗️ 开发和贡献

### 开发设置

```bash
# 克隆仓库
git clone https://github.com/WayneXuCN/HostImageBackup.git
cd HostImageBackup

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 使用 uv 安装开发依赖 (推荐)
uv lock  # 生成锁文件
uv sync --all-extras # 安装所有额外依赖 (dev)

# 设置 pre-commit 钩子
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=src/host_image_backup

# 运行特定测试文件
pytest tests/test_config.py

# 运行带详细输出的测试
pytest -v
```

### 代码质量

```bash
# 格式化代码
ruff format src tests

# 类型检查
mypy src

# 代码检查
ruff check src tests

# 运行所有质量检查
make lint  # 或您喜欢的任务运行器
```

### 添加新提供商

1. **在 `src/host_image_backup/providers/` 中创建提供商类**
2. **从 [BaseProvider](file:///Volumes/Work/DevSpace/01_APP/HostImageBackup/src/host_image_backup/providers/base.py#L10-L51) 实现所需方法**
3. **在 `src/host_image_backup/config.py` 中添加配置类**
4. **在服务和 CLI 模块中更新提供商注册表**
5. **添加全面的测试**
6. **更新文档**

有关详细说明，请参见 [贡献指南](CONTRIBUTING.md)。

---

## 🗺️ 路线图

### 版本 0.2.0

- [ ] **增强错误处理**: 更好的错误消息和恢复
- [ ] **配置验证**: 实时配置验证
- [ ] **进度持久化**: 恢复中断的备份
- [ ] **性能优化**: 更快的并发下载

### 版本 0.3.0

- [ ] **Web UI**: 基于浏览器的配置和监控
- [ ] **数据库支持**: 用于备份元数据的 SQLite
- [ ] **高级过滤**: 日期范围、文件类型、大小限制
- [ ] **云集成**: 直接云到云传输

### 其他提供商

- [ ] **Cloudinary**: 图像管理平台
- [ ] **AWS S3**: 亚马逊云存储
- [ ] **Google Drive**: 谷歌云存储  
- [ ] **Dropbox**: 文件托管服务
- [ ] **OneDrive**: 微软云存储

---

## 🤝 贡献

欢迎贡献！您可以通过以下方式提供帮助：

- 🐛 **报告错误** 和请求功能
- 📝 **改进文档** 和示例
- 🔧 **添加新提供商** 或增强现有提供商
- 🧪 **编写测试** 和提高代码覆盖率
- 🎨 **改进用户体验** 和 CLI 界面

---

## 📄 许可证

本项目采用 **MIT 许可证** - 有关详细信息，请参见 [LICENSE](LICENSE) 文件。

### 第三方许可证

- 所有依赖项保留其各自的许可证
- 有关完整依赖项列表，请参见 [pyproject.toml](pyproject.toml)