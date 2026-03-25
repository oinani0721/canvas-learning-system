/**
 * Unit tests for isValidGlobPattern helper function
 *
 * @source Story 32.6 - AC-32.6.5: 保存前验证pattern语法 (glob格式校验)
 *
 * Validation rules:
 * 1. Non-empty string
 * 2. No null bytes (\0)
 * 3. Balanced brackets [] and {}
 * 4. Valid wildcard usage (*, **)
 *
 * Test Cases:
 * - Valid patterns: **\/*.canvas, 数学/**, 托福/阅读/*.canvas
 * - Invalid patterns: empty, [unclosed, path\0with\0null
 */

import { isValidGlobPattern, GlobValidationResult } from '../src/types/settings';

describe('isValidGlobPattern', () => {
    // =========================================================================
    // AC-32.6.5.1: Rule 1 - Non-empty string
    // =========================================================================
    describe('Rule 1: Non-empty string validation', () => {
        it('should reject empty string', () => {
            const result = isValidGlobPattern('');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Pattern cannot be empty');
        });

        it('should reject whitespace-only string', () => {
            const result = isValidGlobPattern('   ');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Pattern cannot be empty');
        });

        it('should reject string with only tabs and newlines', () => {
            const result = isValidGlobPattern('\t\n');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Pattern cannot be empty');
        });

        it('should accept non-empty pattern', () => {
            const result = isValidGlobPattern('test');
            expect(result.isValid).toBe(true);
            expect(result.error).toBeUndefined();
        });
    });

    // =========================================================================
    // AC-32.6.5.2: Rule 2 - No null bytes
    // =========================================================================
    describe('Rule 2: Null byte validation', () => {
        it('should reject pattern with null byte', () => {
            const result = isValidGlobPattern('path\0with\0null');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Pattern cannot contain null bytes');
        });

        it('should reject pattern with single null byte', () => {
            const result = isValidGlobPattern('\0');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Pattern cannot contain null bytes');
        });

        it('should accept pattern without null bytes', () => {
            const result = isValidGlobPattern('normal/path/*.canvas');
            expect(result.isValid).toBe(true);
        });
    });

    // =========================================================================
    // AC-32.6.5.3: Rule 3 - Balanced brackets [] and {}
    // =========================================================================
    describe('Rule 3: Bracket balancing validation', () => {
        // Square brackets []
        it('should reject unclosed square bracket [', () => {
            const result = isValidGlobPattern('[unclosed');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Unclosed bracket [');
        });

        it('should accept balanced square brackets', () => {
            const result = isValidGlobPattern('[abc].canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept character class with range', () => {
            const result = isValidGlobPattern('[a-z]*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept empty square brackets', () => {
            const result = isValidGlobPattern('[].canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept negated character class', () => {
            const result = isValidGlobPattern('[!abc]*.canvas');
            expect(result.isValid).toBe(true);
        });

        // Curly braces {}
        it('should reject unclosed curly brace {', () => {
            const result = isValidGlobPattern('{unclosed,test');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Unclosed brace {');
        });

        it('should reject unmatched closing brace }', () => {
            const result = isValidGlobPattern('unmatched}');
            expect(result.isValid).toBe(false);
            expect(result.error).toBe('Unmatched closing brace }');
        });

        it('should accept balanced curly braces', () => {
            const result = isValidGlobPattern('{a,b,c}.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept nested curly braces', () => {
            const result = isValidGlobPattern('{a,{b,c}}.canvas');
            expect(result.isValid).toBe(true);
        });

        // Mixed brackets
        it('should accept pattern with both [] and {}', () => {
            const result = isValidGlobPattern('[a-z]{test,prod}/*.canvas');
            expect(result.isValid).toBe(true);
        });

        // Escaped brackets
        it('should accept escaped brackets', () => {
            const result = isValidGlobPattern('\\[escaped\\].canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept escaped braces', () => {
            const result = isValidGlobPattern('\\{escaped\\}.canvas');
            expect(result.isValid).toBe(true);
        });
    });

    // =========================================================================
    // AC-32.6.5.4: Rule 4 - Wildcard usage
    // =========================================================================
    describe('Rule 4: Wildcard validation', () => {
        it('should accept single asterisk wildcard', () => {
            const result = isValidGlobPattern('*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept double asterisk for recursive matching', () => {
            const result = isValidGlobPattern('**/*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept ** at beginning', () => {
            const result = isValidGlobPattern('**/test.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept ** at end', () => {
            const result = isValidGlobPattern('test/**');
            expect(result.isValid).toBe(true);
        });

        it('should accept ** in middle of path', () => {
            const result = isValidGlobPattern('path/**/file.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept question mark wildcard', () => {
            const result = isValidGlobPattern('test?.canvas');
            expect(result.isValid).toBe(true);
        });
    });

    // =========================================================================
    // Story 32.6: Chinese character support (from Dev Notes examples)
    // =========================================================================
    describe('Chinese character support', () => {
        it('should accept pattern with Chinese characters', () => {
            const result = isValidGlobPattern('数学/**/*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept Chinese folder path', () => {
            const result = isValidGlobPattern('托福/阅读/*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept pattern with Chinese keyword', () => {
            const result = isValidGlobPattern('**/*考试*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept complex Chinese path', () => {
            const result = isValidGlobPattern('笔记库/数学/线性代数/**/*.canvas');
            expect(result.isValid).toBe(true);
        });
    });

    // =========================================================================
    // Integration with validateSettings
    // =========================================================================
    describe('Integration scenarios', () => {
        it('should validate typical subject mapping patterns', () => {
            const patterns = [
                '数学/**/*.canvas',
                '托福/阅读/*.canvas',
                '**/*考试*.canvas',
                '物理/力学/*.canvas',
                'English/**',
            ];

            patterns.forEach((pattern) => {
                const result = isValidGlobPattern(pattern);
                expect(result.isValid).toBe(true);
            });
        });

        it('should reject typical invalid patterns', () => {
            const invalidPatterns = [
                { pattern: '', expectedError: 'Pattern cannot be empty' },
                { pattern: '[unclosed', expectedError: 'Unclosed bracket [' },
                { pattern: '{unclosed', expectedError: 'Unclosed brace {' },
                { pattern: 'test}', expectedError: 'Unmatched closing brace }' },
            ];

            invalidPatterns.forEach(({ pattern, expectedError }) => {
                const result = isValidGlobPattern(pattern);
                expect(result.isValid).toBe(false);
                expect(result.error).toBe(expectedError);
            });
        });
    });

    // =========================================================================
    // Edge cases
    // =========================================================================
    describe('Edge cases', () => {
        it('should accept pattern with only asterisks', () => {
            const result = isValidGlobPattern('***');
            expect(result.isValid).toBe(true);
        });

        it('should accept pattern with consecutive wildcards', () => {
            const result = isValidGlobPattern('**/**/*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept very long pattern', () => {
            const longPath = 'a/'.repeat(100) + '*.canvas';
            const result = isValidGlobPattern(longPath);
            expect(result.isValid).toBe(true);
        });

        it('should accept pattern with special characters', () => {
            const result = isValidGlobPattern('path/test-file_v2.0.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should accept pattern with dots in path', () => {
            const result = isValidGlobPattern('./relative/../path/*.canvas');
            expect(result.isValid).toBe(true);
        });

        it('should handle bracket inside character class', () => {
            const result = isValidGlobPattern('[\\]].canvas');
            expect(result.isValid).toBe(true);
        });
    });
});
