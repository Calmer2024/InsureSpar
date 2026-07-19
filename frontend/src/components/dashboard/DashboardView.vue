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
  <div class="dashboard-view min-h-0 flex-1 overflow-y-auto bg-white px-4 pb-4 pt-3 sm:px-6 lg:overflow-hidden xl:px-8">
    <section class="dashboard-surface h-full min-h-0 overflow-hidden" aria-label="学员能力档案">
      <div class="dashboard-grid grid h-full min-h-0 grid-cols-1 overflow-y-auto lg:grid-cols-[280px_minmax(0,1fr)] lg:overflow-hidden">
        <section class="profile-region min-h-0 overflow-hidden" aria-label="个人训练概览">
          <ProfileCard :data="overview" />
        </section>

        <div class="grid min-h-0 grid-cols-1 gap-4 p-4 lg:grid-cols-2 lg:grid-rows-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:pl-0">
          <section class="dashboard-card min-h-0 overflow-hidden" aria-label="综合能力模型">
            <RadarChartCard :data="capabilities" />
          </section>

          <section class="dashboard-card min-h-0 overflow-hidden" aria-label="AI 导师总评">
            <DiagnosticList :data="capabilities" />
          </section>

          <section class="dashboard-card min-h-0 overflow-hidden lg:col-span-2" aria-label="能力成长曲线">
            <GrowthCurveChart :data="growth" />
          </section>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-surface {
  background: transparent;
}

.profile-region {
  min-width: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.dashboard-card {
  min-width: 0;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid rgba(216, 232, 222, 0.9);
  box-shadow: 0 8px 24px rgba(56, 94, 71, 0.06);
}

.dashboard-grid > div {
  min-width: 0;
}
</style>
