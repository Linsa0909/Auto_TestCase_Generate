<template>
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
    <!-- Left Panel -->
    <aside class="lg:col-span-4 flex flex-col gap-6">
      <div class="flex flex-col gap-4">
        <MinimalInput label="需求编号" v-model="form.reqId" placeholder="支持多个以逗号隔开" />
        <MinimalInput label="需求名称" v-model="form.reqName" placeholder="例如：接口直接激励" />
        <div class="grid grid-cols-2 gap-4">
          <MinimalInput label="用例分组" v-model="form.group" placeholder="输入分组" />
          <MinimalSelect
            label="用例类型" v-model="form.type"
            :options="[{ value: '全面覆盖', label: '全面覆盖' }, { value: '仅冒烟', label: '仅冒烟' }, { value: '边界异常', label: '边界异常' }]"
          />
        </div>
      </div>

      <UploadZone :files="form.files" @update:files="form.files = $event" @remove="removeFile" />

      <div class="flex flex-col gap-1.5">
        <label class="text-xs text-zinc-500 uppercase tracking-wider font-medium">需求描述</label>
        <textarea
          v-model="form.desc" rows="4"
          placeholder="粘贴需求描述文本，包括功能概述、流程描述、验收标准..."
          class="w-full pt-2 pb-2 bg-transparent border-b border-zinc-300 focus:border-zinc-500 focus:bg-zinc-50 outline-none transition-all text-sm text-zinc-900 placeholder-zinc-400 resize-none leading-relaxed"
        ></textarea>
      </div>

      <div class="relative">
        <div class="absolute -inset-6 glow-indigo-strong pointer-events-none rounded-2xl" />
        <button
          @click="handleGenerate"
          :disabled="generating"
          class="relative w-full bg-zinc-900 text-white py-3 text-sm font-medium rounded-lg hover:bg-zinc-800 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <div v-if="generating" class="spinner w-4 h-4 !border-zinc-300 !border-t-zinc-900" />
          <Sparkles v-else class="w-4 h-4" :stroke-width="2" />
          {{ generating ? '正在生成...' : '智能解析与生成' }}
        </button>
      </div>

      <div class="flex flex-col gap-3 pt-5 border-t border-zinc-200">
        <div class="flex items-center justify-between">
          <h3 class="text-xs text-zinc-500 uppercase tracking-wider font-medium">生成历史</h3>
          <button @click="loadHistory" class="text-xs text-zinc-400 hover:text-zinc-600 transition-colors flex items-center gap-1">
            <RefreshCw class="w-3 h-3" :stroke-width="2" /> 刷新
          </button>
        </div>
        <div v-if="historyLoading" class="text-sm text-zinc-400 py-5 text-center">加载中...</div>
        <div v-else-if="history.length === 0" class="text-sm text-zinc-400 py-5 text-center">暂无历史记录</div>
        <div v-else class="flex flex-col gap-1.5 max-h-72 overflow-y-auto">
          <div
            v-for="(item, idx) in history" :key="idx"
            :class="[
              'flex items-center gap-3 px-4 py-3 rounded-lg border transition-all cursor-pointer group',
              historyActive?.download_url === item.download_url
                ? 'bg-zinc-200/50 border-zinc-400'
                : 'bg-zinc-50 border-zinc-200 hover:border-zinc-300 hover:scale-[1.01]'
            ]"
            @click="viewHistoryCases(item)"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm text-zinc-900 truncate font-medium">{{ item.requirement_name }}</div>
              <div class="text-xs text-zinc-400 mt-0.5">{{ item.created }} · {{ item.size_kb }} KB</div>
            </div>
            <button
              @click.stop="downloadHistory(item)"
              class="w-6 h-6 flex items-center justify-center rounded text-zinc-400 hover:text-zinc-600 hover:bg-zinc-200 transition-colors opacity-0 group-hover:opacity-100"
              title="下载 Excel"
            >
              <Download class="w-3.5 h-3.5" :stroke-width="2" />
            </button>
          </div>
        </div>
      </div>
    </aside>

    <!-- Right Panel -->
    <section class="lg:col-span-8 flex flex-col gap-5">
      <div class="flex items-center justify-between pb-4 border-b border-zinc-200">
        <div class="flex items-center gap-3">
          <h2 class="text-xs text-zinc-500 uppercase tracking-wider font-medium">
            {{ historyActive ? '历史记录' : '生成结果预览' }}
          </h2>
          <span v-if="result" class="text-xs text-zinc-400 tabular-nums">{{ result.test_cases?.length || 0 }} 条用例</span>
          <button v-if="historyActive" @click="clearHistoryView" class="text-xs text-zinc-400 hover:text-zinc-600 transition-colors">← 返回</button>
        </div>
        <div v-if="result" class="flex items-center gap-2">
          <button
            @click="handleExportEdited" :disabled="exporting"
            class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border border-zinc-300 text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 transition-colors active:scale-[0.98]"
          >
            <Download class="w-3.5 h-3.5" :stroke-width="2" />
            {{ exporting ? '导出中...' : '导出编辑结果' }}
          </button>
          <div class="flex flex-col gap-2">
            <button
              @click="pushCasesToDevops" :disabled="pushingCases"
              class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border border-indigo-400 text-indigo-600 hover:border-indigo-500 hover:text-indigo-700 transition-colors active:scale-[0.98] disabled:opacity-60"
            >
              <CloudDownload class="w-3.5 h-3.5" :stroke-width="2" />
              {{ pushingCases ? pushCasesMsg : `导入到 DevOps (${result?.test_cases?.length || 0}条)` }}
            </button>
            <div v-if="pushingCases" class="h-[3px] bg-zinc-200 rounded-full overflow-hidden">
              <div class="h-full w-1/2 bg-indigo-400 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>
      <StatsPanel :cases="result?.test_cases || []" />
      <DataTable :cases="result?.test_cases || []" :editable="true" @remove-case="removeCase" />
    </section>

    <Teleport to="body">
      <Transition name="fade">
        <div v-if="generating" class="fixed inset-0 bg-white/80 backdrop-blur-md z-30 flex flex-col items-center justify-center gap-5">
          <div class="spinner" />
          <div class="text-center">
            <p class="text-base font-medium text-zinc-900">正在生成测试用例</p>
            <p class="text-sm text-zinc-500 mt-1">AI 正在分析需求和原型图</p>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import { Sparkles, Download, Upload, RefreshCw, CloudDownload } from 'lucide-vue-next'
import MinimalInput from '../components/input/MinimalInput.vue'
import MinimalSelect from '../components/input/MinimalSelect.vue'
import UploadZone from '../components/input/UploadZone.vue'
import DataTable from '../components/output/DataTable.vue'
import StatsPanel from '../components/output/StatsPanel.vue'

const toast = inject('toast')
const form = reactive({ reqId: '', reqName: '', group: '', type: '全面覆盖', desc: '', files: [] })
function removeFile(index) { form.files.splice(index, 1) }
const generating = ref(false)
const result = ref(null)

async function handleGenerate() {
  if (!form.reqName.trim()) { toast('请输入需求名称', 'error'); return }
  if (!form.desc.trim() && form.files.length === 0) { toast('请至少提供需求描述或上传原型图', 'error'); return }
  generating.value = true; result.value = null
  try {
    const fd = new FormData()
    fd.append('requirement_name', form.reqName.trim()); fd.append('description', form.desc.trim())
    fd.append('requirement_id', form.reqId.trim()); fd.append('group', form.group.trim()); fd.append('test_type', form.type)
    for (const file of form.files) {
      if (file instanceof File) fd.append('files', file)
    }
    const res = await fetch('/api/generate', { method: 'POST', body: fd })
    if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || '生成失败') }
    result.value = await res.json()
    toast(`成功生成 ${result.value.count} 条测试用例`, 'success'); loadHistory()
  } catch (e) { toast(e.message, 'error') } finally { generating.value = false }
}

function removeCase(tcIdx) { if (result.value?.test_cases) result.value.test_cases.splice(tcIdx, 1) }
const exporting = ref(false)
async function handleExportEdited() {
  if (!result.value?.test_cases?.length) { toast('没有可导出的测试用例', 'error'); return }
  exporting.value = true
  try {
    const res = await fetch('/api/export', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test_cases: result.value.test_cases, requirement_name: result.value.requirement_name || '导出' }),
    })
    if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || '导出失败') }
    const data = await res.json()
    const a = document.createElement('a'); a.href = data.download_url; a.download = ''
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    toast(`已导出 ${data.count} 条测试用例`, 'success'); loadHistory()
  } catch (e) { toast(e.message, 'error') } finally { exporting.value = false }
}

const pushingCases = ref(false)
const pushCasesMsg = ref('导入到 DevOps')
async function pushCasesToDevops() {
  if (!result.value?.test_cases?.length) { toast('没有可推送的用例', 'error'); return }
  if (!form.reqName.trim()) { toast('请先在左侧填写需求名称', 'error'); return }
  pushingCases.value = true; pushCasesMsg.value = '推送中...'
  try {
    const res = await fetch('/api/push-cases-to-devops', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        test_cases: result.value.test_cases,
        requirement_name: form.reqName.trim(),
        description: form.desc.trim(),
        group: form.group.trim(),
      }),
    })
    if (!res.ok) { const err = await res.json().catch(()=>({detail:res.statusText})); throw new Error(err.detail||'推送失败') }
    const data = await res.json()
    toast(`已导入 DevOps: ${data.result?.case_ids?.length||0} 条用例`, 'success')
    pushCasesMsg.value = '推送完成'
  } catch (e) { toast(e.message, 'error'); pushCasesMsg.value = '导入到 DevOps' }
  finally { pushingCases.value = false }
}

const history = ref([])
const historyLoading = ref(false)
const historyActive = ref(null)
async function loadHistory() {
  historyLoading.value = true
  try { const res = await fetch('/api/history'); history.value = await res.json() }
  catch { history.value = [] } finally { historyLoading.value = false }
}
async function viewHistoryCases(item) {
  historyActive.value = item
  try {
    const res = await fetch('/api/history-cases/' + item.download_url.replace('/api/download/', ''))
    if (!res.ok) throw new Error('加载失败')
    const data = await res.json()
    result.value = { test_cases: data.test_cases, count: data.count, requirement_name: item.requirement_name, download_url: item.download_url }
  } catch (e) {
    toast('加载历史用例失败: ' + e.message, 'error')
    historyActive.value = null
  }
}
function clearHistoryView() {
  historyActive.value = null
  result.value = null
}
function downloadHistory(item) {
  const a = document.createElement('a'); a.href = item.download_url; a.download = ''
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
}
onMounted(() => { loadHistory() })
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 200ms ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
