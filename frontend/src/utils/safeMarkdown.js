import DOMPurify from 'dompurify'
import { marked } from 'marked'

const SANITIZE_OPTIONS = {
  FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'base', 'link', 'style', 'img', 'svg', 'math'],
  FORBID_ATTR: ['srcset'],
}

export function sanitizeHtml(html) {
  return DOMPurify.sanitize(String(html || ''), SANITIZE_OPTIONS)
}

export function renderSafeMarkdown(text) {
  if (!text) return ''
  return sanitizeHtml(marked.parse(String(text)))
}

export function escapeHtmlAttr(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
