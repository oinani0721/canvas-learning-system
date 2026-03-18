import type { NodeTypes } from '@xyflow/react';
import { KnowledgeNode } from './KnowledgeNode';
import { ImageNode } from './ImageNode';

export const nodeTypes: NodeTypes = {
  knowledge: KnowledgeNode,
  image: ImageNode,
};
