<template>
  <div class="flex flex-col min-h-0">
    <!-- Tab Navigation -->
    <div class="flex items-center border-b border-zinc-800/60 px-6">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="handleTabClick(tab.key)"
        :class="[
          'relative px-5 py-3 text-sm font-medium transition-colors',
          activeTab === tab.key ? 'text-white' : 'text-zinc-500 hover:text-zinc-300'
        ]"
      >
        <div class="flex items-center gap-2">
          <component :is="tab.icon" class="w-4 h-4" :stroke-width="1.5" />
          {{ tab.label }}
        </div>
        <div
          v-if="activeTab === tab.key"
          class="absolute bottom-0 left-4 right-4 h-[2px] bg-white rounded-full"
        />
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 min-h-0 overflow-y-auto">
      <div class="max-w-[1400px] mx-auto px-6 py-6">
        <TestCaseView v-if="activeTab === 'cases'" />
        <template v-else>
          <PlanListView
            v-if="!editingPlanId"
            :key="planListKey"
            @open-plan="openPlan"
          />
          <TestPlanView
            v-else
            :plan-id="editingPlanId"
            @back="closePlan"
          />
        </template>
      </div>
    </div>

    <!-- Settings Panel -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showSettings"
          class="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          @click="$emit('close-settings')"
        />
      </Transition>
      <Transition name="slide">
        <div
          v-if="showSettings"
          class="fixed top-0 right-0 h-full w-[400px] bg-zinc-950 border-l border-zinc-800 z-50 p-8 flex flex-col gap-7 overflow-y-auto"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold tracking-tight text-white">API 配置</h3>
            <button
              @click="$emit('close-settings')"
              class="w-8 h-8 flex items-center justify-center rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
            >
              <X class="w-4 h-4" :stroke-width="1.5" />
            </button>
          </div>

          <p class="text-sm text-zinc-400 leading-relaxed">
            配置 OpenAI 兼容 API 信息。支持 OpenAI、DeepSeek、Qwen、Ollama 等服务。
          </p>

          <MinimalInput label="API Key" type="password" v-model="settings.api_key" placeholder="sk-..." />
          <MinimalInput label="API Base URL" v-model="settings.api_base" placeholder="https://api.openai.com/v1" />
          <MinimalInput label="模型名称" v-model="settings.model" placeholder="gpt-4o" />

          <button
            @click="saveSettings"
            class="w-full bg-white text-black py-3 text-sm font-medium rounded-lg hover:shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)] active:scale-[0.99] transition-all"
          >
            保存 AI 配置
          </button>

          <!-- DevOps Config -->
          <div class="border-t border-zinc-800 pt-6 mt-2">
            <h3 class="text-base font-semibold tracking-tight text-white mb-1">DevOps 平台</h3>
            <p class="text-sm text-zinc-400 leading-relaxed mb-4">
              配置 DevOps 测试管理平台，登录后自动获取 Token，按产品名称匹配。
            </p>
            <div class="flex flex-col gap-4">
              <MinimalInput label="平台地址" v-model="devopsSettings.devops_url" placeholder="https://devops.company.com" />
              <MinimalInput label="Token（直接填入则跳过登录）" type="password" v-model="devopsSettings.devops_token" placeholder="从浏览器DevTools获取" />
              <MinimalInput label="用户名" v-model="devopsSettings.devops_username" placeholder="登录用户名" />
              <MinimalInput label="密码" type="password" v-model="devopsSettings.devops_password" placeholder="登录密码" />
              <MinimalInput label="产品名称" v-model="devopsSettings.product_name" placeholder="与 DevOps 中的产品名称一致" />
            </div>
            <button
              @click="saveDevOpsSettings"
              class="w-full mt-4 bg-white text-black py-3 text-sm font-medium rounded-lg hover:shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)] active:scale-[0.99] transition-all"
            >
              保存 DevOps 配置
            </button>
          </div>

          <div
            v-if="configMsg"
            :class="['text-sm px-4 py-3 rounded-lg', configMsg.ok ? 'text-emerald-300 bg-emerald-500/10 border border-emerald-500/20' : 'text-red-300 bg-red-500/10 border border-red-500/20']"
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
import PlanListView from './PlanListView.vue'

const props = defineProps({ showSettings: Boolean })
const emit = defineEmits(['close-settings'])

const tabs = [
  { key: 'plan', label: '测试计划', icon: ClipboardList },
  { key: 'cases', label: '测试用例', icon: FileText },
]
const activeTab = ref('plan')
const editingPlanId = ref(null)
const planListKey = ref(0)

function handleTabClick(key) {
  activeTab.value = key
  if (key !== 'plan') editingPlanId.value = null
}

function openPlan(planId) {
  editingPlanId.value = planId
}

function closePlan() {
  editingPlanId.value = null
  planListKey.value++
}

const settings = reactive({ api_key: '', api_base: 'https://api.deepseek.com', model: 'deepseek-chat' })
const devopsSettings = reactive({ devops_url: '', devops_token: '', devops_username: '', devops_password: '', product_name: '' })
const configMsg = ref(null)

async function loadSettings() {
  try {
    const res = await fetch('/api/config')
    const data = await res.json()
    settings.api_base = data.api_base || 'https://api.deepseek.com'
    settings.model = data.model || 'deepseek-chat'
    settings.api_key = data.api_key || ''
  } catch {}
  try {
    const res = await fetch('/api/devops-config')
    const data = await res.json()
    devopsSettings.devops_url = data.devops_url || ''
    devopsSettings.devops_token = data.devops_token || ''
    devopsSettings.devops_username = data.devops_username || ''
    devopsSettings.devops_password = data.devops_password || ''
    devopsSettings.product_name = data.product_name || ''
  } catch {}
}

async function saveSettings() {
  configMsg.value = null
  try {
    const res = await fetch('/api/config', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
    if (!res.ok) throw new Error('保存失败')
    configMsg.value = { ok: true, text: 'AI 配置保存成功' }
  } catch (e) { configMsg.value = { ok: false, text: e.message } }
}

async function saveDevOpsSettings() {
  configMsg.value = null
  try {
    const res = await fetch('/api/devops-config', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(devopsSettings),
    })
    if (!res.ok) throw new Error('保存失败')
    configMsg.value = { ok: true, text: 'DevOps 配置保存成功' }
  } catch (e) { configMsg.value = { ok: false, text: e.message } }
}

onMounted(() => { loadSettings() })
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
