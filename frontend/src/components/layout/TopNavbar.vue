<template>
  <header class="flex items-center justify-between px-6 h-[52px] border-b border-zinc-800/60">
    <div class="flex items-center gap-3">
      <div class="w-6 h-6 rounded-md bg-white flex items-center justify-center">
        <span class="text-[11px] font-bold text-black">TC</span>
      </div>
      <h1 class="text-[15px] font-semibold tracking-tight text-white">Test Case Intelligence</h1>
    </div>
    <div class="flex items-center gap-3">
      <span class="text-[11px] text-zinc-500 tracking-wider uppercase font-medium">v1.0</span>
      <button
        @click="$emit('toggle-settings')"
        class="w-8 h-8 flex items-center justify-center rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800 transition-all"
      >
        <Settings class="w-4 h-4" :stroke-width="1.5" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { Settings } from 'lucide-vue-next'
defineEmits(['toggle-settings'])
</script>
