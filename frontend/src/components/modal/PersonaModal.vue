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
  if (d === 'hard') return 'bg-rose-50 text-rose-600 border border-rose-100'
  if (d === 'medium') return 'bg-amber-50 text-amber-600 border border-amber-100'
  return 'bg-emerald-50 text-emerald-600 border border-emerald-100'
}

function avatarSvg(d: string): string {
  if (d === 'hard') return 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' // briefcase/cube
  if (d === 'medium') return 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' // monitor
  return 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' // user
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
          class="modal-content bg-white rounded-2xl p-8 w-[540px] max-w-[90vw] shadow-[var(--shadow-modal)] border border-[var(--color-border)]"
        >
          <h2 class="text-lg font-bold text-[var(--color-text-primary)] mb-1 tracking-tight">
            {{ title || '选择客户画像' }}
          </h2>
          <p class="text-xs text-[var(--color-text-secondary)] mb-6">选择一位虚拟客户，开始保险销售对练</p>

          <div class="space-y-3">
            <button
              v-for="p in personas"
              :key="p.persona_id"
              class="w-full flex items-center gap-4 p-4 rounded-xl border border-[var(--color-border)] bg-white hover:border-zinc-300 hover:bg-[var(--color-surface)] transition-all duration-200 group text-left shadow-sm"
              @click="$emit('select', p.persona_id)"
            >
              <div class="w-10 h-10 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border-light)] flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                <svg class="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" :d="avatarSvg(p.difficulty)" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-sm font-semibold text-[var(--color-text-primary)]">{{ p.name }}</h3>
                <p class="text-xs text-[var(--color-text-secondary)] mt-0.5 line-clamp-2 leading-relaxed">{{ p.description }}</p>
              </div>
              <span
                class="text-[10px] font-bold px-2.5 py-1 rounded-md shrink-0"
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
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.96) translateY(12px);
}
</style>