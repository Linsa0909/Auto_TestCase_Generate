<template>
  <div class="flex flex-col gap-2">
    <label class="text-xs text-gray-500 uppercase tracking-widest">{{ label }}</label>
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-2 bg-transparent border-b border-gray-200 focus:border-black outline-none transition-colors text-sm cursor-pointer rounded-none"
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
