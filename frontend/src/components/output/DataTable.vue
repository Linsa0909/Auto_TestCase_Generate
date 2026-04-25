<template>
  <div class="overflow-x-auto">
    <table class="w-full text-left border-collapse">
      <thead>
        <tr class="text-[11px] text-gray-400 border-b border-gray-100">
          <th class="py-4 font-medium w-20">分组</th>
          <th class="py-4 font-medium">用例标题</th>
          <th class="py-4 font-medium w-16">程度</th>
          <th class="py-4 font-medium w-20">类型</th>
          <th class="py-4 font-medium">步骤描述</th>
          <th class="py-4 font-medium w-52">预期结果</th>
          <th v-if="editable" class="py-4 font-medium w-24 text-center">操作</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(tc, tcIdx) in cases" :key="tcIdx">
          <tr
            v-for="(step, sIdx) in tc.steps"
            :key="tcIdx + '-' + sIdx"
            class="border-b border-gray-50 hover:bg-gray-50/80 transition-colors"
          >
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-4 text-gray-400 text-sm align-top">
              {{ tc.group || '-' }}
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-4 pr-4 align-top">
              <input
                v-if="editable"
                v-model="tc.title"
                class="w-full text-sm font-medium bg-transparent border-b border-transparent hover:border-gray-300 focus:border-black outline-none transition-colors"
              />
              <span v-else class="text-sm font-medium">{{ tc.title }}</span>
              <div v-if="tc.precondition" class="text-xs text-gray-400 mt-1">
                前置: {{ tc.precondition }}
              </div>
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-4 align-top">
              <div
                class="w-2 h-2 rounded-full"
                :class="{
                  'bg-black': tc.priority === 'L0',
                  'bg-gray-400': tc.priority === 'L1',
                  'bg-gray-200': tc.priority === 'L2',
                }"
              />
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-4 align-top">
              <StatusBadge :type="tc.priority === 'L0' ? 'smoke' : tc.priority === 'L1' ? 'func' : 'edge'" />
            </td>
            <td class="py-4 pr-4 align-top">
              <span v-if="editable" class="text-gray-300 text-xs mr-1 select-none">{{ sIdx + 1 }}.</span>
              <textarea
                v-if="editable"
                v-model="step.step"
                v-auto-resize
                class="w-full text-sm text-gray-600 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-black outline-none transition-colors resize-none overflow-hidden"
              />
              <span v-else class="text-sm text-gray-600"><span class="text-gray-300 text-xs mr-1">{{ sIdx + 1 }}.</span>{{ step.step }}</span>
            </td>
            <td class="py-4 pr-4 align-top">
              <textarea
                v-if="editable"
                v-model="step.expected"
                v-auto-resize
                class="w-full text-sm text-gray-500 bg-transparent border-b border-transparent hover:border-gray-300 focus:border-black outline-none transition-colors resize-none overflow-hidden"
              />
              <span v-else class="text-sm text-gray-500">{{ step.expected || '-' }}</span>
            </td>
            <td v-if="editable" class="py-4 align-top">
              <div class="flex items-center gap-1">
                <button
                  @click="addStep(tcIdx, sIdx)"
                  class="w-6 h-6 flex items-center justify-center rounded-md text-gray-300 hover:text-black hover:bg-gray-100 transition-all"
                  title="在下方插入步骤"
                >
                  <Plus class="w-3.5 h-3.5" :stroke-width="2" />
                </button>
                <button
                  @click="removeStep(tcIdx, sIdx)"
                  :disabled="tc.steps.length <= 1"
                  class="w-6 h-6 flex items-center justify-center rounded-md text-gray-300 hover:text-red-500 hover:bg-red-50 transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                  title="删除此步骤"
                >
                  <Minus class="w-3.5 h-3.5" :stroke-width="2" />
                </button>
                <button
                  v-if="sIdx === 0"
                  @click="$emit('remove-case', tcIdx)"
                  class="w-6 h-6 flex items-center justify-center rounded-md text-gray-300 hover:text-red-500 hover:bg-red-50 transition-all ml-1"
                  title="删除整个用例"
                >
                  <Trash2 class="w-3.5 h-3.5" :stroke-width="2" />
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
      class="h-64 flex items-center justify-center text-gray-300 text-sm"
    >
      等待解析原型以生成测试用例...
    </div>
  </div>
</template>

<script setup>
import { nextTick } from 'vue'
import { Plus, Minus, Trash2 } from 'lucide-vue-next'
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
