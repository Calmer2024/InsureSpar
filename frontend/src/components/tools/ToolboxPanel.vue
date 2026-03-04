<script setup lang="ts">
import { ref } from 'vue'
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
const loading = ref(false)
const result = ref('')

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
  loading.value = true
  result.value = ''
  try {
    result.value = await toolSearchRules(rulesQuery.value.trim())
  } catch (e: any) {
    result.value = `[错误] 查询失败: ${e.message}`
  } finally {
    loading.value = false
  }
}

async function calcPremium() {
  loading.value = true
  result.value = ''
  try {
    result.value = await toolPremiumRate(premAge.value, premGender.value, premPayPeriod.value, premAmount.value)
  } catch (e: any) {
    result.value = `[错误] 查询失败: ${e.message}`
  } finally {
    loading.value = false
  }
}

async function calcCashValue() {
  loading.value = true
  result.value = ''
  try {
    result.value = await toolCashValue(cvGender.value, cvAge.value, cvPayPeriod.value, cvYear.value, cvAmount.value)
  } catch (e: any) {
    result.value = `[错误] 查询失败: ${e.message}`
  } finally {
    loading.value = false
  }
}

const PAY_PERIODS = [1, 3, 5, 10, 15, 20, 25, 30]
</script>

<template>
  <Transition name="toolbox">
    <div
      v-if="visible"
      class="absolute bottom-[calc(100%+16px)] left-0 w-full bg-white border border-[var(--color-border)] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.15)] rounded-2xl z-20 overflow-hidden flex flex-col"
      style="max-height: 520px"
    >
      <div class="flex items-center justify-between px-5 py-3 border-b border-[var(--color-border)] bg-white shrink-0">
        <div class="flex items-center gap-1 p-1 bg-[var(--color-surface-muted)] rounded-lg">
          <button
            v-for="tab in [
              { key: 'rules', label: '条款查询', svg: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
              { key: 'premium', label: '保费测算', svg: 'M9 7h6m0 10v-3m-3 3v-3m-3 3v-3m2 0h4M9 7v1m6-1v1M9 11h6' },
              { key: 'cashValue', label: '现金价值', svg: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z' },
            ] as const"
            :key="tab.key"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200"
            :class="activeTab === tab.key
              ? 'bg-white text-[var(--color-text-primary)] shadow-sm'
              : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'"
            @click="activeTab = tab.key; result = ''"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="tab.svg" />
            </svg>
            {{ tab.label }}
          </button>
        </div>
        <button
          class="w-7 h-7 flex items-center justify-center rounded-md text-[var(--color-text-muted)] hover:text-zinc-900 hover:bg-[var(--color-surface)] transition-colors"
          @click="$emit('close')"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="flex min-h-0" style="max-height: 460px">
        <div class="w-[300px] shrink-0 p-5 border-r border-[var(--color-border-light)] overflow-y-auto bg-[var(--color-surface-hover)]">
          
          <div v-if="activeTab === 'rules'" class="space-y-4 animate-fade-in">
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
              :disabled="loading || !rulesQuery.trim()"
              class="cta-btn w-full py-2.5 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="searchRules"
            >
              <div v-if="loading" class="w-4 h-4 border-2 border-[var(--color-text-primary)]/20 border-t-[var(--color-text-primary)] rounded-full animate-spin mr-2" />
              {{ loading ? '查询中...' : '检索条款' }}
            </button>
          </div>

          <div v-else-if="activeTab === 'premium'" class="space-y-3.5 animate-fade-in">
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
              :disabled="loading"
              class="cta-btn w-full py-2.5 mt-2 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="calcPremium"
            >
              <div v-if="loading" class="w-4 h-4 border-2 border-[var(--color-text-primary)]/20 border-t-[var(--color-text-primary)] rounded-full animate-spin mr-2" />
              {{ loading ? '计算中...' : '计算保费' }}
            </button>
          </div>

          <div v-else class="space-y-3.5 animate-fade-in">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">性别</label>
                <div class="flex p-1 bg-[var(--color-surface-muted)] rounded-lg border border-[var(--color-border-light)]">
                  <button
                    v-for="g in ['男', '女']" :key="g"
                    class="flex-1 py-1.5 rounded-md text-xs font-medium transition-all"
                    :class="cvGender === g ? 'bg-white text-[var(--color-text-primary)] shadow-sm' : 'text-[var(--color-text-secondary)]'"
                    @click="cvGender = g"
                  >{{ g }}</button>
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">年龄</label>
                <input v-model.number="cvAge" type="number" min="0" max="70" class="w-full px-2 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">交费期</label>
                <select v-model.number="cvPayPeriod" class="w-full px-2 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30 cursor-pointer appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%208l5%205%205-5%22%20stroke%3D%22%23A1A1AA%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E')] bg-[position:right_8px_center] bg-no-repeat pr-6">
                  <option v-for="p in PAY_PERIODS" :key="p" :value="p">{{ p === 1 ? '趸交' : `${p}年交` }}</option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">保单年度</label>
                <input v-model.number="cvYear" type="number" min="1" max="75" class="w-full px-2 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
              </div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">保额（元）</label>
              <input v-model.number="cvAmount" type="number" :step="100000" min="100000" class="w-full px-3 py-2 text-sm bg-white border border-[var(--color-border)] rounded-lg outline-none transition-all focus:border-[#BFE0A9] focus:ring-2 focus:ring-[#BFE0A9]/30" />
            </div>
            <button
              :disabled="loading"
              class="cta-btn w-full py-2.5 mt-2 disabled:opacity-40 disabled:cursor-not-allowed"
              @click="calcCashValue"
            >
              <div v-if="loading" class="w-4 h-4 border-2 border-[var(--color-text-primary)]/20 border-t-[var(--color-text-primary)] rounded-full animate-spin mr-2" />
              {{ loading ? '计算中...' : '计算现金价值' }}
            </button>
          </div>
        </div>

        <div class="flex-1 p-6 overflow-y-auto bg-white">
          <div v-if="loading" class="flex flex-col items-center justify-center h-full">
            <div class="w-8 h-8 border-2 border-[var(--color-border-light)] border-t-[var(--color-text-primary)] rounded-full animate-spin mb-3" />
            <span class="text-xs text-[var(--color-text-secondary)] font-medium">系统正在处理，请稍候...</span>
          </div>
          
          <div v-else-if="result" class="animate-fade-in h-full flex flex-col">
            <h4 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">输出结果</h4>
            <div class="text-sm text-[var(--color-text-primary)] leading-relaxed whitespace-pre-wrap bg-[var(--color-surface)] p-4 rounded-xl border border-[var(--color-border-light)] flex-1 overflow-y-auto">
              {{ result }}
            </div>
          </div>
          
          <div v-else class="flex flex-col items-center justify-center h-full text-[var(--color-text-muted)] animate-fade-in">
            <div class="w-16 h-16 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border-light)] shadow-sm flex items-center justify-center mb-4">
              <svg class="w-8 h-8 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <p class="text-sm font-medium text-[var(--color-text-primary)]">等待输入参数</p>
            <span class="text-xs mt-1.5 text-center leading-relaxed">在左侧配置需要查询的工具信息<br/>结果将在此区域呈现</span>
          </div>
        </div>
      </div>
    </div>
  </Transition>
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