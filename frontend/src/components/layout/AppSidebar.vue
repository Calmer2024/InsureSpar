<script setup lang="ts">
import { ref } from 'vue'
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

const isCollapsed = ref(false)
</script>

<template>
  <aside
    class="desktop-sidebar relative hidden shrink-0 bg-transparent transition-[width,margin-left] duration-200 lg:flex lg:flex-col"
    :class="isCollapsed ? '-ml-3 w-[72px]' : 'ml-0 w-[228px]'"
  >
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div
        class="flex h-[118px] shrink-0 items-center transition-[padding] duration-200"
        :class="isCollapsed ? 'justify-center px-0' : 'gap-2 px-4'"
      >
        <img
          src="/insurespar_logo.png"
          alt="InsureSpar"
          class="shrink-0 rounded-2xl object-cover transition-[width,height] duration-200"
          :class="isCollapsed ? 'h-14 w-14' : 'h-[60px] w-[60px]'"
        />
        <p v-if="!isCollapsed" class="brand-wordmark ui-title whitespace-nowrap text-[21px] text-[var(--color-text-primary)]">InsureSpar</p>
      </div>

      <nav class="space-y-2 pt-2" :class="isCollapsed ? 'px-0' : 'pl-3'" aria-label="主导航">
        <button
          v-for="item in navigation"
          :key="item.id"
          type="button"
          class="group flex h-12 items-center text-[13px] transition-[background-color,color,box-shadow] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/30"
          :class="[
            isCollapsed
              ? 'mx-auto w-12 justify-center rounded-2xl px-0'
              : 'mr-3 w-[calc(100%-0.75rem)] gap-3 rounded-2xl px-4',
            currentView === item.id
              ? 'bg-white text-[var(--color-text-primary)]'
              : 'text-[var(--color-text-secondary)] hover:bg-white/65 hover:text-[var(--color-text-primary)]',
          ]"
          :aria-label="item.label"
          :title="isCollapsed ? item.label : undefined"
          @click="$emit('navigate', item.id)"
        >
          <Icon
            :icon="item.icon"
            class="h-5 w-5 shrink-0"
            :class="currentView === item.id ? 'text-[var(--color-accent-dark)]' : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)]'"
          />
          <span v-if="!isCollapsed" class="truncate">{{ item.label }}</span>
        </button>
      </nav>

      <div class="mx-5 my-4 h-px shrink-0 bg-[var(--color-border)]" :class="isCollapsed ? 'opacity-0' : 'opacity-100'" />

      <div :class="isCollapsed ? 'px-0' : 'px-3'">
        <button
          type="button"
          class="group flex h-12 items-center rounded-2xl text-[13px] text-[var(--color-text-secondary)] transition-[background-color,color] hover:bg-white/65 hover:text-[var(--color-text-primary)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/30"
          :class="isCollapsed ? 'mx-auto w-12 justify-center px-0' : 'w-full gap-3 px-4'"
          aria-label="历史复盘"
          :title="isCollapsed ? '历史复盘' : undefined"
          @click="$emit('show-history')"
        >
          <Icon icon="lucide:history" class="h-5 w-5 shrink-0 text-[var(--color-text-muted)] group-hover:text-[var(--color-accent)]" />
          <span v-if="!isCollapsed" class="truncate">历史复盘</span>
        </button>
      </div>

      <div class="mt-auto p-3">
        <button
          v-if="isCollapsed"
          type="button"
          class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[var(--color-accent)] text-white shadow-[0_5px_14px_rgba(42,114,75,0.16)] transition-colors hover:bg-[var(--color-accent-hover)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/30 focus-visible:ring-offset-2"
          aria-label="新建对练"
          title="新建对练"
          @click="$emit('new-session')"
        >
          <Icon icon="lucide:message-square-plus" class="h-5 w-5" />
        </button>

        <div v-else class="rounded-2xl border border-[#d9e9df] bg-white/72 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]">
          <div class="ui-title flex items-center gap-2 text-[13px] text-[var(--color-text-primary)]">
            <Icon icon="lucide:sparkles" class="h-4 w-4 text-[var(--color-accent)]" />
            AI 对练助手
          </div>
          <p class="mt-2 text-xs leading-5 text-[var(--color-text-secondary)]">选择客户画像和销售策略，开始一次针对性训练。</p>
          <button
            type="button"
            class="mt-3 flex h-9 w-full items-center justify-center gap-2 rounded-full bg-[var(--color-accent)] px-3 text-xs text-white transition-colors hover:bg-[var(--color-accent-hover)]"
            @click="$emit('new-session')"
          >
            <Icon icon="lucide:plus" class="h-4 w-4" />
            新建对练
          </button>
        </div>
      </div>
    </div>

    <button
      type="button"
      class="absolute right-0 top-1/2 z-20 grid h-10 w-10 translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-white/80 bg-white text-[var(--color-accent-dark)] transition-colors hover:bg-[#f7fbf8] hover:text-[var(--color-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]/30"
      :aria-label="isCollapsed ? '展开侧边栏' : '折叠侧边栏'"
      :title="isCollapsed ? '展开侧边栏' : '折叠侧边栏'"
      :aria-expanded="!isCollapsed"
      @click="isCollapsed = !isCollapsed"
    >
      <Icon :icon="isCollapsed ? 'lucide:arrow-right' : 'lucide:arrow-left'" class="h-[18px] w-[18px]" />
    </button>
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
