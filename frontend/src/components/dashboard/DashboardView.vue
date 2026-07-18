<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DashboardOverview, DashboardCapabilities, DashboardGrowth } from '../../services/api'
import { fetchDashboardOverview, fetchDashboardCapabilities, fetchDashboardGrowth } from '../../services/api'
import ProfileCard from './ProfileCard.vue'
import RadarChartCard from './RadarChartCard.vue'
import GrowthCurveChart from './GrowthCurveChart.vue'
import DiagnosticList from './DiagnosticList.vue'

const overview = ref<DashboardOverview | null>(null)
const capabilities = ref<DashboardCapabilities | null>(null)
const growth = ref<DashboardGrowth | null>(null)

onMounted(async () => {
  const [o, c, g] = await Promise.all([
    fetchDashboardOverview(),
    fetchDashboardCapabilities(),
    fetchDashboardGrowth(),
  ])
  overview.value = o
  capabilities.value = c
  growth.value = g
})
</script>

<template>
  <div class="min-h-0 flex-1 overflow-y-auto px-4 pb-8 pt-3 sm:px-6 xl:px-8 xl:pb-10">
    <div class="grid grid-cols-1 gap-x-10 gap-y-10 xl:grid-cols-3 xl:gap-y-12">
      <section class="min-w-0 xl:col-span-1" aria-label="个人训练概览">
        <ProfileCard :data="overview" />
      </section>

      <section class="min-w-0 xl:col-span-2" aria-label="综合能力模型">
        <RadarChartCard :data="capabilities" />
      </section>

      <section class="min-w-0 xl:col-span-2" aria-label="能力成长曲线">
        <GrowthCurveChart :data="growth" />
      </section>

      <section class="min-w-0 xl:col-span-1" aria-label="AI 导师总评">
        <DiagnosticList :data="capabilities" />
      </section>
    </div>
  </div>
</template>
