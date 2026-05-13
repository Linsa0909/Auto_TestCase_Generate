<template>
  <div class="flex flex-col items-center justify-center min-h-full py-16">
    <div class="w-full max-w-[720px]">

      <!-- Iteration List (drilled into a product) -->
      <template v-if="selectedProduct">
        <div class="flex items-center gap-3 mb-6">
          <button @click="selectedProduct = null"
            class="w-7 h-7 flex items-center justify-center rounded-md text-zinc-500 hover:text-white hover:bg-zinc-800 transition-colors">
            <ArrowLeft class="w-4 h-4" :stroke-width="2" />
          </button>
          <div>
            <h2 class="text-xl font-semibold tracking-tight text-white">{{ selectedProduct }}</h2>
            <p class="text-sm text-zinc-400 mt-0.5">{{ iterationPlans.length }} 个迭代</p>
          </div>
          <button @click="openCreateForProduct"
            class="ml-auto flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)] transition-all active:scale-[0.98]">
            <Plus class="w-4 h-4" :stroke-width="2" />
            新建迭代
          </button>
        </div>

        <!-- Create Form (pre-filled product) -->
        <div v-if="showCreate" class="mb-6 p-5 rounded-xl border border-zinc-800 bg-zinc-900/50">
          <h3 class="text-sm font-semibold text-white mb-4">新建测试计划</h3>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-xs text-zinc-400 uppercase tracking-wider font-medium mb-1.5">产品名称</label>
              <input :value="form.productName" disabled
                class="w-full rounded-lg border border-zinc-800 bg-zinc-900/30 px-4 py-2.5 text-sm text-zinc-500 cursor-not-allowed" />
            </div>
            <div>
              <label class="block text-xs text-zinc-400 uppercase tracking-wider font-medium mb-1.5">迭代名称 <span class="text-rose-400">*</span></label>
              <input
                v-model="form.iterationName"
                placeholder="例如：Sprint 75"
                class="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:border-zinc-500 focus:outline-none transition-colors"
              />
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button @click="createPlan"
              :disabled="!form.iterationName.trim()"
              class="px-5 py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)] transition-all active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed">
              创建
            </button>
            <button @click="showCreate = false; form.iterationName = ''"
              class="px-5 py-2.5 rounded-lg text-sm font-medium text-zinc-400 border border-zinc-800 hover:border-zinc-600 hover:text-white transition-colors">
              取消
            </button>
          </div>
        </div>

        <!-- Iteration Cards -->
        <div v-if="iterationPlans.length > 0" class="flex flex-col gap-3">
          <div
            v-for="plan in iterationPlans"
            :key="plan.id"
            @click="$emit('open-plan', plan.id)"
            class="group p-5 rounded-xl border border-zinc-800 bg-zinc-900/30 hover:border-zinc-600 hover:scale-[1.01] transition-all cursor-pointer"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs text-zinc-500 font-mono">{{ plan.id }}</span>
                </div>
                <h3 class="text-base font-semibold text-white truncate">{{ plan.iteration_name }}</h3>
              </div>
              <button
                @click.stop="deletePlan(plan.id)"
                class="w-7 h-7 flex items-center justify-center rounded-md text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100 shrink-0"
              >
                <Trash2 class="w-3.5 h-3.5" :stroke-width="2" />
              </button>
            </div>

            <div class="flex items-center gap-4 mt-3 pt-3 border-t border-zinc-800/60">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-indigo-400" />
                <span class="text-xs text-zinc-400"><span class="text-white font-semibold tabular-nums">{{ plan.total }}</span> 需求</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-emerald-400" />
                <span class="text-xs text-zinc-400"><span class="text-white font-semibold tabular-nums">{{ plan.completed }}</span> 完成</span>
              </div>
              <div class="flex-1 h-[3px] bg-zinc-800 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="plan.completed === plan.total && plan.total > 0 ? 'bg-emerald-400' : 'bg-indigo-400'"
                  :style="{ width: (plan.total ? plan.completed / plan.total * 100 : 0) + '%' }"
                />
              </div>
              <span class="text-[11px] text-zinc-600">{{ plan.updated_at?.slice(0, 10) }}</span>
            </div>
          </div>
        </div>

        <!-- Empty iterations -->
        <div v-else class="micro-dots flex flex-col items-center justify-center py-20 rounded-xl">
          <div class="bg-zinc-900/80 rounded-xl p-8 flex flex-col items-center gap-3 border border-zinc-800/40">
            <ClipboardList class="w-8 h-8 text-zinc-500" :stroke-width="1" />
            <p class="text-sm text-zinc-400">暂无迭代计划</p>
            <p class="text-xs text-zinc-600">点击右上角「新建迭代」开始</p>
          </div>
        </div>
      </template>

      <!-- Product List (default view) -->
      <template v-else>
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-xl font-semibold tracking-tight text-white">测试计划</h2>
            <p class="text-sm text-zinc-400 mt-0.5">按产品管理测试计划，每个产品下可创建多个迭代</p>
          </div>
          <button
            @click="showCreate = true; form.productName = ''; form.iterationName = ''"
            class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)] transition-all active:scale-[0.98]"
          >
            <Plus class="w-4 h-4" :stroke-width="2" />
            新建计划
          </button>
        </div>

        <!-- Create Form -->
        <div v-if="showCreate" class="mb-6 p-5 rounded-xl border border-zinc-800 bg-zinc-900/50">
          <h3 class="text-sm font-semibold text-white mb-4">新建测试计划</h3>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-xs text-zinc-400 uppercase tracking-wider font-medium mb-1.5">产品名称 <span class="text-rose-400">*</span></label>
              <input
                v-model="form.productName"
                placeholder="例如：数据管理平台"
                class="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:border-zinc-500 focus:outline-none transition-colors"
              />
            </div>
            <div>
              <label class="block text-xs text-zinc-400 uppercase tracking-wider font-medium mb-1.5">迭代名称 <span class="text-rose-400">*</span></label>
              <input
                v-model="form.iterationName"
                placeholder="例如：Sprint 75"
                class="w-full rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:border-zinc-500 focus:outline-none transition-colors"
              />
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
              @click="createPlan"
              :disabled="!form.productName.trim() || !form.iterationName.trim()"
              class="px-5 py-2.5 rounded-lg text-sm font-medium bg-white text-black hover:shadow-[inset_0_1px_4px_rgba(255,255,255,0.2)] transition-all active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              创建
            </button>
            <button
              @click="showCreate = false; form.productName = ''; form.iterationName = ''"
              class="px-5 py-2.5 rounded-lg text-sm font-medium text-zinc-400 border border-zinc-800 hover:border-zinc-600 hover:text-white transition-colors"
            >
              取消
            </button>
          </div>
        </div>

        <!-- Product Cards -->
        <div v-if="products.length > 0" class="flex flex-col gap-3">
          <div
            v-for="prod in products"
            :key="prod.name"
            @click="selectedProduct = prod.name"
            class="group p-5 rounded-xl border border-zinc-800 bg-zinc-900/30 hover:border-zinc-600 hover:scale-[1.01] transition-all cursor-pointer"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <h3 class="text-base font-semibold text-white truncate">{{ prod.name }}</h3>
                <p class="text-sm text-zinc-400 mt-0.5">{{ prod.plans.length }} 个迭代</p>
              </div>
              <div class="flex items-center gap-1.5">
                <ChevronRight class="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </div>

            <div class="flex items-center gap-4 mt-3 pt-3 border-t border-zinc-800/60">
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-indigo-400" />
                <span class="text-xs text-zinc-400"><span class="text-white font-semibold tabular-nums">{{ prod.total }}</span> 需求</span>
              </div>
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-emerald-400" />
                <span class="text-xs text-zinc-400"><span class="text-white font-semibold tabular-nums">{{ prod.completed }}</span> 完成</span>
              </div>
              <div class="flex-1 h-[3px] bg-zinc-800 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="prod.completed === prod.total && prod.total > 0 ? 'bg-emerald-400' : 'bg-indigo-400'"
                  :style="{ width: (prod.total ? prod.completed / prod.total * 100 : 0) + '%' }"
                />
              </div>
              <span class="text-[11px] text-zinc-600">{{ prod.lastUpdated }}</span>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="micro-dots flex flex-col items-center justify-center py-20 rounded-xl">
          <div class="bg-zinc-900/80 rounded-xl p-8 flex flex-col items-center gap-3 border border-zinc-800/40">
            <ClipboardList class="w-8 h-8 text-zinc-500" :stroke-width="1" />
            <p class="text-sm text-zinc-400">暂无测试计划</p>
            <p class="text-xs text-zinc-600">点击右上角「新建计划」开始</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, inject } from 'vue'
import { Plus, Trash2, ClipboardList, ArrowLeft, ChevronRight } from 'lucide-vue-next'

const emit = defineEmits(['open-plan'])
const toast = inject('toast')

const plans = ref([])
const selectedProduct = ref(null)
const showCreate = ref(false)
const form = reactive({ productName: '', iterationName: '' })

// Group plans by product_name
const products = computed(() => {
  const map = new Map()
  for (const p of plans.value) {
    const name = p.product_name || '未命名产品'
    if (!map.has(name)) {
      map.set(name, { name, plans: [], total: 0, completed: 0, lastUpdated: '' })
    }
    const prod = map.get(name)
    prod.plans.push(p)
    prod.total += p.total
    prod.completed += p.completed
    const updatedAt = p.updated_at || p.created_at || ''
    if (updatedAt > prod.lastUpdated) prod.lastUpdated = updatedAt
  }
  return Array.from(map.values())
})

// Plans for selected product
const iterationPlans = computed(() => {
  if (!selectedProduct.value) return []
  return plans.value.filter(p => (p.product_name || '未命名产品') === selectedProduct.value)
})

async function loadPlans() {
  try {
    const res = await fetch('/api/plans')
    plans.value = await res.json()
  } catch {
    plans.value = []
  }
}

function openCreateForProduct() {
  form.productName = selectedProduct.value || ''
  form.iterationName = ''
  showCreate.value = true
}

async function createPlan() {
  const productName = form.productName.trim()
  const iterationName = form.iterationName.trim()
  if (!productName || !iterationName) return
  try {
    const res = await fetch('/api/plans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_name: productName, iteration_name: iterationName }),
    })
    if (!res.ok) throw new Error('创建失败')
    const plan = await res.json()
    toast('测试计划已创建', 'success')
    showCreate.value = false
    form.productName = ''
    form.iterationName = ''
    emit('open-plan', plan.id)
  } catch (e) {
    toast(e.message, 'error')
  }
}

async function deletePlan(id) {
  try {
    await fetch(`/api/plans/${id}`, { method: 'DELETE' })
    plans.value = plans.value.filter(p => p.id !== id)
    toast('已删除', 'success')
  } catch (e) {
    toast(e.message, 'error')
  }
}

onMounted(() => { loadPlans() })
</script>
