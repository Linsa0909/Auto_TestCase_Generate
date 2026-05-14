<template>
  <div v-if="cases.length" class="grid grid-cols-2 md:grid-cols-4 gap-3">
    <div class="rounded-lg bg-zinc-50 border border-zinc-200 p-4 hover:border-zinc-300 transition-colors">
      <div class="text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">总用例数</div>
      <div class="text-2xl font-semibold tracking-tight text-zinc-900 tabular-nums">{{ cases.length }}</div>
    </div>

    <div class="rounded-lg bg-zinc-50 border border-zinc-200 p-4 hover:border-zinc-300 transition-colors">
      <div class="text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">类型分布</div>
      <div class="flex flex-col gap-2 mt-1">
        <div v-for="item in typeStats" :key="item.label" class="flex items-center gap-2">
          <span class="text-xs text-zinc-700 w-8 shrink-0 font-medium">{{ item.label }}</span>
          <div class="flex-1 h-[5px] bg-zinc-200 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700 ease-out" :class="item.barClass" :style="{ width: item.pct + '%' }" />
          </div>
          <span class="text-xs text-zinc-500 w-5 text-right shrink-0 tabular-nums">{{ item.count }}</span>
        </div>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-50 border border-zinc-200 p-4 hover:border-zinc-300 transition-colors">
      <div class="text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">优先级分布</div>
      <div class="flex flex-col gap-2 mt-1">
        <div v-for="item in priorityStats" :key="item.label" class="flex items-center gap-2">
          <span class="text-xs text-zinc-700 w-8 shrink-0 font-medium">{{ item.label }}</span>
          <div class="flex-1 h-[5px] bg-zinc-200 rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700 ease-out" :class="item.barClass" :style="{ width: item.pct + '%' }" />
          </div>
          <span class="text-xs text-zinc-500 w-5 text-right shrink-0 tabular-nums">{{ item.count }}</span>
        </div>
      </div>
    </div>

    <div class="rounded-lg bg-zinc-50 border border-zinc-200 p-4 hover:border-zinc-300 transition-colors">
      <div class="text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">步骤总数</div>
      <div class="text-2xl font-semibold tracking-tight text-zinc-900 tabular-nums">{{ totalSteps }}</div>
      <div class="text-xs text-zinc-500 mt-1">平均 {{ avgSteps }} 步/用例</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ cases: { type: Array, default: () => [] } })
const total = computed(() => props.cases.length)
const typeStats = computed(() => {
  const map = {}
  for (const tc of props.cases) { const t = tc.raw_type || '功能'; map[t] = (map[t] || 0) + 1 }
  const barClasses = { '冒烟': 'bg-zinc-900', '功能': 'bg-zinc-500', '边界': 'bg-zinc-400', '异常': 'bg-zinc-500' }
  return ['冒烟', '功能', '边界', '异常'].filter(k => map[k]).map(k => ({
    label: k, count: map[k], pct: total.value ? (map[k] / total.value * 100) : 0, barClass: barClasses[k] || 'bg-zinc-500',
  }))
})
const priorityStats = computed(() => {
  const map = { L0: 0, L1: 0, L2: 0 }
  for (const tc of props.cases) { const p = tc.priority || 'L1'; if (map[p] !== undefined) map[p]++ }
  return [
    { label: 'L0', count: map.L0, pct: total.value ? (map.L0 / total.value * 100) : 0, barClass: 'bg-zinc-900' },
    { label: 'L1', count: map.L1, pct: total.value ? (map.L1 / total.value * 100) : 0, barClass: 'bg-zinc-500' },
    { label: 'L2', count: map.L2, pct: total.value ? (map.L2 / total.value * 100) : 0, barClass: 'bg-zinc-400' },
  ]
})
const totalSteps = computed(() => props.cases.reduce((sum, tc) => sum + (tc.steps?.length || 0), 0))
const avgSteps = computed(() => total.value ? (totalSteps.value / total.value).toFixed(1) : '0')
</script>
