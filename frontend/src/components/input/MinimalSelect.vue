<template>
  <div class="flex flex-col gap-1">
    <label class="text-[11px] text-gray-500 uppercase tracking-[0.08em] font-medium">{{ label }}</label>
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-1.5 bg-transparent border-b border-gray-200 focus:border-gray-900 focus:bg-gray-50/30 outline-none transition-all text-[13px] cursor-pointer text-gray-900"
    >
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  modelValue: { type: String, default: '' },
  options: { type: Array, default: () => [] },
})

defineEmits(['update:modelValue'])
</script>
