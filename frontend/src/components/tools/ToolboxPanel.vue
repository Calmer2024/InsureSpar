<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Icon } from '@iconify/vue'
import { toolSearchRules, toolPremiumRate, toolCashValue } from '../../services/api'

defineProps<{
  visible: boolean
}>()

defineEmits<{
  (e: 'close'): void
}>()

// ── 当前 Tab ──
const activeTab = ref<'rules' | 'premium' | 'cashValue'>('rules')

// ── 通用状态 ──
const rulesLoading = ref(false)
const premiumLoading = ref(false)
const cvLoading = ref(false)

const rulesResult = ref('')
const premiumResult = ref('')
const cvResult = ref('')

// ── 条款查询 ──
const rulesQuery = ref('')

// ── 保费计算 ──
const premAge = ref(30)
const premGender = ref('男')
const premPayPeriod = ref(20)
const premAmount = ref(500000)

// ── 现金价值 ──
const cvGender = ref('男')
const cvAge = ref(30)
const cvPayPeriod = ref(20)
const cvYear = ref(10)
const cvAmount = ref(500000)

async function searchRules() {
  if (!rulesQuery.value.trim()) return
  rulesLoading.value = true
  rulesResult.value = ''
  try {
    rulesResult.value = await toolSearchRules(rulesQuery.value.trim())
  } catch (e: any) {
    rulesResult.value = `[错误] 查询失败: ${e.message}`
  } finally {
    rulesLoading.value = false
  }
}

async function calcPremium() {
  premiumLoading.value = true
  premiumResult.value = ''
  try {
    premiumResult.value = await toolPremiumRate(premAge.value, premGender.value, premPayPeriod.value, premAmount.value)
  } catch (e: any) {
    premiumResult.value = `[错误] 查询失败: ${e.message}`
  } finally {
    premiumLoading.value = false
  }
}

async function calcCashValue() {
  cvLoading.value = true
  cvResult.value = ''
  try {
    cvResult.value = await toolCashValue(cvGender.value, cvAge.value, cvPayPeriod.value, cvYear.value, cvAmount.value)
  } catch (e: any) {
    cvResult.value = `[错误] 查询失败: ${e.message}`
  } finally {
    cvLoading.value = false
  }
}

const PAY_PERIODS = [1, 3, 5, 10, 15, 20, 25, 30]

const position = ref({ x: 200, y: 100 })
const panelRef = ref<HTMLElement | null>(null)
const isDragging = ref(false)
let dragOffset = { x: 0, y: 0 }

function startDrag(e: MouseEvent) {
  isDragging.value = true
  dragOffset.x = e.clientX - position.value.x
  dragOffset.y = e.clientY - position.value.y
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  requestAnimationFrame(() => {
    const width = panelRef.value?.offsetWidth || Math.min(660, window.innerWidth - 24)
    const height = panelRef.value?.offsetHeight || Math.min(480, window.innerHeight - 24)
    position.value.x = Math.min(Math.max(12, e.clientX - dragOffset.x), window.innerWidth - width - 12)
    position.value.y = Math.min(Math.max(12, e.clientY - dragOffset.y), window.innerHeight - height - 12)
  })
}

function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    position.value = {
      x: Math.max(12, (window.innerWidth - Math.min(660, window.innerWidth - 24)) / 2),
      y: Math.max(12, (window.innerHeight - Math.min(480, window.innerHeight - 24)) / 2)
    }
  }
})

onUnmounted(() => {
  stopDrag()
})
</script>

<template>
  <Teleport to="body">
    <Transition name="toolbox">
      <div
        v-show="visible"
        ref="panelRef"
        class="fixed z-50 flex h-[min(480px,calc(100dvh-1.5rem))] w-[min(660px,calc(100vw-1.5rem))] flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-white shadow-2xl"
        :style="{ left: position.x + 'px', top: position.y + 'px' }"
      >
        <div 
          class="flex items-center justify-between px-5 py-3 border-b border-[var(--color-border)] bg-gray-50 shrink-0 cursor-move select-none"
          @mousedown="startDrag"
        >
        <div class="flex min-w-0 items-center gap-1 overflow-x-auto p-1 bg-[var(--color-surface-muted)] rounded-lg">
          <button
            v-for="tab in [
              { key: 'rules', label: '条款查询', icon: 'lucide:file-search' },
              { key: 'premium', label: '保费测算', icon: 'lucide:calculator' },
              { key: 'cashValue', label: '现金价值', icon: 'lucide:chart-no-axes-combined' },
            ] as const"
            :key="tab.key"
            class="flex shrink-0 items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200"
            :class="activeTab === tab.key
              ? 'bg-white text-[var(--color-text-primary)] shadow-sm'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'"
            @click="activeTab = tab.key"
          >
            <Icon :icon="tab.icon" class="w-3.5 h-3.5" />
            {{ tab.label }}
          </button>
        </div>
        <button
          aria-label="关闭工具箱"
          title="关闭工具箱"
          class="w-7 h-7 flex items-center justify-center rounded-md text-[var(--color-text-muted)] hover:text-zinc-900 hover:bg-[var(--color-surface)] transition-colors"
          @click="$emit('close')"
        >
          <Icon icon="lucide:x" class="w-4 h-4" />
        </button>
      </div>

      <div class="flex min-h-0 flex-1 flex-col md:flex-row">
        <div class="w-full shrink-0 overflow-y-auto border-b border-[var(--color-border-light)] bg-[var(--color-surface-hover)] p-4 md:w-[270px] md:border-b-0 md:border-r">
          
          <div v-show="activeTab === 'rules'" class="space-y-4 animate-fade-in">
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">查询关键词</label>
              <input
                v-model="rulesQuery"
                type="text"
                placeholder="如：高血压能投保吗"
                class="w-full px-3 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30"
                @keypress.enter="searchRules"
              />
            </div>
            <button
              :disabled="rulesLoading || !rulesQuery.trim()"
              class="cta-btn w-full py-2.5 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="searchRules"
            >
              <div v-if="rulesLoading" class="w-4 h-4 border-2 border-[var(--color-text-primary)]/20 border-t-[var(--color-text-primary)] rounded-full animate-spin mr-2" />
              {{ rulesLoading ? '查询中...' : '检索条款' }}
            </button>
          </div>

          <div v-show="activeTab === 'premium'" class="space-y-3.5 animate-fade-in">
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">投保年龄</label>
              <input v-model.number="premAge" type="number" min="0" max="70" class="w-full px-3 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
            </div>
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">被保人性别</label>
              <div class="flex p-1 bg-[var(--color-surface-muted)] rounded-lg border border-[var(--color-border-light)]">
                <button
                  v-for="g in ['男', '女']" :key="g"
                  class="flex-1 py-1.5 rounded-md text-xs font-medium transition-all"
                  :class="premGender === g ? 'bg-white text-[var(--color-text-primary)] shadow-sm' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'"
                  @click="premGender = g"
                >{{ g }}</button>
              </div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">交费期</label>
              <select v-model.number="premPayPeriod" class="w-full px-3 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30 cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%208l5%205%205-5%22%20stroke%3D%22%23A1A1AA%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_8px_center] bg-no-repeat pr-8">
                <option v-for="p in PAY_PERIODS" :key="p" :value="p">{{ p === 1 ? '趸交' : `${p}年交` }}</option>
              </select>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">保额（元）</label>
              <input v-model.number="premAmount" type="number" :step="100000" min="100000" class="w-full px-3 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
            </div>
            <button
              :disabled="premiumLoading"
              class="cta-btn w-full py-2.5 mt-2 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="calcPremium"
            >
              <div v-if="premiumLoading" class="w-4 h-4 border-2 border-[var(--color-text-primary)]/20 border-t-[var(--color-text-primary)] rounded-full animate-spin mr-2" />
              {{ premiumLoading ? '计算中...' : '计算保费' }}
            </button>
          </div>

          <div v-show="activeTab === 'cashValue'" class="space-y-3.5 animate-fade-in">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">性别</label>
                <div class="flex p-1 bg-[var(--color-surface-muted)] rounded-lg border border-[var(--color-border-light)]">
                  <button
                    v-for="g in ['男', '女']" :key="g"
                    class="flex-1 py-1 rounded-md text-xs font-medium transition-all"
                    :class="cvGender === g ? 'bg-white text-[var(--color-text-primary)] shadow-sm' : 'text-[var(--color-text-secondary)]'"
                    @click="cvGender = g"
                  >{{ g }}</button>
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">年龄</label>
                <input v-model.number="cvAge" type="number" min="0" max="70" class="w-full px-2 py-1.5 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">交费期</label>
                <select v-model.number="cvPayPeriod" class="w-full px-2 py-1.5 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30 cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%208l5%205%205-5%22%20stroke%3D%22%23A1A1AA%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_8px_center] bg-no-repeat pr-6">
                  <option v-for="p in PAY_PERIODS" :key="p" :value="p">{{ p === 1 ? '趸交' : `${p}年交` }}</option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">保单年度</label>
                <input v-model.number="cvYear" type="number" min="1" max="75" class="w-full px-2 py-1.5 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
              </div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">保额（元）</label>
              <input v-model.number="cvAmount" type="number" :step="100000" min="100000" class="w-full px-3 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
            </div>
            <button
              :disabled="cvLoading"
              class="cta-btn w-full py-2.5 mt-2 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="calcCashValue"
            >
              <div v-if="cvLoading" class="w-4 h-4 border-2 border-[var(--color-text-primary)]/20 border-t-[var(--color-text-primary)] rounded-full animate-spin mr-2" />
              {{ cvLoading ? '计算中...' : '计算现金价值' }}
            </button>
          </div>
        </div>

          <div class="flex-1 p-6 overflow-y-auto bg-white flex flex-col items-stretch">
            <template v-if="activeTab === 'rules'">
              <div v-if="rulesLoading" class="flex flex-col items-center justify-center h-full">
                <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-[var(--color-text-primary)] rounded-full animate-spin mb-3" />
                <span class="text-xs text-[var(--color-text-secondary)] font-medium">系统正在检索条款...</span>
              </div>
              <div v-else-if="rulesResult" class="animate-fade-in h-full flex flex-col">
                <h4 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">条款原文结果</h4>
                <div class="text-sm text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap bg-[var(--color-surface)] p-4 rounded-xl border border-[var(--color-border-light)] flex-1 overflow-y-auto overflow-x-hidden min-h-0">
                  {{ rulesResult }}
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center h-full text-[var(--color-text-muted)] animate-fade-in">
                <div class="w-16 h-16 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-4">
                  <Icon icon="lucide:file-search" class="w-8 h-8 text-[var(--color-text-muted)]" />
                </div>
                <p class="text-sm font-medium text-[var(--color-text-primary)]">等待输入参数</p>
                <span class="text-xs mt-1.5 text-center leading-relaxed">在左侧输入关键词，点击检索</span>
              </div>
            </template>

            <template v-else-if="activeTab === 'premium'">
              <div v-if="premiumLoading" class="flex flex-col items-center justify-center h-full">
                <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-[var(--color-text-primary)] rounded-full animate-spin mb-3" />
                <span class="text-xs text-[var(--color-text-secondary)] font-medium">系统正在计算保费...</span>
              </div>
              <div v-else-if="premiumResult" class="animate-fade-in h-full flex flex-col">
                <h4 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">保费计算结果</h4>
                <div class="text-sm text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap bg-[var(--color-surface)] p-4 rounded-xl border border-[var(--color-border-light)] flex-1 overflow-y-auto overflow-x-hidden min-h-0">
                  {{ premiumResult }}
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center h-full text-[var(--color-text-muted)] animate-fade-in">
                <div class="w-16 h-16 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-4">
                  <Icon icon="lucide:circle-dollar-sign" class="w-8 h-8 text-[var(--color-text-muted)]" />
                </div>
                <p class="text-sm font-medium text-[var(--color-text-primary)]">等待输入参数</p>
                <span class="text-xs mt-1.5 text-center leading-relaxed">配置完参数后点击计算保费</span>
              </div>
            </template>

            <template v-else-if="activeTab === 'cashValue'">
              <div v-if="cvLoading" class="flex flex-col items-center justify-center h-full">
                <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-[var(--color-text-primary)] rounded-full animate-spin mb-3" />
                <span class="text-xs text-[var(--color-text-secondary)] font-medium">系统正在处理现金价值...</span>
              </div>
              <div v-else-if="cvResult" class="animate-fade-in h-full flex flex-col">
                <h4 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">现金价值查询结果</h4>
                <div class="text-sm text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap bg-[var(--color-surface)] p-4 rounded-xl border border-[var(--color-border-light)] flex-1 overflow-y-auto overflow-x-hidden min-h-0">
                  {{ cvResult }}
                </div>
              </div>
              <div v-else class="flex flex-col items-center justify-center h-full text-[var(--color-text-muted)] animate-fade-in">
                <div class="w-16 h-16 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-4">
                  <Icon icon="lucide:chart-no-axes-combined" class="w-8 h-8 text-[var(--color-text-muted)]" />
                </div>
                <p class="text-sm font-medium text-[var(--color-text-primary)]">等待输入参数</p>
                <span class="text-xs mt-1.5 text-center leading-relaxed">修改参数自动进行现金价值计算</span>
              </div>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.toolbox-enter-active,
.toolbox-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.toolbox-enter-from,
.toolbox-leave-to {
  opacity: 0;
  /* 优化3: 退场动画同步拉开距离 */
  transform: translateY(20px) scale(0.98); 
}
</style>
