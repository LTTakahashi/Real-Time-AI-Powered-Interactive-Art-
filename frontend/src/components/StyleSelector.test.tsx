import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import StyleSelector from './StyleSelector'

describe('StyleSelector', () => {
    const styles = [
        { id: 'photorealistic', name: 'Photorealistic', color: 'bg-blue-500' },
        { id: 'anime', name: 'Anime', color: 'bg-pink-500' }
    ]

    it('should render all styles', () => {
        render(<StyleSelector styles={styles} selected="photorealistic" onSelect={() => { }} />)
        expect(screen.getByText('Photorealistic')).toBeInTheDocument()
        expect(screen.getByText('Anime')).toBeInTheDocument()
    })

    it('should highlight selected style', () => {
        render(<StyleSelector styles={styles} selected="photorealistic" onSelect={() => { }} />)
        const selectedBtn = screen.getByText('Photorealistic').closest('button')
        // The ring class is on the inner div (first child)
        const circle = selectedBtn?.querySelector('div')
        expect(circle).toHaveClass('ring-2')
    })

    it('should call onSelect when clicked', () => {
        const onSelect = vi.fn()
        render(<StyleSelector styles={styles} selected="photorealistic" onSelect={onSelect} />)

        fireEvent.click(screen.getByText('Anime'))
        expect(onSelect).toHaveBeenCalledWith('anime')
    })
})
