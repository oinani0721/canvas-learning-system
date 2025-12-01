/**
 * Canvas Review System - Jest Configuration
 *
 * @version 1.0.0
 */

module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'node',
    roots: ['<rootDir>/tests'],
    testMatch: ['**/*.test.ts'],
    moduleFileExtensions: ['ts', 'js'],
    collectCoverageFrom: [
        'src/**/*.ts',
        'main.ts',
        '!**/node_modules/**'
    ],
    coverageThreshold: {
        global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80
        }
    },
    moduleNameMapper: {
        '^@types/(.*)$': '<rootDir>/src/types/$1',
        '^@managers/(.*)$': '<rootDir>/src/managers/$1',
        '^@components/(.*)$': '<rootDir>/src/components/$1',
        '^@utils/(.*)$': '<rootDir>/src/utils/$1'
    },
    transform: {
        '^.+\\.ts$': ['ts-jest', {
            tsconfig: 'tsconfig.json'
        }]
    }
};
