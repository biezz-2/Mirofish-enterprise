module.exports = {
  apps: [
    {
      name: 'mirofish-backend',
      script: 'run.py',
      cwd: './backend',
      interpreter: './.venv/bin/python',
      // Arsitektur B6 (Makalah Resmi): Wajib `instances: 1` dalam mode fork untuk SQLite (default/WAL)
      // guna mencegah race condition dan dual-writer corruption.
      // Jika ingin menjalankan cluster multi-instance, wajib konfigurasikan PostgreSQL via DATABASE_URI.
      instances: 1,
      exec_mode: 'fork',
      env: {
        FLASK_PORT: 5001,
        PORT: 5001,
        FLASK_HOST: '0.0.0.0',
        PYTHONPATH: '.:backend'
      }
    },
    {
      name: 'mirofish-frontend',
      script: 'npm',
      args: 'run dev -- --host 0.0.0.0 --port 3001',
      cwd: './frontend',
      instances: 1,
      exec_mode: 'fork',
      env: {
        PORT: 3001
      }
    },
    {
      name: 'mirofish-mcp-server',
      script: '/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend/mcp_server/main.py',
      args: '--transport http --port 8091 --no-auth',
      cwd: '/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend',
      interpreter: '/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend/.venv/bin/python',
      instances: 1,
      exec_mode: 'fork',
      env: {
        PORT: 8091,
        PYTHONPATH: '/home/biezz/Documents/Project/coding/Mirofish-enterprise/backend'
      }
    },
    {
      name: 'mirofish-9router',
      script: 'app/services/nine_router_daemon.py',
      cwd: './backend',
      interpreter: './.venv/bin/python',
      instances: 1,
      exec_mode: 'fork',
      env: {
        ROUTER_PORT: 8787,
        PYTHONPATH: '.:backend'
      }
    },
    {
      name: 'mirofish-webhook-worker',
      script: 'app/services/webhook_worker.py',
      cwd: './backend',
      interpreter: './.venv/bin/python',
      instances: 1,
      exec_mode: 'fork',
      env: {
        WEBHOOK_WORKER_POLL_INTERVAL: 15,
        PYTHONPATH: '.:backend'
      }
    }
  ]
};
