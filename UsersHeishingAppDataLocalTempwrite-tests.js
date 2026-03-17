// Helper script to write test files for Story 7.1
// Run with: node write-tests.js
const fs = require('fs');
const path = require('path');

const basePath = 'C:/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/tests';

// Read template files and write them
const files = {
  'unit/test_faithfulness_check.py': 'unit_fc',
  'unit/test_prompt_injection_guard.py': 'unit_pig',
  'integration/test_qa_pipeline.py': 'int_qa',
};

for (const [relPath, key] of Object.entries(files)) {
  const fullPath = path.join(basePath, relPath);
  const templatePath = path.join(basePath, `_template_${key}.py`);
  console.log(`Will write: ${fullPath}`);
}

console.log('Template writer ready. Run write-tests-exec.js instead.');
