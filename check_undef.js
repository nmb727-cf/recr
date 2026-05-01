const fs = require('fs');
const path = require('path');

const dir = 'frontend/src/pages/workflows';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.tsx'));

files.forEach(file => {
  const content = fs.readFileSync(path.join(dir, file), 'utf-8');
  
  // extract all <ComponentName
  const jsxTags = [...content.matchAll(/<([A-Z][a-zA-Z0-9_]*)/g)].map(m => m[1]);
  const uniqueTags = [...new Set(jsxTags)];
  
  // extract all imports
  const imports = [...content.matchAll(/import\s+{([^}]+)}\s+from/g)].map(m => m[1]).join(', ');
  const defaultImports = [...content.matchAll(/import\s+([A-Z][a-zA-Z0-9_]*)\s+from/g)].map(m => m[1]);
  
  const allImports = imports.split(',').map(s => s.trim().split(' as ')[0]).concat(defaultImports);
  
  const undef = uniqueTags.filter(tag => 
    !allImports.includes(tag) && 
    tag !== 'React' && 
    tag !== 'Fragment' &&
    !content.includes(`function ${tag}`) &&
    !content.includes(`const ${tag} =`) &&
    !content.includes(`class ${tag}`)
  );
  
  if (undef.length > 0) {
    console.log(`${file}: Missing imports for: ${undef.join(', ')}`);
  }
});
