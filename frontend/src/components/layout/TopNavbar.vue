<template>
  <header class="flex items-center justify-between px-10 py-7 border-b border-gray-100">
    <h1 class="text-xl font-semibold tracking-tight">Test Case Intelligence</h1>
    <div class="flex items-center gap-5">
      <span class="text-xs text-gray-300 tracking-widest uppercase">v1.0</span>
      <button
        @click="$emit('toggle-settings')"
        class="w-9 h-9 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
      >
        <Settings :class="['w-[18px] h-[18px] text-gray-400']" :stroke-width="1.5" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { Settings } from 'lucide-vue-next'

defineEmits(['toggle-settings'])
</script>
