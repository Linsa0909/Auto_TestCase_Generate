<template>
  <div>
    <div
      :class="[
        'border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all group',
        dragging ? 'border-black bg-gray-50' : 'border-gray-200 hover:border-gray-400 hover:bg-gray-50',
      ]"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="handleDrop"
      @click="triggerInput"
    >
      <UploadCloud
        :class="['w-6 h-6 transition-colors', dragging ? 'text-black' : 'text-gray-300 group-hover:text-black']"
        :stroke-width="1.5"
      />
      <p class="text-sm text-gray-400 text-center">
        {{ dragging ? '释放以上传' : '拖拽或点击上传原型文件' }}
        <span class="text-gray-300 mt-1 inline-block">(支持 HTML, ZIP, PNG, JPG)</span>
      </p>
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
    <div v-if="files.length" class="mt-3 flex flex-col gap-1">
      <div
        v-for="(file, i) in files"
        :key="i"
        class="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 text-sm"
      >
        <FileText class="w-3.5 h-3.5 text-gray-400 shrink-0" :stroke-width="1.5" />
        <span class="flex-1 text-gray-600 truncate">{{ file.name }}</span>
        <span class="text-gray-300">{{ formatSize(file.size) }}</span>
        <button
          @click="$emit('remove', i)"
          class="text-gray-300 hover:text-red-500 transition-colors"
        >
          <X class="w-3.5 h-3.5" :stroke-width="1.5" />
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
