import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/* ============================================================
   SECTIONS — chapitres (contiennent des sons)
   ============================================================ */
export const SECTIONS = [
  { id: 'fundamentals', number: '01', name: 'Fundamentals',      soundCount: 3, soundIds: ['kick', 'hihat', 'snare'], unlocked: true  },
  { id: 'mouth-fx',     number: '02', name: 'Mouth FX',          soundCount: 5, soundIds: [], unlocked: false  },
  { id: 'bass-lows',    number: '03', name: 'Bass & lows',       soundCount: 4, soundIds: [], unlocked: false  },
  { id: 'hi-hats',      number: '04', name: 'Hi-hats',           soundCount: 4, soundIds: [], unlocked: false  },
  { id: 'snares',       number: '05', name: 'Advanced snares',   soundCount: 4, soundIds: [], unlocked: false },
  { id: 'vocals',       number: '06', name: 'Vocals & textures', soundCount: 3, soundIds: [], unlocked: false },
  { id: 'patterns',     number: '07', name: 'Full patterns',     soundCount: 2, soundIds: [], unlocked: false },
  { id: 'freestyle',    number: '08', name: 'Free style',        soundCount: 2, soundIds: [], unlocked: false },
]

/* ============================================================
   SONS — catalogue
   ============================================================ */
export const SOUNDS = [
  { id: 'kick',   n: '01', name: 'Kick Drum', sub: 'the foot kick · the base.', label: 'Kick Drum',     unlocked: true },
  { id: 'hihat',  n: '02', name: 'Hi-Hat',    sub: 'ts · ts · ts.',             label: 'Hi-hat',         unlocked: true },
  { id: 'snare',  n: '03', name: 'Snare',     sub: 'the central snap.',         label: 'K Snare inward', unlocked: true },
]

const EXO_IDS = ['01', '02', '03', '04', '05', '06']

export const useProgressStore = defineStore('progress', () => {
  /* states[soundId] = { '01': 'done', '02': 'current', ... } */
  const states = ref({})
  const currentSoundId = ref(null)
  const currentSectionId = ref(null)

  /* ---------- SECTION COURANTE ---------- */
  function setCurrentSection(sectionId) {
    currentSectionId.value = sectionId
  }

  const currentSection = computed(() =>
    SECTIONS.find((s) => s.id === currentSectionId.value) || null
  )

  // nb de sons maîtrisés (tous exos done) dans une section
  function sectionDoneCount(sectionId) {
    const section = SECTIONS.find((s) => s.id === sectionId)
    if (!section) return 0
    return section.soundIds.filter((id) => soundState(id) === 'done').length
  }

  /* ---------- SON COURANT ---------- */
  function setCurrentSound(soundId) {
    currentSoundId.value = soundId
    if (!states.value[soundId]) states.value[soundId] = {}
  }

  const currentSound = computed(() =>
    SOUNDS.find((s) => s.id === currentSoundId.value) || null
  )

  /* ---------- ÉTAT D'UN EXO (pour le son courant) ---------- */
  function getState(exoId) {
    if (!currentSoundId.value) return 'todo'
    return states.value[currentSoundId.value]?.[exoId] || 'todo'
  }

  function markDone(exoId) {
    if (!currentSoundId.value) return
    if (!states.value[currentSoundId.value]) states.value[currentSoundId.value] = {}
    states.value[currentSoundId.value][exoId] = 'done'
  }

  function markCurrent(exoId) {
    if (!currentSoundId.value) return
    if (!states.value[currentSoundId.value]) states.value[currentSoundId.value] = {}
    if (states.value[currentSoundId.value][exoId] !== 'done') {
      states.value[currentSoundId.value][exoId] = 'current'
    }
  }

  function reset() {
    states.value = {}
    currentSoundId.value = null
    currentSectionId.value = null
  }

  /* ---------- COMPTEURS ---------- */
  // nb d'exos done pour le son courant
  const doneCount = computed(() => {
    if (!currentSoundId.value) return 0
    const s = states.value[currentSoundId.value] || {}
    return EXO_IDS.filter((id) => s[id] === 'done').length
  })

  // nb d'exos done pour un son donné (utilisé sur l'écran de sélection)
  function doneCountFor(soundId) {
    const s = states.value[soundId] || {}
    return EXO_IDS.filter((id) => s[id] === 'done').length
  }

  // état global d'un son : 'avail' | 'current' | 'done'
  function soundState(soundId) {
    const done = doneCountFor(soundId)
    if (done === 0) return 'avail'
    if (done >= EXO_IDS.length) return 'done'
    return 'current'
  }

  return {
    // catalogues
    SECTIONS,
    SOUNDS,
    EXO_IDS,
    // section courante
    currentSectionId,
    currentSection,
    setCurrentSection,
    sectionDoneCount,
    // son courant
    currentSoundId,
    currentSound,
    setCurrentSound,
    // exos
    getState,
    markDone,
    markCurrent,
    reset,
    // compteurs
    doneCount,
    doneCountFor,
    soundState,
    allIds: EXO_IDS,
  }
})