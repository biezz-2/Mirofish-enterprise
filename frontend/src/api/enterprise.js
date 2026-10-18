import request from './index'

/**
 * Enterprise API client wrapper for MiroFish Operations Dashboard.
 * Single Pane of Glass access to all enterprise endpoints.
 */

// Panel 1: Platform Algorithm Calibration Matrix
export function getPlatformMatrix() {
  return request({
    url: '/enterprise/platforms',
    method: 'get'
  })
}

export function simulatePareto(data) {
  return request({
    url: '/enterprise/platforms/simulate-pareto',
    method: 'post',
    data
  })
}

// Panel 2: GraphRAG & Knowledge Explorer
export function getGraphProjects(limit = 50) {
  return request({
    url: '/graph/project/list',
    method: 'get',
    params: { limit }
  })
}

export function getGraphData(graphId) {
  return request({
    url: `/graph/data/${graphId}`,
    method: 'get'
  })
}

export function getGraphitiSubgraph(params) {
  return request({
    url: '/enterprise/graphiti/subgraph',
    method: 'get',
    params
  })
}

// Panel 3: Live Swarm Simulation Console
export function getSimulationList() {
  return request({
    url: '/simulation/list',
    method: 'get'
  })
}

export function getSimulationPosts(simulationId, platform = null) {
  const params = platform ? { platform } : {}
  return request({
    url: `/simulation/${simulationId}/posts`,
    method: 'get',
    params
  })
}

export function getSimulationAgentStats(simulationId) {
  return request({
    url: `/simulation/${simulationId}/agent-stats`,
    method: 'get'
  })
}

export function getSimulationTimeline(simulationId) {
  return request({
    url: `/simulation/${simulationId}/timeline`,
    method: 'get'
  })
}

// Panel 4: Webhook & API Manager
export function getWebhookSubscriptions() {
  return request({
    url: '/enterprise/webhooks/subscriptions',
    method: 'get'
  })
}

export function createWebhookSubscription(data) {
  return request({
    url: '/enterprise/webhooks/subscriptions',
    method: 'post',
    data
  })
}

export function deleteWebhookSubscription(subscriptionId) {
  return request({
    url: `/enterprise/webhooks/subscriptions/${subscriptionId}`,
    method: 'delete'
  })
}

export function getWebhookStats() {
  return request({
    url: '/enterprise/webhooks/stats',
    method: 'get'
  })
}

export function getWebhookDlq(params = {}) {
  return request({
    url: '/enterprise/webhooks/dlq',
    method: 'get',
    params
  })
}

export function redriveWebhookDlq(data = {}) {
  return request({
    url: '/enterprise/webhooks/dlq/redrive',
    method: 'post',
    data
  })
}

export function clearWebhookDlq() {
  return request({
    url: '/enterprise/webhooks/dlq',
    method: 'delete'
  })
}

// Panel 5: FastMCP Canonical Tools & Sandbox
export function getMcpTools() {
  return request({
    url: '/enterprise/mcp/tools',
    method: 'get'
  })
}

export function invokeMcpTool(toolName, parameters = {}) {
  return request({
    url: '/enterprise/mcp/invoke',
    method: 'post',
    data: {
      tool_name: toolName,
      parameters
    }
  })
}

export function getMcpHealth() {
  return request({
    url: '/enterprise/mcp/health',
    method: 'get'
  })
}

// Panel 6: Audit & Security Center
export function getContracts() {
  return request({
    url: '/enterprise/contracts',
    method: 'get'
  })
}

export function sanitizeShieldPrompt(prompt, context = {}) {
  return request({
    url: '/enterprise/shield/sanitize',
    method: 'post',
    data: {
      prompt,
      context
    }
  })
}

export function getWatchdogStatus() {
  return request({
    url: '/enterprise/orchestrator/watchdog',
    method: 'get'
  })
}

// Panel 7: System Health & Diagnostics
export function getSystemHealth() {
  return request({
    url: '/health',
    method: 'get'
  })
}

export function getResearchHealth() {
  return request({
    url: '/research/health',
    method: 'get'
  })
}

export function getEnterpriseStatus() {
  return request({
    url: '/enterprise/status',
    method: 'get'
  })
}

export function getActiveJobs() {
  return request({
    url: '/jobs',
    method: 'get'
  })
}

export function recoverJob(jobId) {
  return request({
    url: `/jobs/${jobId}/recover`,
    method: 'post'
  })
}
