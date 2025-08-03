import { describe, it, expect, vi, beforeEach } from 'vitest'
import { handleCancel } from '../../src/utils/misc.js'
import { isCancel } from '@clack/prompts'

vi.mock('@clack/prompts')

describe('misc utils', () => {
  describe('handleCancel', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('should return value when not cancelled', () => {
      vi.mocked(isCancel).mockReturnValue(false)
      const result = handleCancel('test')
      expect(result).toBe('test')
    })

    it('should exit process when cancelled', () => {
      const mockExit = vi.spyOn(process, 'exit').mockImplementation(() => {
        throw new Error('process.exit called')
      })

      // Mock isCancel to return true for our test
      vi.mocked(isCancel).mockReturnValue(true)

      expect(() => {
        handleCancel(Symbol.for('clack.cancel'))
      }).toThrow('process.exit called')

      mockExit.mockRestore()
    })

    it('should throw error for unexpected symbol', () => {
      vi.mocked(isCancel).mockReturnValue(false)
      expect(() => {
        handleCancel(Symbol('test'))
      }).toThrow('Unexpected symbol value')
    })
  })
})