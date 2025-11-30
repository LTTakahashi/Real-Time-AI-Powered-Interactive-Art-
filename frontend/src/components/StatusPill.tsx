import React from 'react'
import { Activity, Edit2, Loader2, Hand, MousePointer2 } from 'lucide-react'
import { clsx } from 'clsx'

export type SystemStatus = 'idle' | 'drawing' | 'processing' | 'hovering' | 'disconnected'

interface StatusPillProps {
    status: SystemStatus
}

const StatusPill: React.FC<StatusPillProps> = ({ status }) => {
    const config = {
        idle: {
            text: 'Ready',
            icon: Hand,
            color: 'bg-white/10 text-white border-white/20'
        },
        hovering: {
            text: 'Hovering',
            icon: MousePointer2,
            color: 'bg-blue-500/20 text-blue-200 border-blue-500/30'
        },
        drawing: {
            text: 'Drawing',
            icon: Edit2,
            color: 'bg-green-500/20 text-green-200 border-green-500/30'
        },
        processing: {
            text: 'Processing',
            icon: Loader2,
            color: 'bg-purple-500/20 text-purple-200 border-purple-500/30'
        },
        disconnected: {
            text: 'Disconnected',
            icon: Activity,
            color: 'bg-red-500/20 text-red-200 border-red-500/30'
        }
    }

    const { text, icon: Icon, color } = config[status] || config.idle

    return (
        <div className={clsx(
            "flex items-center gap-2 px-4 py-2 rounded-full border backdrop-blur-md transition-all duration-300",
            color
        )}>
            <Icon className={clsx("w-4 h-4", status === 'processing' && "animate-spin")} />
            <span className="text-sm font-medium tracking-wide">{text}</span>
        </div>
    )
}

export default StatusPill
