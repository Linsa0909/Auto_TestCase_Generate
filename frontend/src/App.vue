<template>
  <div class="min-h-screen bg-white text-gray-900 font-sans selection:bg-gray-200">
    <TopNavbar @toggle-settings="showSettings = !showSettings" />

    <main class="h-[calc(100vh-48px)]">
      <Workbench
        :show-settings="showSettings"
        @close-settings="showSettings = false"
      />
    </main>

    <!-- Toast -->
    <Teleport to="body">
      <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        <TransitionGroup>
          <div
            v-for="t in toasts"
            :key="t.id"
            :class="[
              'pointer-events-auto px-4 py-2.5 bg-white shadow-md rounded-lg text-[13px] border-l-[3px] max-w-xs',
              t.type === 'success' ? 'border-l-emerald-500' :
              t.type === 'error'   ? 'border-l-red-500' :
                                     'border-l-gray-800',
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
