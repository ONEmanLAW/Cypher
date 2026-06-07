// src/composables/useBeatboxDetector.js
import { ref, onBeforeUnmount } from 'vue'

// 👇 absorbe espaces/casse entre label modèle et label cible
const normalize = (s) => String(s ?? '').trim().toLowerCase()

export function useBeatboxDetector({ targetLabel, onHit, threshold = 0.6 }) {
  const isListening = ref(false)
  const lastLabel = ref(null)
  const lastConfidence = ref(0)
  const error = ref(null)

  let audioCtx = null
  let stream = null
  let processor = null
  let source = null
  let ws = null
  let buffer = []

  const CHUNK_SAMPLES = 24000
  const HOP_SAMPLES = 6000

  const RMS_GATE = 0.015
  let aboveGateSince = -1
  let lastSentAt = 0
  const MIN_SEND_INTERVAL_MS = 80

  let lastHitAt = 0
  const COOLDOWN_MS = 180

  async function start() {
    if (isListening.value) return
    try {
      error.value = null
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      })

      audioCtx = new AudioContext({ sampleRate: 48000 })
      source = audioCtx.createMediaStreamSource(stream)
      processor = audioCtx.createScriptProcessor(2048, 1, 1)

      ws = new WebSocket('ws://localhost:8000/detect')
      ws.binaryType = 'arraybuffer'
      await new Promise((res, rej) => {
        ws.onopen = res
        ws.onerror = () => rej(new Error('Cannot connect to detector'))
      })

      ws.onmessage = (e) => {
        const { label, confidence } = JSON.parse(e.data)
        lastLabel.value = label
        lastConfidence.value = confidence

        const now = performance.now()
        if (
          normalize(label) === normalize(targetLabel.value) &&
          confidence >= threshold &&
          now - lastHitAt > COOLDOWN_MS
        ) {
          lastHitAt = now
          onHit?.({ label, confidence })
        }
      }

      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0)

        let sum = 0
        for (let i = 0; i < input.length; i++) sum += input[i] * input[i]
        const frameRms = Math.sqrt(sum / input.length)

        for (let i = 0; i < input.length; i++) buffer.push(input[i])

        if (frameRms > RMS_GATE && aboveGateSince < 0) {
          aboveGateSince = buffer.length
        }
        if (frameRms < RMS_GATE / 2) {
          aboveGateSince = -1
        }

        if (buffer.length > CHUNK_SAMPLES * 2) {
          buffer = buffer.slice(-CHUNK_SAMPLES * 2)
        }

        const now = performance.now()
        const hasOnset = aboveGateSince > 0
        const enoughSamples = buffer.length >= CHUNK_SAMPLES

        if (
          hasOnset &&
          enoughSamples &&
          now - lastSentAt > MIN_SEND_INTERVAL_MS &&
          ws?.readyState === WebSocket.OPEN
        ) {
          const chunk = new Float32Array(buffer.slice(-CHUNK_SAMPLES))
          ws.send(chunk.buffer)
          lastSentAt = now
        }
      }

      source.connect(processor)
      processor.connect(audioCtx.destination)
      isListening.value = true
    } catch (e) {
      error.value = e.message
      stop()
    }
  }

  function stop() {
    try { processor?.disconnect() } catch {}
    try { source?.disconnect() } catch {}
    stream?.getTracks().forEach((t) => t.stop())
    audioCtx?.close().catch(() => {})
    ws?.close()
    processor = source = stream = audioCtx = ws = null
    buffer = []
    aboveGateSince = -1
    isListening.value = false
  }

  function toggle() {
    isListening.value ? stop() : start()
  }

  onBeforeUnmount(stop)

  return { isListening, lastLabel, lastConfidence, error, start, stop, toggle }
}