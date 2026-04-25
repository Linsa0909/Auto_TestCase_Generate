<template>
  <div class="flex flex-col gap-2">
    <label class="text-xs text-gray-500 uppercase tracking-widest">{{ label }}</label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-2 bg-transparent border-b border-gray-200 focus:border-black outline-none transition-colors text-sm placeholder-gray-300"
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
