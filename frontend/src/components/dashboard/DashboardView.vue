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
  <div class="flex-1 overflow-y-auto px-6 pb-6">

    <!-- Dashboard Grid -->
    <div class="grid grid-cols-3 gap-6 max-w-[1800px] mx-auto">
      <!-- Left column: Profile -->
      <div class="col-span-1">
        <ProfileCard :data="overview" />
      </div>

      <!-- Middle + Right: Radar -->
      <div class="col-span-2">
        <RadarChartCard :data="capabilities" />
      </div>

      <!-- Bottom Left: Growth Curve (wider) -->
      <div class="col-span-2">
        <GrowthCurveChart :data="growth" />
      </div>

      <!-- Bottom Right: Diagnostics -->
      <div class="col-span-1">
        <DiagnosticList :data="capabilities" />
      </div>
    </div>
  </div>
</template>
