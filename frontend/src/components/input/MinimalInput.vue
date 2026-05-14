<template>
  <div class="flex flex-col gap-1.5">
    <label class="text-xs text-zinc-500 uppercase tracking-wider font-medium">{{ label }}</label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-2 bg-transparent border-b border-zinc-300 focus:border-zinc-500 focus:bg-zinc-50 outline-none transition-all text-sm text-zinc-900 placeholder-zinc-400"
    />
  </div>
</template>

<script setup>
defineProps({ label: { type: String, default: '' }, modelValue: { type: String, default: '' }, placeholder: { type: String, default: '' }, type: { type: String, default: 'text' } })
defineEmits(['update:modelValue'])
</script>
