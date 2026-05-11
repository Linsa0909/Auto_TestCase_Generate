<template>
  <div class="flex flex-col h-full">
    <!-- Top Bar -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-150">
      <div class="flex items-center gap-4">
        <input
          v-model="planName"
          placeholder="输入迭代名称"
          class="text-[15px] font-semibold text-gray-900 bg-transparent border-0 border-b border-transparent pb-0 focus:border-gray-400 focus:outline-none transition-colors placeholder-gray-400 w-48"
        />
        <div class="flex items-center gap-3 text-[13px]">
          <span class="text-gray-500"><span class="text-gray-900 font-semibold tabular-nums">{{ requirements.length }}</span> 需求</span>
          <span class="text-gray-300">·</span>
          <span class="text-gray-500"><span :class="completedCount === requirements.length && requirements.length > 0 ? 'text-gray-900' : 'text-gray-600'" class="font-semibold tabular-nums">{{ completedCount }}</span> 完成</span>
        </div>
      </div>
      <button
        v-if="completedCount > 0"
        @click="exportBatch"
        :disabled="batchExporting"
        class="flex items-center gap-1.5 px-3.5 py-[7px] rounded-md text-[13px] font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors active:scale-[0.98]"
      >
        <Download class="w-3.5 h-3.5" :stroke-width="2" />
        {{ batchExporting ? '导出中...' : '导出全部' }}
      </button>
    </div>

    <!-- Import Section (collapsible) -->
    <div class="border-b border-gray-150">
      <button
        @click="importExpanded = !importExpanded"
        class="w-full flex items-center justify-between px-4 py-2 text-[13px] text-gray-700 hover:text-gray-900 transition-colors"
      >
        <span class="flex items-center gap-1.5">
          <ChevronDown :class="['w-3 h-3 transition-transform', importExpanded ? '' : '-rotate-90']" :stroke-width="2.5" />
          <span class="font-medium">导入需求</span>
          <span v-if="requirements.length > 0 && !importExpanded" class="text-gray-400">（已导入 {{ requirements.length }} 个）</span>
        </span>
        <span class="text-[11px] text-gray-400">支持从项目管理工具粘贴</span>
      </button>
      <div v-if="importExpanded" class="px-4 pb-2.5">
        <div class="flex gap-2.5">
          <textarea
            v-model="importText"
            rows="3"
            placeholder="粘贴需求列表，支持多种格式：&#10;#194038  数据字典建模工具开发-概念模型  王沁雪  sprint75  2026-04-29  2026-05-15&#10;#188657  【0321】功能名称  2026-04-13  2026-04-22  余超逸"
            class="flex-1 rounded-md border border-gray-200 bg-white px-3 py-2 text-[13px] text-gray-800 placeholder-gray-400 focus:border-gray-400 focus:outline-none resize-none leading-relaxed"
          ></textarea>
          <div class="flex flex-col gap-1.5">
            <button
              @click="parseImport"
              class="px-4 py-2 rounded-md text-[12px] font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors active:scale-[0.98] whitespace-nowrap"
            >
              解析导入
            </button>
            <button
              @click="addEmptyRow"
              class="px-4 py-2 rounded-md text-[12px] font-medium text-gray-600 border border-gray-200 hover:bg-gray-50 hover:text-gray-900 transition-colors whitespace-nowrap"
            >
              手动添加
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content: Two Columns -->
    <div class="flex flex-1 min-h-0 overflow-hidden">
      <!-- Left: Requirement Cards -->
      <div class="w-[320px] shrink-0 border-r border-gray-150 flex flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto">
          <div
            v-for="(req, idx) in requirements"
            :key="idx"
            @click="selectedIdx = idx"
            :class="[
              'px-4 py-2.5 border-b border-gray-100 cursor-pointer transition-colors relative',
              selectedIdx === idx ? 'bg-gray-50' : 'hover:bg-gray-50/50'
            ]"
          >
            <div
              v-if="selectedIdx === idx"
              class="absolute left-0 top-1.5 bottom-1.5 w-[2.5px] bg-gray-900 rounded-full"
            />
            <div class="flex items-start gap-2">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5 mb-0.5">
                  <span class="text-[11px] text-gray-500 font-mono shrink-0">{{ req.id }}</span>
                  <span
                    v-if="req.status === 'done' && req.testCases?.length"
                    class="text-[10px] px-1.5 py-[1px] rounded bg-gray-900 text-white font-medium leading-tight"
                  >{{ req.testCases.length }} 条</span>
                </div>
                <div class="text-[13px] text-gray-900 font-medium truncate leading-snug">{{ req.name }}</div>
                <div class="flex items-center gap-1.5 mt-0.5 text-[11px] text-gray-500">
                  <span v-if="req.owner">{{ req.owner }}</span>
                  <span v-if="req.owner && req.startDate" class="text-gray-300">·</span>
                  <span v-if="req.startDate" class="tabular-nums text-gray-400">{{ req.startDate.slice(5) }}~{{ req.endDate?.slice(5) }}</span>
                </div>
              </div>
              <div class="flex items-center gap-1 pt-0.5">
                <span
                  v-if="req.status === 'pending'"
                  class="w-[6px] h-[6px] rounded-full bg-gray-300 shrink-0"
                />
                <span
                  v-else-if="req.status === 'generating'"
                  class="w-[6px] h-[6px] rounded-full bg-amber-500 animate-pulse shrink-0"
                />
                <span
                  v-else
                  class="w-[6px] h-[6px] rounded-full bg-emerald-500 shrink-0"
                />
                <button
                  @click.stop="removeRequirement(idx)"
                  class="w-4 h-4 flex items-center justify-center rounded text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors"
                >
                  <X class="w-2.5 h-2.5" :stroke-width="2.5" />
                </button>
              </div>
            </div>
          </div>

          <div v-if="requirements.length === 0" class="flex flex-col items-center justify-center py-20 text-gray-400">
            <ClipboardList class="w-7 h-7 mb-2" :stroke-width="1.2" />
            <p class="text-[13px]">粘贴需求列表开始</p>
          </div>
        </div>

        <div v-if="requirements.length > 0" class="p-3 border-t border-gray-150">
          <button
            @click="batchGenerate"
            :disabled="batchGenerating"
            class="w-full py-2 rounded-md bg-gray-900 text-white text-[13px] font-medium hover:bg-gray-800 transition-colors active:scale-[0.99] flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <div v-if="batchGenerating" class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <Sparkles v-else class="w-3 h-3" :stroke-width="2" />
            {{ batchGenerating ? `生成中 ${progressDone}/${requirements.length}` : '一键生成全部用例' }}
          </button>
          <div v-if="batchGenerating" class="h-[3px] bg-gray-200 rounded-full overflow-hidden mt-2">
            <div
              class="h-full bg-gray-900 rounded-full transition-all duration-500 ease-out"
              :style="{ width: (progressDone / requirements.length * 100) + '%' }"
            />
          </div>
        </div>
      </div>

      <!-- Right: Detail Panel -->
      <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div v-if="selectedReq == null" class="flex flex-col items-center justify-center flex-1 text-gray-400">
          <FileText class="w-7 h-7 mb-2" :stroke-width="1.2" />
          <p class="text-[13px]">选择左侧需求查看详情</p>
        </div>

        <template v-else>
          <div class="flex-1 overflow-y-auto px-5 py-4">
            <div class="max-w-[580px]">
              <!-- Header -->
              <div class="mb-4">
                <div class="text-[11px] text-gray-500 font-mono mb-0.5">{{ selectedReq.id }}</div>
                <h3 class="text-[15px] font-semibold text-gray-900 leading-snug">{{ selectedReq.name }}</h3>
                <div class="flex items-center gap-2 mt-1 text-[11px] text-gray-500">
                  <span v-if="selectedReq.owner">{{ selectedReq.owner }}</span>
                  <span v-if="selectedReq.startDate" class="text-gray-400">{{ selectedReq.startDate }} ~ {{ selectedReq.endDate }}</span>
                  <span
                    v-if="selectedReq.status === 'pending'"
                    class="px-1.5 py-[1px] rounded bg-gray-200 text-gray-700 font-medium"
                  >待生成</span>
                  <span
                    v-else-if="selectedReq.status === 'generating'"
                    class="px-1.5 py-[1px] rounded bg-amber-100 text-amber-800 font-medium"
                  >生成中</span>
                  <span
                    v-else
                    class="px-1.5 py-[1px] rounded bg-emerald-100 text-emerald-800 font-medium"
                  >已完成</span>
                </div>
              </div>

              <!-- Description -->
              <div class="mb-3">
                <label class="block text-[11px] text-gray-500 font-medium mb-1">需求描述</label>
                <textarea
                  v-model="selectedReq.description"
                  rows="3"
                  placeholder="添加需求描述，包括功能概述、业务场景、验收标准..."
                  class="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-[13px] text-gray-800 placeholder-gray-400 focus:border-gray-400 focus:outline-none resize-none leading-relaxed"
                ></textarea>
              </div>

              <!-- Prototype Files -->
              <div class="mb-3">
                <label class="block text-[11px] text-gray-500 font-medium mb-1">原型文件</label>
                <UploadZone
                  :files="selectedReq.files"
                  @update:files="selectedReq.files = $event"
                />
              </div>

              <!-- Generated Cases -->
              <div v-if="selectedReq.testCases?.length > 0" class="mb-3">
                <label class="block text-[11px] text-gray-500 font-medium mb-1">已生成用例 ({{ selectedReq.testCases.length }})</label>
                <div class="rounded-md border border-gray-200 bg-white divide-y divide-gray-100 max-h-52 overflow-y-auto">
                  <div
                    v-for="(tc, ti) in selectedReq.testCases"
                    :key="ti"
                    class="flex items-center gap-2.5 px-3 py-1.5 text-[13px]"
                  >
                    <span class="text-[11px] text-gray-400 w-4 tabular-nums shrink-0">{{ ti + 1 }}</span>
                    <span class="text-gray-800 flex-1 truncate">{{ tc.title }}</span>
                    <span class="text-[10px] px-1.5 py-[1px] rounded bg-gray-100 text-gray-600 font-medium whitespace-nowrap">{{ tc.raw_type }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="px-5 py-2.5 border-t border-gray-150">
            <div class="max-w-[580px] flex items-center gap-2.5">
              <button
                @click="generateSingle(selectedIdx)"
                :disabled="selectedReq.status === 'generating' || selectedReq.status === 'done'"
                class="flex-1 py-2 rounded-md text-[13px] font-medium bg-gray-900 text-white hover:bg-gray-800 transition-colors active:scale-[0.98] flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Sparkles class="w-3 h-3" :stroke-width="2" />
                {{ selectedReq.status === 'generating' ? '生成中...' : selectedReq.status === 'done' ? '已生成' : '生成用例' }}
              </button>
              <button
                @click="removeRequirement(selectedIdx)"
                class="px-3.5 py-2 rounded-md text-[13px] font-medium text-gray-500 border border-gray-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>

  <!-- Batch Loading Overlay -->
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="batchGenerating"
        class="fixed inset-0 bg-white/80 backdrop-blur-md z-30 flex flex-col items-center justify-center gap-4"
      >
        <div class="w-7 h-7 border-2 border-gray-200 border-t-gray-800 rounded-full animate-spin" />
        <div class="text-center">
          <p class="text-[13px] font-medium text-gray-800">正在批量生成测试用例</p>
          <p class="text-[11px] text-gray-500 mt-0.5">{{ progressDone }} / {{ requirements.length }} 个需求已完成</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { Sparkles, Download, X, ClipboardList, FileText, ChevronDown } from 'lucide-vue-next'
import UploadZone from '../components/input/UploadZone.vue'

const toast = inject('toast')

// --- Plan Info ---
const planName = ref('')

// --- Import ---
const importText = ref('')
const importExpanded = ref(true)

function parseRequirementLine(line) {
  const result = { id: '', name: '', startDate: '', endDate: '', owner: '', description: '', files: [], status: 'pending', testCases: [] }
  const idMatch = line.match(/#(\d+)/)
  if (idMatch) result.id = '#' + idMatch[1]
  const datePattern = /(\d{4}-\d{2}-\d{2})/g
  const dates = []
  let m
  while ((m = datePattern.exec(line)) !== null) dates.push(m[1])
  if (dates.length >= 1) result.startDate = dates[0]
  if (dates.length >= 2) result.endDate = dates[1]
  let remaining = line
  if (idMatch) remaining = remaining.replace(/#\d+/, '')
  remaining = remaining.replace(/\d{4}-\d{2}-\d{2}/g, '')
  remaining = remaining.replace(/sprint\d+/gi, '')
  const parts = remaining.split(/[\t]+|\s{2,}/).map(s => s.trim()).filter(Boolean)
  let nameParts = []
  for (const part of parts) {
    if (/^[\u4e00-\u9fa5]{2,4}$/.test(part) && !result.owner) {
      result.owner = part
    } else {
      nameParts.push(part)
    }
  }
  result.name = nameParts.join(' ').trim()
  return result
}

function parseImport() {
  if (!importText.value.trim()) {
    toast('请粘贴需求列表', 'error')
    return
  }
  const lines = importText.value.trim().split('\n').filter(l => l.trim())
  let parsed = 0
  for (const line of lines) {
    if (/^(工作项|负责人|所属迭代|开始时间|结束时间|操作|#?\s*$)/.test(line.trim())) continue
    if (line.trim().length < 3) continue
    const req = parseRequirementLine(line)
    if (req.name || req.id) {
      requirements.value.push(req)
      parsed++
    }
  }
  if (parsed > 0) {
    toast(`成功导入 ${parsed} 个需求`, 'success')
    importText.value = ''
    if (selectedIdx.value == null) selectedIdx.value = 0
  } else {
    toast('未能解析到任何需求，请检查格式', 'error')
  }
}

function addEmptyRow() {
  requirements.value.push({
    id: '', name: '新需求', startDate: '', endDate: '', owner: '',
    description: '', files: [], status: 'pending', testCases: [],
  })
  selectedIdx.value = requirements.value.length - 1
}

// --- Requirements ---
const requirements = ref([])
const selectedIdx = ref(null)

const selectedReq = computed(() => {
  if (selectedIdx.value == null || selectedIdx.value >= requirements.value.length) return null
  return requirements.value[selectedIdx.value]
})

function removeRequirement(idx) {
  requirements.value.splice(idx, 1)
  if (selectedIdx.value === idx) {
    selectedIdx.value = requirements.value.length > 0 ? Math.min(idx, requirements.value.length - 1) : null
  } else if (selectedIdx.value > idx) {
    selectedIdx.value--
  }
}

const completedCount = computed(() => requirements.value.filter(r => r.status === 'done').length)

// --- Generate ---
const batchGenerating = ref(false)
const progressDone = ref(0)

async function generateSingle(idx) {
  const req = requirements.value[idx]
  if (!req || req.status === 'done' || req.status === 'generating') return

  req.status = 'generating'
  try {
    const fd = new FormData()
    fd.append('requirement_name', req.name)
    fd.append('description', req.description || '')
    fd.append('requirement_id', req.id)
    fd.append('test_type', '全面覆盖')
    for (const file of req.files) {
      fd.append('files', file)
    }
    const res = await fetch('/api/generate', { method: 'POST', body: fd })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || '生成失败')
    }
    const data = await res.json()
    req.testCases = data.test_cases || []
    req.status = 'done'
    toast(`${req.name}: 已生成 ${req.testCases.length} 条用例`, 'success')
  } catch (e) {
    req.status = 'pending'
    toast(`${req.name} 生成失败: ${e.message}`, 'error')
  }
}

async function batchGenerate() {
  const pending = requirements.value.filter(r => r.status !== 'done')
  if (pending.length === 0) {
    toast('所有需求已生成', 'error')
    return
  }
  batchGenerating.value = true
  progressDone.value = requirements.value.filter(r => r.status === 'done').length

  for (const req of pending) {
    req.status = 'generating'
    try {
      const fd = new FormData()
      fd.append('requirement_name', req.name)
      fd.append('description', req.description || '')
      fd.append('requirement_id', req.id)
      fd.append('test_type', '全面覆盖')
      for (const file of req.files) {
        fd.append('files', file)
      }
      const res = await fetch('/api/generate', { method: 'POST', body: fd })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || '生成失败')
      }
      const data = await res.json()
      req.testCases = data.test_cases || []
      req.status = 'done'
    } catch (e) {
      req.status = 'pending'
      toast(`${req.name} 生成失败: ${e.message}`, 'error')
    }
    progressDone.value++
  }

  batchGenerating.value = false
  if (completedCount.value === requirements.value.length) {
    toast(`全部 ${requirements.value.length} 个需求已生成`, 'success')
  }
}

// --- Export ---
const batchExporting = ref(false)

async function exportBatch() {
  const allCases = []
  for (const req of requirements.value) {
    if (req.testCases?.length) {
      allCases.push({ requirement_name: req.name, test_cases: req.testCases })
    }
  }
  if (allCases.length === 0) {
    toast('没有可导出的用例', 'error')
    return
  }
  batchExporting.value = true
  try {
    const res = await fetch('/api/export-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan_name: planName.value || '测试计划', requirements: allCases }),
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
    toast('已导出全部测试用例', 'success')
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    batchExporting.value = false
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 250ms ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
