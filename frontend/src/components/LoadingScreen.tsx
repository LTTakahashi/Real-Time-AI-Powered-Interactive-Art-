import React from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

interface LoadingScreenProps {
    message?: string
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ message = 'Loading...' }) => {
    return (
        <div className="fixed inset-0 flex items-center justify-center bg-neutral-950">
            <div className="flex flex-col items-center gap-6">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                >
                    <Loader2 className="w-16 h-16 text-purple-400" />
                </motion.div>

                <div className="flex flex-col items-center gap-2">
                    <h2 className="text-2xl font-bold text-white">{message}</h2>
                    <p className="text-white/50 text-sm">This may take up to 30 seconds...</p>
                </div>

                <div className="flex gap-1 mt-4">
                    {[0, 1, 2].map((i) => (
                        <motion.div
                            key={i}
                            className="w-2 h-2 bg-purple-400 rounded-full"
                            animate={{
                                scale: [1, 1.5, 1],
                                opacity: [0.5, 1, 0.5],
                            }}
                            transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                delay: i * 0.2,
                            }}
                        />
                    ))}
                </div>
            </div>
        </div>
    )
}

export default LoadingScreen
