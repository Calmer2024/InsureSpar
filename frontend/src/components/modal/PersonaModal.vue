<script setup lang="ts">
import type { Persona } from '../../types'

defineProps<{
  visible: boolean
  personas: Persona[]
  title?: string
}>()

defineEmits<{
  (e: 'select', personaId: string): void
  (e: 'close'): void
}>()

function difficultyLabel(d: string): string {
  return d === 'hard' ? '困难' : d === 'medium' ? '中等' : '简单'
}

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
          class="bg-surface-card rounded-2xl p-8 w-[540px] max-w-[90vw] animate-fade-in-up"
          :style="{ boxShadow: 'var(--shadow-modal)' }"
        >
          <h2 class="text-lg font-bold text-text-primary mb-1">
            🎭 {{ title || '选择客户画像' }}
          </h2>
          <p class="text-xs text-text-secondary mb-6">选择一位虚拟客户，开始保险销售对练</p>

          <div class="space-y-3">
            <button
              v-for="p in personas"
              :key="p.persona_id"
              class="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-border bg-surface hover:border-primary-400 hover:bg-primary-50/30 transition-all duration-200 group text-left"
              @click="$emit('select', p.persona_id)"
            >
              <span class="text-3xl group-hover:scale-110 transition-transform">{{ avatar(p.difficulty) }}</span>
              <div class="flex-1 min-w-0">
                <h3 class="text-sm font-semibold text-text-primary">{{ p.name }}</h3>
                <p class="text-xs text-text-secondary mt-0.5 line-clamp-2">{{ p.description }}</p>
              </div>
              <span
                class="text-[10px] font-bold px-2.5 py-1 rounded-full shrink-0"
                :class="difficultyColor(p.difficulty)"
              >
                {{ difficultyLabel(p.difficulty) }}
              </span>
            </button>
          </div>
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
.modal-enter-from .bg-surface-card,
.modal-leave-to .bg-surface-card {
  transform: scale(0.95) translateY(10px);
}
</style>
