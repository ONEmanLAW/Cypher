// import { defineStore } from 'pinia'
// import { ref, computed } from 'vue'

// const STORAGE_KEY = 'cypher.progress.v1'

// function loadInitial() {
//   try {
//     const raw = localStorage.getItem(STORAGE_KEY)
//     if (!raw) return {}
//     return JSON.parse(raw)
//   } catch {
//     return {}
//   }
// }

// export const useProgressStore = defineStore('progress', () => {
//   const states = ref(loadInitial())
//   const allIds = ['01', '02', '03', '04', '05', '06']

//   function persist() {
//     try {
//       localStorage.setItem(STORAGE_KEY, JSON.stringify(states.value))
//     } catch {}
//   }

//   function getState(id) {
//     return states.value[id] || 'todo'
//   }

//   function markDone(id) {
//     states.value[id] = 'done'
//     persist()
//   }

//   function markCurrent(id) {
//     if (states.value[id] !== 'done') {
//       states.value[id] = 'current'
//       persist()
//     }
//   }

//   function reset() {
//     states.value = {}
//     persist()
//   }

//   const doneCount = computed(
//     () => allIds.filter((id) => states.value[id] === 'done').length,
//   )

//   return {
//     states,
//     getState,
//     markDone,
//     markCurrent,
//     reset,
//     doneCount,
//     allIds,
//   }
// })

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useProgressStore = defineStore('progress', () => {
  const states = ref({})
  const allIds = ['01', '02', '03', '04', '05', '06']

  function getState(id) {
    return states.value[id] || 'todo'
  }

  function markDone(id) {
    states.value[id] = 'done'
  }

  function markCurrent(id) {
    if (states.value[id] !== 'done') {
      states.value[id] = 'current'
    }
  }

  function reset() {
    states.value = {}
  }

  const doneCount = computed(
    () => allIds.filter((id) => states.value[id] === 'done').length,
  )

  return {
    states,
    getState,
    markDone,
    markCurrent,
    reset,
    doneCount,
    allIds,
  }
})