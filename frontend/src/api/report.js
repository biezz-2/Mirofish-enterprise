import service from './index'

/**
 * 开始报告生成
 * @param {Object} data - { simulation_id, force_regenerate? }
 */
export const generateReport = (data) => {
  return service.post('/api/report/generate', data)
}

/**
 * 获取报告生成状态
 * @param {string} reportId
 */
export const getReportStatus = (reportId) => {
  return service.get(`/api/report/generate/status`, { params: { report_id: reportId } })
}

/**
 * 获取 Agent 日志（增量）
 * @param {string} reportId
 * @param {number} fromLine - 从第几行开始获取
 */
export const getAgentLog = (reportId, fromLine = 0) => {
  return service.get(`/api/report/${reportId}/agent-log`, { params: { from_line: fromLine } })
}

/**
 * 获取控制台日志（增量）
 * @param {string} reportId
 * @param {number} fromLine - 从第几行开始获取
 */
export const getConsoleLog = (reportId, fromLine = 0) => {
  return service.get(`/api/report/${reportId}/console-log`, { params: { from_line: fromLine } })
}

/**
 * 获取报告详情
 * @param {string} reportId
 */
export const getReport = (reportId) => {
  return service.get(`/api/report/${reportId}`)
}

/**
 * 与 Report Agent 对话
 * @param {Object} data - { simulation_id, message, chat_history? }
 */
export const chatWithReport = (data) => {
  return service.post('/api/report/chat', data)
}

/**
 * Hubungkan ke Server-Sent Events (SSE) stream untuk log penalaran Report Agent secara real-time.
 * @param {string} reportId
 * @param {Object} options - { fromLine, onLog, onConnected, onDone, onError, onTimeout }
 * @returns {EventSource}
 */
export const createAgentLogEventSource = (reportId, options = {}) => {
  const { fromLine = 0, onLog, onConnected, onDone, onError, onTimeout } = options
  const token = localStorage.getItem('token') || localStorage.getItem('access_token') || ''
  const apiBase = import.meta.env.VITE_API_BASE_URL || ''

  const queryParams = new URLSearchParams({
    from_line: fromLine.toString()
  })
  if (token) {
    queryParams.append('token', token)
  }

  const url = `${apiBase}/api/report/${reportId}/agent-log/events?${queryParams.toString()}`
  const eventSource = new EventSource(url)

  eventSource.addEventListener('connected', (event) => {
    try {
      const data = JSON.parse(event.data)
      if (onConnected) onConnected(data)
    } catch (e) {
      console.warn('Failed to parse SSE connected event:', e)
    }
  })

  eventSource.addEventListener('log', (event) => {
    try {
      const data = JSON.parse(event.data)
      if (onLog) onLog(data, event.lastEventId)
    } catch (e) {
      console.warn('Failed to parse SSE log event:', e)
    }
  })

  eventSource.addEventListener('done', (event) => {
    try {
      const data = JSON.parse(event.data)
      if (onDone) onDone(data)
    } catch (e) {
      console.warn('Failed to parse SSE done event:', e)
    }
    eventSource.close()
  })

  eventSource.addEventListener('timeout', (event) => {
    try {
      const data = JSON.parse(event.data)
      if (onTimeout) onTimeout(data)
    } catch (e) {
      console.warn('Failed to parse SSE timeout event:', e)
    }
    eventSource.close()
  })

  eventSource.addEventListener('error', (event) => {
    if (onError) onError(event)
  })

  return eventSource
}

