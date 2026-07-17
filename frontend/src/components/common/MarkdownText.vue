<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import type Token from 'markdown-it/lib/token.mjs'
import type Renderer from 'markdown-it/lib/renderer.mjs'
import type { RenderRule } from 'markdown-it/lib/renderer.mjs'

const props = defineProps<{
  text: string
}>()

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true,
  typographer: false,
})

md.disable('image')

const defaultLinkOpen =
  md.renderer.rules.link_open ??
  ((tokens: Token[], idx: number, options, _env, self: Renderer) =>
    self.renderToken(tokens, idx, options))

md.renderer.rules.link_open = ((tokens, idx, options, env, self) => {
  const token = tokens[idx]
  if (token) {
    token.attrSet('target', '_blank')
    token.attrSet('rel', 'noopener noreferrer')
  }
  return defaultLinkOpen(tokens, idx, options, env, self)
}) satisfies RenderRule

const rendered = computed(() => md.render(props.text))
</script>

<template>
  <div class="markdown-text" v-html="rendered" />
</template>

<style scoped>
.markdown-text {
  overflow-wrap: anywhere;
}

.markdown-text :deep(*) {
  margin: 0;
}

.markdown-text :deep(p + p),
.markdown-text :deep(p + ul),
.markdown-text :deep(p + ol),
.markdown-text :deep(ul + p),
.markdown-text :deep(ol + p),
.markdown-text :deep(pre + p),
.markdown-text :deep(p + pre) {
  margin-top: 0.75rem;
}

.markdown-text :deep(strong) {
  font-weight: 700;
  color: #1f2937;
}

.markdown-text :deep(em) {
  font-style: italic;
}

.markdown-text :deep(ul),
.markdown-text :deep(ol) {
  padding-left: 1.25rem;
}

.markdown-text :deep(ul) {
  list-style: disc;
}

.markdown-text :deep(ol) {
  list-style: decimal;
}

.markdown-text :deep(li + li) {
  margin-top: 0.25rem;
}

.markdown-text :deep(a) {
  color: #047857;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-text :deep(code) {
  border-radius: 5px;
  background: rgba(4, 120, 87, 0.1);
  padding: 0.1rem 0.3rem;
  color: #065f46;
  font-size: 0.92em;
}

.markdown-text :deep(pre) {
  overflow-x: auto;
  border-radius: 8px;
  background: rgba(17, 24, 39, 0.92);
  padding: 0.85rem 1rem;
  color: #f9fafb;
}

.markdown-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.markdown-text :deep(blockquote) {
  border-left: 3px solid #86efac;
  padding-left: 0.75rem;
  color: #4b5563;
}
</style>
