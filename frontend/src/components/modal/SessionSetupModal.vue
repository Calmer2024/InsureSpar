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

// 弹窗打开时重置选择（修复闪烁问题 #6）
watch(() => props.visible, (v) => {
  if (v) {
    selectedPersona.value = null
    selectedStrategy.value = null
  }
})

function difficultyTag(d?: string) {
  if (d === 'hard' || d === '困难') return { label: '困难', cls: 'bg-red-50 text-red-500' }
  if (d === 'medium' || d === '中等') return { label: '中等', cls: 'bg-amber-50 text-amber-600' }
  return { label: '简单', cls: 'bg-emerald-50 text-emerald-600' }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div
          class="bg-surface-card rounded-2xl p-8 w-[720px] max-w-[92vw] animate-fade-in-up"
          style="box-shadow: var(--shadow-modal);"
        >
          <h2 class="text-lg font-bold text-text-primary mb-1">开始对练</h2>
          <p class="text-xs text-text-secondary mb-6">选择客户画像 + 销售策略，支持手动输入和 AI 自动推进</p>

          <div class="flex gap-6">
            <!-- 画像选择 -->
            <div class="flex-1">
              <p class="text-[11px] font-semibold text-text-muted mb-3 uppercase tracking-wider">客户画像</p>
              <div class="space-y-2">
                <button
                  v-for="p in personas"
                  :key="p.persona_id"
                  class="w-full text-left p-3 rounded-xl border-2 transition-all duration-200"
                  :class="selectedPersona === p.persona_id
                    ? 'border-primary-500 bg-primary-50/50 shadow-sm'
                    : 'border-border hover:border-primary-300'"
                  @click="selectedPersona = p.persona_id"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-semibold text-text-primary">{{ p.name }}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded-full ml-auto" :class="difficultyTag(p.difficulty).cls">
                      {{ difficultyTag(p.difficulty).label }}
                    </span>
                  </div>
                  <p class="text-[11px] text-text-muted mt-1 line-clamp-2">{{ p.description }}</p>
                </button>
              </div>
            </div>

            <!-- 策略选择 -->
            <div class="flex-1">
              <p class="text-[11px] font-semibold text-text-muted mb-3 uppercase tracking-wider">销售策略</p>
              <div class="space-y-2">
                <button
                  v-for="s in strategies"
                  :key="s.strategy_id"
                  class="w-full text-left p-3 rounded-xl border-2 transition-all duration-200"
                  :class="selectedStrategy === s.strategy_id
                    ? 'border-primary-500 bg-primary-50/50 shadow-sm'
                    : 'border-border hover:border-primary-300'"
                  @click="selectedStrategy = s.strategy_id"
                >
                  <h3 class="text-xs font-semibold text-text-primary">{{ s.name }}</h3>
                  <p class="text-[11px] text-text-muted mt-0.5 line-clamp-1">{{ s.description }}</p>
                  <p v-if="s.strengths" class="text-[10px] text-primary-600 mt-1">优势: {{ s.strengths }}</p>
                </button>
              </div>
            </div>
          </div>

          <button
            :disabled="!selectedPersona || !selectedStrategy"
            class="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.98] transition-all duration-150 disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
            @click="selectedPersona && selectedStrategy && $emit('start', selectedPersona, selectedStrategy)"
          >
            开始对练
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active { transition: all 0.25s ease; }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
</style>
