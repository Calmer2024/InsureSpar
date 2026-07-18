<script setup lang="ts">
import { Icon } from '@iconify/vue'

type View = 'home' | 'practice' | 'dashboard'

defineProps<{
  currentView: View
}>()

defineEmits<{
  (e: 'navigate', view: View): void
  (e: 'new-session'): void
  (e: 'show-history'): void
}>()

const navigation: Array<{ id: View; label: string; icon: string }> = [
  { id: 'home', label: '首页', icon: 'lucide:house' },
  { id: 'practice', label: '实战对练', icon: 'lucide:messages-square' },
  { id: 'dashboard', label: '能力中心', icon: 'lucide:chart-no-axes-combined' },
]
</script>

<template>
  <aside class="hidden w-[228px] shrink-0 bg-transparent lg:flex lg:flex-col">
    <div class="flex h-[120px] flex-col items-start justify-center px-6">
      <img src="/insurespar_logo.png" alt="InsureSpar" class="h-[68px] w-[68px] rounded-xl object-cover" />
      <p class="brand-wordmark ui-title mt-1 truncate text-[22px] text-[var(--color-text-primary)]">InsureSpar</p>
    </div>

    <nav class="space-y-1 px-3 pt-3" aria-label="主导航">
      <button
        v-for="item in navigation"
        :key="item.id"
        type="button"
        class="group flex h-11 w-full items-center gap-3 rounded-lg px-3 text-[13px] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/30"
        :class="currentView === item.id
          ? 'bg-white text-[var(--color-accent-dark)] shadow-[var(--shadow-sm)]'
          : 'text-[var(--color-text-secondary)] hover:bg-white/70 hover:text-[var(--color-text-primary)]'"
        @click="$emit('navigate', item.id)"
      >
        <Icon
          :icon="item.icon"
          class="h-[18px] w-[18px]"
          :class="currentView === item.id ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)]'"
        />
        {{ item.label }}
      </button>
    </nav>

    <div class="mx-5 my-4 h-px bg-[var(--color-border)]" />

    <div class="space-y-1 px-3">
      <button
        type="button"
        class="flex h-11 w-full items-center gap-3 rounded-lg px-3 text-[13px] text-[var(--color-text-secondary)] transition-colors hover:bg-white/70 hover:text-[var(--color-text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/30"
        @click="$emit('show-history')"
      >
        <Icon icon="lucide:history" class="h-[18px] w-[18px] text-[var(--color-text-muted)]" />
        历史复盘
      </button>
    </div>

    <div class="mt-auto p-4">
      <div class="rounded-xl border border-[#d9e9df] bg-white/70 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]">
        <div class="ui-title flex items-center gap-2 text-[13px] text-[var(--color-text-primary)]">
          <Icon icon="lucide:sparkles" class="h-4 w-4 text-[var(--color-accent)]" />
          AI 对练助手
        </div>
        <p class="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">选择客户画像和销售策略，开始一次针对性训练。</p>
        <button
          type="button"
          class="mt-3 flex h-9 w-full items-center justify-center gap-2 rounded-full bg-[var(--color-accent)] px-3 text-xs font-semibold text-white transition-colors hover:bg-[var(--color-accent-hover)]"
          @click="$emit('new-session')"
        >
          <Icon icon="lucide:plus" class="h-4 w-4" />
          新建对练
        </button>
      </div>
    </div>
  </aside>

  <header class="flex h-16 shrink-0 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-sidebar)] px-4 lg:hidden">
    <button type="button" class="flex min-w-0 items-center gap-2" @click="$emit('navigate', 'home')">
      <img src="/insurespar_logo.png" alt="InsureSpar" class="h-12 w-12 rounded-xl object-cover" />
      <span class="brand-wordmark ui-title truncate text-xl">InsureSpar</span>
    </button>
    <button
      type="button"
      aria-label="新建对练"
      title="新建对练"
      class="grid h-9 w-9 place-items-center rounded-full bg-[var(--color-accent)] text-white"
      @click="$emit('new-session')"
    >
      <Icon icon="lucide:message-square-plus" class="h-[18px] w-[18px]" />
    </button>
  </header>

  <nav class="fixed inset-x-0 bottom-0 z-40 grid h-16 grid-cols-4 border-t border-[var(--color-border)] bg-white/95 px-2 backdrop-blur lg:hidden" aria-label="移动端导航">
    <button
      v-for="item in navigation"
      :key="item.id"
      type="button"
      class="flex flex-col items-center justify-center gap-1 text-[11px] font-medium"
      :class="currentView === item.id ? 'text-[var(--color-accent-dark)]' : 'text-[var(--color-text-muted)]'"
      @click="$emit('navigate', item.id)"
    >
      <Icon :icon="item.icon" class="h-5 w-5" />
      {{ item.label }}
    </button>
    <button type="button" class="flex flex-col items-center justify-center gap-1 text-[11px] font-medium text-[var(--color-text-muted)]" @click="$emit('show-history')">
      <Icon icon="lucide:history" class="h-5 w-5" />
      历史
    </button>
  </nav>
</template>
