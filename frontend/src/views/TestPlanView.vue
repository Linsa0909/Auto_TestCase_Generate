<template>
  <div class="flex flex-col h-full">
    <!-- Top Bar -->
    <div class="flex items-center justify-between px-5 py-3 border-b border-zinc-200">
      <div class="flex items-center gap-5">
        <button @click="goBack" class="w-7 h-7 flex items-center justify-center rounded-md text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors">
          <ArrowLeft class="w-4 h-4" :stroke-width="2" />
        </button>
        <input
          v-model="productName"
          placeholder="产品名称 *"
          class="text-base font-semibold tracking-tight text-zinc-900 bg-transparent border-0 border-b border-transparent pb-0 focus:border-zinc-400 focus:outline-none transition-colors placeholder-zinc-400 w-36"
        />
        <span class="text-zinc-300">/</span>
        <input
          v-model="iterationName"
          placeholder="迭代名称 *"
          class="text-base font-semibold tracking-tight text-zinc-900 bg-transparent border-0 border-b border-transparent pb-0 focus:border-zinc-400 focus:outline-none transition-colors placeholder-zinc-400 w-36"
        />
        <div class="flex items-center gap-3 text-sm">
          <span class="text-zinc-500"><span class="text-zinc-900 font-semibold tabular-nums">{{ requirements.length }}</span> 需求</span>
          <span class="text-zinc-300">·</span>
          <span class="text-zinc-500"><span :class="completedCount === requirements.length && requirements.length > 0 ? 'text-zinc-900' : 'text-zinc-700'" class="font-semibold tabular-nums">{{ completedCount }}</span> 完成</span>
        </div>
        <svg v-if="requirements.length > 0" class="w-5 h-5" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="8" fill="none" stroke="#e4e4e7" stroke-width="2" />
          <circle cx="10" cy="10" r="8" fill="none" :stroke="completedCount === requirements.length ? '#22c55e' : '#818cf8'" stroke-width="2" stroke-linecap="round"
            :stroke-dasharray="2 * Math.PI * 8" :stroke-dashoffset="2 * Math.PI * 8 * (1 - completedCount / requirements.length)" transform="rotate(-90 10 10)" class="transition-all duration-500" />
        </svg>
      </div>
      <div class="flex items-center gap-2">
        <button @click="savePlan" :disabled="saving || !productName.trim() || !iterationName.trim()"
          class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-zinc-900 text-white hover:bg-zinc-800 transition-all active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed">
          <Save class="w-3.5 h-3.5" :stroke-width="2" />
          {{ saving ? '保存中...' : '保存' }}
        </button>
        <button v-if="completedCount > 0" @click="exportBatch" :disabled="batchExporting"
          class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border border-zinc-300 text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 transition-all active:scale-[0.98]">
          <Download class="w-4 h-4" :stroke-width="2" />
          {{ batchExporting ? '导出中...' : '导出全部' }}
        </button>
        <button v-if="completedCount > 0" @click="pushToDevOps" :disabled="pushingToDevOps"
          class="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium border border-indigo-400 text-indigo-600 hover:border-indigo-500 hover:text-indigo-700 transition-all active:scale-[0.98]">
          <Upload class="w-4 h-4" :stroke-width="2" />
          {{ pushingToDevOps ? pushProgress.message : '推送 DevOps' }}
        </button>
      </div>
    </div>

    <!-- Import Section -->
    <div class="border-b border-zinc-200">
      <button @click="importExpanded = !importExpanded"
        class="w-full flex items-center justify-between px-5 py-2.5 text-sm text-zinc-500 hover:text-zinc-700 transition-colors">
        <span class="flex items-center gap-2">
          <ChevronDown :class="['w-3.5 h-3.5 transition-transform', importExpanded ? '' : '-rotate-90']" :stroke-width="2.5" />
          <span class="font-medium text-zinc-700">导入需求</span>
          <span v-if="requirements.length > 0 && !importExpanded" class="text-zinc-400">（已导入 {{ requirements.length }} 个）</span>
        </span>
        <span class="text-xs text-zinc-400">以 #编号 分隔每条需求</span>
      </button>
      <div v-if="importExpanded" class="px-5 pb-4">
        <div class="flex gap-3">
          <textarea v-model="importText" rows="5"
            placeholder="粘贴需求列表，每条以 #编号 开头：&#10;&#10;#194968&#10;【0304】组件视图新增服务分组功能&#10;王海波  backlog  2026-05-09  2026-05-30  进行中&#10;&#10;#194739&#10;【0304】操作输出参数支持自由绑定&#10;王沁雪  sprint75  2026-05-09  2026-05-13  测试中"
            class="flex-1 rounded-lg border border-zinc-300 bg-white px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none resize-none leading-relaxed transition-colors font-mono"></textarea>
          <div class="flex flex-col gap-2">
            <button @click="parseImport"
              class="px-5 py-3 rounded-lg text-sm font-medium bg-zinc-900 text-white hover:bg-zinc-800 transition-all active:scale-[0.98] whitespace-nowrap">
              解析导入
            </button>
            <button @click="addEmptyRow"
              class="px-5 py-3 rounded-lg text-sm font-medium text-zinc-600 border border-zinc-300 hover:border-zinc-400 hover:text-zinc-900 transition-colors whitespace-nowrap">
              手动添加
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content: Two Columns -->
    <div class="flex flex-1 min-h-0 overflow-hidden">
      <!-- Left: Requirement Cards -->
      <div class="w-[380px] shrink-0 border-r border-zinc-200 flex flex-col overflow-hidden">
        <div class="flex-1 overflow-y-auto">
          <div v-for="(req, idx) in requirements" :key="idx" @click="selectedIdx = idx"
            :class="['px-4 py-2.5 border-b border-zinc-200/60 cursor-pointer transition-all relative group', selectedIdx === idx ? 'bg-zinc-100' : 'hover:bg-zinc-50']">
            <div v-if="selectedIdx === idx" class="absolute left-0 top-2 bottom-2 w-[2.5px] rounded-full" :class="statusAccentClass(req)" />
            <div class="flex items-start gap-2">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5 mb-0.5 flex-wrap">
                  <span class="text-xs text-zinc-500 font-mono shrink-0">{{ req.id || '(新)' }}</span>
                  <span v-if="req.group" class="text-[10px] px-1.5 py-[0.5px] rounded bg-indigo-100 text-indigo-600 font-medium shrink-0">{{ req.group }}</span>
                  <span v-if="req.workStatus" :class="workStatusClass(req.workStatus)" class="text-[10px] px-1.5 py-[0.5px] rounded-full font-medium shrink-0">{{ req.workStatus }}</span>
                  <span v-if="req.status === 'done' && req.testCases?.length" class="text-[10px] px-1.5 py-[0.5px] rounded bg-zinc-900 text-white font-semibold shrink-0">{{ req.testCases.length }}条</span>
                  <span v-if="req.testType && req.testType !== '全面覆盖'" class="text-[10px] px-1.5 py-[0.5px] rounded bg-zinc-200 text-zinc-600 font-medium shrink-0">{{ req.testType }}</span>
                </div>
                <div class="text-sm text-zinc-900 font-medium truncate leading-snug">{{ req.name }}</div>
                <div class="flex items-center gap-2 mt-0.5 text-xs text-zinc-400">
                  <span v-if="req.owner" class="text-zinc-500">{{ req.owner }}</span>
                  <span v-if="req.owner && req.startDate">·</span>
                  <span v-if="req.startDate" class="tabular-nums">{{ req.startDate.slice(5) }}~{{ req.endDate?.slice(5) }}</span>
                </div>
              </div>
              <div class="flex items-center gap-1 pt-0.5">
                <span v-if="req.status === 'pending'" class="w-2 h-2 rounded-full shrink-0" :class="workStatusDotClass(req.workStatus)" />
                <span v-else-if="req.status === 'generating'" class="w-2 h-2 rounded-full bg-amber-500 animate-pulse shrink-0" />
                <span v-else class="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                <button @click.stop="removeRequirement(idx)" class="w-5 h-5 flex items-center justify-center rounded text-zinc-400 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100">
                  <X class="w-3 h-3" :stroke-width="2.5" />
                </button>
              </div>
            </div>
          </div>
          <div v-if="requirements.length === 0" class="micro-dots flex flex-col items-center justify-center py-24">
            <div class="bg-zinc-100 rounded-xl p-6 flex flex-col items-center gap-3 border border-zinc-200">
              <ClipboardList class="w-6 h-6 text-zinc-400" :stroke-width="1.2" />
              <p class="text-sm text-zinc-500">粘贴需求列表开始</p>
            </div>
          </div>
        </div>
        <div v-if="requirements.length > 0" class="p-4 border-t border-zinc-200">
          <div class="relative">
            <div class="absolute -inset-5 glow-indigo pointer-events-none rounded-xl" />
            <button @click="batchGenerate" :disabled="batchGenerating"
              class="relative w-full py-2.5 rounded-lg bg-zinc-900 text-white text-sm font-medium hover:bg-zinc-800 transition-all active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
              <div v-if="batchGenerating" class="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              <Sparkles v-else class="w-3.5 h-3.5" :stroke-width="2" />
              {{ batchGenerating ? `生成中 ${progressDone}/${batchTotal}` : '一键生成全部用例' }}
            </button>
          </div>
          <div v-if="batchGenerating" class="h-[3px] bg-zinc-200 rounded-full overflow-hidden mt-3">
            <div class="h-full bg-zinc-900 rounded-full transition-all duration-500 ease-out" :style="{ width: (batchTotal ? progressDone / batchTotal * 100 : 0) + '%' }" />
          </div>
        </div>
      </div>

      <!-- Right: Detail Panel -->
      <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
        <div v-if="selectedReq == null" class="flex-1 micro-dots flex items-center justify-center">
          <div class="bg-zinc-100 rounded-xl p-6 flex flex-col items-center gap-3 border border-zinc-200">
            <FileText class="w-6 h-6 text-zinc-400" :stroke-width="1.2" />
            <p class="text-sm text-zinc-500">选择左侧需求查看详情</p>
          </div>
        </div>
        <template v-else>
          <div class="flex-1 overflow-y-auto px-8 py-6">
            <div class="max-w-[600px]">
              <div class="mb-6">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs text-zinc-500 font-mono">{{ selectedReq.id || '新建' }}</span>
                  <span v-if="selectedReq.workStatus" :class="workStatusClass(selectedReq.workStatus)" class="text-xs px-2.5 py-[2px] rounded-full font-medium">{{ selectedReq.workStatus }}</span>
                </div>
                <div class="mb-2">
                  <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-1">需求名称</label>
                  <input v-model="selectedReq.name" placeholder="输入需求名称"
                    class="w-full rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none transition-colors font-semibold" />
                </div>
                <div class="grid grid-cols-2 gap-3 mb-2">
                  <div>
                    <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-1">用例分组</label>
                    <input v-model="selectedReq.group" placeholder="例如：0304"
                      class="w-full rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none transition-colors" />
                  </div>
                  <div>
                    <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-1">需求编号</label>
                    <input v-model="selectedReq.id" placeholder="例如：#194968"
                      class="w-full rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none transition-colors font-mono" />
                  </div>
                </div>
                <div class="flex items-center gap-3 text-xs text-zinc-500">
                  <span v-if="selectedReq.owner" class="text-zinc-600">{{ selectedReq.owner }}</span>
                  <span v-if="selectedReq.startDate" class="text-zinc-400">{{ selectedReq.startDate }} ~ {{ selectedReq.endDate }}</span>
                  <span v-if="selectedReq.status === 'pending'" class="px-2 py-0.5 rounded bg-zinc-200 text-zinc-600 font-medium">待生成</span>
                  <span v-else-if="selectedReq.status === 'generating'" class="px-2 py-0.5 rounded bg-amber-100 text-amber-600 font-medium">生成中</span>
                  <span v-else class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-600 font-medium">已完成</span>
                </div>
              </div>

              <!-- Inline stats -->
              <div v-if="selectedReq.testCases?.length > 0" class="flex items-center gap-3 mb-5 p-3 rounded-lg bg-zinc-50 border border-zinc-200">
                <div class="flex items-center gap-1.5"><div class="w-2 h-2 rounded-full bg-emerald-500" /><span class="text-xs text-zinc-500">已生成</span><span class="text-sm text-zinc-900 font-semibold tabular-nums">{{ selectedReq.testCases.length }}</span><span class="text-xs text-zinc-400">条</span></div>
                <div class="h-3 w-px bg-zinc-200" />
                <div class="flex items-center gap-1.5"><span class="text-xs text-zinc-500">冒烟</span><span class="text-sm text-zinc-900 font-semibold tabular-nums">{{ selectedReq.testCases.filter(t => t.raw_type === '冒烟').length }}</span></div>
                <div class="flex items-center gap-1.5"><span class="text-xs text-zinc-500">功能</span><span class="text-sm text-zinc-900 font-semibold tabular-nums">{{ selectedReq.testCases.filter(t => t.raw_type === '功能').length }}</span></div>
                <div class="flex items-center gap-1.5"><span class="text-xs text-zinc-500">边界</span><span class="text-sm text-zinc-900 font-semibold tabular-nums">{{ selectedReq.testCases.filter(t => t.raw_type === '边界').length }}</span></div>
                <div class="flex items-center gap-1.5"><span class="text-xs text-zinc-500">异常</span><span class="text-sm text-zinc-900 font-semibold tabular-nums">{{ selectedReq.testCases.filter(t => t.raw_type === '异常').length }}</span></div>
              </div>

              <!-- Test Type Selector -->
              <div class="mb-5">
                <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">用例类型</label>
                <div class="flex items-center gap-2">
                  <button
                    v-for="opt in testTypeOptions" :key="opt.value"
                    @click="selectedReq.testType = opt.value"
                    :class="[
                      'px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all',
                      selectedReq.testType === opt.value
                        ? 'bg-zinc-900 text-white'
                        : 'border border-zinc-300 text-zinc-500 hover:border-zinc-400 hover:text-zinc-700'
                    ]"
                  >{{ opt.label }}</button>
                </div>
              </div>

              <div class="mb-5">
                <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">需求描述</label>
                <textarea v-model="selectedReq.description" rows="4" placeholder="添加需求描述..."
                  class="w-full rounded-lg border border-zinc-300 bg-white px-4 py-3 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none resize-none leading-relaxed transition-colors"></textarea>
              </div>
              <div class="mb-5">
                <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">原型文件</label>
                <UploadZone :files="selectedReq.files" @update:files="selectedReq.files = $event" />
              </div>
              <div v-if="selectedReq.testCases?.length > 0" class="mb-5">
                <label class="block text-xs text-zinc-500 uppercase tracking-wider font-medium mb-2">用例列表 ({{ selectedReq.testCases.length }} 条)</label>
                <div class="flex flex-col gap-2">
                  <div v-for="(tc, ti) in selectedReq.testCases" :key="ti"
                    class="rounded-lg border border-zinc-200 bg-zinc-50 overflow-hidden">
                    <div @click="toggleCaseExpand(ti)"
                      class="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-zinc-100 transition-colors">
                      <ChevronDown :class="['w-3 h-3 text-zinc-400 transition-transform shrink-0', expandedCases.has(ti) ? '' : '-rotate-90']" :stroke-width="2.5" />
                      <span class="text-xs text-zinc-400 tabular-nums shrink-0">{{ ti + 1 }}</span>
                      <span class="text-sm text-zinc-700 flex-1 truncate">{{ tc.title }}</span>
                      <span v-if="tc.priority" class="text-[10px] px-1.5 py-[0.5px] rounded font-medium shrink-0"
                        :class="tc.priority === 'L0' ? 'bg-zinc-900 text-white' : tc.priority === 'L1' ? 'bg-zinc-200 text-zinc-600' : 'bg-zinc-100 text-zinc-500'">{{ tc.priority }}</span>
                      <span :class="typePillClass(tc.raw_type)" class="text-[10px] px-1.5 py-[0.5px] rounded font-medium whitespace-nowrap shrink-0">{{ tc.raw_type }}</span>
                    </div>
                    <div v-if="expandedCases.has(ti)" class="border-t border-zinc-200 px-3 py-2 bg-white">
                      <div v-if="tc.precondition" class="text-xs text-zinc-400 mb-2">
                        <span class="text-zinc-500">前置条件：</span>{{ tc.precondition }}
                      </div>
                      <div v-for="(step, si) in tc.steps" :key="si" class="flex gap-2 py-1.5" :class="si > 0 ? 'border-t border-zinc-100' : ''">
                        <span class="text-xs text-zinc-400 w-4 tabular-nums shrink-0 pt-0.5">{{ si + 1 }}</span>
                        <div class="flex-1 min-w-0">
                          <div class="text-sm text-zinc-700">{{ step.step }}</div>
                          <div class="text-xs text-zinc-400 mt-0.5">预期：{{ step.expected }}</div>
                        </div>
                      </div>
                      <div v-if="!tc.steps?.length" class="text-xs text-zinc-400 py-1">无步骤信息</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="px-8 py-3 border-t border-zinc-200">
            <div class="max-w-[600px] flex items-center gap-3">
              <div class="relative flex-1 flex flex-col gap-2">
                <div class="relative">
                  <div class="absolute -inset-4 glow-indigo pointer-events-none rounded-xl" />
                  <button @click="generateSingle(selectedIdx)" :disabled="selectedReq.status === 'generating'"
                    class="relative w-full py-2.5 rounded-lg text-sm font-medium bg-zinc-900 text-white hover:bg-zinc-800 transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                    <div v-if="selectedReq.status === 'generating'" class="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    <Sparkles v-else class="w-4 h-4" :stroke-width="2" />
                    {{ selectedReq.status === 'generating' ? '生成中...' : selectedReq.status === 'done' ? '重新生成' : '生成用例' }}
                  </button>
                </div>
                <div v-if="selectedReq.status === 'generating'" class="h-[3px] bg-zinc-200 rounded-full overflow-hidden">
                  <div class="h-full w-1/2 bg-zinc-900 rounded-full animate-pulse" />
                </div>
              </div>
              <button @click="removeRequirement(selectedIdx)" class="px-4 py-2.5 rounded-lg text-sm font-medium text-zinc-500 border border-zinc-300 hover:border-red-300 hover:text-red-500 hover:bg-red-50 transition-colors">删除</button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <Transition name="fade">
      <div v-if="batchGenerating" class="fixed inset-0 bg-white/80 backdrop-blur-md z-30 flex flex-col items-center justify-center gap-5">
        <div class="spinner" />
        <div class="text-center">
          <p class="text-base font-medium text-zinc-900">正在批量生成测试用例</p>
          <p class="text-sm text-zinc-500 mt-1">{{ progressDone }} / {{ batchTotal }} 个需求已完成</p>
        </div>
        <button @click="cancelBatchGenerate" :disabled="batchCancelled"
          class="px-6 py-2.5 rounded-lg text-sm font-medium border border-zinc-300 text-zinc-600 hover:border-red-300 hover:text-red-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
          {{ batchCancelled ? '正在取消...' : '取消生成' }}
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, inject, onMounted, watch } from 'vue'
import { Sparkles, Download, X, ClipboardList, FileText, ChevronDown, ArrowLeft, Save, Upload } from 'lucide-vue-next'
import UploadZone from '../components/input/UploadZone.vue'

const props = defineProps({ planId: { type: String, required: true } })
const emit = defineEmits(['back'])
const toast = inject('toast')

const productName = ref('')
const iterationName = ref('')
const importText = ref('')
const importExpanded = ref(true)
const saving = ref(false)
const expandedCases = ref(new Set())

function toggleCaseExpand(idx) {
  const s = new Set(expandedCases.value)
  if (s.has(idx)) s.delete(idx); else s.add(idx)
  expandedCases.value = s
}

const testTypeOptions = [
  { value: '全面覆盖', label: '全面覆盖' },
  { value: '仅冒烟', label: '仅冒烟' },
  { value: '功能测试', label: '功能测试' },
  { value: '边界异常', label: '边界异常' },
]

const requirements = ref([])
const selectedIdx = ref(null)
const selectedReq = computed(() => {
  if (selectedIdx.value == null || selectedIdx.value >= requirements.value.length) return null
  return requirements.value[selectedIdx.value]
})

// --- Status helpers ---
const WORK_STATUS_COLORS = {
  '进行中': { bg: 'bg-blue-100', text: 'text-blue-600', dot: 'bg-blue-500' },
  '测试中': { bg: 'bg-violet-100', text: 'text-violet-600', dot: 'bg-violet-500' },
  '未开始': { bg: 'bg-zinc-200', text: 'text-zinc-500', dot: 'bg-zinc-400' },
  '验收中': { bg: 'bg-emerald-100', text: 'text-emerald-600', dot: 'bg-emerald-500' },
  '已完成': { bg: 'bg-emerald-100', text: 'text-emerald-600', dot: 'bg-emerald-500' },
  'backlog': { bg: 'bg-zinc-200', text: 'text-zinc-500', dot: 'bg-zinc-400' },
}
function workStatusClass(s) { const c = WORK_STATUS_COLORS[s]; return c ? `${c.bg} ${c.text}` : 'bg-zinc-200 text-zinc-500' }
function workStatusDotClass(s) { const c = WORK_STATUS_COLORS[s]; return c ? c.dot : 'bg-zinc-400' }
function statusAccentClass(req) {
  if (req.status === 'done') return 'bg-emerald-500'
  if (req.status === 'generating') return 'bg-amber-500'
  const c = WORK_STATUS_COLORS[req.workStatus]; return c ? c.dot : 'bg-zinc-400'
}
function typePillClass(t) {
  return { '冒烟': 'bg-indigo-100 text-indigo-600', '功能': 'bg-cyan-100 text-cyan-600', '边界': 'bg-amber-100 text-amber-600', '异常': 'bg-rose-100 text-rose-600' }[t] || 'bg-zinc-200 text-zinc-600'
}

// --- Load plan from backend ---
async function loadPlan() {
  try {
    const res = await fetch(`/api/plans/${props.planId}`)
    if (!res.ok) throw new Error('加载失败')
    const data = await res.json()
    productName.value = data.product_name || ''
    iterationName.value = data.iteration_name || ''
    // Filter out corrupted entries (empty name / NaN)
    const cleanReqs = (data.requirements || []).filter(r => {
      const name = String(r.name || '').trim()
      return name && name !== 'nan' && name !== 'NaN' && name !== 'null' && name !== 'undefined'
    })
    requirements.value = cleanReqs.map(r => ({
      ...r,
      files: r.files || [],
      testCases: r.testCases || [],
      status: r.status || 'pending',
    }))
    if (requirements.value.length > 0 && selectedIdx.value == null) selectedIdx.value = 0
  } catch (e) {
    toast('加载计划失败: ' + e.message, 'error')
  }
}

// --- Save plan ---
async function savePlan() {
  if (!productName.value.trim() || !iterationName.value.trim()) {
    toast('请填写产品名称和迭代名称', 'error'); return
  }
  saving.value = true
  try {
    const res = await fetch(`/api/plans/${props.planId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productName.value.trim(),
        iteration_name: iterationName.value.trim(),
        requirements: requirements.value.map(r => ({ ...r })),
      }),
    })
    if (!res.ok) throw new Error('保存失败')
    toast('计划已保存', 'success')
  } catch (e) { toast(e.message, 'error') } finally { saving.value = false }
}

// --- Parser ---
function parseImport() {
  const raw = importText.value.trim()
  if (!raw) { toast('请粘贴需求列表', 'error'); return }
  const blocks = []
  const lines = raw.split('\n')
  let currentBlock = []
  for (const line of lines) {
    const trimmed = line.trim()
    if (/^#\d{6}\b/.test(trimmed)) {
      if (currentBlock.length > 0) blocks.push(currentBlock)
      currentBlock = [trimmed]
    } else if (trimmed.length > 0) {
      currentBlock.push(trimmed)
    }
  }
  if (currentBlock.length > 0) blocks.push(currentBlock)
  let parsed = 0
  for (const block of blocks) {
    const req = parseRequirementBlock(block)
    if (req.name && req.name !== 'nan' && req.name !== 'NaN') { requirements.value.push(req); parsed++ }
  }
  if (parsed > 0) {
    toast(`成功导入 ${parsed} 个需求`, 'success')
    if (selectedIdx.value == null) selectedIdx.value = 0
  } else { toast('未能解析到任何需求，请检查格式', 'error') }
}

function parseRequirementBlock(lines) {
  const result = { id: '', name: '', group: '', testType: '全面覆盖', startDate: '', endDate: '', owner: '', workStatus: '', description: '', files: [], status: 'pending', testCases: [] }

  // Line-by-line parsing to avoid name/owner merge
  let nameLine = ''
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    // Extract ID from #NNNNNN
    const idMatch = trimmed.match(/#(\d{6})/)
    if (idMatch) { result.id = '#' + idMatch[1]; continue }

    // Detect metadata line: contains dates, sprint, or status keywords
    const hasDate = /\d{4}-\d{2}-\d{2}/.test(trimmed)
    const hasSprint = /sprint\d+/i.test(trimmed)
    const hasStatus = /(进行中|测试中|未开始|验收中|已完成|backlog)/i.test(trimmed)

    if (hasDate || hasSprint || hasStatus) {
      // This is a metadata line — extract dates, status, owner
      const datePattern = /(\d{4}-\d{2}-\d{2})/g
      const dates = []; let m
      while ((m = datePattern.exec(trimmed)) !== null) dates.push(m[1])
      if (dates.length >= 1) result.startDate = dates[0]
      if (dates.length >= 2) result.endDate = dates[1]

      const statusMatch = trimmed.match(/(进行中|测试中|未开始|验收中|已完成|backlog)/i)
      if (statusMatch) result.workStatus = statusMatch[1]

      // Extract owner: remove dates, sprint, status, tabs/spaces, remaining standalone token
      let metaRemaining = trimmed
      metaRemaining = metaRemaining.replace(/\d{4}-\d{2}-\d{2}/g, '')
      metaRemaining = metaRemaining.replace(/sprint\d+/gi, '')
      metaRemaining = metaRemaining.replace(/(进行中|测试中|未开始|验收中|已完成|backlog)/gi, '')
      const metaParts = metaRemaining.split(/[\t]+|\s{2,}/).map(s => s.trim()).filter(Boolean)
      for (const part of metaParts) {
        if (/^[\u4e00-\u9fa5]{2,4}$/.test(part) && !result.owner) result.owner = part
      }
    } else if (!nameLine) {
      // This is the name line (first non-ID, non-metadata line)
      // Extract 【xxx】 as group from the name line
      let name = trimmed
      const groupMatch = name.match(/【([^】]+)】/)
      if (groupMatch) {
        result.group = groupMatch[1]
        name = name.replace(/【[^】]+】/, '').trim()
      }
      nameLine = name
    }
  }

  result.name = nameLine.trim()
  return result
}

function addEmptyRow() {
  requirements.value.push({ id: '', name: '新需求', group: '', testType: '全面覆盖', startDate: '', endDate: '', owner: '', workStatus: '', description: '', files: [], status: 'pending', testCases: [] })
  selectedIdx.value = requirements.value.length - 1
}

function removeRequirement(idx) {
  requirements.value.splice(idx, 1)
  if (selectedIdx.value === idx) selectedIdx.value = requirements.value.length > 0 ? Math.min(idx, requirements.value.length - 1) : null
  else if (selectedIdx.value > idx) selectedIdx.value--
}

const completedCount = computed(() => requirements.value.filter(r => r.status === 'done').length)
const batchGenerating = ref(false)
const batchCancelled = ref(false)
const batchTotal = ref(0)
const pushingToDevOps = ref(false)
const pushProgress = ref({ step: 0, total: 8, message: '', done: false })
const progressDone = ref(0)
const abortController = ref(null)

async function generateSingle(idx) {
  const req = requirements.value[idx]
  if (!req || req.status === 'generating') return
  req.status = 'generating'
  try {
    const fd = new FormData()
    fd.append('requirement_name', req.name); fd.append('description', req.description || '')
    fd.append('requirement_id', req.id); fd.append('test_type', req.testType || '全面覆盖')
    fd.append('group', req.group || '')
    for (const file of req.files) {
      if (file instanceof File) fd.append('files', file)
    }
    const res = await fetch('/api/generate', { method: 'POST', body: fd })
    if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || '生成失败') }
    const data = await res.json()
    req.testCases = data.test_cases || []; req.status = 'done'
    toast(`${req.name}: 已生成 ${req.testCases.length} 条用例`, 'success')
    autoSave()
  } catch (e) { req.status = 'pending'; toast(`${req.name} 生成失败: ${e.message}`, 'error') }
}

async function autoSave() {
  if (!productName.value.trim() || !iterationName.value.trim()) return
  try {
    await fetch(`/api/plans/${props.planId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productName.value.trim(),
        iteration_name: iterationName.value.trim(),
        requirements: requirements.value.map(r => ({ ...r })),
      }),
    })
  } catch {}
}

async function goBack() {
  await autoSave()
  emit('back')
}

async function pushToDevOps() {
  if (pushingToDevOps.value) return
  pushingToDevOps.value = true
  pushProgress.value = { step: 0, total: 8, message: '开始推送...', done: false }
  try {
    // Start push (non-blocking, we poll progress)
    const pushRes = await fetch(`/api/push-to-devops/${props.planId}`, { method: 'POST' })
    if (!pushRes.ok) {
      const err = await pushRes.json()
      throw new Error(err.detail || '推送失败')
    }
    pushProgress.value = { step: 8, total: 8, message: '推送完成', done: true }
    toast('已成功推送到 DevOps 平台', 'success')
  } catch (e) {
    pushProgress.value = { step: 0, total: 8, message: `推送失败: ${e.message}`, done: true }
    toast(e.message, 'error')
  } finally {
    pushingToDevOps.value = false
  }
}

async function batchGenerate() {
  const pending = requirements.value.filter(r => r.status !== 'generating')
  if (pending.length === 0) { toast('所有需求正在生成中', 'error'); return }
  batchGenerating.value = true
  batchCancelled.value = false
  batchTotal.value = pending.length
  // Save snapshot for cancel rollback
  const snapshot = pending.map(r => ({ ref: r, prevStatus: r.status, prevCases: [...(r.testCases || [])] }))
  progressDone.value = 0
  for (const req of pending) {
    if (batchCancelled.value) break
    req.status = 'generating'
    try {
      const fd = new FormData()
      fd.append('requirement_name', req.name); fd.append('description', req.description || '')
      fd.append('requirement_id', req.id); fd.append('test_type', req.testType || '全面覆盖')
      fd.append('group', req.group || '')
      for (const file of req.files) {
        if (file instanceof File) fd.append('files', file)
      }
      abortController.value = new AbortController()
      const res = await fetch('/api/generate', { method: 'POST', body: fd, signal: abortController.value.signal })
      if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || '生成失败') }
      const data = await res.json()
      req.testCases = data.test_cases || []; req.status = 'done'
    } catch (e) {
      if (e.name === 'AbortError') { req.status = 'generating'; break }
      req.status = 'pending'; toast(`${req.name} 生成失败: ${e.message}`, 'error')
    }
    progressDone.value++
  }
  // If cancelled, rollback un-finished items
  if (batchCancelled.value) {
    for (const s of snapshot) {
      if (s.ref.status === 'generating') {
        s.ref.status = s.prevStatus
        s.ref.testCases = s.prevCases
      }
    }
    toast('已取消生成', 'error')
  }
  batchGenerating.value = false
  abortController.value = null
  autoSave()
  if (!batchCancelled.value && completedCount.value === requirements.value.length) {
    toast(`全部 ${requirements.value.length} 个需求已生成`, 'success')
  }
}

function cancelBatchGenerate() {
  batchCancelled.value = true
  if (abortController.value) {
    abortController.value.abort()
  }
}

const batchExporting = ref(false)
async function exportBatch() {
  const allCases = []
  for (const req of requirements.value) {
    if (req.testCases?.length) {
      // Inject group from requirement into each test case if missing
      const casesWithGroup = req.testCases.map(tc => ({
        ...tc,
        group: tc.group || req.group || '',
      }))
      allCases.push({ requirement_name: req.name, test_cases: casesWithGroup })
    }
  }
  if (allCases.length === 0) { toast('没有可导出的用例', 'error'); return }
  batchExporting.value = true
  try {
    const res = await fetch('/api/export-batch', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plan_name: iterationName.value || '测试计划', requirements: allCases }),
    })
    if (!res.ok) { const err = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(err.detail || '导出失败') }
    const data = await res.json()
    const a = document.createElement('a'); a.href = data.download_url; a.download = ''
    document.body.appendChild(a); a.click(); document.body.removeChild(a)
    toast('已导出全部测试用例', 'success')
  } catch (e) { toast(e.message, 'error') } finally { batchExporting.value = false }
}

onMounted(() => { loadPlan() })
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 250ms ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
