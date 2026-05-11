<template>
  <span
    :class="[
      'inline-flex items-center px-1.5 py-[1px] text-[10px] tracking-wide rounded font-medium',
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
  func: { label: '功能', class: 'bg-gray-100 text-gray-700' },
  edge: { label: '边界', class: 'bg-gray-100 text-gray-600' },
  error: { label: '异常', class: 'bg-gray-100 text-gray-600' },
}

const label = computed(() => typeMap[props.type]?.label || '功能')
const typeClass = computed(() => typeMap[props.type]?.class || 'bg-gray-100 text-gray-700')
</script>
