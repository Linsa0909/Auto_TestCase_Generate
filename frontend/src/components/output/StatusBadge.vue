<template>
  <span :class="['inline-flex items-center px-2 py-[2px] text-xs tracking-wide rounded font-medium', typeClass]">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ type: { type: String, default: 'func' } })
const typeMap = {
  smoke: { label: '冒烟', class: 'bg-zinc-900 text-white' },
  func: { label: '功能', class: 'bg-zinc-200 text-zinc-700' },
  edge: { label: '边界', class: 'bg-zinc-200 text-zinc-600' },
  error: { label: '异常', class: 'bg-zinc-200 text-zinc-600' },
}
const label = computed(() => typeMap[props.type]?.label || '功能')
const typeClass = computed(() => typeMap[props.type]?.class || 'bg-zinc-200 text-zinc-600')
</script>
