<template>
  <div class="overflow-x-auto">
    <table class="w-full text-left border-collapse">
      <thead>
        <tr class="text-[10px] text-gray-500 border-b border-gray-200">
          <th class="py-2.5 font-medium w-20">分组</th>
          <th class="py-2.5 font-medium">用例标题</th>
          <th class="py-2.5 font-medium w-14">程度</th>
          <th class="py-2.5 font-medium w-16">类型</th>
          <th class="py-2.5 font-medium">步骤描述</th>
          <th class="py-2.5 font-medium w-48">预期结果</th>
          <th v-if="editable" class="py-2.5 font-medium w-20 text-center">操作</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(tc, tcIdx) in cases" :key="tcIdx">
          <tr
            v-for="(step, sIdx) in tc.steps"
            :key="tcIdx + '-' + sIdx"
            class="border-b border-gray-100/80 group/row"
          >
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 text-gray-500 text-[12px] align-top">
              {{ tc.group || '-' }}
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 pr-3 align-top">
              <input
                v-if="editable"
                v-model="tc.title"
                class="w-full text-[13px] font-medium text-gray-900 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-gray-900 outline-none transition-all py-0.5"
              />
              <span v-else class="text-[13px] font-medium text-gray-900">{{ tc.title }}</span>
              <div v-if="tc.precondition" class="text-[11px] text-gray-400 mt-1 leading-relaxed">
                前置: {{ tc.precondition }}
              </div>
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 align-top">
              <div
                class="w-[6px] h-[6px] rounded-full"
                :class="{
                  'bg-gray-900': tc.priority === 'L0',
                  'bg-gray-400': tc.priority === 'L1',
                  'bg-gray-200': tc.priority === 'L2',
                }"
              />
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 align-top">
              <StatusBadge :type="tc.priority === 'L0' ? 'smoke' : tc.priority === 'L1' ? 'func' : 'edge'" />
            </td>
            <td class="py-2.5 pr-3 align-top">
              <div class="flex items-start gap-1.5">
                <span class="text-[10px] text-gray-300 mt-[3px] shrink-0 select-none tabular-nums">{{ sIdx + 1 }}</span>
                <textarea
                  v-if="editable"
                  v-model="step.step"
                  v-auto-resize
                  class="flex-1 text-[12px] text-gray-700 bg-transparent border-b border-transparent hover:border-gray-200 focus:border-gray-900 focus:bg-gray-50/30 outline-none transition-all resize-none overflow-hidden py-0.5"
                />
                <span v-else class="text-[12px] text-gray-700 leading-relaxed">{{ step.step }}</span>
              </div>
            </td>
            <td class="py-2.5 pr-3 align-top">
              <textarea
                v-if="editable"
                v-model="step.expected"
                v-auto-resize
                class="w-full text-[12px] text-gray-600 bg-transparent border-b border-transparent hover:border-gray-200 focus:border-gray-900 focus:bg-gray-50/30 outline-none transition-all resize-none overflow-hidden py-0.5"
              />
              <span v-else class="text-[12px] text-gray-600 leading-relaxed">{{ step.expected || '-' }}</span>
            </td>
            <td v-if="editable" class="py-2.5 align-top">
              <div class="flex items-center gap-0.5 opacity-0 group-hover/row:opacity-100 transition-opacity duration-150">
                <button
                  @click="addStep(tcIdx, sIdx)"
                  class="w-5 h-5 flex items-center justify-center rounded text-gray-300 hover:text-emerald-600 hover:bg-emerald-50 transition-colors active:scale-90"
                  title="在下方插入步骤"
                >
                  <Plus class="w-3 h-3" :stroke-width="2" />
                </button>
                <button
                  @click="removeStep(tcIdx, sIdx)"
                  :disabled="tc.steps.length <= 1"
                  class="w-5 h-5 flex items-center justify-center rounded text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors active:scale-90 disabled:opacity-20 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-gray-300"
                  title="删除此步骤"
                >
                  <Minus class="w-3 h-3" :stroke-width="2" />
                </button>
                <button
                  v-if="sIdx === 0"
                  @click="$emit('remove-case', tcIdx)"
                  class="w-5 h-5 flex items-center justify-center rounded text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors active:scale-90 ml-0.5"
                  title="删除整个用例"
                >
                  <Trash2 class="w-3 h-3" :stroke-width="2" />
                </button>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <!-- Empty state -->
    <div
      v-if="!cases || cases.length === 0"
      class="h-48 flex flex-col items-center justify-center gap-2"
    >
      <FileText class="w-5 h-5 text-gray-300" :stroke-width="1.5" />
      <p class="text-[12px] text-gray-400">等待解析原型以生成测试用例</p>
    </div>
  </div>
</template>

<script setup>
import { nextTick } from 'vue'
import { Plus, Minus, Trash2, FileText } from 'lucide-vue-next'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  cases: { type: Array, default: () => [] },
  editable: { type: Boolean, default: false },
})

defineEmits(['remove-case'])

function addStep(tcIdx, afterIdx) {
  const tc = props.cases[tcIdx]
  tc.steps.splice(afterIdx + 1, 0, { step: '', expected: '' })
}

function removeStep(tcIdx, sIdx) {
  const tc = props.cases[tcIdx]
  if (tc.steps.length <= 1) return
  tc.steps.splice(sIdx, 1)
}

const vAutoResize = {
  mounted(el) {
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  },
  updated(el) {
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  },
}
</script>
