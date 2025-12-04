import React from 'react'
import { motion } from 'framer-motion'
import { Hand, Pointer, MousePointer2, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'
import type { SystemStatus } from './StatusPill'

interface GestureIndicatorProps {
    status: SystemStatus
}

const GestureIndicator: React.FC<GestureIndicatorProps> = ({ status }) => {
    const getGestureInfo = () => {
        switch (status) {
            case 'drawing':
                return {
                    icon: Pointer,
                    label: 'Drawing',
                    color: 'text-green-400',
                    bg: 'bg-green-500/20',
                    border: 'border-green-500/50'
                }
            case 'hovering':
                return {
                    icon: Hand,
                    label: 'Hovering',
                    color: 'text-blue-400',
                    bg: 'bg-blue-500/20',
                    border: 'border-blue-500/50'
                }
            case 'processing':
                return {
                    icon: MousePointer2, // Or a spinner
                    label: 'Processing',
                    color: 'text-purple-400',
                    bg: 'bg-purple-500/20',
                    border: 'border-purple-500/50'
                }
            case 'disconnected':
                return {
                    icon: AlertCircle,
                    label: 'Disconnected',
                    color: 'text-red-400',
                    bg: 'bg-red-500/20',
                    border: 'border-red-500/50'
                }
            default: // idle
                return {
                    icon: Hand,
                    label: 'Ready',
                    color: 'text-gray-400',
                    bg: 'bg-gray-500/20',
                    border: 'border-gray-500/50'
                }
        }
    }

    const info = getGestureInfo()
    const Icon = info.icon

    return (
        <div className="flex items-center gap-3">
            <motion.div
                initial={false}
                animate={{
                    backgroundColor: status === 'drawing' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(0,0,0,0.3)',
                    borderColor: status === 'drawing' ? 'rgba(34, 197, 94, 0.5)' : 'rgba(255,255,255,0.1)',
                }}
                className={clsx(
                    "flex items-center gap-3 px-4 py-2 rounded-full border backdrop-blur-md transition-colors duration-300",
                    info.bg,
                    info.border
                )}
            >
                <motion.div
                    key={status}
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.8, opacity: 0 }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                >
                    <Icon className={clsx("w-5 h-5", info.color)} />
                </motion.div>

                <div className="flex flex-col">
                    <span className={clsx("text-xs font-bold tracking-wider uppercase", info.color)}>
                        {info.label}
                    </span>
                    <span className="text-[10px] text-white/50 font-medium">
                        {status === 'drawing' ? 'Index Finger Extended' :
                            status === 'hovering' ? 'Open Palm' :
                                status === 'processing' ? 'Generating Art...' : 'Waiting for Hand'}
                    </span>
                </div>
            </motion.div>
        </div>
    )
}

export default GestureIndicator
