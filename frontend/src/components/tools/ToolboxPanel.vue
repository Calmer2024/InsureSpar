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
    result.value = `❌ 查询失败: ${e.message}`
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
    result.value = `❌ 查询失败: ${e.message}`
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
    result.value = `❌ 查询失败: ${e.message}`
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
      class="absolute bottom-full left-0 w-full bg-surface-card border-t border-border shadow-[0_-8px_24px_rgba(0,0,0,0.08)] rounded-t-2xl z-20 overflow-hidden"
      style="max-height: 420px"
    >
      <!-- 头部 -->
      <div class="flex items-center justify-between px-4 py-2.5 border-b border-border bg-surface">
        <div class="flex gap-1">
          <button
            v-for="tab in [
              { key: 'rules', icon: '📄', label: '条款' },
              { key: 'premium', icon: '💰', label: '保费' },
              { key: 'cashValue', icon: '📊', label: '现金价值' },
            ] as const"
            :key="tab.key"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
            :class="activeTab === tab.key
              ? 'bg-primary-500 text-white shadow-sm'
              : 'text-text-secondary hover:bg-surface-hover'"
            @click="activeTab = tab.key; result = ''"
          >
            {{ tab.icon }} {{ tab.label }}
          </button>
        </div>
        <button
          class="w-7 h-7 flex items-center justify-center rounded-lg text-text-muted hover:text-danger hover:bg-red-50 transition text-sm"
          @click="$emit('close')"
        >✕</button>
      </div>

      <div class="flex min-h-0" style="max-height: 360px">
        <!-- 左侧：输入区域 -->
        <div class="w-[280px] shrink-0 p-4 border-r border-border overflow-y-auto">
          <!-- 条款查询 -->
          <div v-if="activeTab === 'rules'" class="space-y-3">
            <label class="block text-[11px] font-semibold text-text-secondary uppercase tracking-wider">查询关键词</label>
            <input
              v-model="rulesQuery"
              type="text"
              placeholder="如：高血压能投保吗"
              class="w-full px-3 py-2 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400 focus:ring-1 focus:ring-primary-100"
              @keypress.enter="searchRules"
            />
            <button
              :disabled="loading || !rulesQuery.trim()"
              class="w-full py-2 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.97] transition-all disabled:opacity-30"
              @click="searchRules"
            >
              {{ loading ? '查询中…' : '🔍 查询条款' }}
            </button>
          </div>

          <!-- 保费计算 -->
          <div v-else-if="activeTab === 'premium'" class="space-y-2.5">
            <div>
              <label class="block text-[11px] font-semibold text-text-secondary mb-1">年龄</label>
              <input v-model.number="premAge" type="number" min="0" max="70" class="w-full px-3 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400" />
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-text-secondary mb-1">性别</label>
              <div class="flex gap-2">
                <button
                  v-for="g in ['男', '女']" :key="g"
                  class="flex-1 py-1.5 rounded-lg text-xs font-medium border transition-all"
                  :class="premGender === g ? 'bg-primary-500 text-white border-primary-500' : 'border-border-light text-text-secondary hover:border-primary-300'"
                  @click="premGender = g"
                >{{ g }}</button>
              </div>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-text-secondary mb-1">交费期</label>
              <select v-model.number="premPayPeriod" class="w-full px-3 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400">
                <option v-for="p in PAY_PERIODS" :key="p" :value="p">{{ p === 1 ? '趸交' : `${p}年交` }}</option>
              </select>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-text-secondary mb-1">保额（元）</label>
              <input v-model.number="premAmount" type="number" :step="100000" min="100000" class="w-full px-3 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400" />
            </div>
            <button
              :disabled="loading"
              class="w-full py-2 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.97] transition-all disabled:opacity-30"
              @click="calcPremium"
            >
              {{ loading ? '计算中…' : '💰 计算保费' }}
            </button>
          </div>

          <!-- 现金价值 -->
          <div v-else class="space-y-2.5">
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] font-semibold text-text-secondary mb-1">性别</label>
                <div class="flex gap-1">
                  <button
                    v-for="g in ['男', '女']" :key="g"
                    class="flex-1 py-1.5 rounded-lg text-[11px] font-medium border transition-all"
                    :class="cvGender === g ? 'bg-primary-500 text-white border-primary-500' : 'border-border-light text-text-secondary'"
                    @click="cvGender = g"
                  >{{ g }}</button>
                </div>
              </div>
              <div>
                <label class="block text-[11px] font-semibold text-text-secondary mb-1">年龄</label>
                <input v-model.number="cvAge" type="number" min="0" max="70" class="w-full px-2 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-[11px] font-semibold text-text-secondary mb-1">交费期</label>
                <select v-model.number="cvPayPeriod" class="w-full px-2 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400">
                  <option v-for="p in PAY_PERIODS" :key="p" :value="p">{{ p === 1 ? '趸交' : `${p}年交` }}</option>
                </select>
              </div>
              <div>
                <label class="block text-[11px] font-semibold text-text-secondary mb-1">保单年度</label>
                <input v-model.number="cvYear" type="number" min="1" max="75" class="w-full px-2 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400" />
              </div>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-text-secondary mb-1">保额（元）</label>
              <input v-model.number="cvAmount" type="number" :step="100000" min="100000" class="w-full px-3 py-1.5 text-sm bg-surface-muted border border-border-light rounded-lg outline-none focus:border-primary-400" />
            </div>
            <button
              :disabled="loading"
              class="w-full py-2 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:opacity-90 active:scale-[0.97] transition-all disabled:opacity-30"
              @click="calcCashValue"
            >
              {{ loading ? '计算中…' : '📊 计算现金价值' }}
            </button>
          </div>
        </div>

        <!-- 右侧：结果展示 -->
        <div class="flex-1 p-4 overflow-y-auto">
          <div v-if="loading" class="flex items-center justify-center h-full">
            <div class="w-5 h-5 border-2 border-border border-t-primary-500 rounded-full animate-spin" />
          </div>
          <div v-else-if="result" class="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">
            {{ result }}
          </div>
          <div v-else class="flex flex-col items-center justify-center h-full text-text-muted">
            <span class="text-2xl mb-2">🧰</span>
            <span class="text-xs">选择工具并输入参数，结果将在此显示</span>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.toolbox-enter-active,
.toolbox-leave-active {
  transition: all 0.25s ease;
}
.toolbox-enter-from,
.toolbox-leave-to {
  opacity: 0;
  transform: translateY(16px);
}
</style>
