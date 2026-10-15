module.exports = {
  apps: [
    {
      name: 'mirofish-backend',
      script: 'app/main.py',
      cwd: './backend',
      interpreter: './backend/.venv/bin/python3',
      instances: 2,
      exec_mode: 'cluster',
      env: {
        PORT: 8000,
        PYTHONPATH: '.:backend'
      }
    },
    {
      name: 'mirofish-mcp-server',
      script: 'mcp_server/main.py',
      cwd: './backend',
      interpreter: './backend/.venv/bin/python3',
      instances: 1,
      env: {
        PORT: 8091,
        PYTHONPATH: '.:backend'
      }
    }
  ]
};
