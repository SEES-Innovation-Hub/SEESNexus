import { useEffect, useRef, useState } from 'react'
import { generateImage } from '../../api/imageGeneration'
import { errorMessage } from '../../api/client'
import { uploadImage } from '../../api/upload'
import Button from '../Button'
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
  // Lets the host form hold back Save while the accepted image uploads.
  onUploadingChange?: (isUploading: boolean) => void
}

export default function ImageGenerator({ defaultTopic = '', onUploaded, onUploadingChange }: ImageGeneratorProps) {
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
    onUploadingChange?.(true)
    try {
      const { url } = await uploadImage(image.file)
      setImage(null)
      onUploaded(url)
    } catch (uploadError) {
      setError(errorMessage(uploadError, 'Could not upload the image. Try again.'))
    } finally {
      setStatus('idle')
      onUploadingChange?.(false)
    }
  }

  const isBusy = status !== 'idle'

  return (
    <div className="space-y-4">
      {/* Enter here means Generate; left alone it would submit the host form. */}
      <div
        onKeyDown={(event) => {
          if (event.key !== 'Enter') return
          event.preventDefault()
          if (!isBusy && topic.trim() !== '') void handleGenerate()
        }}
      >
        <TextField id="image-topic" label="Describe the image" value={topic} onChange={setTopic} />
      </div>

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
          <Button variant="secondary" onClick={() => controllerRef.current?.abort()}>
            Cancel
          </Button>
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
          <Button
            onClick={handleUse}
            disabled={isBusy}
            isLoading={status === 'uploading'}
            className="flex-1"
          >
            {status === 'uploading' ? 'Uploading…' : 'Use this image'}
          </Button>
        )}
        <Button
          variant="secondary"
          onClick={handleGenerate}
          disabled={isBusy || topic.trim() === ''}
          className="flex-1"
        >
          {image ? 'Generate again' : 'Generate'}
        </Button>
      </div>

      <p className="text-xs text-white/50">
        Your description is sent to an image-generation service (pollinations.ai) to create the image.
      </p>
    </div>
  )
}
