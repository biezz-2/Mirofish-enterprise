/**
 * DOMPurify-compatible Strict XSS Sanitizer for Markdown and Dynamic HTML
 * Blocks: javascript:, vbscript:, data:text/html, event handlers (onload, onerror, onclick, etc.)
 */

/**
 * Escapes raw HTML control characters to prevent tag injection
 * @param {string} str
 * @returns {string}
 */
export const escapeHtml = (str) => {
  if (typeof str !== 'string') return ''
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Validates and sanitizes a URL against XSS schemes (javascript:, vbscript:, data:text/html, etc.)
 * @param {string} url
 * @param {string} fallback
 * @returns {string}
 */
export const sanitizeUrl = (url, fallback = '#') => {
  if (!url || typeof url !== 'string') return fallback

  // Normalize and trim whitespace, control chars, null bytes
  const trimmed = url.trim().replace(/[\x00-\x1f\x7f-\x9f]/g, '')

  // Collapse whitespace/tabs inside URL to prevent scheme obfuscation (e.g. "java\nscript:")
  const collapsed = trimmed.replace(/\s+/g, '')

  // Disallow javascript:, vbscript:, and data:text/html (or any non-whitelisted data: type)
  const lower = collapsed.toLowerCase()
  if (
    lower.startsWith('javascript:') ||
    lower.startsWith('vbscript:') ||
    lower.startsWith('data:text/html') ||
    lower.startsWith('data:text/javascript') ||
    lower.startsWith('data:application/javascript') ||
    lower.startsWith('file:') ||
    lower.startsWith('blob:')
  ) {
    return fallback
  }

  // Safe schemes: http, https, mailto, tel, or relative path / hash / query
  const isSafeRelative = /^(\/|#|\.|\?|[a-zA-Z0-9_-]+\/)/.test(trimmed)
  const isSafeAbsolute = /^(https?|mailto|tel):/i.test(trimmed)

  if (!isSafeRelative && !isSafeAbsolute) {
    return fallback
  }

  // Escape quotes to prevent HTML attribute breakout
  return trimmed
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

/**
 * Sanitizes an HTML string by removing dangerous tags, event handlers, and malicious URLs
 * @param {string} html
 * @returns {string}
 */
export const sanitizeHtml = (html) => {
  if (!html || typeof html !== 'string') return ''

  let sanitized = html

  // 1. Strip script, iframe, object, embed, applet, meta, link, style, base, form tags and their contents
  sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
  sanitized = sanitized.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '')
  sanitized = sanitized.replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
  sanitized = sanitized.replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '')
  sanitized = sanitized.replace(/<embed\b[^>]*>/gi, '')
  sanitized = sanitized.replace(/<applet\b[^<]*(?:(?!<\/applet>)<[^<]*)*<\/applet>/gi, '')
  sanitized = sanitized.replace(/<meta\b[^>]*>/gi, '')
  sanitized = sanitized.replace(/<link\b[^>]*>/gi, '')
  sanitized = sanitized.replace(/<base\b[^>]*>/gi, '')
  sanitized = sanitized.replace(/<form\b[^<]*(?:(?!<\/form>)<[^<]*)*<\/form>/gi, '')

  // 2. Strip all inline DOM event handlers: onload=, onerror=, onclick=, onmouseover=, etc.
  sanitized = sanitized.replace(/\s+on[a-zA-Z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, '')

  // 3. Disarm dangerous schemes in href, src, action, or xlink:href attributes
  sanitized = sanitized.replace(
    /\s+(href|src|action|xlink:href)\s*=\s*(["'])(.*?)\2/gi,
    (match, attr, quote, val) => {
      const cleanVal = sanitizeUrl(val, '#')
      return ` ${attr}=${quote}${cleanVal}${quote}`
    }
  )

  // Also handle unquoted href/src attributes
  sanitized = sanitized.replace(
    /\s+(href|src|action|xlink:href)\s*=\s*([^\s>"']+)/gi,
    (match, attr, val) => {
      const cleanVal = sanitizeUrl(val, '#')
      return ` ${attr}="${cleanVal}"`
    }
  )

  return sanitized
}
