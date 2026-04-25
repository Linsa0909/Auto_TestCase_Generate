<template>
  <div class="min-h-screen bg-white text-black font-sans selection:bg-gray-200">
    <TopNavbar @toggle-settings="showSettings = !showSettings" />

    <main class="max-w-[1600px] mx-auto px-10 pb-20 mt-8">
      <Workbench
        :show-settings="showSettings"
        @close-settings="showSettings = false"
      />
    </main>

    <!-- Toast -->
    <Teleport to="body">
      <div class="fixed top-6 right-6 z-50 flex flex-col gap-2 pointer-events-none">
        <TransitionGroup>
          <div
            v-for="t in toasts"
            :key="t.id"
            :class="[
              'pointer-events-auto px-5 py-3.5 bg-white shadow-lg rounded-xl text-sm border-l-[3px]',
              t.type === 'success' ? 'border-l-emerald-600' :
              t.type === 'error'   ? 'border-l-red-600' :
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
