// src/composables/useBeatboxDetector.js
import { ref, onBeforeUnmount } from 'vue'

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
  const CHUNK_SAMPLES = 48000 // 1s @ 48kHz
  let lastHitAt = 0
  const COOLDOWN_MS = 300

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
      processor = audioCtx.createScriptProcessor(4096, 1, 1)

      ws = new WebSocket('ws://localhost:8000/detect')
      ws.binaryType = 'arraybuffer'

      await new Promise((res, rej) => {
        ws.onopen = res
        ws.onerror = () => rej(new Error('Cannot connect to detector (is backend running?)'))
      })

      ws.onmessage = (e) => {
        const { label, confidence } = JSON.parse(e.data)
        lastLabel.value = label
        lastConfidence.value = confidence

        const now = performance.now()
        if (
          label === targetLabel.value &&
          confidence >= threshold &&
          now - lastHitAt > COOLDOWN_MS
        ) {
          lastHitAt = now
          onHit?.({ label, confidence })
        }
      }

      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0)
        for (let i = 0; i < input.length; i++) buffer.push(input[i])

        if (buffer.length >= CHUNK_SAMPLES) {
          const chunk = new Float32Array(buffer.slice(0, CHUNK_SAMPLES))
          buffer = buffer.slice(CHUNK_SAMPLES / 2) // overlap 50%
          if (ws?.readyState === WebSocket.OPEN) ws.send(chunk.buffer)
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
    isListening.value = false
  }

  function toggle() {
    isListening.value ? stop() : start()
  }

  onBeforeUnmount(stop)

  return { isListening, lastLabel, lastConfidence, error, start, stop, toggle }
}