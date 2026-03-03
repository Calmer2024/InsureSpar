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
  if (d === 'hard') return 'bg-red-50 text-red-500'
  if (d === 'medium') return 'bg-amber-50 text-amber-600'
  return 'bg-emerald-50 text-emerald-600'
}

function avatar(d: string): string {
  return d === 'hard' ? '👔' : d === 'medium' ? '💻' : '👩'
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
          class="bg-surface-card rounded-2xl p-8 w-[680px] max-w-[92vw] animate-fade-in-up"
          :style="{ boxShadow: 'var(--shadow-modal)' }"
        >
          <h2 class="text-lg font-bold text-text-primary mb-1">🤖 配置自动对战</h2>
          <p class="text-xs text-text-secondary mb-6">选择客户画像 + 销售策略，系统将全自动完成对话并评分</p>

          <div class="flex gap-6">
            <!-- 画像选择 -->
            <div class="flex-1">
              <p class="text-[11px] font-semibold text-text-muted mb-3 uppercase tracking-wider">1️⃣ 选择客户</p>
              <div class="space-y-2">
                <button
                  v-for="p in personas"
                  :key="p.persona_id"
                  class="w-full text-left p-3 rounded-xl border-2 transition-all duration-200"
                  :class="selectedPersona === p.persona_id
                    ? 'border-primary-500 bg-primary-50/50'
                    : 'border-border hover:border-primary-300'"
                  @click="selectedPersona = p.persona_id"
                >
                  <div class="flex items-center gap-2">
                    <span class="text-lg">{{ avatar(p.difficulty) }}</span>
                    <span class="text-xs font-semibold text-text-primary">{{ p.name }}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded-full ml-auto" :class="difficultyColor(p.difficulty)">
                      {{ p.difficulty === 'hard' ? '困难' : p.difficulty === 'medium' ? '中等' : '简单' }}
                    </span>
                  </div>
                  <p class="text-[11px] text-text-muted mt-1 line-clamp-1">{{ p.description }}</p>
                </button>
              </div>
            </div>

            <!-- 策略选择 -->
            <div class="flex-1">
              <p class="text-[11px] font-semibold text-text-muted mb-3 uppercase tracking-wider">2️⃣ 选择销售策略</p>
              <div class="space-y-2">
                <button
                  v-for="s in strategies"
                  :key="s.strategy_id"
                  class="w-full text-left p-3 rounded-xl border-2 transition-all duration-200"
                  :class="selectedStrategy === s.strategy_id
                    ? 'border-primary-500 bg-primary-50/50'
                    : 'border-border hover:border-primary-300'"
                  @click="selectedStrategy = s.strategy_id"
                >
                  <h3 class="text-xs font-semibold text-text-primary">{{ s.name }}</h3>
                  <p class="text-[11px] text-text-muted mt-0.5 line-clamp-1">{{ s.description }}</p>
                  <div class="flex gap-1.5 mt-1.5">
                    <span
                      v-for="tag in s.tags"
                      :key="tag"
                      class="text-[10px] px-2 py-0.5 rounded-full bg-primary-50 text-primary-600"
                    >
                      {{ tag }}
                    </span>
                  </div>
                </button>
              </div>
            </div>
          </div>

          <button
            :disabled="!selectedPersona || !selectedStrategy"
            class="mt-6 w-full py-3 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.98] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
            @click="selectedPersona && selectedStrategy && $emit('start', selectedPersona, selectedStrategy)"
          >
            🚀 开始自动对战
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
