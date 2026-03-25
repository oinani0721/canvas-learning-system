/**
 * Tests for Canvas Type Definitions
 * Story 13.2: Canvas API集成 - Task 5
 */

import {
  CanvasPresetColor,
  CanvasColor,
  CanvasNode,
  CanvasTextNode,
  CanvasFileNode,
  CanvasEdge,
  CANVAS_COLORS,
  LEARNING_COLORS,
  isTextNode,
  isFileNode,
  isLinkNode,
  isGroupNode,
  isPresetColor,
  isHexColor,
  isValidCanvasColor,
} from '../../src/types/canvas';

describe('Canvas Type Definitions', () => {
  describe('CANVAS_COLORS constant', () => {
    it('should have all 6 preset colors defined', () => {
      expect(Object.keys(CANVAS_COLORS)).toHaveLength(6);
      expect(CANVAS_COLORS['1']).toBe('Red');
      expect(CANVAS_COLORS['2']).toBe('Orange');
      expect(CANVAS_COLORS['3']).toBe('Yellow');
      expect(CANVAS_COLORS['4']).toBe('Green');
      expect(CANVAS_COLORS['5']).toBe('Cyan');
      expect(CANVAS_COLORS['6']).toBe('Purple');
    });
  });

  describe('LEARNING_COLORS constant', () => {
    it('should have semantic color mappings', () => {
      expect(LEARNING_COLORS.NOT_UNDERSTOOD).toBe('1');
      expect(LEARNING_COLORS.PARTIAL).toBe('6');
      expect(LEARNING_COLORS.UNDERSTOOD).toBe('4');
      expect(LEARNING_COLORS.PERSONAL_UNDERSTANDING).toBe('3');
    });
  });

  describe('Type Guards', () => {
    const textNode: CanvasTextNode = {
      id: 'text-1',
      type: 'text',
      x: 0,
      y: 0,
      width: 250,
      height: 60,
      text: 'Test content',
    };

    const fileNode: CanvasFileNode = {
      id: 'file-1',
      type: 'file',
      x: 100,
      y: 100,
      width: 400,
      height: 300,
      file: 'path/to/file.md',
    };

    describe('isTextNode', () => {
      it('should return true for text nodes', () => {
        expect(isTextNode(textNode)).toBe(true);
      });

      it('should return false for non-text nodes', () => {
        expect(isTextNode(fileNode)).toBe(false);
      });
    });

    describe('isFileNode', () => {
      it('should return true for file nodes', () => {
        expect(isFileNode(fileNode)).toBe(true);
      });

      it('should return false for non-file nodes', () => {
        expect(isFileNode(textNode)).toBe(false);
      });
    });

    describe('isLinkNode', () => {
      const linkNode = {
        id: 'link-1',
        type: 'link' as const,
        x: 0,
        y: 0,
        width: 400,
        height: 300,
        url: 'https://example.com',
      };

      it('should return true for link nodes', () => {
        expect(isLinkNode(linkNode)).toBe(true);
      });

      it('should return false for non-link nodes', () => {
        expect(isLinkNode(textNode)).toBe(false);
      });
    });

    describe('isGroupNode', () => {
      const groupNode = {
        id: 'group-1',
        type: 'group' as const,
        x: 0,
        y: 0,
        width: 500,
        height: 400,
        label: 'Test Group',
      };

      it('should return true for group nodes', () => {
        expect(isGroupNode(groupNode)).toBe(true);
      });

      it('should return false for non-group nodes', () => {
        expect(isGroupNode(textNode)).toBe(false);
      });
    });
  });

  describe('Color Type Guards', () => {
    describe('isPresetColor', () => {
      it('should return true for valid preset colors', () => {
        expect(isPresetColor('1')).toBe(true);
        expect(isPresetColor('2')).toBe(true);
        expect(isPresetColor('3')).toBe(true);
        expect(isPresetColor('4')).toBe(true);
        expect(isPresetColor('5')).toBe(true);
        expect(isPresetColor('6')).toBe(true);
      });

      it('should return false for invalid preset colors', () => {
        expect(isPresetColor('0')).toBe(false);
        expect(isPresetColor('7')).toBe(false);
        expect(isPresetColor('red')).toBe(false);
        expect(isPresetColor('#FF0000')).toBe(false);
      });
    });

    describe('isHexColor', () => {
      it('should return true for valid hex colors', () => {
        expect(isHexColor('#FF0000')).toBe(true);
        expect(isHexColor('#00FF00')).toBe(true);
        expect(isHexColor('#0000FF')).toBe(true);
        expect(isHexColor('#AABBCC')).toBe(true);
        expect(isHexColor('#aabbcc')).toBe(true);
      });

      it('should return false for invalid hex colors', () => {
        expect(isHexColor('FF0000')).toBe(false);
        expect(isHexColor('#FFF')).toBe(false);
        expect(isHexColor('#GGGGGG')).toBe(false);
        expect(isHexColor('1')).toBe(false);
      });
    });

    describe('isValidCanvasColor', () => {
      it('should return true for preset colors', () => {
        expect(isValidCanvasColor('1')).toBe(true);
        expect(isValidCanvasColor('6')).toBe(true);
      });

      it('should return true for hex colors', () => {
        expect(isValidCanvasColor('#FF5733')).toBe(true);
      });

      it('should return false for invalid colors', () => {
        expect(isValidCanvasColor('invalid')).toBe(false);
        expect(isValidCanvasColor('7')).toBe(false);
      });
    });
  });
});
