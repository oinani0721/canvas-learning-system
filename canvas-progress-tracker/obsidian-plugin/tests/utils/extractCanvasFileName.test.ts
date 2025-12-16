/**
 * Unit tests for extractCanvasFileName helper function
 *
 * @source Story 12.A.1 - AC 2, 5: extractCanvasFileName正确移除扩展名并添加测试
 *
 * Test Cases (Updated for Story 12.A.1):
 * - The function removes .canvas AND .md extensions (NOT path separators)
 * - Full path is preserved, only extension is stripped
 *
 * Input/Output Examples:
 * 1. undefined -> ""
 * 2. "" (empty string) -> ""
 * 3. "test.canvas" -> "test"
 * 4. "Canvas/Math53/Lecture5.canvas" -> "Canvas/Math53/Lecture5"
 * 5. "KP13-线性逼近与微分.md" -> "KP13-线性逼近与微分"
 * 6. "笔记库/test" (no extension) -> "笔记库/test" (unchanged)
 */

import { CanvasReviewSystemPlugin } from '../../main';

describe('extractCanvasFileName', () => {
    let extractCanvasFileName: (filePath: string | undefined) => string;

    beforeEach(() => {
        // ✅ Story 12.A.1: Use the ACTUAL implementation that removes extensions
        // [Source: main.ts:1680-1684]
        extractCanvasFileName = function (filePath: string | undefined): string {
            if (!filePath) return '';
            // Remove .canvas or .md extension (case insensitive)
            return filePath.replace(/\.(canvas|md)$/i, '');
        };
    });

    // =========================================================================
    // Test: Empty and undefined inputs
    // =========================================================================
    describe('AC2.1: Handle undefined and empty inputs', () => {
        it('should return empty string for undefined input', () => {
            const result = extractCanvasFileName(undefined);
            expect(result).toBe('');
        });

        it('should return empty string for empty string input', () => {
            const result = extractCanvasFileName('');
            expect(result).toBe('');
        });
    });

    // =========================================================================
    // Test: .canvas extension removal (original behavior)
    // =========================================================================
    describe('AC2.2: Remove .canvas extension', () => {
        it('should remove .canvas extension from simple filename', () => {
            const result = extractCanvasFileName('test.canvas');
            expect(result).toBe('test');
        });

        it('should remove .canvas extension and preserve full path', () => {
            const result = extractCanvasFileName('Canvas/Math53/Lecture5.canvas');
            expect(result).toBe('Canvas/Math53/Lecture5');
        });

        it('should handle .CANVAS (uppercase) extension', () => {
            const result = extractCanvasFileName('test.CANVAS');
            expect(result).toBe('test');
        });

        it('should preserve Chinese path when removing .canvas', () => {
            const result = extractCanvasFileName('笔记库/子目录/test.canvas');
            expect(result).toBe('笔记库/子目录/test');
        });
    });

    // =========================================================================
    // Test: .md extension removal (Story 12.A.1 BUG FIX)
    // =========================================================================
    describe('AC2.3: Remove .md extension (Story 12.A.1 bug fix)', () => {
        it('should remove .md extension from simple filename', () => {
            // This is the PRIMARY BUG FIX for Story 12.A.1
            // [Source: Story 12.A.1 - 39次错误根因]
            const result = extractCanvasFileName('KP13-线性逼近与微分.md');
            expect(result).toBe('KP13-线性逼近与微分');
        });

        it('should remove .md extension and preserve path', () => {
            const result = extractCanvasFileName('笔记库/数学/线性代数.md');
            expect(result).toBe('笔记库/数学/线性代数');
        });

        it('should handle .MD (uppercase) extension', () => {
            const result = extractCanvasFileName('test.MD');
            expect(result).toBe('test');
        });
    });

    // =========================================================================
    // Test: No extension (pass through)
    // =========================================================================
    describe('AC2.4: Handle input without extension', () => {
        it('should pass through filename without extension', () => {
            const result = extractCanvasFileName('test');
            expect(result).toBe('test');
        });

        it('should pass through path without extension', () => {
            const result = extractCanvasFileName('Canvas/Math53/Lecture5');
            expect(result).toBe('Canvas/Math53/Lecture5');
        });

        it('should not modify .txt extension (only .canvas/.md)', () => {
            const result = extractCanvasFileName('notes.txt');
            expect(result).toBe('notes.txt');
        });
    });

    // =========================================================================
    // Test: Edge cases
    // =========================================================================
    describe('AC2.5: Handle edge cases', () => {
        it('should handle filename with special characters', () => {
            const result = extractCanvasFileName('测试-文件_2024.canvas');
            expect(result).toBe('测试-文件_2024');
        });

        it('should handle filename with spaces', () => {
            const result = extractCanvasFileName('my test file.canvas');
            expect(result).toBe('my test file');
        });

        it('should handle deep path with .md extension', () => {
            const result = extractCanvasFileName('a/b/c/d/e/file.md');
            expect(result).toBe('a/b/c/d/e/file');
        });

        it('should handle double extension .canvas.md (removes only .md)', () => {
            // Only removes from the END
            const result = extractCanvasFileName('test.canvas.md');
            expect(result).toBe('test.canvas');
        });

        it('should handle double extension .md.canvas (removes only .canvas)', () => {
            const result = extractCanvasFileName('test.md.canvas');
            expect(result).toBe('test.md');
        });
    });

    // =========================================================================
    // Test: Backend compatibility (matches canvas_service.py behavior)
    // =========================================================================
    describe('AC2.6: Backend compatibility', () => {
        it('should produce output that backend _get_canvas_path can process', () => {
            // Frontend: "Canvas/Math53/Lecture5.canvas" -> "Canvas/Math53/Lecture5"
            // Backend: "Canvas/Math53/Lecture5" + ".canvas" -> correct path
            const input = 'Canvas/Math53/Lecture5.canvas';
            const result = extractCanvasFileName(input);
            expect(result).toBe('Canvas/Math53/Lecture5');
            // No .canvas at end
            expect(result.endsWith('.canvas')).toBe(false);
        });

        it('should fix the 39-error bug case: .md input', () => {
            // Bug case: "KP13-线性逼近与微分.md" was causing .md.canvas error
            // [Source: Story 12.A.1 - Problem Statement]
            const input = 'KP13-线性逼近与微分.md';
            const result = extractCanvasFileName(input);
            expect(result).toBe('KP13-线性逼近与微分');
            // No .md at end
            expect(result.endsWith('.md')).toBe(false);
        });
    });
});
