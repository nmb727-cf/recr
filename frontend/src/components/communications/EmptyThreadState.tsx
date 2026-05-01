import { Button } from 'antd'
import { MessageSquarePlus } from 'lucide-react'

interface Props {
  onNewThread?: () => void
}

export function EmptyThreadState({ onNewThread }: Props) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center bg-slate-50 text-center px-8">
      <div className="w-16 h-16 rounded-2xl bg-indigo-100 flex items-center justify-center mb-4">
        <MessageSquarePlus className="h-8 w-8 text-indigo-500" />
      </div>
      <h3 className="text-base font-semibold text-slate-800 mb-1">No conversation selected</h3>
      <p className="text-sm text-slate-500 max-w-[260px] mb-5">
        Pick a thread from the list or start a new conversation.
      </p>
      {onNewThread && (
        <Button type="primary" onClick={onNewThread} icon={<MessageSquarePlus className="h-4 w-4" />}>
          New conversation
        </Button>
      )}
    </div>
  )
}
