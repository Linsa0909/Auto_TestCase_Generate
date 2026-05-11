<template>
  <div class="flex flex-col min-h-0">
    <!-- Top Tab Navigation -->
    <div class="flex items-center gap-0 border-b border-gray-150 px-4">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'relative px-4 py-2.5 text-[13px] font-medium transition-colors',
          activeTab === tab.key
            ? 'text-gray-900'
            : 'text-gray-400 hover:text-gray-600'
        ]"
      >
        <div class="flex items-center gap-1.5">
          <component :is="tab.icon" class="w-3.5 h-3.5" :stroke-width="1.5" />
          {{ tab.label }}
        </div>
        <div
          v-if="activeTab === tab.key"
          class="absolute bottom-0 left-3 right-3 h-[2px] bg-gray-900 rounded-full"
        />
      </button>
    </div>

    <!-- Content Area -->
    <div class="flex-1 min-h-0 overflow-y-auto">
      <div class="max-w-[1400px] mx-auto px-4 py-5">
        <TestCaseView v-if="activeTab === 'cases'" />
        <TestPlanView v-else />
      </div>
    </div>

    <!-- Settings Panel (Slide-in) -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showSettings"
          class="fixed inset-0 bg-black/5 backdrop-blur-sm z-40"
          @click="$emit('close-settings')"
        />
      </Transition>
      <Transition name="slide">
        <div
          v-if="showSettings"
          class="fixed top-0 right-0 h-full w-[360px] bg-white shadow-2xl z-50 p-6 flex flex-col gap-6 overflow-y-auto"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-[15px] font-semibold tracking-tight text-gray-900">API 配置</h3>
            <button
              @click="$emit('close-settings')"
              class="w-6 h-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <X class="w-3.5 h-3.5" :stroke-width="2" />
            </button>
          </div>

          <p class="text-[12px] text-gray-500 leading-relaxed">
            配置 OpenAI 兼容 API 信息。支持 OpenAI、DeepSeek、Qwen、Ollama 等服务。
          </p>

          <MinimalInput label="API Key" type="password" v-model="settings.api_key" placeholder="sk-..." />
          <MinimalInput label="API Base URL" v-model="settings.api_base" placeholder="https://api.openai.com/v1" />
          <MinimalInput label="模型名称" v-model="settings.model" placeholder="gpt-4o" />

          <button
            @click="saveSettings"
            class="mt-auto w-full bg-gray-900 text-white py-2.5 text-[13px] font-medium rounded-md hover:bg-gray-800 active:bg-gray-900 active:scale-[0.99] transition-all"
          >
            保存配置
          </button>

          <div
            v-if="configMsg"
            :class="['text-[12px] px-3 py-2 rounded-md', configMsg.ok ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50']"
          >
            {{ configMsg.text }}
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { FileText, ClipboardList, X } from 'lucide-vue-next'
import MinimalInput from '../components/input/MinimalInput.vue'
import TestCaseView from './TestCaseView.vue'
import TestPlanView from './TestPlanView.vue'

const props = defineProps({ showSettings: Boolean })
const emit = defineEmits(['close-settings'])

// --- Tab ---
const tabs = [
  { key: 'cases', label: '测试用例', icon: FileText },
  { key: 'plan', label: '测试计划', icon: ClipboardList },
]
const activeTab = ref('cases')

// --- Settings ---
const settings = reactive({
  api_key: '',
  api_base: 'http://172.16.3.6:8589',
  model: 'GLM-5.1',
})
const configMsg = ref(null)

async function loadSettings() {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    settings.api_base = data.api_base || 'http://172.16.3.6:8589'
    settings.model = data.model || 'GLM-5.1'
    settings.api_key = data.api_key || ''
  } catch { /* no config yet */ }
}

async function saveSettings() {
  configMsg.value = null
  try {
    const res = await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
    if (!res.ok) throw new Error('保存失败')
    configMsg.value = { ok: true, text: '配置保存成功' }
  } catch (e) {
    configMsg.value = { ok: false, text: e.message }
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 200ms ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

.slide-enter-active,
.slide-leave-active { transition: transform 250ms cubic-bezier(0.16, 1, 0.3, 1), opacity 200ms ease; }
.slide-enter-from,
.slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
