<template>
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
    <!-- ===== Left Panel: Input ===== -->
    <aside class="lg:col-span-4 flex flex-col gap-5">
      <!-- Section: Basic Info -->
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-3.5">
          <MinimalInput label="需求编号" v-model="form.reqId" placeholder="支持多个以逗号隔开" />
          <MinimalInput label="需求名称" v-model="form.reqName" placeholder="例如：接口直接激励" />

          <div class="grid grid-cols-2 gap-4">
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
      </div>

      <!-- Section: Upload -->
      <UploadZone :files="form.files" @update:files="form.files = $event" @remove="removeFile" />

      <!-- Section: Description -->
      <div class="flex flex-col gap-1">
        <label class="text-[11px] text-gray-500 uppercase tracking-[0.08em] font-medium">需求描述</label>
        <textarea
          v-model="form.desc"
          rows="4"
          placeholder="粘贴需求描述文本，包括功能概述、流程描述、验收标准..."
          class="w-full pt-1.5 pb-1.5 bg-transparent border-b border-gray-200 focus:border-gray-900 focus:bg-gray-50/30 outline-none transition-all text-[13px] text-gray-900 placeholder-gray-400 resize-none leading-relaxed"
        ></textarea>
      </div>

      <!-- Generate Button -->
      <button
        @click="handleGenerate"
        :disabled="generating"
        class="w-full bg-gray-900 text-white py-2.5 text-[13px] font-medium rounded-md hover:bg-gray-800 active:bg-gray-900 active:scale-[0.99] transition-all flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed disabled:active:scale-100"
      >
        <div v-if="generating" class="spinner w-3.5 h-3.5 !border-gray-500 !border-t-white" />
        <Sparkles v-else class="w-3.5 h-3.5" :stroke-width="2" />
        {{ generating ? '正在生成...' : '智能解析与生成' }}
      </button>

      <!-- Section: History -->
      <div class="flex flex-col gap-2 pt-3 border-t border-gray-100">
        <div class="flex items-center justify-between">
          <h3 class="text-[11px] text-gray-500 uppercase tracking-[0.08em] font-medium">生成历史</h3>
          <button
            @click="loadHistory"
            class="text-[11px] text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1"
          >
            <RefreshCw class="w-2.5 h-2.5" :stroke-width="2" />
            刷新
          </button>
        </div>

        <div v-if="historyLoading" class="text-[13px] text-gray-400 py-4 text-center">加载中...</div>

        <div v-else-if="history.length === 0" class="text-[13px] text-gray-400 py-4 text-center">
          暂无历史记录
        </div>

        <div v-else class="flex flex-col gap-1 max-h-64 overflow-y-auto">
          <div
            v-for="(item, idx) in history"
            :key="idx"
            class="flex items-center gap-2.5 px-3 py-2 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer group"
            @click="downloadHistory(item)"
          >
            <div class="flex-1 min-w-0">
              <div class="text-[13px] text-gray-800 truncate font-medium">{{ item.requirement_name }}</div>
              <div class="text-[11px] text-gray-400 mt-0.5">{{ item.created }} · {{ item.size_kb }} KB</div>
            </div>
            <Download
              class="w-3.5 h-3.5 text-gray-300 group-hover:text-gray-900 transition-all"
              :stroke-width="1.5"
            />
          </div>
        </div>
      </div>
    </aside>

    <!-- ===== Right Panel: Output ===== -->
    <section class="lg:col-span-8 flex flex-col gap-4">
      <!-- Header -->
      <div class="flex items-center justify-between pb-3 border-b border-gray-100">
        <div class="flex items-center gap-2.5">
          <h2 class="text-[11px] text-gray-500 uppercase tracking-[0.08em] font-medium">生成结果预览</h2>
          <span v-if="result" class="text-[11px] text-gray-400 tabular-nums">{{ result.test_cases?.length || 0 }} 条用例</span>
        </div>
        <div v-if="result" class="flex items-center gap-2">
          <button
            @click="handleExportEdited"
            :disabled="exporting"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors active:scale-[0.98]"
          >
            <Download class="w-3 h-3" :stroke-width="2" />
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

    <!-- Loading Overlay -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="generating"
          class="fixed inset-0 bg-white/80 backdrop-blur-md z-30 flex flex-col items-center justify-center gap-4"
        >
          <div class="spinner" />
          <div class="text-center">
            <p class="text-[13px] font-medium text-gray-800">正在生成测试用例</p>
            <p class="text-[11px] text-gray-500 mt-0.5">AI 正在分析需求和原型图</p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import { Sparkles, Download, RefreshCw } from 'lucide-vue-next'
import MinimalInput from '../components/input/MinimalInput.vue'
import MinimalSelect from '../components/input/MinimalSelect.vue'
import UploadZone from '../components/input/UploadZone.vue'
import DataTable from '../components/output/DataTable.vue'
import StatsPanel from '../components/output/StatsPanel.vue'

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
  loadHistory()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 200ms ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
