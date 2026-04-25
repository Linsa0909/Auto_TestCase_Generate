<template>
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-16">
    <!-- ===== Left Panel: Input ===== -->
    <aside class="lg:col-span-4 flex flex-col gap-8">
      <div class="flex flex-col gap-6">
        <MinimalInput label="需求编号" v-model="form.reqId" placeholder="支持多个以逗号隔开" />
        <MinimalInput label="需求名称" v-model="form.reqName" placeholder="例如：接口直接激励" />

        <div class="grid grid-cols-2 gap-8">
          <MinimalInput label="用例分组" v-model="form.group" placeholder="输入分组" />
          <MinimalSelect
            label="用例类型"
            v-model="form.type"
            :options="[
              { value: '全面覆盖', label: '全面覆盖' },
              { value: '仅冒烟', label: '仅冒烟' },
              { value: '边界异常', label: '边界异常' },
            ]"
          />
        </div>
      </div>

      <UploadZone :files="form.files" @update:files="form.files = $event" @remove="removeFile" />

      <div class="flex flex-col gap-2">
        <label class="text-[11px] text-gray-500 uppercase tracking-widest">需求描述</label>
        <textarea
          v-model="form.desc"
          rows="4"
          placeholder="粘贴需求描述文本，包括功能概述、流程描述、验收标准..."
          class="w-full pt-2 pb-2 bg-transparent border-b border-gray-200 focus:border-black outline-none transition-colors text-sm placeholder-gray-300 resize-none"
        ></textarea>
      </div>

      <button
        @click="handleGenerate"
        :disabled="generating"
        class="mt-2 w-full bg-black text-white py-4 text-sm font-medium tracking-wide rounded-lg hover:bg-gray-800 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <div v-if="generating" class="spinner w-4 h-4 !border-gray-400 !border-t-white" />
        <Sparkles v-else class="w-4 h-4" :stroke-width="1.5" />
        {{ generating ? '正在生成...' : '智能解析与生成' }}
      </button>

      <!-- ===== History Panel ===== -->
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <h3 class="text-[11px] text-gray-500 uppercase tracking-widest">生成历史</h3>
          <button
            @click="loadHistory"
            class="text-xs text-gray-400 hover:text-black transition-colors"
          >
            刷新
          </button>
        </div>

        <div v-if="historyLoading" class="text-sm text-gray-300 py-4 text-center">加载中...</div>

        <div v-else-if="history.length === 0" class="text-sm text-gray-300 py-4 text-center">
          暂无历史记录
        </div>

        <div v-else class="flex flex-col gap-2 max-h-80 overflow-y-auto">
          <div
            v-for="(item, idx) in history"
            :key="idx"
            class="flex items-center gap-3 px-4 py-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer group"
            @click="downloadHistory(item)"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm text-gray-700 truncate">{{ item.requirement_name }}</div>
              <div class="text-xs text-gray-400 mt-0.5">{{ item.created }} · {{ item.size_kb }} KB</div>
            </div>
            <Download
              class="w-3.5 h-3.5 text-gray-300 group-hover:text-black transition-colors shrink-0"
              :stroke-width="1.5"
            />
          </div>
        </div>
      </div>
    </aside>

    <!-- ===== Right Panel: Output ===== -->
    <section class="lg:col-span-8 flex flex-col gap-6">
      <!-- Header -->
      <div class="flex items-center justify-between pb-5">
        <div class="flex items-center gap-3">
          <h2 class="text-sm text-gray-500 uppercase tracking-widest">生成结果预览</h2>
          <span v-if="result" class="text-xs text-gray-400">{{ result.test_cases?.length || 0 }} 条用例</span>
        </div>
        <div v-if="result" class="flex items-center gap-4">
          <button
            @click="handleExportEdited"
            :disabled="exporting"
            class="flex items-center gap-2 px-4 py-2 rounded-lg text-xs text-gray-500 hover:bg-gray-50 hover:text-black transition-all"
          >
            <Download class="w-4 h-4" :stroke-width="1.5" />
            {{ exporting ? '导出中...' : '导出编辑结果' }}
          </button>
        </div>
      </div>

      <!-- Stats Panel -->
      <StatsPanel :cases="result?.test_cases || []" />

      <!-- Data Table (editable) -->
      <DataTable
        :cases="result?.test_cases || []"
        :editable="true"
        @remove-case="removeCase"
      />
    </section>

    <!-- ===== Settings Panel (Slide-in) ===== -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showSettings"
          class="fixed inset-0 bg-black/10 z-40"
          @click="$emit('close-settings')"
        />
      </Transition>
      <Transition name="slide">
        <div
          v-if="showSettings"
          class="fixed top-0 right-0 h-full w-[400px] bg-white shadow-2xl z-50 p-10 flex flex-col gap-8 overflow-y-auto"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-medium tracking-wide">API 配置</h3>
            <button @click="$emit('close-settings')" class="text-gray-400 hover:text-black transition-colors">
              <X class="w-4 h-4" :stroke-width="1.5" />
            </button>
          </div>

          <p class="text-xs text-gray-400 leading-relaxed">
            配置 OpenAI 兼容 API 信息。支持 OpenAI、DeepSeek、Qwen、Ollama 等服务。
          </p>

          <MinimalInput label="API Key" type="password" v-model="settings.api_key" placeholder="sk-..." />
          <MinimalInput label="API Base URL" v-model="settings.api_base" placeholder="https://api.openai.com/v1" />
          <MinimalInput label="模型名称" v-model="settings.model" placeholder="gpt-4o" />

          <button
            @click="saveSettings"
            class="mt-auto w-full bg-black text-white py-3.5 text-sm font-medium tracking-wide rounded-lg hover:bg-gray-800 transition-colors"
          >
            保存配置
          </button>

          <div
            v-if="configMsg"
            :class="['text-xs px-3 py-2', configMsg.ok ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50']"
          >
            {{ configMsg.text }}
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Loading Overlay -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="generating"
          class="fixed inset-0 bg-white/80 backdrop-blur-md z-30 flex flex-col items-center justify-center gap-5"
        >
          <div class="spinner" />
          <p class="text-sm text-gray-500">正在生成测试用例</p>
          <p class="text-xs text-gray-300">AI 正在分析需求和原型图</p>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import { Sparkles, Download, X } from 'lucide-vue-next'
import MinimalInput from '../components/input/MinimalInput.vue'
import MinimalSelect from '../components/input/MinimalSelect.vue'
import UploadZone from '../components/input/UploadZone.vue'
import DataTable from '../components/output/DataTable.vue'
import StatsPanel from '../components/output/StatsPanel.vue'

const props = defineProps({ showSettings: Boolean })
const emit = defineEmits(['close-settings'])
const toast = inject('toast')

// --- Form ---
const form = reactive({
  reqId: '',
  reqName: '',
  group: '',
  type: '全面覆盖',
  desc: '',
  files: [],
})

function removeFile(index) {
  form.files.splice(index, 1)
}

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
    toast('API 配置已保存', 'success')
  } catch (e) {
    configMsg.value = { ok: false, text: e.message }
  }
}

// --- Generate ---
const generating = ref(false)
const result = ref(null)

async function handleGenerate() {
  if (!form.reqName.trim()) {
    toast('请输入需求名称', 'error')
    return
  }
  if (!form.desc.trim() && form.files.length === 0) {
    toast('请至少提供需求描述或上传原型图', 'error')
    return
  }

  generating.value = true
  result.value = null

  try {
    const fd = new FormData()
    fd.append('requirement_name', form.reqName.trim())
    fd.append('description', form.desc.trim())
    fd.append('requirement_id', form.reqId.trim())
    fd.append('group', form.group.trim())
    fd.append('test_type', form.type)
    for (const file of form.files) {
      fd.append('files', file)
    }

    const res = await fetch('/api/generate', { method: 'POST', body: fd })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || '生成失败')
    }

    result.value = await res.json()
    toast(`成功生成 ${result.value.count} 条测试用例`, 'success')
    loadHistory()
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    generating.value = false
  }
}

// --- Remove Case ---
function removeCase(tcIdx) {
  if (result.value?.test_cases) {
    result.value.test_cases.splice(tcIdx, 1)
  }
}

// --- Export Edited ---
const exporting = ref(false)

async function handleExportEdited() {
  if (!result.value?.test_cases?.length) {
    toast('没有可导出的测试用例', 'error')
    return
  }

  exporting.value = true
  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        test_cases: result.value.test_cases,
        requirement_name: result.value.requirement_name || '导出',
      }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || '导出失败')
    }

    const data = await res.json()
    const a = document.createElement('a')
    a.href = data.download_url
    a.download = ''
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    toast(`已导出 ${data.count} 条测试用例`, 'success')
    loadHistory()
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    exporting.value = false
  }
}

// --- History ---
const history = ref([])
const historyLoading = ref(false)

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await fetch('/api/history')
    history.value = await res.json()
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

function downloadHistory(item) {
  const a = document.createElement('a')
  a.href = item.download_url
  a.download = ''
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

onMounted(() => {
  loadSettings()
  loadHistory()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 200ms ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

.slide-enter-active,
.slide-leave-active { transition: transform 250ms ease, opacity 200ms ease; }
.slide-enter-from,
.slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
