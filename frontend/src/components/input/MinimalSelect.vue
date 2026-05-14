<template>
  <div class="flex flex-col gap-1.5">
    <label class="text-xs text-zinc-500 uppercase tracking-wider font-medium">{{ label }}</label>
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-2 bg-transparent border-b border-zinc-300 focus:border-zinc-500 focus:bg-zinc-50 outline-none transition-all text-sm cursor-pointer text-zinc-900"
    >
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
  </div>
</template>

<script setup>
defineProps({ label: { type: String, default: '' }, modelValue: { type: String, default: '' }, options: { type: Array, default: () => [] } })
defineEmits(['update:modelValue'])
</script>
