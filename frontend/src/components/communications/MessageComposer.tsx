import { useRef, KeyboardEvent } from 'react'
import { Button, Tooltip } from 'antd'
import { Send, Paperclip, Smile } from 'lucide-react'
import { cn } from '@/utils/cn'
import { useCommunicationsStore } from '@/store/communicationsStore'

interface Props {
  threadId: string
  onSend: (text: string) => Promise<void>
  isSending?: boolean
  disabled?: boolean
}

export function MessageComposer({ threadId, onSend, isSending, disabled }: Props) {
  const composerText = useCommunicationsStore((s) => s.composerText)
  const setComposerText = useCommunicationsStore((s) => s.setComposerText)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const isEmpty = !composerText.trim()

  const handleSend = async () => {
    if (isEmpty || isSending) return
    const text = composerText.trim()
    setComposerText('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    await onSend(text)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`
  }

  return (
    <div className="border-t border-slate-100 bg-white px-4 py-3 flex-shrink-0">
      <div className={cn(
        'flex items-end gap-2 rounded-xl border transition-colors',
        disabled ? 'border-slate-200 bg-slate-50' : 'border-slate-200 bg-white focus-within:border-indigo-400',
      )}>
        <textarea
          ref={textareaRef}
          value={composerText}
          onChange={(e) => setComposerText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder="Write a message… (Enter to send, Shift+Enter for new line)"
          rows={1}
          className={cn(
            'flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder-slate-400',
            'px-3 py-2.5 outline-none min-h-[40px] max-h-[140px] leading-relaxed',
            disabled && 'cursor-not-allowed',
          )}
        />
        <div className="flex items-center gap-0.5 pr-2 pb-1.5 flex-shrink-0">
          <Tooltip title="Attach file (coming soon)">
            <Button
              type="text"
              size="small"
              icon={<Paperclip className="h-4 w-4 text-slate-400" />}
              disabled
              className="flex items-center justify-center opacity-50"
            />
          </Tooltip>
          <Tooltip title="Emoji (coming soon)">
            <Button
              type="text"
              size="small"
              icon={<Smile className="h-4 w-4 text-slate-400" />}
              disabled
              className="flex items-center justify-center opacity-50"
            />
          </Tooltip>
          <Tooltip title={isEmpty ? 'Type a message first' : 'Send (Enter)'}>
            <Button
              type="primary"
              size="small"
              icon={<Send className="h-3.5 w-3.5" />}
              onClick={handleSend}
              loading={isSending}
              disabled={isEmpty || disabled}
              className={cn(
                'flex items-center justify-center rounded-lg h-8 w-8 ml-1',
                isEmpty ? 'opacity-40' : '',
              )}
            />
          </Tooltip>
        </div>
      </div>
      <p className="text-[10px] text-slate-400 mt-1.5 px-1">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}
