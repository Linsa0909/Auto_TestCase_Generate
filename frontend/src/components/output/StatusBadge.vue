<template>
  <span
    :class="[
      'inline-block px-2.5 py-0.5 text-[11px] tracking-wide rounded-md',
      typeClass,
    ]"
  >
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'func' },
})

const typeMap = {
  smoke: { label: '冒烟', class: 'bg-gray-900 text-white' },
  func: { label: '功能', class: 'bg-gray-100 text-gray-600' },
  edge: { label: '边界', class: 'bg-gray-50 text-gray-400' },
  error: { label: '异常', class: 'bg-gray-50 text-gray-400 border border-gray-200' },
}

const label = computed(() => typeMap[props.type]?.label || '功能')
const typeClass = computed(() => typeMap[props.type]?.class || 'bg-gray-100 text-gray-600')
</script>
