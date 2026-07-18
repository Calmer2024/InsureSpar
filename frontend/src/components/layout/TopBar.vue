<script setup lang="ts">
import type { AppStatus } from '../../types'
import StatusDot from '../common/StatusDot.vue'
import RichText from '../common/RichText.vue'
import { Icon } from '@iconify/vue'

defineProps<{
  status: AppStatus
  statusText: string
  turnCount: number
  stageLabel: string
  sessionId: string | null
  showBackButton?: boolean
  evalOpen?: boolean
}>()

defineEmits<{
  (e: 'new-session'): void
  (e: 'show-history'): void
  (e: 'show-dashboard'): void
  (e: 'back'): void
  (e: 'toggle-evaluation'): void
}>()
</script>

<template>
  <div class="flex min-h-11 w-full items-center justify-between gap-3">
    <div class="flex min-w-0 items-center gap-3">
      <button
        type="button"
        aria-label="返回首页"
        title="返回首页"
        class="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-[var(--color-border)] bg-white text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]"
        @click="$emit('back')"
      >
        <Icon icon="lucide:arrow-left" class="h-4 w-4" />
      </button>
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <h1 class="truncate text-base font-bold sm:text-lg">实战对练</h1>
          <span v-if="turnCount > 0" class="hidden rounded-full bg-[var(--color-accent-soft)] px-2 py-0.5 text-[10px] font-semibold text-[var(--color-accent-dark)] sm:inline">第 {{ turnCount }} 轮</span>
        </div>
        <div class="mt-0.5 flex min-w-0 items-center gap-1.5 text-[11px] text-[var(--color-text-muted)]">
          <StatusDot :status="status" />
          <RichText :text="statusText" class="max-w-[180px] truncate sm:max-w-[320px]" />
        </div>
      </div>
    </div>

    <div class="flex shrink-0 items-center gap-2">
      <details v-if="sessionId" class="group/session relative hidden md:block">
        <summary class="flex h-9 cursor-pointer list-none items-center gap-2 rounded-lg border border-[var(--color-border)] bg-white px-3 text-xs font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-surface)]">
          <Icon icon="lucide:route" class="h-4 w-4" />
          会话信息
          <Icon icon="lucide:chevron-down" class="h-3.5 w-3.5 transition-transform group-open/session:rotate-180" />
        </summary>
        <div class="absolute right-0 top-full z-50 mt-2 w-72 rounded-lg border border-[var(--color-border)] bg-white p-4 shadow-[var(--shadow-modal)]">
          <p class="text-[11px] text-[var(--color-text-muted)]">当前训练阶段</p>
          <RichText :text="stageLabel" class="mt-1 block truncate text-sm font-semibold" />
          <p class="mt-3 pt-3 text-[11px] text-[var(--color-text-muted)]">会话 ID</p>
          <code class="mt-1 block break-all rounded-lg bg-[var(--color-surface)] px-2 py-1.5 text-[10px] text-[var(--color-text-secondary)]">{{ sessionId }}</code>
        </div>
      </details>

      <button
        type="button"
        aria-label="历史记录"
        title="历史记录"
        class="grid h-9 w-9 place-items-center rounded-full border border-[var(--color-border)] bg-white text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]"
        @click="$emit('show-history')"
      >
        <Icon icon="lucide:history" class="h-4 w-4" />
      </button>

      <button
        type="button"
        aria-label="实时反馈"
        title="实时反馈"
        :aria-expanded="evalOpen"
        class="grid h-9 w-9 place-items-center rounded-full border border-[var(--color-border)] bg-white text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]"
        :class="evalOpen ? 'bg-[var(--color-accent-soft)] text-[var(--color-accent-dark)]' : ''"
        @click="$emit('toggle-evaluation')"
      >
        <Icon icon="lucide:list-checks" class="h-4 w-4" />
      </button>

      <button
        type="button"
        class="flex h-9 items-center gap-2 rounded-lg bg-[var(--color-accent)] px-3 text-xs font-semibold text-white transition-colors hover:bg-[var(--color-accent-hover)] sm:px-4"
        @click="$emit('new-session')"
      >
        <Icon icon="lucide:plus" class="h-4 w-4" />
        <span class="hidden sm:inline">新建对练</span>
      </button>
    </div>
  </div>
</template>
