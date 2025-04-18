# UV 支持说明

## UV 简介

UV是一个现代化的Python依赖管理和虚拟环境工具，由Astral(前身为Sentry)开发，使用Rust编写。它旨在解决pip和conda在速度、可靠性和用户体验方面的不足。

## UV 相比 pip 和 conda 的优势

### 速度优势
- **极快的依赖解析**: UV的依赖解析速度比pip快10-100倍
- **并行下载**: 同时下载多个包，大大减少安装时间
- **预编译轮子**: 优先使用预编译的轮子，减少从源代码构建的需要
- **缓存机制**: 智能缓存已下载的包，减少重复下载

### 可靠性优势
- **确定性安装**: 生成锁文件确保在不同环境中获得相同的依赖版本
- **解决依赖冲突**: 更强大的依赖冲突解决算法
- **原子操作**: 安装要么完全成功，要么完全失败，不会留下半完成状态
- **权限问题更少**: 更好地处理文件权限问题

### 用户体验优势
- **统一的命令接口**: 集成了虚拟环境管理和包管理功能
- **更好的错误信息**: 提供更清晰的错误消息和解决建议
- **与现代工具兼容**: 完全支持pyproject.toml和PEP 621标准
- **无需额外安装**: 单个可执行文件，不需要预先安装Python

## 如何使用UV安装getcity

### 安装UV
```bash
# 使用pip安装UV
pip install uv

# 或者按照官方文档的其他安装方式
# https://github.com/astral-sh/uv
```

### 使用UV安装getcity
```bash
# 基本安装
uv pip install getcity

# 安装带Web界面的版本
uv pip install "getcity[web]"

# 安装开发版本
uv pip install "getcity[dev]"

# 从GitHub直接安装
uv pip install git+https://github.com/yourusername/getcity.git
```

### 使用UV创建虚拟环境并安装getcity
```bash
# 创建新的虚拟环境并安装getcity
uv venv .venv
uv pip install -e . --venv .venv
```

## 为什么getcity支持UV？

我们为getcity添加了UV支持，因为：

1. **更快的安装体验**: 特别是对于有多个依赖的web界面版本
2. **更一致的开发环境**: 为所有贡献者提供一致的依赖版本
3. **更少的依赖问题**: 减少用户在不同操作系统上可能遇到的安装问题
4. **拥抱Python生态系统的未来**: UV代表了Python包管理的未来方向

## getcity的UV特定配置

在`pyproject.toml`中，我们添加了UV特定的配置:

```toml
[tool.uv]
exclude = ["tests"]
requirements = ["requirements.txt"]
resolution = "highest"
```

这些配置确保UV能够以最优的方式处理getcity的依赖。 