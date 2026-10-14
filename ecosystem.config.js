module.exports = {
  apps: [
    {
      name: "mirofish-backend",
      script: "run.py",
      interpreter: "/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend/.venv/bin/python",
      cwd: "/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        PORT: 5001,
        FLASK_PORT: 5001,
        FLASK_HOST: "0.0.0.0",
        PYTHONUNBUFFERED: "1",
        DATABASE_URI: "sqlite:////home/biezz/Documents/Project/coding/Mirofish-enterprise/backend/mirofish.db",
        SEARCHXNG_URL: "http://192.168.101.19:8089",
        LLM_MODEL_NAME: "mirofish-agent",
        DEFAULT_LOCALE: "id"
      }
    },
    {
      name: "mirofish-frontend",
      script: "npm",
      args: "run dev -- --host 0.0.0.0 --port 3001",
      cwd: "/home/biezz/Documents/Project/coding/Mirofish-enterprise/frontend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PORT: 3000,
        NODE_ENV: "development"
      }
    }
  ]
};
