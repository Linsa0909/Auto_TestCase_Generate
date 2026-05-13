<template>
  <div class="min-h-screen bg-black text-white font-sans selection:bg-indigo-500/30">
    <TopNavbar @toggle-settings="showSettings = !showSettings" />

    <main class="h-[calc(100vh-52px)]">
      <Workbench
        :show-settings="showSettings"
        @close-settings="showSettings = false"
      />
    </main>

    <!-- Toast -->
    <Teleport to="body">
      <div class="fixed top-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
        <TransitionGroup>
          <div
            v-for="t in toasts"
            :key="t.id"
            :class="[
              'pointer-events-auto px-5 py-3 rounded-lg text-sm border max-w-sm backdrop-blur-sm',
              t.type === 'success' ? 'bg-zinc-900/90 border-emerald-500/30 text-emerald-300' :
              t.type === 'error'   ? 'bg-zinc-900/90 border-red-500/30 text-red-300' :
                                     'bg-zinc-900/90 border-zinc-700 text-zinc-200',
            ]"
          >
            {{ t.message }}
          </div>
        </TransitionGroup>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import TopNavbar from './components/layout/TopNavbar.vue'
import Workbench from './views/Workbench.vue'

const showSettings = ref(false)
const toasts = ref([])
let toastId = 0

function showToast(message, type = 'info') {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}

provide('toast', showToast)
</script>
