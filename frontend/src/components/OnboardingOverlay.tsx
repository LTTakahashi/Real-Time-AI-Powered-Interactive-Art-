import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Pointer, Hand, HelpCircle } from 'lucide-react'

interface OnboardingOverlayProps {
    isOpen: boolean
    onClose: () => void
}

const OnboardingOverlay: React.FC<OnboardingOverlayProps> = ({ isOpen, onClose }) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.9, opacity: 0, y: 20 }}
                        className="relative w-full max-w-2xl bg-neutral-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden"
                    >
                        {/* Background Gradients */}
                        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-purple-500/20 to-transparent pointer-events-none" />
                        <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-pink-500/20 rounded-full blur-3xl pointer-events-none" />

                        <div className="relative p-8 md:p-12 flex flex-col gap-8">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h2 className="text-3xl font-bold text-white mb-2">Welcome to GestureCanvas</h2>
                                    <p className="text-white/60 text-lg">Control the digital canvas with your hands.</p>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="p-2 rounded-full hover:bg-white/10 transition-colors text-white/50 hover:text-white"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            <div className="grid md:grid-cols-2 gap-6">
                                {/* Gesture 1: Point */}
                                <div className="bg-white/5 border border-white/5 rounded-2xl p-6 flex flex-col gap-4 hover:bg-white/10 transition-colors group">
                                    <div className="w-12 h-12 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 group-hover:scale-110 transition-transform">
                                        <Pointer size={24} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">Point to Draw</h3>
                                        <p className="text-white/60 text-sm">Extend your <span className="text-green-400 font-bold">Index Finger</span> to draw lines on the canvas.</p>
                                    </div>
                                </div>

                                {/* Gesture 2: Hover */}
                                <div className="bg-white/5 border border-white/5 rounded-2xl p-6 flex flex-col gap-4 hover:bg-white/10 transition-colors group">
                                    <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                                        <Hand size={24} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1">Palm to Hover</h3>
                                        <p className="text-white/60 text-sm">Show an <span className="text-blue-400 font-bold">Open Palm</span> to move the cursor without drawing.</p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col md:flex-row gap-4 items-center justify-between pt-4 border-t border-white/10">
                                <div className="flex items-center gap-2 text-white/40 text-sm">
                                    <HelpCircle size={16} />
                                    <span>You can open this guide anytime from the menu.</span>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="px-8 py-3 rounded-full bg-white text-black font-bold hover:bg-gray-200 transition-all hover:scale-105 active:scale-95 shadow-lg shadow-white/10"
                                >
                                    Get Started
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}

export default OnboardingOverlay
