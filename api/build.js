const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

let frontendDir = path.resolve(__dirname, 'frontend');
if (!fs.existsSync(path.join(frontendDir, 'package.json'))) {
  frontendDir = path.resolve(__dirname, '..', 'frontend');
}

if (!fs.existsSync(path.join(frontendDir, 'package.json'))) {
  console.error('Could not locate frontend directory at:', frontendDir);
  process.exit(1);
}

console.log('Building GroundTruth.ai frontend from:', frontendDir);
execSync(`npm --prefix "${frontendDir}" install`, { stdio: 'inherit' });
execSync(`npm --prefix "${frontendDir}" run build`, { stdio: 'inherit' });
console.log('GroundTruth.ai frontend build succeeded!');
