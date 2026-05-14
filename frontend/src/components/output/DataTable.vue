<template>
  <div class="overflow-x-auto">
    <table class="w-full text-left border-collapse">
      <thead>
        <tr class="text-xs text-zinc-500 border-b border-zinc-200">
          <th class="py-3 font-medium w-24">分组</th>
          <th class="py-3 font-medium">用例标题</th>
          <th class="py-3 font-medium w-16">程度</th>
          <th class="py-3 font-medium w-20">类型</th>
          <th class="py-3 font-medium">步骤描述</th>
          <th class="py-3 font-medium w-52">预期结果</th>
          <th v-if="editable" class="py-3 font-medium w-20 text-center">操作</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(tc, tcIdx) in cases" :key="tcIdx">
          <tr v-for="(step, sIdx) in tc.steps" :key="tcIdx + '-' + sIdx" class="border-b border-zinc-200/60 group/row">
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 text-zinc-500 text-sm align-top">
              {{ tc.group || '-' }}
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 pr-4 align-top">
              <input v-if="editable" v-model="tc.title"
                class="w-full text-sm font-medium text-zinc-900 bg-transparent border-b border-transparent hover:border-zinc-400 focus:border-zinc-500 focus:bg-zinc-50 outline-none transition-all py-0.5" />
              <span v-else class="text-sm font-medium text-zinc-900">{{ tc.title }}</span>
              <div v-if="tc.precondition" class="text-xs text-zinc-400 mt-1 leading-relaxed">前置: {{ tc.precondition }}</div>
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 align-top">
              <div class="w-2 h-2 rounded-full" :class="{ 'bg-zinc-900': tc.priority === 'L0', 'bg-zinc-500': tc.priority === 'L1', 'bg-zinc-400': tc.priority === 'L2' }" />
            </td>
            <td v-if="sIdx === 0" :rowspan="tc.steps.length" class="py-3 align-top">
              <StatusBadge :type="tc.priority === 'L0' ? 'smoke' : tc.priority === 'L1' ? 'func' : 'edge'" />
            </td>
            <td class="py-2.5 pr-4 align-top">
              <div class="flex items-start gap-2">
                <span class="text-xs text-zinc-400 mt-[4px] shrink-0 select-none tabular-nums">{{ sIdx + 1 }}</span>
                <textarea v-if="editable" v-model="step.step" v-auto-resize
                  class="flex-1 text-sm text-zinc-700 bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-zinc-500 focus:bg-zinc-50 outline-none transition-all resize-none overflow-hidden py-0.5" />
                <span v-else class="text-sm text-zinc-700 leading-relaxed">{{ step.step }}</span>
              </div>
            </td>
            <td class="py-2.5 pr-4 align-top">
              <textarea v-if="editable" v-model="step.expected" v-auto-resize
                class="w-full text-sm text-zinc-600 bg-transparent border-b border-transparent hover:border-zinc-300 focus:border-zinc-500 focus:bg-zinc-50 outline-none transition-all resize-none overflow-hidden py-0.5" />
              <span v-else class="text-sm text-zinc-600 leading-relaxed">{{ step.expected || '-' }}</span>
            </td>
            <td v-if="editable" class="py-2.5 align-top">
              <div class="flex items-center gap-0.5 opacity-0 group-hover/row:opacity-100 transition-opacity duration-150">
                <button @click="addStep(tcIdx, sIdx)" class="w-6 h-6 flex items-center justify-center rounded text-zinc-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors active:scale-90" title="插入步骤">
                  <Plus class="w-3.5 h-3.5" :stroke-width="2" />
                </button>
                <button @click="removeStep(tcIdx, sIdx)" :disabled="tc.steps.length <= 1"
                  class="w-6 h-6 flex items-center justify-center rounded text-zinc-400 hover:text-red-500 hover:bg-red-50 transition-colors active:scale-90 disabled:opacity-20 disabled:cursor-not-allowed" title="删除步骤">
                  <Minus class="w-3.5 h-3.5" :stroke-width="2" />
                </button>
                <button v-if="sIdx === 0" @click="$emit('remove-case', tcIdx)"
                  class="w-6 h-6 flex items-center justify-center rounded text-zinc-400 hover:text-red-500 hover:bg-red-50 transition-colors active:scale-90 ml-0.5" title="删除用例">
                  <Trash2 class="w-3.5 h-3.5" :stroke-width="2" />
                </button>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <div v-if="!cases || cases.length === 0" class="h-56 micro-dots flex flex-col items-center justify-center gap-2 rounded-lg">
      <div class="bg-zinc-100 rounded-xl px-5 py-4 flex flex-col items-center gap-2">
        <FileText class="w-5 h-5 text-zinc-400" :stroke-width="1.5" />
        <p class="text-sm text-zinc-500">等待解析原型以生成测试用例</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Minus, Trash2, FileText } from 'lucide-vue-next'
import StatusBadge from './StatusBadge.vue'
const props = defineProps({ cases: { type: Array, default: () => [] }, editable: { type: Boolean, default: false } })
defineEmits(['remove-case'])
function addStep(tcIdx, afterIdx) { props.cases[tcIdx].steps.splice(afterIdx + 1, 0, { step: '', expected: '' }) }
function removeStep(tcIdx, sIdx) { const tc = props.cases[tcIdx]; if (tc.steps.length <= 1) return; tc.steps.splice(sIdx, 1) }
const vAutoResize = {
  mounted(el) { el.style.height = 'auto'; el.style.height = el.scrollHeight + 'px' },
  updated(el) { el.style.height = 'auto'; el.style.height = el.scrollHeight + 'px' },
}
</script>
