module.exports = {
  apps: [
    {
      name: "mirofish-backend",
      script: "python3",
      args: "run.py",
      cwd: "/home/biezz/Project/apps/MiroFish/backend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        PORT: 5001,
        PYTHONUNBUFFERED: "1",
        DATABASE_URI: "sqlite:////home/biezz/Project/apps/MiroFish/backend/mirofish.db",
        SEARCHXNG_URL: "http://localhost:8888",
        DEFAULT_LOCALE: "id"
      }
    },
    {
      name: "mirofish-frontend",
      script: "npm",
      args: "run dev -- --host 0.0.0.0 --port 3000",
      cwd: "/home/biezz/Project/apps/MiroFish/frontend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PORT: 3000,
        NODE_ENV: "development"
      }
    },
    {
      name: "mirofish-mcp",
      script: "python3",
      args: "-m mcp_server.main",
      cwd: "/home/biezz/Project/apps/MiroFish/backend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "300M",
      env: {
        PYTHONUNBUFFERED: "1"
      }
    }
  ]
};
