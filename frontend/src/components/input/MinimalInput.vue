<template>
  <div class="flex flex-col gap-1.5">
    <label class="text-xs text-zinc-400 uppercase tracking-wider font-medium">{{ label }}</label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
      class="w-full pb-2 bg-transparent border-b border-zinc-800 focus:border-zinc-400 focus:bg-zinc-900/30 outline-none transition-all text-sm text-white placeholder-zinc-600"
    />
  </div>
</template>

<script setup>
defineProps({ label: { type: String, default: '' }, modelValue: { type: String, default: '' }, placeholder: { type: String, default: '' }, type: { type: String, default: 'text' } })
defineEmits(['update:modelValue'])
</script>
