<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { DashboardOverview, DashboardCapabilities, DashboardGrowth } from '../../services/api'
import { fetchDashboardOverview, fetchDashboardCapabilities, fetchDashboardGrowth } from '../../services/api'
import ProfileCard from './ProfileCard.vue'
import RadarChartCard from './RadarChartCard.vue'
import GrowthCurveChart from './GrowthCurveChart.vue'
import DiagnosticList from './DiagnosticList.vue'
import MentorReview from './MentorReview.vue'

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
      <div class="dashboard-grid grid h-full min-h-0 grid-cols-1 overflow-y-auto lg:grid-rows-[250px_minmax(0,1fr)] lg:overflow-hidden">
        <section class="profile-region min-h-0" aria-label="个人训练概览">
          <ProfileCard :data="overview" />
        </section>

        <div class="analysis-grid grid min-h-0 grid-cols-1 gap-y-3 px-4 pb-4 lg:grid-cols-[repeat(3,minmax(0,1fr))] lg:grid-rows-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <section class="radar-region data-region min-h-0 overflow-auto" aria-label="综合能力模型">
            <RadarChartCard :data="capabilities" />
          </section>

          <section class="diagnostic-region data-region min-h-0 overflow-auto" aria-label="高频失分项">
            <DiagnosticList :data="capabilities" />
          </section>

          <section class="mentor-region data-region min-h-0 overflow-auto" aria-label="AI 导师总评">
            <MentorReview :data="capabilities" />
          </section>

          <section class="growth-region data-region min-h-0 overflow-auto" aria-label="能力成长曲线">
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

.data-region {
  min-width: 0;
  width: 100%;
  background: transparent;
  border: 0;
  box-shadow: none;
  scrollbar-width: none;
}

.data-region::-webkit-scrollbar {
  display: none;
}

@media (min-width: 1024px) {
  .analysis-grid {
    grid-template-columns:
      minmax(280px, 1fr)
      40px
      minmax(240px, 0.72fr)
      12px
      minmax(0, 1.28fr);
    column-gap: 0;
  }

  .radar-region {
    grid-column: 1;
    grid-row: 1;
  }

  .diagnostic-region {
    grid-column: 3;
    grid-row: 1;
  }

  .mentor-region {
    grid-column: 5;
    grid-row: 1;
  }

  .growth-region {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}

.dashboard-grid > div {
  min-width: 0;
}
</style>
