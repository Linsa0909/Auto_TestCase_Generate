<template>
  <div class="flex flex-col gap-1">
    <label class="text-[11px] text-gray-500 uppercase tracking-[0.08em] font-medium">{{ label }}</label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-1.5 bg-transparent border-b border-gray-200 focus:border-gray-900 focus:bg-gray-50/30 outline-none transition-all text-[13px] text-gray-900 placeholder-gray-400"
    />
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  type: { type: String, default: 'text' },
})

defineEmits(['update:modelValue'])
</script>
