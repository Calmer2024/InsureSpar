<script setup lang="ts">
import type { Persona, Strategy } from '../../types'
import { ref } from 'vue'

defineProps<{
  visible: boolean
  personas: Persona[]
  strategies: Strategy[]
}>()

defineEmits<{
  (e: 'start', personaId: string, strategyId: string): void
  (e: 'close'): void
}>()

const selectedPersona = ref<string | null>(null)
const selectedStrategy = ref<string | null>(null)

function difficultyColor(d: string): string {
  if (d === 'hard') return 'bg-rose-50 text-rose-600 border border-rose-100'
  if (d === 'medium') return 'bg-amber-50 text-amber-600 border border-amber-100'
  return 'bg-emerald-50 text-emerald-600 border border-emerald-100'
}

function avatarSvg(d: string): string {
  if (d === 'hard') return 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4'
  if (d === 'medium') return 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z'
  return 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div
          class="modal-content bg-white rounded-2xl p-8 w-[760px] max-w-[92vw] shadow-[var(--shadow-modal)] border border-[var(--color-border)]"
        >
          <div class="mb-6">
            <h2 class="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">自动对战测试</h2>
            <p class="text-xs text-[var(--color-text-secondary)] mt-1">系统将基于选定的画像与策略，全自动完成销售交锋并输出评估</p>
          </div>

          <div class="flex gap-6">
            <div class="flex-1">
              <p class="text-[11px] font-bold text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">1. 选择测试客户</p>
              <div class="space-y-2.5 max-h-[40vh] overflow-y-auto pr-1">
                <button
                  v-for="p in personas"
                  :key="p.persona_id"
                  class="w-full text-left p-4 rounded-xl border transition-all duration-200 focus:outline-none"
                  :class="selectedPersona === p.persona_id
                    ? 'border-zinc-900 bg-zinc-50 shadow-sm ring-1 ring-zinc-900/10'
                    : 'border-[var(--color-border)] bg-white hover:border-zinc-300 hover:bg-[var(--color-surface)]'"
                  @click="selectedPersona = p.persona_id"
                >
                  <div class="flex items-center gap-2.5 mb-2">
                    <div class="w-7 h-7 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border-light)] flex items-center justify-center shrink-0">
                      <svg class="w-3.5 h-3.5 text-[var(--color-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" :d="avatarSvg(p.difficulty)" />
                      </svg>
                    </div>
                    <span class="text-sm font-semibold text-[var(--color-text-primary)]">{{ p.name }}</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-md ml-auto" :class="difficultyColor(p.difficulty)">
                      {{ p.difficulty === 'hard' ? '困难' : p.difficulty === 'medium' ? '中等' : '简单' }}
                    </span>
                  </div>
                  <p class="text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed">{{ p.description }}</p>
                </button>
              </div>
            </div>

            <div class="flex-1">
              <p class="text-[11px] font-bold text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">2. 绑定执行策略</p>
              <div class="space-y-2.5 max-h-[40vh] overflow-y-auto pr-1">
                <button
                  v-for="s in strategies"
                  :key="s.strategy_id"
                  class="w-full text-left p-4 rounded-xl border transition-all duration-200 focus:outline-none"
                  :class="selectedStrategy === s.strategy_id
                    ? 'border-zinc-900 bg-zinc-50 shadow-sm ring-1 ring-zinc-900/10'
                    : 'border-[var(--color-border)] bg-white hover:border-zinc-300 hover:bg-[var(--color-surface)]'"
                  @click="selectedStrategy = s.strategy_id"
                >
                  <h3 class="text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">{{ s.name }}</h3>
                  <p class="text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed mb-2">{{ s.description }}</p>
                  <div v-if="s.tags?.length" class="flex flex-wrap gap-1.5">
                    <span
                      v-for="tag in s.tags"
                      :key="tag"
                      class="text-[10px] font-medium px-2 py-0.5 rounded-md bg-white border border-[var(--color-border)] text-[var(--color-text-secondary)]"
                    >
                      {{ tag }}
                    </span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <div class="mt-8 flex items-center justify-end gap-3 pt-4 border-t border-[var(--color-border-light)]">
            <button
              class="px-5 py-2.5 rounded-xl border border-[var(--color-border)] bg-white text-sm font-medium text-[var(--color-text-secondary)] hover:text-zinc-900 hover:bg-[var(--color-surface)] transition-all"
              @click="$emit('close')"
            >
              取消
            </button>
            <button
              :disabled="!selectedPersona || !selectedStrategy"
              class="cta-btn px-8 py-2.5 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="selectedPersona && selectedStrategy && $emit('start', selectedPersona, selectedStrategy)"
            >
              运行自动测试
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active { transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
.modal-enter-from .modal-content,
.modal-leave-to .modal-content { transform: scale(0.96) translateY(12px); }
</style>