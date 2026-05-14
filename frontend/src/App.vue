<template>
  <div class="min-h-screen bg-white text-zinc-900 font-sans selection:bg-indigo-500/15">
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
              t.type === 'success' ? 'bg-white/95 border-emerald-300 text-emerald-700 shadow-lg' :
              t.type === 'error'   ? 'bg-white/95 border-red-300 text-red-700 shadow-lg' :
                                     'bg-white/95 border-zinc-300 text-zinc-700 shadow-lg',
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
