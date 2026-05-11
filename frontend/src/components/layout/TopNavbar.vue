<template>
  <header class="flex items-center justify-between px-4 py-3">
    <div>
      <h1 class="text-[15px] font-semibold tracking-tight text-gray-900">Test Case Intelligence</h1>
    </div>
    <div class="flex items-center gap-3">
      <span class="text-[10px] text-gray-300 tracking-[0.08em] uppercase font-medium">v1.0</span>
      <button
        @click="$emit('toggle-settings')"
        class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-gray-100 transition-colors active:scale-95"
      >
        <Settings class="w-[15px] h-[15px] text-gray-400 hover:text-gray-600" :stroke-width="1.5" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { Settings } from 'lucide-vue-next'

defineEmits(['toggle-settings'])
</script>
