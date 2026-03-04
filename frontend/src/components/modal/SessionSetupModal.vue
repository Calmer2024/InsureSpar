<script setup lang="ts">
import type { Persona, Strategy } from '../../types'
import { ref, watch } from 'vue'

const props = defineProps<{
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

watch(() => props.visible, (v) => {
  if (v) {
    selectedPersona.value = null
    selectedStrategy.value = null
  }
})

function difficultyTag(d?: string) {
  if (d === 'hard' || d === '困难') return { label: '困难', cls: 'bg-rose-50 text-rose-600 border border-rose-100' }
  if (d === 'medium' || d === '中等') return { label: '中等', cls: 'bg-amber-50 text-amber-600 border border-amber-100' }
  return { label: '简单', cls: 'bg-emerald-50 text-emerald-600 border border-emerald-100' }
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
            <h2 class="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">配置新对练</h2>
            <p class="text-xs text-[var(--color-text-secondary)] mt-1">选择目标客户与对应策略，配置完成后即可开始</p>
          </div>

          <div class="flex gap-6">
            <div class="flex-1">
              <p class="text-[11px] font-bold text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">目标客户</p>
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
                  <div class="flex items-center justify-between mb-1.5">
                    <span class="text-sm font-semibold text-[var(--color-text-primary)]">{{ p.name }}</span>
                    <span class="text-[10px] font-medium px-2 py-0.5 rounded-md" :class="difficultyTag(p.difficulty).cls">
                      {{ difficultyTag(p.difficulty).label }}
                    </span>
                  </div>
                  <p class="text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed">{{ p.description }}</p>
                </button>
              </div>
            </div>

            <div class="flex-1">
              <p class="text-[11px] font-bold text-[var(--color-text-muted)] mb-3 uppercase tracking-wider">执行策略</p>
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
                  <p class="text-xs text-[var(--color-text-secondary)] line-clamp-2 leading-relaxed">{{ s.description }}</p>
                  <div v-if="s.strengths" class="mt-2 text-[10px] font-medium text-[var(--color-text-primary)] bg-white border border-[var(--color-border)] rounded-md px-2 py-1 inline-block">
                    重点: {{ s.strengths }}
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
              开始对练
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