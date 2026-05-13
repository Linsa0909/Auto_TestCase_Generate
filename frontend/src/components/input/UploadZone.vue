<template>
  <div>
    <div
      :class="[
        'border border-dashed rounded-lg p-6 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all duration-150 group',
        dragging ? 'border-zinc-400 bg-zinc-900/60' : 'border-zinc-800 hover:border-zinc-600 hover:bg-zinc-900/30',
      ]"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="handleDrop"
      @click="triggerInput"
    >
      <UploadCloud
        :class="['w-5 h-5 transition-all', dragging ? 'text-white' : 'text-zinc-500 group-hover:text-zinc-300']"
        :stroke-width="1.5"
      />
      <p class="text-sm text-zinc-400 text-center">{{ dragging ? '释放以上传' : '拖拽或点击上传原型文件' }}</p>
      <p class="text-xs text-zinc-600">支持 HTML, ZIP, PNG, JPG</p>
      <input ref="fileInput" type="file" multiple accept=".html,.zip,.png,.jpg,.jpeg" class="hidden" @change="handleSelect" />
    </div>

    <div v-if="files.length" class="mt-3 flex flex-col gap-1.5">
      <div
        v-for="(file, i) in files" :key="i"
        class="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800/60 hover:border-zinc-600 text-sm transition-colors group/file"
      >
        <FileText class="w-4 h-4 text-zinc-500 shrink-0" :stroke-width="1.5" />
        <span class="flex-1 text-zinc-200 truncate">{{ file.name }}</span>
        <span class="text-xs text-zinc-600">{{ formatSize(file.size) }}</span>
        <button
          @click="$emit('remove', i)"
          class="w-5 h-5 flex items-center justify-center rounded text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors opacity-0 group-hover/file:opacity-100"
        >
          <X class="w-3 h-3" :stroke-width="2.5" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadCloud, FileText, X } from 'lucide-vue-next'
const props = defineProps({ files: { type: Array, default: () => [] } })
const emit = defineEmits(['update:files', 'remove'])
const dragging = ref(false)
const fileInput = ref(null)
function triggerInput() { fileInput.value?.click() }
function handleDrop(e) { dragging.value = false; addFiles(Array.from(e.dataTransfer.files)) }
function handleSelect(e) { addFiles(Array.from(e.target.files || [])); e.target.value = '' }
function addFiles(newFiles) {
  const allowed = ['.html', '.zip', '.png', '.jpg', '.jpeg']
  const valid = newFiles.filter(f => allowed.includes('.' + f.name.split('.').pop().toLowerCase()))
  if (valid.length) emit('update:files', [...props.files, ...valid])
}
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>
