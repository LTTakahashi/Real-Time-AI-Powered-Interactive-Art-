import React from 'react'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'

export interface StyleOption {
    id: string
    name: string
    color: string // Tailwind bg class for placeholder
    image?: string // Optional thumbnail
}

interface StyleSelectorProps {
    styles: StyleOption[]
    selected: string
    onSelect: (id: string) => void
}

const StyleSelector: React.FC<StyleSelectorProps> = ({ styles, selected, onSelect }) => {
    return (
        <div className="flex gap-4 p-4 bg-black/30 backdrop-blur-md rounded-2xl border border-white/10">
            {styles.map((style) => (
                <button
                    key={style.id}
                    onClick={() => onSelect(style.id)}
                    className={clsx(
                        "group relative flex flex-col items-center gap-2 transition-all duration-300",
                        selected === style.id ? "scale-110" : "opacity-70 hover:opacity-100 hover:scale-105"
                    )}
                >
                    <div
                        className={clsx(
                            "w-16 h-16 rounded-full shadow-lg border-2 transition-all overflow-hidden",
                            style.color,
                            selected === style.id ? "border-white ring-2 ring-white/50 ring-offset-2 ring-offset-black/50" : "border-transparent"
                        )}
                    >
                        {/* Placeholder or Image */}
                        {style.image && <img src={style.image} alt={style.name} className="w-full h-full object-cover" />}
                    </div>
                    <span className="text-xs font-medium text-white/90 drop-shadow-md">
                        {style.name}
                    </span>

                    {selected === style.id && (
                        <motion.div
                            layoutId="selection-dot"
                            className="absolute -bottom-2 w-1 h-1 bg-white rounded-full"
                        />
                    )}
                </button>
            ))}
        </div>
    )
}

export default StyleSelector
