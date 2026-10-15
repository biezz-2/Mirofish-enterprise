FROM python:3.11

# 安装 Node.js （满足 >=18）及必要工具
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# 从 uv 官方镜像复制 uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# 创建非 root 用户 (appuser) 和用户组 (appgroup)
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin -c "Docker image user" appuser

WORKDIR /app
RUN chown -R appuser:appgroup /app

# 先复制依赖描述文件以利用缓存
COPY --chown=appuser:appgroup package.json package-lock.json ./
COPY --chown=appuser:appgroup frontend/package.json frontend/package-lock.json ./frontend/
COPY --chown=appuser:appgroup backend/pyproject.toml backend/uv.lock ./backend/

# 安装依赖（Node + Python），临时切换回root或保留权限
# 使用 appuser 运行安装
USER appuser

# 设置缓存路径给 uv 以防权限问题
ENV UV_CACHE_DIR=/app/.cache/uv

RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && uv sync --frozen

# 复制项目源码
COPY --chown=appuser:appgroup . .

EXPOSE 3000 5001

# 同时启动前后端（开发模式）
CMD ["npm", "run", "dev"]