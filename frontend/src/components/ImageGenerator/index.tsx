import { useEffect, useRef, useState } from 'react'
import { generateImage } from '../../api/imageGeneration'
import { errorMessage } from '../../api/client'
import { uploadImage } from '../../api/upload'
import TextField from '../TextField'

// A fresh image can take ~45s upstream; give it well over that before giving up.
const GENERATION_TIMEOUT_MS = 90_000

interface GeneratedImage {
  file: File
  previewUrl: string
}

interface ImageGeneratorProps {
  defaultTopic?: string
  // Called with the stored (uploaded) image URL once the author accepts an image.
  onUploaded: (url: string) => void
}

export default function ImageGenerator({ defaultTopic = '', onUploaded }: ImageGeneratorProps) {
  const [topic, setTopic] = useState(defaultTopic)
  const [image, setImage] = useState<GeneratedImage | null>(null)
  const [status, setStatus] = useState<'idle' | 'generating' | 'uploading'>('idle')
  const [error, setError] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  // An object URL keeps the image bytes in memory until revoked — an external
  // resource, so its cleanup can't live in a handler (it must also run on unmount).
  useEffect(() => {
    return () => {
      if (image) URL.revokeObjectURL(image.previewUrl)
    }
  }, [image])

  async function handleGenerate() {
    const controller = new AbortController()
    controllerRef.current = controller
    const timeout = AbortSignal.timeout(GENERATION_TIMEOUT_MS)
    setError(null)
    setStatus('generating')
    try {
      const file = await generateImage(topic, AbortSignal.any([controller.signal, timeout]))
      setImage({ file, previewUrl: URL.createObjectURL(file) })
    } catch {
      if (controller.signal.aborted) return // the author cancelled — nothing to report
      setError(
        timeout.aborted
          ? 'The image took too long to generate. Try again.'
          : "Couldn't generate an image right now. Try again.",
      )
    } finally {
      setStatus('idle')
    }
  }

  async function handleUse() {
    if (!image) return
    setError(null)
    setStatus('uploading')
    try {
      const { url } = await uploadImage(image.file)
      setImage(null)
      onUploaded(url)
    } catch (uploadError) {
      setError(errorMessage(uploadError, 'Could not upload the image. Try again.'))
    } finally {
      setStatus('idle')
    }
  }

  const isBusy = status !== 'idle'

  return (
    <div className="space-y-4">
      <TextField
        id="image-topic"
        label="Describe the image"
        value={topic}
        onChange={setTopic}
        required={false}
      />

      {status === 'generating' && (
        <div
          role="status"
          className="flex aspect-video w-full flex-col items-center justify-center gap-3 rounded-xl border border-sees-teal/40 bg-sees-glass p-4 text-center"
        >
          <div
            aria-hidden="true"
            className="size-8 animate-spin rounded-full border-2 border-sees-teal border-t-sees-mint"
          />
          <p className="text-sm text-white/70">Generating… this can take up to a minute.</p>
          <button
            type="button"
            onClick={() => controllerRef.current?.abort()}
            className="min-h-11 px-3 text-sm text-sees-mustard underline hover:text-sees-mint"
          >
            Cancel
          </button>
        </div>
      )}

      {image && status !== 'generating' && (
        <img
          src={image.previewUrl}
          alt="Generated preview"
          width={576}
          height={324}
          className="aspect-video w-full rounded-xl object-cover"
        />
      )}

      {error && (
        <p role="alert" className="text-sm text-red-400">
          {error}
        </p>
      )}

      <div className="flex gap-3">
        {image && (
          <button
            type="button"
            onClick={handleUse}
            disabled={isBusy}
            className="flex-1 rounded bg-sees-mint py-2.5 font-medium text-sees-forest transition-shadow hover:shadow-sees-glow disabled:opacity-50"
          >
            {status === 'uploading' ? 'Uploading…' : 'Use this image'}
          </button>
        )}
        <button
          type="button"
          onClick={handleGenerate}
          disabled={isBusy || topic.trim() === ''}
          className="flex-1 rounded border border-sees-teal py-2.5 font-medium text-sees-mint hover:border-sees-mint disabled:opacity-50"
        >
          {image ? 'Generate again' : 'Generate'}
        </button>
      </div>

      <p className="text-xs text-white/50">
        Your description is sent to an image-generation service (pollinations.ai) to create the image.
      </p>
    </div>
  )
}
