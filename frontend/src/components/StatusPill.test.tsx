import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusPill from './StatusPill'

describe('StatusPill', () => {
    it('should render correct text for state', () => {
        render(<StatusPill status="drawing" />)
        expect(screen.getByText('Drawing')).toBeInTheDocument()

        render(<StatusPill status="processing" />)
        expect(screen.getByText('Processing')).toBeInTheDocument()
    })

    it('should have correct color class', () => {
        const { container } = render(<StatusPill status="drawing" />)
        expect(container.firstChild).toHaveClass('bg-green-500/20')
    })
})
