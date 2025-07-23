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

> **Host Image Backup** 是一个模块化的 Python 命令行工具，支持从多种图床服务备份图片到本地。

---

## 功能特性

- 模块化架构，易于扩展
- 支持阿里云 OSS、腾讯云 COS、SM.MS、Imgur、GitHub
- 备份进度条显示
- 丰富的命令行界面
- 灵活的配置管理
- 支持断点续传
- 详细日志记录

---

## 支持的图床

| 图床      | 支持功能                   | 限制说明                       |
|-----------|----------------------------|--------------------------------|
| OSS       | 列表、备份、断点续传、跳过 | 需有效阿里云凭据               |
| COS       | 列表、备份、断点续传、跳过 | 需有效腾讯云凭据               |
| SM.MS     | 列表、备份                 | 公共 API，可能有速率限制        |
| Imgur     | 列表、备份                 | 需 Imgur client ID/secret      |
| GitHub    | 列表、备份                 | 需 GitHub token 和仓库权限      |

---

## 安装

### 环境要求

- Python 3.8+
- pip 或 uv
- （推荐）虚拟环境

### 依赖说明

- 详见 [pyproject.toml](pyproject.toml)。
- 兼容 Linux、macOS、Windows。

### 源码安装

```bash
pip install -e .
# 或
uv pip install -e .
```

### 通过 PyPI 安装

```bash
pip install host-image-backup
# 升级到最新版
pip install --upgrade host-image-backup
```

---

## 配置说明

配置文件位于 `~/.config/host-image-backup/config.yaml`。  
每个图床需填写有效凭据。

### 配置字段说明

| 字段             | 说明                         |
|------------------|------------------------------|
| access_key_id    | 阿里云 OSS access key        |
| access_key_secret| 阿里云 OSS secret key        |
| bucket           | 存储桶名称                   |
| endpoint         | OSS 访问端点                 |
| prefix           | 图片路径前缀                 |
| secret_id        | 腾讯云 COS secret ID         |
| secret_key       | 腾讯云 COS secret key        |
| region           | COS 区域                     |
| client_id        | Imgur client ID              |
| client_secret    | Imgur client secret          |
| token            | GitHub token                 |
| repo             | GitHub 仓库名称              |

#### 示例：阿里云 OSS

```yaml
providers:
  oss:
    access_key_id: "your_access_key"
    access_key_secret: "your_secret_key"
    bucket: "your_bucket_name"
    endpoint: "oss-cn-hangzhou.aliyuncs.com"
    prefix: "images/"
```

#### 示例：腾讯云 COS

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

## 命令行用法

### 命令总览

| 命令                  | 说明                                 |
|-----------------------|--------------------------------------|
| `init`                | 初始化配置文件                       |
| `backup`              | 从指定图床备份图片                   |
| `list-providers`      | 列出支持的图床                       |
| `test`                | 测试图床连接                         |

### 命令详解

#### `init`

初始化默认配置文件。

```bash
host-image-backup init
```

#### `backup`

从指定图床备份图片。

```bash
host-image-backup backup --provider oss --output ./backup
```

**常用参数：**

- `--provider <name>`：指定图床（oss, cos, smms, imgur, github）
- `--output <dir>`：备份输出目录
- `--config <path>`：自定义配置文件路径
- `--limit <n>`：限制下载图片数量
- `--skip-existing`：跳过已下载文件
- `--verbose`：显示详细日志

#### `list-providers`

列出所有支持的图床。

```bash
host-image-backup list-providers
```

#### `test`

测试指定图床连接。

```bash
host-image-backup test --provider oss
```

---

## 典型用例场景

- 将云端图床图片镜像备份到本地磁盘，便于迁移或归档。
- 聚合多图床图片到统一本地目录，便于统一管理。
- 结合定时任务或 CI/CD 自动化定期备份。

---

## 错误处理与常见问题

### 常见问题

- **凭据无效**：请检查配置文件是否有拼写错误。
- **网络错误**：请确保网络连接正常。
- **速率限制**：部分图床（如 SM.MS、Imgur）可能限制请求频率。
- **权限不足**：请确认输出目录有写入权限。

### 排查建议

- 使用 `--verbose` 参数获取详细日志。
- 检查输出目录下的日志文件。
- 针对图床相关问题，请参考其官方文档。

---

## 安全性说明

- **凭据保护**：请勿公开分享你的配置文件或凭据。
- 建议使用环境变量或密钥管理工具存储敏感信息。
- 配置文件建议设置权限为仅自己可读写（`chmod 600 ~/.config/host-image-backup/config.yaml`）。

---

## 扩展与自定义开发

- 新增图床支持：在 `src/host_image_backup/providers/` 下实现子类。
- 参考 [src/host_image_backup/providers/base.py](src/host_image_backup/providers/base.py) 了解 provider 接口。
- 欢迎贡献新 provider！

---

## 项目路线图

- [ ] 增加更多图床支持
- [ ] 提供 Web UI 配置与监控
- [ ] 支持定时自动备份
- [ ] 错误报告增强
- [ ] 多线程下载优化

---

## 开发与测试

### 环境搭建

```bash
git clone git@github.com:WayneXuCN/HostImageBackup.git
cd HostImageBackup
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -e ".[dev]"
pre-commit install
```

### 测试

```bash
pytest
```

### 代码格式化

```bash
black src tests
```

### 类型检查

```bash
mypy src
```

---

## 贡献流程

1. Fork 仓库
2. 创建分支 (`git checkout -b feature/foo`)
3. 提交更改 (`git commit -am 'Add foo feature'`)
4. 推送分支 (`git push origin feature/foo`)
5. 创建 Pull Request

详细流程请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 社区与支持

- GitHub Issues：[提交问题](https://github.com/WayneXuCN/HostImageBackup/issues)
- 讨论区：[GitHub Discussions](https://github.com/WayneXuCN/HostImageBackup/discussions)
- 邮箱：[wayne.xu.cn@gmail.com](mailto:wayne.xu.cn@gmail.com)

---

## 许可证

MIT License
