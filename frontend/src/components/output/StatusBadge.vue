<template>
  <span :class="['inline-flex items-center px-2 py-[2px] text-xs tracking-wide rounded font-medium', typeClass]">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ type: { type: String, default: 'func' } })
const typeMap = {
  smoke: { label: '冒烟', class: 'bg-white text-black' },
  func: { label: '功能', class: 'bg-zinc-700 text-zinc-200' },
  edge: { label: '边界', class: 'bg-zinc-700 text-zinc-300' },
  error: { label: '异常', class: 'bg-zinc-700 text-zinc-300' },
}
const label = computed(() => typeMap[props.type]?.label || '功能')
const typeClass = computed(() => typeMap[props.type]?.class || 'bg-zinc-700 text-zinc-200')
</script>
