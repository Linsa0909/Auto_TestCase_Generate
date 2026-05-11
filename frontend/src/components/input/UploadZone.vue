<template>
  <div>
    <div
      :class="[
        'border border-dashed rounded-md p-5 flex flex-col items-center justify-center gap-1.5 cursor-pointer transition-all duration-150 group',
        dragging ? 'border-gray-900 bg-gray-50 scale-[1.005]' : 'border-gray-200 hover:border-gray-400 hover:bg-gray-50/50',
      ]"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="handleDrop"
      @click="triggerInput"
    >
      <UploadCloud
        :class="['w-4 h-4 transition-all duration-150', dragging ? 'text-gray-900 scale-110' : 'text-gray-400 group-hover:text-gray-600']"
        :stroke-width="1.5"
      />
      <p class="text-[12px] text-gray-500 text-center">
        {{ dragging ? '释放以上传' : '拖拽或点击上传原型文件' }}
      </p>
      <p class="text-[10px] text-gray-400">支持 HTML, ZIP, PNG, JPG</p>
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".html,.zip,.png,.jpg,.jpeg"
        class="hidden"
        @change="handleSelect"
      />
    </div>

    <!-- File list -->
    <div v-if="files.length" class="mt-2 flex flex-col gap-1">
      <div
        v-for="(file, i) in files"
        :key="i"
        class="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-gray-50 text-[12px] transition-colors hover:bg-gray-100"
      >
        <FileText class="w-3 h-3 text-gray-400 shrink-0" :stroke-width="1.5" />
        <span class="flex-1 text-gray-700 truncate">{{ file.name }}</span>
        <span class="text-[10px] text-gray-400">{{ formatSize(file.size) }}</span>
        <button
          @click="$emit('remove', i)"
          class="w-4 h-4 flex items-center justify-center rounded text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors"
        >
          <X class="w-2.5 h-2.5" :stroke-width="2.5" />
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

function triggerInput() {
  fileInput.value?.click()
}

function handleDrop(e) {
  dragging.value = false
  addFiles(Array.from(e.dataTransfer.files))
}

function handleSelect(e) {
  addFiles(Array.from(e.target.files || []))
  e.target.value = ''
}

function addFiles(newFiles) {
  const allowed = ['.html', '.zip', '.png', '.jpg', '.jpeg']
  const valid = newFiles.filter(f => {
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    return allowed.includes(ext)
  })
  if (valid.length) {
    emit('update:files', [...props.files, ...valid])
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>
